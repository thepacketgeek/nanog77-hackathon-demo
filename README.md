# nanog77-hackathon-demo
 Demo of Traffic Exceptions for Nanog77 Hackathon

# The Lab Network
There are 4 routers and 2 Ubuntu hosts. The network has:
- IGP: OSPF & OSPFv3
- BGP: IPv6 Sessions carrying IPv4/IPv6 advertisements
- BGP Peering with the ExaBGP peer for receiving injected NLRI

![Topology Diagram](./Topology.png)

# The Scenario
- Router2 is in a Traffic Analysis segment of the network where we might have special traffic monitoring happening for troubleshooting.
- When interesting flows occur, we want to divert that traffic from the normal, steady-state path to our special Traffic Analysis segment.
- Router2 has high OSPF interface costs so it will not typically be a transit hop. Flows between Host1 and Host2 will typically transit through Router3:

![Steady State](./SteadyState.png)

- For this demo, our interesting traffic are DNS Requests/Responses for blacklisted hostnames.
- When the interesting traffic flows are detected (via our Sniffer and the detect.py script), an API call is made to the ExaBGP host.
- ExaBGP will then announce a route into the eBGP peering session with Router2.
- Router2 advertises the route NLRI to the rest of the network with a next-hop of itself, in order to draw the interesting traffic towards it.
- Router1 and Router4 install the advertised route (since the match is /32 or /128 and local-preference is high) and redirect traffic to the next-hop (in this case, Router2).


# Setting up the Demo
We'll need the following components setup to get the Demo up and running. There are guides to setup each component along with steps for verification along the way. Follow these guides in the order specified:
1. Network setup ([Router configs](./configs))
1. ExaBGP ([Host setup](./exabgp))
1. Detection/Sniffer ([Host setup](./sniffer))


## Sniffer to ExaBGP Communication

    curl --form "command=announce route 3001:0:dead:beef::/64 next-hop self" \
        http://[3001:2:e10a::10]:5000/command

### Check BGP Routes
Shows us the routes learned from ExaBGP:

    router2# show bgp ipv6 uni | b Network
    Network            Next Hop            Metric LocPrf Weight Path
    *> 3001:0:dead:beef::/64
                      3001:2:e10a::10            4294967295      0 65010 i
    *>i3001:1:ca9::/64    3001:1::1                0    100      0 i
    *> 3001:2:e10a::/64   ::                       0         32768 i
    *> 3001:99:a::/64     3001:2:e10a::10                        0 65010 i
    *> 3001:99:b::/64     3001:2:e10a::10                        0 65010 i

And advertised from Router2 to other iBGP peers:

    router4> show route protocol bgp table inet6.0 3001:0:dead:beef::/64

    inet6.0: 22 destinations, 22 routes (22 active, 0 holddown, 0 hidden)
    + = Active Route, - = Last Active, * = Both

    3001:0:dead:beef::/64
                    *[BGP/170] 00:04:32, localpref 4294967295, from 3001:2::2
                        AS path: 65010 I, validation-state: unverified
                        >  to fe80::9099:ff:fe07:1 via ge-0/0/0.0

# Automatic Detection
We're now to the point where we can enable automatic detection from our Sniffer host

## Running the script
The `detect.py` script can be run to sniff packets on the wire:

    sniffer$ ./detect.py
    Detecting DNS queries from wire...

It will analyze DNS Responses send messages to the ExaBGP host specified in the Python file.

If you want to trigger from captured packets instead, just pass a filepath to a Pcap file:

    sniffer$ ./detect.py traffic.pcap 
    INFO:root:Detecting DNS queries from traffic.pcap...
    WARNING:root:Request for badhacks.com.: 3001:10:66::5
    DEBUG:root:Sending command to ExaBGP: announce route 3001:10:66::5/128 next-hop self
    DNS Response with 3001:10:66::5 is a malicious query


## Verifying the ExaBGP Influence
Running the `detect.py` script against the included traffic.pcap file, we can see that the command was sent to ExaBGP and we now see a new route for the destination host 3001:10:66::5 that `badhacks.com` resolves to

On Router2:

    router2#show bgp ipv6 uni 3001:10:66::5/128
    Tue Oct  1 18:54:01.332 UTC
    BGP routing table entry for 3001:10:66::5/128
    Versions:
      Process           bRIB/RIB  SendTblVer
      Speaker                 51          51
    Last Modified: Oct  1 18:51:11.125 for 00:02:50
    Paths: (1 available, best #1)
      Advertised IPv6 Unicast paths to update-groups (with more than one peer):
        0.3
      Path #1: Received by speaker 0
      Advertised IPv6 Unicast paths to update-groups (with more than one peer):
        0.3
      65010
        3001:2:e10a::10 from 3001:2:e10a::10 (10.10.10.10)
        Origin IGP, localpref 4294967295, valid, external, best, group-best
        Received Path ID 0, Local Path ID 1, version 51
        Origin-AS validity: (disabled)

And Router4:

    router4> show route protocol bgp 3001:10:66::5

    inet6.0: 24 destinations, 24 routes (24 active, 0 holddown, 0 hidden)
    + = Active Route, - = Last Active, * = Both

    3001:10:66::5/128  *[BGP/170] 00:03:40, localpref 4294967295, from 3001:2::2
                        AS path: 65010 I, validation-state: unverified
                        >  to fe80::9099:ff:fe07:1 via ge-0/0/0.0

And Router1:

    router1#show bgp ipv6 uni 3001:10:66::5/128
    Tue Oct  1 18:55:20.105 UTC
    BGP routing table entry for 3001:10:66::5/128
    Versions:
      Process           bRIB/RIB  SendTblVer
      Speaker                 51          51
    Last Modified: Oct  1 18:51:11.051 for 00:04:09
    Paths: (1 available, best #1)
      Not advertised to any peer
      Path #1: Received by speaker 0
      Not advertised to any peer
      65010
          3001:2:e10a::10 (metric 1) from 3001:2::2 (2.2.2.2)
          Origin IGP, localpref 4294967295, valid, internal, best, group-best
          Received Path ID 0, Local Path ID 1, version 51