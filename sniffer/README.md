# Setting up the Detection/Sniffer Host
In order to get the Detection host up and running, we'll need:
- Python3 & pip
- Scapy package
- Detection script copied & running


# Installing Python & Scapy
Similar to the ExaBGP host, we'll need to install Python, Scapy, and get the `detect.py` script running:

    sudo apt-get install python3 python3-venv python3-pip -y
    pip3 install scapy --user

    # Create python file
    touch ~/detect.py
    chmod +x detect.py
    # Copy and paste the file contents from GitHub

    # IPv6 SLAAC will learn the 3001:1:ca9::/64 prefix and setup default route to 3001:1:ca9::1
    ping -c 3 3001:1:ca9::1
    # Default route through Router1
    ping -c 3 3001:2::2

    # Download the test .pcap file:
    wget -O traffic.pcap https://github.com/thepacketgeek/nanog77-hackathon-demo/raw/basic-bgp/sniffer/traffic.pcap
