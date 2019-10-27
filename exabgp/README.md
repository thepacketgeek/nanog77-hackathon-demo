# Setting up the ExaBGP Host
In order to get the ExaBGP host up and running, we'll need:
- Python3 & pip
- ExaBGP and Flask packages
- Network setup to talk with Router2
- ExaBGP Config


## Commands for ExaBGP Host
This should work with copy/paste; confirmations are used along the way for troubleshooting

    # Install Python/Pip/Etc on Ubuntu
    sudo apt-get install python3 python3-venv python3-pip -y
    pip3 install exabgp --user
    pip3 install flask --user

    # Confirm Python installation
    python3 -V
    pip3 list | grep exabgp
    pip3 list | grep Flask

    # Setup networking
    sudo ip addr add 3001:2:e10a::10/64 dev eth1
    # Test networking
    ping -c 3 3001:2:e10a::2
    # Default route through Router2
    ping -c 3 3001:1::1

    # Add ExaBGP API (using Flask)
    # You can edit and copy/paste this block to update the http_api.py file
    echo "from flask import Flask, request
    from sys import stdout

    app = Flask(__name__)

    # Setup a command route to listen for prefix advertisements 
    @app.route('/command', methods=['POST'])
    def command():
        command = request.form['command']
        stdout.write('%s\n' % command)
        stdout.flush()
        return '%s\n' % command

    if __name__ == '__main__':
        app.run(host='3001:2:e10a::10', port=5000)
    " > ~/http_api.py
    
    # Add exabgp conf
    # You can edit and copy/paste this block to replace the ExaBGP config
    echo "process http-api {
        run /usr/bin/python3 /home/tesutocli/http_api.py;
        encoder json;
    }

    neighbor 3001:2:e10a::2 {
        router-id 10.10.10.10;
        local-address 3001:2:e10a::10;
        local-as 65010;
        peer-as 65000;

        family {
            ipv4 unicast;
            ipv6 unicast;
        }

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


# Confirming Setup

## Check BGP Peers
We can see the BGP peering from Router2 to ExaBGP:

    router2#show bgp ipv6 unicast summary | b Neighbor
    Neighbor        Spk    AS MsgRcvd MsgSent   TblVer  InQ OutQ  Up/Down  St/PfxRcd
    3001:1::1         0 65000      62      65       10    0    0 00:56:50          1
    3001:2:e10a::10   0 65010      12       8       10    0    0 00:00:45          2
    3001:3::3         0 65000     128     120       10    0    0 00:56:45          0
    3001:4::4         0 65000     128     120       10    0    0 00:56:34          0


## Check ExaBGP Test Routes
And we should also see the test routes announced by ExaBGP:

    router2#show bgp ipv6 uni | b Network
    Network            Next Hop            Metric LocPrf Weight Path
    *>i3001:1:ca9::/64    3001:1::1                0    100      0 i
    *> 3001:2:e10a::/64   ::                       0         32768 i
    *> 3001:99:a::/64     3001:2:e10a::10                        0 65010 i
    *> 3001:99:b::/64     3001:2:e10a::10                        0 65010 i

