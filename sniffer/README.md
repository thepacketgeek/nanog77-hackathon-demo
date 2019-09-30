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
    sudo ip addr add 3001:1:ca9::10/64 dev eth1
    ping -c 3 3001:1:ca9::1
    # Add default route through Router1
    sudo ip -6 route add default via 3001:1:ca9::1
    ping -c 3 3001:2::2

    # Download the test .pcap file:
    wget https://github.com/thepacketgeek/nanog77-hackathon-demo/blob/flowspec/sniffer/host_retransmit.pcap

    # Run the detect.py script
    sudo ./detect.py host_retransmit.pcap


## Running the script
The `detect.py` script can be run to sniff packets on the wire:

    $ ./detect.py
    Detecting retransmits from wire...

It will analyze sniffed TCP flows for retransmits and send messages them to the ExaBGP host specified in the Python file.

If you want to trigger from captured packets instead, just pass a filepath to a Pcap file:

    $ ./detect.py host_retransmit.pcap
    INFO:root:Detecting retransmits from host_retransmit.pcap...
    reading from file host_retransmit.pcap, link-type EN10MB (Ethernet)
    DEBUG:root:Sending command to ExaBGP: announce flow route source 3001:4:b::10/128 destination 3001:1:a::10/128 redirect 6:302
    DEBUG:root:Sending command to ExaBGP: announce flow route source 3001:1:a::10/128 destination 3001:4:b::10/128 redirect 6:302
    Flow 3001:4:b::10:443 <--> 3001:1:a::10:58719 has 5 retransmits!
    Flow 3001:4:b::10:443 <--> 3001:1:a::10:58719 has 5 retransmits!
    Flow 3001:4:b::10:443 <--> 3001:1:a::10:58719 has 5 retransmits!
    Flow 3001:4:b::10:443 <--> 3001:1:a::10:58719 has 5 retransmits!
    Flow 3001:4:b::10:443 <--> 3001:1:a::10:58719 has 5 retransmits!
    DEBUG:root:Flow ended: 3001:4:b::10:443 <--> 3001:1:a::10:58719
    DEBUG:root:Flow ended: 3001:1:a::10:58719 <--> 3001:4:b::10:443
    DEBUG:root:Flow ended: 3001:1:a::10:58719 <--> 3001:4:b::10:443
    


## Verifying the ExaBGP Influence
Running the `detect.py` script against the included host_retransmit.pcap file, we can see that the command was sent to ExaBGP and we now see a new FlowSpec route for the destination host 63.116.243.97

On Router2:

    router2> show route protocol bgp table inet6flow.0

    inet6flow.0: 2 destinations, 2 routes (2 active, 0 holddown, 0 hidden)
    + = Active Route, - = Last Active, * = Both

    3001:1:a::10/128,3001:4:b::10/128/term:1
                    *[BGP/170] 00:06:12, localpref 65000, from 3001:2:e10a::10
                        AS path: 65010 I, validation-state: unverified
                        Receive
    3001:4:b::10/128,3001:1:a::10/128/term:2
                    *[BGP/170] 00:06:12, localpref 65000, from 3001:2:e10a::10
                        AS path: 65010 I, validation-state: unverified
                        Receive
