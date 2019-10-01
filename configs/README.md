# Setting up the Network

In order to get the ExaBGP host up and running, we'll need:
- Tesuto Devices Added
- Connections between topology devices
- Router configs applied

## Import Tesuto Config
I have attached a [Tesuto topology export](nanog77-hackathon-basic-demo.export) that you can import once logged into Tesuto

![Tesuto Import](tesuto-import.png)


## Apply Router Configs

There are configs for all 4 routers included, you should be able to copy/paste them onto the devices once you're connected via the Tesuto console or SSH:

- Router1: IOS-XRv (IOS-XR 6.5.3) ([config](router1.iosxr.cfg))
- Router2: IOX-XRv (IOS-XR 6.5.3) ([config](router2.iosxr.cfg))
- Router3: vMX (Junos 18.4R1) ([config](router3.junos.cfg))
- Router4: vMX (Junos 18.4R1) ([config](router4.junos.cfg))

