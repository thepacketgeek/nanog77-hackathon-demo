# Installing Python & Scapy
Similar to the ExaBGP host, we'll need to install Python, Scapy, and get networking setup:

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
    wget https://packetlife.net/media/captures/TCP_SACK.cap
    # Rename file to .pcap for Scapy
    mv TCP_SACK.{,p}cap

    # Run the detect.py script
    sudo ./detect.py TCP_SACK.pcap


## Running the script
The `detect.py` script can be run to sniff packets on the wire:

    $ ./detect.py
    Detecting retransmits from wire...

It will analyze sniffed TCP flows for retransmits and send messages them to the ExaBGP host specified in the Python file.

If you want to trigger from captured packets instead, just pass a filepath to a Pcap file:

    $ ./detect.py TCP_SACK.cap
    Detecting retransmits from TCP_SACK.cap...
    reading from file TCP_SACK.cap, link-type EN10MB (Ethernet)
    Flow from 192.168.1.3:58816 --> 63.116.243.97:80 has 3 retransmits!
    Flow from 192.168.1.3:58816 --> 63.116.243.97:80 has 4 retransmits!
    Flow from 192.168.1.3:58816 --> 63.116.243.97:80 has 5 retransmits!
    Flow from 192.168.1.3:58816 --> 63.116.243.97:80 has 5 retransmits!