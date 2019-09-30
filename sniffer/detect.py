#!/usr/bin/env python3
import logging
import sys
from collections import Counter
from http.client import HTTPConnection
from functools import partial
from typing import Dict, NamedTuple, Optional
from urllib.parse import urlencode

from scapy.all import sniff, IP, IPv6, TCP
from scapy.packet import Packet

# A Proof-of-Concept Python script that keeps track of TCP flows
# and triggers a function when a retransmit condition is detected
# Not production ready!
#
# More details available at:
#     https://thepacketgeek.com/scapy-sniffing-with-custom-actions-part-1/
#     https://thepacketgeek.com/scapy-sniffing-with-custom-actions-part-2/
#     https://thepacketgeek.com/importing-packets-from-trace-files/


# Number of retransmits to wait until traffic redirection
RETRANSMIT_THRESHOLD = 5
EXABGP_HOST = "[3001:2:e10a::10]:5000"

logging.basicConfig(level=logging.DEBUG)


class SessionTerminated(Exception):
    """ Exception to trigger flow cleanup """


class FlowKey(NamedTuple):
    """ Flow Signature

        Hashable so it can be used as a Dict key (like in a Counter)
    """
    src_ip: str
    src_port: int
    dest_ip: str
    dest_port: int

    @classmethod
    def from_packet(cls, packet: Packet) -> Optional["FlowKey"]:
        if IP in packet and TCP in packet:
            return cls(
                packet[IP].src,
                packet[TCP].sport,
                packet[IP].dst,
                packet[TCP].dport,
            )
        if IPv6 in packet and TCP in packet:
            return cls(
                packet[IPv6].src,
                packet[TCP].sport,
                packet[IPv6].dst,
                packet[TCP].dport,
            )
        return None
    
    def __repr__(self) -> str:
        return f"{self.src_ip}:{self.src_port} <--> {self.dest_ip}:{self.dest_port}"


class FlowStatus(object):
    """ Flow Object to keep track of retransmits

        Hashable so it can be used as a Dict key (like in a Counter)
    """

    def __init__(self, flow_key: FlowKey) -> None:
        self.flow_key = flow_key
        self.retransmits = 0
        # Sequence is Tuple[seq, ack]
        self.last_sequence: Tuple(int, int) = (0, 0)

        # Keep track of whether this flow has been sent to ExaBGP yet
        self.has_been_triggered = False

    def analyze(self, packet: Packet) -> int:
        """ Check TCP sequence number of packet to detect retransmits

            Returns current TCP retransmit count
        """
        sequence = (packet[TCP].seq, packet[TCP].ack)
        if sequence > self.last_sequence:
            self.last_sequence = sequence
        else:
            self.retransmits += 1

        # Naive way to detect a session ending and delete from Current Flows
        if packet[TCP].flags.F or packet[TCP].flags.R:
            # Will not catch the final ACK, but flow will be left
            # in an untriggered state and retrans count of 0
            raise SessionTerminated()

        return self.retransmits


# Keep track of status for each Flow
flows: Dict[FlowKey, FlowStatus] = {}


def send_exabgp_command(command: str):
    """ Send a command to ExaBGP using HTTP POST and form data """
    params = urlencode({'command': command})
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain",
    }
    logging.debug(f"Sending command to ExaBGP: {command}")
    try:
        client = HTTPConnection(EXABGP_HOST)
        client.request("POST", "/command", params, headers)
    except Exception as e:
        logging.error(f"Couldn't send command to ExaBGP: {e}")


def trigger_exabgp(flow: FlowKey):
    """ Build the commands to redirect this flow and send to ExaBGP """
    # We send two commands since FlowSpec flows are unidirection and we want the
    # bidirectional traffic to go through Router2
    # This could also include the TCP src/dest ports
    command_templates = [
        "announce flow route source {src_ip}/128 destination {dest_ip}/128 redirect 6:302",
        "announce flow route source {dest_ip}/128 destination {src_ip}/128 redirect 6:302",
    ]
    for template in command_templates:
        command = template.format(src_ip=flow.src_ip, dest_ip=flow.dest_ip)
        send_exabgp_command(command)
    


def process_packet(packet: Packet) -> Optional[str]:
    """ Process the incoming packet, checking if it's a retransmit

        Since this is the `prn` callback in Scapy's `sniff()` function,
        whatever is returned will be output to the console
    """
    key = FlowKey.from_packet(packet)

    if not key:
        # Nothing for us to process
        return None

    if key not in flows:
        # Initialize a new flow
        flows[key] = FlowStatus(key)

    try:
        flow_retransmits = flows[key].analyze(packet)
        if flow_retransmits >= RETRANSMIT_THRESHOLD:
            if not flows[key].has_been_triggered:
                trigger_exabgp(key)
            flows[key].has_been_triggered = True
            return f"Flow {key!r} has {flow_retransmits} retransmits!"
    except SessionTerminated:
        logging.debug(f"Flow ended: {key!r}")
        del flows[key]


if __name__ == "__main__":
    # Check for Pcap filepath if present, otherwise sniff from wire
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = None

    # Set common kwargs for scapy.sniff()
    sniff_func = partial(sniff, prn=process_packet, filter="tcp")

    if filepath:
        logging.info(f"Detecting retransmits from {filepath}...")
        packets = sniff_func(offline=filepath)
    else:
        logging.info("Detecting retransmits from wire...")
        packets = sniff_func()
