# nanog77-hackathon-demo
 Demo of Traffic Exceptions for Nanog77 Hackathon

# The Lab Network
There are 4 routers and 2 Ubuntu hosts. The network has:
- IGP: OSPF & OSPFv3
- BGP: IPv6 Sessions carrying IPv4/IPv6 advertisements
- BGP Peering with the ExaBGP peer for receiving injected NLRI

![Topology Diagram](./Topology.png)


# Setting up the Demo
We'll need the following components setup to get the Demo up and running. There are guides to setup each component along with steps for verification along the way. Follow these guides in the order specified:
1. Network setup ([Router configs](./configs))
1. ExaBGP ([Host setup](./exabgp))
1. Detection/Sniffer ([Host setup](./sniffer))
