# Setting up the Detection/Sniffer Host
In order to get the Detection host up and running, we'll need:
- Python3 & pip
- Scapy package
- Detection script copied & running


# Installing Python & Scapy
Similar to the ExaBGP host, we'll need to install Python, Scapy, and get the `detect_retransmits.py` script running:

    sudo apt-get install python3 python3-venv python3-pip -y
    pip3 install scapy --user

    # Download existing detect_retransmits.py file from GitHub
    wget https://github.com/thepacketgeek/nanog77-hackathon-demo/raw/flowspec/sniffer/detect_retransmits.py
    chmod +x detect_retransmits.py

    # IPv6 SLAAC will learn the 3001:1:ca9::/64 prefix and setup default route to 3001:1:ca9::1
    sudo ip addr add 3001:1:ca9::10/64 dev eth1
    ping -c 3 3001:1:ca9::1
    # Add default route through Router1
    sudo ip -6 route add default via 3001:1:ca9::1
    ping -c 3 3001:2::2

    # Download the test .pcap file:
    wget https://github.com/thepacketgeek/nanog77-hackathon-demo/raw/flowspec/sniffer/host_retransmit.pcap


Once this is setup, [continue with the demo](../)...
