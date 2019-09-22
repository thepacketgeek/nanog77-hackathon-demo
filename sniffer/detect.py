#!/usr/bin/env python3
import logging
import sys
from collections import Counter
from http.client import HTTPConnection
from functools import partial
from typing import Dict, NamedTuple, Optional
from urllib.parse import urlencode

from scapy.all import sniff, IP, TCP
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
RETRANSMIT_THRESHOLD = 2
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
    dst_ip: str
    dst_port: int

    @classmethod
    def from_packet(cls, packet: Packet) -> Optional["FlowKey"]:
        if IP in packet and TCP in packet:
            return cls(
                packet[IP].src,
                packet[TCP].sport,
                packet[IP].dst,
                packet[TCP].dport,
            )
        return None


class FlowStatus(object):
    """ Flow Object to keep track of retransmits

        Hashable so it can be used as a Dict key (like in a Counter)
    """

    def __init__(self, flow_key: FlowKey) -> None:
        self.flow_key = flow_key
        self.retransmits = 0
        # Sequence is Tuple[seq, ack]
        self.last_sequence: Tuple(int, int) = (0, 0)

    def analyze(self, packet: Packet) -> int:
        """ Check TCP sequence number of packet to detect retransmits

            Returns current TCP retransmit count
        """
        sequence = (packet[TCP].seq, packet[TCP].ack)
        if sequence > self.last_sequence:
            self.last_sequence = sequence
        else:
            self.retransmits += 1

        # TODO: Handle TCP Flow end to reset the counter
        #       raise SessionTerminated()

        return self.retransmits


# Keep track of status for each Flow
flows: Dict[FlowKey, FlowStatus] = {}


def trigger_exabgp(dst_ip: str):
    """ Receive a destination IP address and send to ExaBGP """
    command_template = "announce route {dst_ip}/32 next-hop 3.3.3.3"
    command = command_template.format(dst_ip=dst_ip)
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
        if flow_retransmits > RETRANSMIT_THRESHOLD:
            trigger_exabgp(key.dst_ip)
            return (
                f"Flow from {key.src_ip}:{key.src_port} --> "
                f"{key.dst_ip}:{key.dst_port} "
                f"has {flow_retransmits} retransmits!"
            )
    except SessionTerminated:
        # Cleanup FlowStatus from flows Dict
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
