# -*- coding: utf-8 -*-
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import eventlet
from log import Log
from remote import RemoteComputer, RemoteComputerManager
import queue
from obs import Obs
import configparser
import json
import csv
import threading
import time

# Read the configuration
config = configparser.RawConfigParser()
config.read('config.conf')
config = config['DEFAULT']

# Configure our web server
eventlet.monkey_patch()
app = Flask(__name__)
app.debug = True
socketio = SocketIO(app, async_mode="eventlet")
 
# Create event queue
event_queue = queue.Queue()

def main():
   # And connect to obs
    obs = Obs("127.0.0.1", 4444, "", event_queue)
    # The load the user list

    # Read user data
    remote_computers = []
    with open('users.csv', 'r') as user_file:
        user_reader = csv.reader(user_file)
        # Skip header
        next(user_reader, None)
        for user_line in user_reader:
            host, user = user_line
            remote_computers.append(RemoteComputer(host, user))

    # Create the preview objects
    previews = []
    for i in range(config.getint('number_of_previews')):
        log = Log(config.getint('history_length'), event_queue)
        log.onMessage(lambda message, i=i, log=log: send_log(i, log))
        previews.append((10001 + i, log))

    # Create the preview manager
    command = ['ssh', '-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no', '{user}@{host}',
            'bash', '-s', '--', '{user}', 'udp://{master_host}:{local_port}'];
    with open('remote-script.sh', 'r') as script_file:
        script = bytearray(script_file.read(), 'utf-8')
    remote_manager = RemoteComputerManager(remote_computers, previews, config.get('master_host'), command, script)

    @app.route('/')
    def index():
        return render_template('index.html')

    @socketio.on('client_connected')
    def handle_client_connect_event(json):
        emit('welcome', { 'number_of_previews': config.getint('number_of_previews') })

    @socketio.on('change_preview')
    def handle_change_preview_event(json):
        event_queue.put(lambda json=json: remote_manager.connect(json['preview_number'] - 1, json['remote_number']))

    def send_log(preview_number, log):
        socketio.emit('log', { 'preview_number': preview_number, 'log': log.get_messages() }, broadcast=True);

    def hearbeat():
        while True:
            #print('Beat')
            #socketio.emit('beat', {})
            time.sleep(1)
    thread = threading.Thread(target=hearbeat)
    thread.daemon = True
    thread.start()

def event_loop():
    while True:
        try:
            #socketio.emit('log', { 'preview_number': 1, 'log': ['moi'] });
            task = event_queue.get_nowait()
            task()
        except queue.Empty:
            # No more tasks to handle
            #time.sleep(0.1)
            eventlet.sleep()

if __name__ == '__main__':
    #event_thread = threading.Thread(target=event_loop)
    #event_thread.daemon = True
    #event_thread.start()
    eventlet.spawn(event_loop)

    event_queue.put(main)
    #main()

    socketio.run(app)
