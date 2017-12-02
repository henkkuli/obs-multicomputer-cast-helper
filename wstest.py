from obswebsocket import obsws, events, requests
import logging
import time
import subprocess
import readline,json
commands = sorted(list(map(lambda v: "requests."+v,dir(requests))))

def completer(text, state):
    options = [i for i in commands if i.startswith(text)]
    if state < len(options):
        return options[state]
    else:
        return None

readline.parse_and_bind("tab: complete")
readline.set_completer(completer)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def on_event(message):
    try: print(json.dumps(message.datain,indent=4))
    except: logger.debug("Got message: %r"%message)

def prettyprint_result(message):
    print(json.dumps(message.datain,indent=4))


ws = obsws("127.0.0.1", 4444, "")
ws.register(on_event)
ws.connect()
while True:
    prettyprint_result(ws.call(eval(input())))

