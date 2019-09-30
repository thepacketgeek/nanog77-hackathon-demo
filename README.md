# nanog77-hackathon-demo
 Demo of Traffic Exceptions for Nanog77 Hackathon

# The Scenario
Router2 is in a Traffic Analysis segment of the network where we have traffic monitors and packet captures happening in order to 

# The Lab Network
The network has:
- 4 Routers
  - OSPFv3, BGP peerings over IPv6 (carrying IPv6 Unicast & FlowSpec)
- 1 ExaBGP Host
  - Peering with Router2 to inject FlowSpec NLRI
- 1 Sniffer Host
  - Used to trigger on TCP Retransmit traffic
- 2 Test Hosts
  - The demo is trying to influence traffic between these hosts

![Topology Diagram](./Topology.png)


# Setting up the Demo
We'll need the following components setup to get the Demo up and running. There are guides to setup each component along with steps for verification along the way. Follow these guides in the order specified:
1. Network setup ([Router configs](./configs))
1. ExaBGP ([Host setup](./exabgp))
1. Sniffer ([Host setup](./sniffer))


# Setting up the test hosts
We need to get our test hosts ready to communicate using the network we've just built

Host1:

    # Install Traceroute
    sudo apt-get install traceroute
    # Setup networking
    sudo ip addr add 3001:1:a::10/64 dev eth1
    sudo ip addr add 3001:1:a::20/64 dev eth1
    sudo ip -6 route add default via 3001:1:a::1
    # Test networking
    ping -c 3 3001:4:b::4
    ping -c 3 3001:2:e10a::2


Host2:

    sudo ip addr add 3001:4:b::10/64 dev eth1
    sudo ip -6 route add default via 3001:4:b::1
    # Test networking
    ping -c 3 3001:1:a::10


# Testing traffic influence
Ok, now let's see what FlowSpec can do for us.

## Steady State
We can see there are currently no FlowSpec rules on Router1:

    router1> show route table inet6flow.0
    inet6flow.0: 1 destinations, 1 routes (0 active, 0 holddown, 1 hidden)

Nor Router4:

    router4#show bgp ipv6 flow
    router4#

![SteadyStateTrafficFlow](SteadyState.png)


Due to the high OSPF cost of Router2's interface, that will not be used for transit between Router1 and Router4:

    host1$ traceroute -s 3001:1:a::10 3001:4:b::10
    traceroute to 3001:4:b::10 (3001:4:b::10), 30 hops max, 80 byte packets
     1  3001:1:a::1 (3001:1:a::1)  6.959 ms  6.915 ms  6.888 ms
     2  3001:13::3 (3001:13::3)  14.177 ms  14.120 ms  14.123 ms
     3  3001:34::4 (3001:34::4)  14.091 ms  14.062 ms  14.044 ms
     4  3001:4:b::10 (3001:4:b::10)  22.202 ms  22.186 ms  22.169 ms
    
    $ traceroute -s 3001:1:a::20 3001:4:b::10
    traceroute to 3001:4:b::10 (3001:4:b::10), 30 hops max, 80 byte packets
     1  3001:1:a::1 (3001:1:a::1)  7.885 ms  7.730 ms  7.756 ms
     2  3001:13::3 (3001:13::3)  23.147 ms  23.121 ms  23.099 ms
     3  3001:34::4 (3001:34::4)  23.053 ms  22.991 ms  23.010 ms
     4  3001:4:b::10 (3001:4:b::10)  22.994 ms  22.963 ms  22.946 ms


## Traffic Exception, FlowSpec rule injected
From Host1, we'll simulate a FlowSpec announcement (that would typically be coming from Sniffer):

    curl --form "command=announce flow route source 3001:1:a::10/128 destination 3001:4:b::10/128 redirect 6:302" \
        http://[3001:2:e10a::10]:5000/command

And we can see the FlowSpec rule on Router1:

    router1> show route table inet6flow.0

    inet6flow.0: 1 destinations, 1 routes (1 active, 0 holddown, 0 hidden)
    + = Active Route, - = Last Active, * = Both

    3001:1:a::10/128,3001:4:b::10/128/term:1
                    *[BGP/170] 00:38:34, localpref 65000
                        AS path: 65010 I, validation-state: unverified
                        >  to 3001:2::2
    router1> show firewall filter __flowspec_default_inet6__

    Filter: __flowspec_default_inet6__
    Counters:
    Name                                                Bytes              Packets
    3001:4:b::10/128,3001:1:a::10/128                    1760                   22

And Router4:
   
   router4#show bgp ipv6 flow | b Network
        Network          Next Hop            Metric LocPrf Weight Path
    * i  Dest:3001:4:B::10/0-128,Source:3001:1:A::10/0-128
                        3001:2::2

Viola!!! See that the traffic from ::10 is now being diverted through Router2  (and our ::20 traffic continues transiting through Router3) :D

    $ traceroute -s 3001:1:a::10 3001:4:b::10
    traceroute to 3001:4:b::10 (3001:4:b::10), 30 hops max, 80 byte packets
     1  3001:1:a::1 (3001:1:a::1)  2.321 ms  2.241 ms  2.208 ms
     2  3001:12::2 (3001:12::2)  9.576 ms  9.544 ms  9.499 ms
     3  3001:24::4 (3001:24::4)  21.666 ms  21.637 ms  21.618 ms
     4  * 3001:4:b::10 (3001:4:b::10)  21.559 ms  21.502 ms

    $ traceroute -s 3001:1:a::20 3001:4:b::10
    traceroute to 3001:4:b::10 (3001:4:b::10), 30 hops max, 80 byte packets
     1  3001:1:a::1 (3001:1:a::1)  7.527 ms  7.399 ms  7.399 ms
     2  3001:13::3 (3001:13::3)  14.992 ms  14.953 ms  14.955 ms
     3  3001:34::4 (3001:34::4)  30.839 ms  30.804 ms  30.805 ms
     4  3001:4:b::10 (3001:4:b::10)  22.710 ms  22.618 ms  22.583 ms

![FlowSpec Traffic Influence](FlowSpecResult.png)

Note that the FlowSpec route is unidirectional, so return traffic from Host2 will still transit through Router2. Since we most likely want the bidirectional flow to transit Router2 for analysis, we'd want our traffic trigger to advertise both directions of the flow to ExaBGP. E.g.:

    curl --form "command=announce flow route source 3001:4:b::10/128 destination 3001:1:a::10/128 redirect 6:302" \
        http://[3001:2:e10a::10]:5000/command

You can remove the Flowspec route with:

    curl --form "command=withdraw flow route source 3001:1:a::10/128 destination 3001:4:b::10/128 redirect 6:302" \
         http://[3001:2:e10a::10]:5000/command

# References
A big thanks to all the tools and articles that helped make this demo possible:
- [ExaBGP](https://github.com/Exa-Networks/exabgp)
- [Tesuto](https://www.tesuto.com/) - Network Emulation
- ["BGP Flowspec redirect with ExaBGP" by Tim Gregory](https://tgregory.org/2018/01/31/bgp-flowspec-redirect-with-exabgp/)
- ["Using BGP Flowspec (DDoS Mitigation)"](https://archive.nanog.org/sites/default/files/tuesday_general_ddos_ryburn_63.16.pdf) [[video](https://www.youtube.com/watch?v=ttDUoDf6xzM&t=1935s)]
- ["BGP Flowspec Tutorial" - Mark Brochu](https://meetings.internet2.edu/media/medialibrary/2018/10/19/20181015-brochu-BGP-Flowspec.pdf)
- ["Controlling ExaBGP: Interacting from the API"](https://github.com/Exa-Networks/exabgp/wiki/Controlling-ExaBGP-:-interacting-from-the-API)

And some of my own articles that came in handy:
- [Influence Routing Decisions with Python and ExaBGP](https://thepacketgeek.com/influence-routing-decisions-with-python-and-exabgp/)
- Scapy: Per-packet actions [part 1](https://thepacketgeek.com/scapy-sniffing-with-custom-actions-part-1/), [part 2](https://thepacketgeek.com/scapy-sniffing-with-custom-actions-part-2/)
- [Give ExaBGP an HTTP API](https://thepacketgeek.com/give-exabgp-an-http-api-with-flask/)