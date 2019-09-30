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
    pip3 list | grep flask

    # Setup networking
    sudo ip addr add 3001:2:e10a::10/64 dev eth1
    sudo ip -6 route add default via 3001:2:e10a::2
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
            ipv4 flow;
            ipv6 unicast;
            ipv6 flow;
        }
        announce {
            ipv6 {
                # Test routes to confirm ExaBGP advertisement is working
                unicast 3001:99:a::/64 next-hop self;
                unicast 3001:99:b::/64 next-hop self;
            }
        }

        # Static FlowSpec test to confirm ExaBGP advertisement is working
        # Uncomment to add this flow at ExaBGP startup time
        # flow {
        #     route TEST {
        #         match {
        #             source 3001:99:a::10/128;
        #             destination 3001:99:b::10/128;
        #         }
        #         then {
        #             redirect 6:302;
        #         }
        #     }
        # }
    }
    " > ~/exabgp-conf.ini

    # Run ExaBGP (Ctrl+C to stop)
    # You can update the config above and restart the process to reload config
    python3 -m exabgp ~/exabgp-conf.ini


# Confirming Setup

## Router2 Peering

### Check BGP Peers
    router2> show bgp summary
    ...
    Peer                     AS      InPkt     OutPkt    OutQ   Flaps Last Up/Dwn State...
    3001:2:e10a::10       65010         38         36       0       4       16:27 Establ
        inet6.0: 2/2/2/0
        inet6flow.0: 0/0/0/0

### Check BGP Routes

    router2> show route protocol bgp all table inet6

    inet6.0: 25 destinations, 25 routes (25 active, 0 holddown, 0 hidden)
    + = Active Route, - = Last Active, * = Both

    3001:99:a::/64     *[BGP/170] 00:18:00, localpref 100
                        AS path: 65010 I, validation-state: unverified
                        >  to 3001:2:e10a::10 via ge-0/0/9.0
    3001:99:b::/64     *[BGP/170] 00:17:59, localpref 100
                        AS path: 65010 I, validation-state: unverified
                        >  to 3001:2:e10a::10 via ge-0/0/9.0
