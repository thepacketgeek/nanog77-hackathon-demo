# Setting up the Network

In order to get the ExaBGP host up and running, we'll need:
- Tesuto Devices Added
- Connections between topology devices
- Router configs applied

## Import Tesuto Config
I have attached a [Tesuto topology export](nanog77-hackathon-demo.export) that you can import once logged into Tesuto

![Tesuto Import](tesuto-import.png)


## Apply Router Configs

There are configs for all 4 routers included, you should be able to copy/paste them onto the devices once you're connected via the Tesuto console or SSH:

- **Router1**: vMX (Junos 18.4R1) ([config](router1.junos.cfg))
- **Router2**: vMX (Junos 18.4R1) ([config](router2.junos.cfg))
- **Router3**: CSR1000v (IOS-XE 16.08.1a) ([config](router3.iosxe.cfg))
- **Router4**: CSR1000v (IOS-XE 16.08.1a) ([config](router4.iosxe.cfg))

