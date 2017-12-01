from obswebsocket import obsws, events, requests
import logging
import time
import random
import subprocess
import curses

logging.basicConfig(handlers = [], level=logging.DEBUG)
logger = logging.getLogger(__name__)

source_prefix = "computer-source-"

def on_event(message):
    logger.debug("Got message: %r"%message)

class CursesLoggingHandler(logging.Handler):
    def __init__(self, screen):
        logging.Handler.__init__(self)
        self.screen = screen

    def emit(self, record):
        try:
            screen = self.screen
            msg = self.format(record)
            screen.addstr('\n%s' % msg)
            screen.refresh()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

class RemoteComputer:
    def __init__(self, address, user, password):
        self.address = address
        self.user = user
        self.password = password

class RemoteComputerManager:
    def __init__(self, computers):
        self.computers = computers


def main(scr):
    # Setup curses
    curses.noecho()
    curses.cbreak()
    scr.nodelay(True)
    while scr.getch() != curses.ERR: pass

    screen_width = 0
    screen_height = 0
    win = None
    curses_logger = None
    def handle_resize():
        nonlocal curses_logger
        nonlocal screen_width, screen_height
        nonlocal win
        nonlocal curses_logger

        screen_height, screen_width = scr.getmaxyx()
        win = curses.newwin(screen_height, screen_width, 0, 0)
        win.scrollok(True)
        win.idlok(True)
        win.leaveok(True)

        root_logger = logging.getLogger()
        if curses_logger != None:
            root_logger.removeHandler(curses_logger)
        curses_logger = CursesLoggingHandler(win)
        curses_logger.setFormatter(logging.Formatter('%(asctime)-8s|%(name)-12s|%(levelname)-6s|%(message)-s', '%H:%M:%S'))
        root_logger.addHandler(curses_logger)

    handle_resize()

    selected_computer = 1
    streaming_computers = []

    def handle_switch_scenes(message):
        nonlocal selected_computer, streaming_computers
        streaming_computers = []

        for source in message.getSources():
            name = source['name']
            if name.startswith(source_prefix):
                index = int(name[len(source_prefix):])
                streaming_computers.append(index)

        logger.info('Currently streaming computers: %r' % streaming_computers)

        if selected_computer in streaming_computers:
            selected_computer = -1

    ws = obsws("127.0.0.1", 4444, "")
    ws.register(on_event)
    ws.register(handle_switch_scenes, events.SwitchScenes)
    ws.connect()

    # Initialize currently selected scenes
    handle_switch_scenes(ws.call(requests.GetCurrentScene()))
    # TODO: Handle SceneItemAdded
    # TODO: Handle recursive scenes

    try:
        while True:
            key = scr.getch()
            if key == curses.KEY_RESIZE:
                handle_resize()
            if ord('0') <= key <= ord('9'):
                new_selection = key-ord('0')
                while new_selection < 1: new_selection += 10
                if new_selection in streaming_computers:
                    logger.warning('Cannot change the source of currently streaming computer')
                else:
                    logger.info('Selected computer: %d' % new_selection)
                    selected_computer = new_selection


            #ws.call(requests.SetPreviewScene(random.choice(scenes)['name']))
            #time.sleep(.5)
            #ws.call(requests.TransitionToProgram('fade'))
            #time.sleep(.5)
    except KeyboardInterrupt:
        pass

    ws.disconnect()

curses.wrapper(main)
