# nanog77-hackathon-demo
 Demo of Traffic Exceptions for Nanog77 Hackathon

![Topology Diagram](./Topology.png)

# Setting up the ExaBGP Host
In order to get the ExaBGP Host up and running, we'll need:
- Python3 & pip
- ExaBGP
- Network setup to talk with Router2
- ExaBGP Config


## Commands for ExaBGP Host
This should work with copy/paste; confirmations are used along the way for troubleshooting

    # Ubuntu install Python/Pip/Etc
    sudo apt-get install python3 python3-venv python3-pip -y
    pip3 install exabgp --user

    # Confirm Python installations
    python3 -V
    pip3 list | grep exabgp

    # Setup networking
    sudo ip addr add 3001:2:e10a::10/64 dev eth1
    # Test networking
    ping -c 3 3001:2:e10a::2
    ping -c 3 3001:1::1

    # Add exabgp conf
    # You can edit and copy/paste this block to replace the ExaBGP config
    echo "neighbor 3001:2:e10a::2 {
        router-id 10.10.10.10;
        local-address 3001:2:e10a::10;
        local-as 65010;
        peer-as 65000;

        announce {
            ipv6 {
                # Test routes to confirm ExaBGP advertisement is working
                unicast 3001:99:a::/64 next-hop self;
                unicast 3001:99:b::/64 next-hop self;
            }
        }
    }
    " > ~/exabgp-conf.ini

    # Run ExaBGP (Ctrl+C to stop)
    # You can update the config above and restart the process to reload config
    python3 -m exabgp ~/exabgp-conf.ini


# Router Configs
- [Router1](./configs/router1.iosxr.cfg) (IOSXR)
- [Router2](./configs/router2.iosxr.cfg) (IOSXR)

# Confirming Setup

## Router2

### Check BGP Peers
    show bgp ipv6 unicast summary | b Neighbor

Should ouput something similar to:

    Neighbor        Spk    AS MsgRcvd MsgSent   TblVer  InQ OutQ  Up/Down  St/PfxRcd
    3001:1::1         0 65000      45      47        6    0    0 00:41:38          1
    3001:2:e10a::10   0 65010      53      52        6    0    0 00:08:09          2

    show route ipv6 bgp

### Check BGP Routes

Shows us the Router 1 connection and ExaBGP test routes:

    B    3001:1:ca9::/64
        [200/0] via 3001:1::1, 00:42:43
    B    3001:99:a::/64
        [20/0] via 3001:2:e10a::10, 00:09:19
    B    3001:99:b::/64
        [20/0] via 3001:2:e10a::10, 00:09:19
