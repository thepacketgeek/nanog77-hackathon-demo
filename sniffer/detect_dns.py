#!/usr/bin/env python3
import logging
import sys
from collections import Counter
from http.client import HTTPConnection
from functools import partial
from typing import Dict, NamedTuple, Optional
from urllib.parse import urlencode

from scapy.all import sniff, IP, UDP, DNS
from scapy.packet import Packet

# A Proof-of-Concept Python script that monitors for malicious
# DNS requests/requests and triggers a function when this condition is detected
# Not production ready!
#
# More details available at:
#     https://thepacketgeek.com/scapy-sniffing-with-custom-actions-part-1/
#     https://thepacketgeek.com/scapy-sniffing-with-custom-actions-part-2/
#     https://thepacketgeek.com/importing-packets-from-trace-files/


EXABGP_HOST = "[3001:2:e10a::10]:5000"

logging.basicConfig(level=logging.DEBUG)


BAD_QUERIES = {
    "badhacks.com.",
    "malicious-mail-order.net.",
}


def analyze(packet: Packet) -> Optional[str]:
    """ Check for malicious DNS query/response

        If we return a DNS response with a malicious name:
            we want to redirect the traffic destined to that host
            to our traffic analysis segment

        If this packet matches, return the destination IP address
    """
    if DNS in packet:
        if (
            packet[DNS].qr  # Is this a Response?
            and packet[DNS].qd.qname.decode() in BAD_QUERIES
        ):
            logging.warning(f"Request for {packet[DNS].qd.qname.decode()}: {packet[DNS].an.rdata}")
            return packet[DNS].an.rdata
        


def trigger_exabgp(dst_ip: str):
    """ Receive a destination IP address and send to ExaBGP """
    command_template = "announce route {dst_ip}/128 next-hop self"
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
    """ Process the incoming packet

        Since this is the `prn` callback in Scapy's `sniff()` function,
        whatever is returned will be output to the console
    """
    dest_ip = analyze(packet)
    if dest_ip:
        trigger_exabgp(dest_ip)
        return f"DNS Response with {dest_ip} is a malicious query"


if __name__ == "__main__":
    # Check for Pcap filepath if present, otherwise sniff from wire
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = None

    # Set common kwargs for scapy.sniff()
    sniff_func = partial(sniff, prn=process_packet, filter="udp port 53")

    if filepath:
        logging.info(f"Detecting DNS queries from {filepath}...")
        packets = sniff_func(offline=filepath)
    else:
        logging.info("Detecting DNS queries from wire...")
        packets = sniff_func()
