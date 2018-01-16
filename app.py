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

config = configparser.RawConfigParser()
config.read('config.conf')
config = config['DEFAULT']

eventlet.monkey_patch()

app = Flask(__name__)
app.debug = True
socketio = SocketIO(app)

event_queue = queue.Queue()
obs = Obs("ws://127.0.0.1", 4444, "", event_queue)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('client_connected')
def handle_client_connect_event(json):
    emit('welcome', ({ 'number_pf_previews': config.get('number_of_previews') }))

if __name__ == '__main__':
    socketio.run(app)
