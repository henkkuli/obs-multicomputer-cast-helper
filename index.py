from obswebsocket import obsws, events, requests
import logging
import time
import random
import subprocess
import curses
import csv
import threading
import socket
import shutil
import queue

logging.basicConfig(handlers = [], level=logging.INFO)
logger = logging.getLogger(__name__)

source_prefix = "computer-source-"
overlay_prefix = "computer-overlay-"
user_overlay_path = "user-overlays/user-{user}.png"
overlay_path = "source-overlay-{source}.png"
master_host = socket.gethostbyname(socket.gethostname())
show_remote_log = False

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
    def __init__(self, computers, command, stdin):
        self.computers = computers
        self.command = command
        self.stdin = stdin
        self.connections = {}

    def connect(self, preview_index, remote_computer_index):
        local_port = preview_index + 10000
        if local_port in self.connections:
            self.connections[local_port].kill()

        remote_computer = self.computers[remote_computer_index]

        # Start streaming from the computer
        command = []
        for part in self.command:
            command.append(part.format(
                host = remote_computer.host,
                user = remote_computer.user,
                master_host = master_host,
                local_port = local_port,
            ))
        logger.debug('Calling command: %r' % command)

        connection = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.connections[local_port] = connection

        connection.stdin.write(self.stdin);
        connection.stdin.flush();

        # Capture log
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

        if show_remote_log:
            stdout_thread.start()
            stderr_thread.start()

        # Change computer overlay
        try:
            shutil.copyfile(user_overlay_path.format(user=remote_computer_index+1), overlay_path.format(source=preview_index))
        except Exception as e:
            # Copying failed, ignore silently
            logger.warning("Failed copying user overlay: %r" % e)
            pass

def get_currently_streaming_computers(ws):
    # First request a list of scenes
    scenes = ws.call(requests.GetSceneList())
    current_scene = scenes.getCurrentScene()
    scenes = scenes.getScenes()

    logger.info("Finding out currently streaming computers")
    
    # Then organize them by name
    scenes = {scene['name']: scene for scene in scenes}

    streaming_computers = []
    def handle_scene(scene):
        for source in scene['sources']:
            type = source['type']
            if type == 'ffmpeg_source':
                name = source['name']
                if name.startswith(source_prefix):
                    index = int(name[len(source_prefix):])
                    streaming_computers.append(index)
            elif type == 'scene':
                handle_scene(scenes[source['name']])

    handle_scene(scenes[current_scene])
    return streaming_computers


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

    task_queue = queue.Queue()

    def handle_switch_scenes(message):
        def handler():
            nonlocal selected_computer, streaming_computers, ws
            streaming_computers = get_currently_streaming_computers(ws)

            logger.info('Currently streaming computers: %r' % streaming_computers)

            if selected_computer in streaming_computers:
                selected_computer = -1
        task_queue.put(handler)

    # Read user data
    remote_computers = []
    with open('users.csv', 'r') as user_file:
        user_reader = csv.reader(user_file)
        # Skip header
        next(user_reader, None)
        for user_line in user_reader:
            host, user = user_line
            remote_computers.append(RemoteComputer(host, user))

    command = ['ssh', '-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no', '{user}@{host}',
            'bash', '-s', '--', '{user}', 'udp://{master_host}:{local_port}'];
    with open('remote-script.sh', 'r') as script_file:
        script = bytearray(script_file.read(), 'utf-8')
    remote_manager = RemoteComputerManager(remote_computers, command, script);

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
            while True:
                try:
                    task = task_queue.get_nowait()
                    task()
                except queue.Empty:
                    # No more tasks to handle
                    break

            key = scr.getch()
            if key == curses.KEY_RESIZE:
                handle_resize()
            if ord('0') <= key <= ord('9'):
                new_selection = key-ord('0')
                while new_selection < 1: new_selection += 10
                if new_selection in streaming_computers:
                    logger.warning('Cannot change the source of currently streaming computer')
                    selected_computer = 0
                else:
                    logger.info('Selected computer: %d' % new_selection)
                    selected_computer = new_selection
            # TODO: A more intuitive way to connect to remote computers
            else:
                char = key - ord('A')
                if char >= 26:
                    char = key - ord('a')
                if 0 <= char < len(remote_computers):
                    if selected_computer == 0:
                        logger.warning('No computer selected')
                    else:
                        remote_machine = char
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
