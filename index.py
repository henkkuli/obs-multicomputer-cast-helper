from obswebsocket import obsws, events, requests
import logging
import time
import random
import subprocess
import curses
import csv
import threading
import socket

logging.basicConfig(handlers = [], level=logging.DEBUG)
logger = logging.getLogger(__name__)

source_prefix = "computer-source-"
master_host = socket.gethostbyname(socket.gethostname())

def on_event(message):
    #logger.debug("Got message: %r"%message)
    pass

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
    def __init__(self, host, user):
        self.host = host
        self.user = user

class RemoteComputerManager:
    def __init__(self, computers, command):
        self.computers = computers
        self.command = command
        self.connections = {}

    def connect(self, preview_index, remote_computer_index):
        local_port = preview_index + 10000
        if local_port in self.connections:
            self.connections[local_port].kill()

        remote_computer = self.computers[remote_computer_index]

        command = []
        for part in self.command:
            command.append(part.format(
                host = remote_computer.host,
                user = remote_computer.user,
                master_host = master_host,
                local_port = local_port,
            ))
        logger.debug('Calling command: %r' % command)

        connection = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.connections[local_port] = connection

        def enqueue_stdout():
            for line in iter(connection.stdout.readline, b''):
                logger.info("Computer %d: %s" % (remote_computer_index, line))
            connection.stdout.close()
        def enqueue_stderr():
            for line in iter(connection.stderr.readline, b''):
                logger.warning("Computer %d: %s" % (remote_computer_index, line))
            connection.stderr.close()

        stdout_thread = threading.Thread(target=enqueue_stdout)
        stdout_thread.daemon = True

        stderr_thread = threading.Thread(target=enqueue_stderr)
        stderr_thread.daemon = True

        #stdout_thread.start()
        #stderr_thread.start()

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

    # Read user data
    remote_computers = []
    with open('users.csv', 'r') as user_file:
        user_reader = csv.reader(user_file)
        # Skip header
        next(user_reader, None)
        for user_line in user_reader:
            host, user = user_line
            remote_computers.append(RemoteComputer(host, user))

    # TODO: Add bitrate options etc.
    remote_manager = RemoteComputerManager(remote_computers,
        ['ssh', '{user}@{host}',
         'ffmpeg',
         '-video_size', '1920x1080',
         '-f', 'x11grab',
         # TODO: Is this replace a security hazard?
         #'-i', '$(who | grep {user} | awk \'{{print $5}}\' | tr -d \'()\' | grep \':[[:digit:]]*\' | head -n1)+0,0',
         '-i', ':0',
         '-f', 'mpegts', 'udp://{master_host}:{local_port}',
         ])

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
            # TODO: A more intuitive way to connect to remote computers
            elif ord('A') <= key < ord('A') + len(remote_computers):
                if selected_computer == 0:
                    logger.warning('No computer selected')
                else:
                    remote_machine = key-ord('A')
                    logger.info('Starting streaming %d to preview %d', remote_machine, selected_computer)
                    remote_manager.connect(selected_computer, remote_machine)


            #ws.call(requests.SetPreviewScene(random.choice(scenes)['name']))
            #time.sleep(.5)
            #ws.call(requests.TransitionToProgram('fade'))
            #time.sleep(.5)
    except KeyboardInterrupt:
        pass

    ws.disconnect()

curses.wrapper(main)
