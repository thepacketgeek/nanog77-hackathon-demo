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


## Verifying the ExaBGP Influence
Running the `detect.py` script against the included TCP_SACK.pcap file, we can see that the command was sent to ExaBGP and we now see a new route for the destination host 63.116.243.97

On Router2:

    # show bgp ipv4 unicast | b Network
    Sun Sep 22 01:16:14.785 UTC
    Network            Next Hop            Metric LocPrf Weight Path
    *>i1.1.1.1/32         3001:1::1                0    100      0 i
    *> 2.2.2.2/32         0.0.0.0                  0         32768 i
    *>i3.3.3.3/32         3.3.3.3                       100      0 i
    *>i4.4.4.4/32         4.4.4.4                       100      0 i
    *  63.116.243.97/32   3.3.3.3                                0 65010 i

    Processed 5 prefixes, 5 paths
