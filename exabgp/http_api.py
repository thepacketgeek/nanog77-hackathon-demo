from flask import Flask, request
from sys import stdout

app = Flask(__name__)

# Setup a command route to listen for prefix advertisements 
@app.route('/command', methods=['POST'])
def command():
    command = request.form['command']
    # Write command to stdout for ExaBGP process to consume
    stdout.write('%s\n' % command)
    stdout.flush()
    return '%s\n' % command

if __name__ == '__main__':
    app.run(host='3001:2:e10a::10', port=5000)