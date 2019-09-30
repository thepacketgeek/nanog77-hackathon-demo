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
    3001:1::1             65000        183        198       0       0     1:20:53 Establ
    inet.0: 0/1/1/0
    inet6.0: 0/0/0/0
    3001:2:e10a::10       65010         13          5       0       2        2:28 Establ
    inet6.0: 2/3/2/0
    inet6flow.0: 0/0/0/0

### Check BGP Routes

    router2> show route protocol bgp all table inet6

    inet6.0: 21 destinations, 21 routes (20 active, 0 holddown, 1 hidden)
    + = Active Route, - = Last Active, * = Both

    3001:0:dead:beef::/64
                        [BGP ] 00:00:27, from 3001:2:e10a::10
                        AS path: 65010 I, validation-state: unverified
                        >  to 3001:3::3 via ge-0/0/9.0
    3001:99:a::/64     *[BGP/170] 00:01:53, localpref 100
                        AS path: 65010 I, validation-state: unverified
                        >  to 3001:2:e10a::10 via ge-0/0/9.0
    3001:99:b::/64     *[BGP/170] 00:01:53, localpref 100
                        AS path: 65010 I, validation-state: unverified
                        >  to 3001:2:e10a::10 via ge-0/0/9.0

### Check the FlowSpec routes:

Router2:

    router2> show route protocol bgp table inet6flow.0

    inet6flow.0: 1 destinations, 1 routes (1 active, 0 holddown, 0 hidden)
    + = Active Route, - = Last Active, * = Both

    3001:4:b2::10/128,3001:1:a1::10/128/term:1
                    *[BGP/170] 00:00:14, localpref 100, from 3001:2:e10a::10
                        AS path: 65010 I, validation-state: unverified
                        >  to 3001:3::3

Router1:

    router1> show route protocol bgp table inet6flow

    inet6flow.0: 2 destinations, 2 routes (1 active, 0 holddown, 1 hidden)
    + = Active Route, - = Last Active, * = Both

    3001:99:b::10/128,3001:99:a::10/128/term:1
                    *[BGP/170] 00:02:30, localpref 100, from 3001:2::2
                        AS path: 65010 I, validation-state: unverified
                        >  to 3001:3::3

Router4:
    
    router4#show bgp ipv6 flowspec
    BGP table version is 2, local router ID is 4.4.4.4
    Status codes: s suppressed, d damped, h history, * valid, > best, i - internal,
                r RIB-failure, S Stale, m multipath, b backup-path, f RT-Filter,
                x best-external, a additional-path, c RIB-compressed,
                t secondary path, L long-lived-stale,
    Origin codes: i - IGP, e - EGP, ? - incomplete
    RPKI validation codes: V valid, I invalid, N Not found

        Network          Next Hop            Metric LocPrf Weight Path
    * i  Dest:3001:99::/0-32,Source:3001:99:1::10/0-128
                        3001:3::3                     100      0 65010 i
    *>i  Dest:3001:99:B::10/0-128,Source:3001:99:A::10/0-128
                        3001:3::3                     100      0 65010 i