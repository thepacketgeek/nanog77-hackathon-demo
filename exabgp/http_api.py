#!/usr/bin/env python3

# A Proof-of-Concept Python script that allows ExaBGP to receive and
# process commands received in HTTP POST requests
# Not production ready!
#
# More details available at:
#     https://thepacketgeek.com/give-exabgp-an-http-api-with-flask/

from flask import Flask, request
from sys import stdout

app = Flask(__name__)

# Setup a command route to listen for prefix advertisements
@app.route("/command", methods=["POST"])
def command():
    command = request.form["command"]
    # Write command to stdout for ExaBGP process to consume
    stdout.write(f"{command}\n")
    stdout.flush()
    return f"{command}\n"


if __name__ == "__main__":
    app.run(host="3001:2:e10a::10", port=5000)

