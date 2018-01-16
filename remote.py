import subprocess
import threading
import shutil

class RemoteComputer:
    def __init__(self, host, user, real_name):
        self.host = host
        self.user = user
        self.real_name = real_name

class RemoteComputerManager:
    def __init__(self, computers, previews, master_host, user_overlay_path, overlay_path, command, stdin):
        self.computers = computers
        self.previews = previews
        self.master_host = master_host
        self.user_overlay_path = user_overlay_path
        self.overlay_path = overlay_path
        self.command = command
        self.stdin = stdin
        self.connections = {}

    def connect(self, preview_index, remote_computer_index):
        print("Connecting {0} and {1}".format(preview_index, remote_computer_index))
        if preview_index >= len(self.previews):
            return

        preview = self.previews[preview_index]
        local_port = preview[0]
        if local_port in self.connections:
            self.connections[local_port].kill()

        if remote_computer_index == -1:
            return          # The old stream is now killed so everythin is done

        remote_computer = self.computers[remote_computer_index]

        # Start streaming from the computer
        command = []
        for part in self.command:
            command.append(part.format(
                host = remote_computer.host,
                user = remote_computer.user,
                master_host = self.master_host,
                local_port = local_port,
            ))
        #logger.debug('Calling command: %r' % command)

        connection = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.connections[local_port] = connection

        connection.stdin.write(self.stdin);
        connection.stdin.flush();

        # Capture log
        def enqueue_stdout():
            for line in iter(connection.stdout.readline, b''):
                preview[1].log(line)
            connection.stdout.close()
        def enqueue_stderr():
            for line in iter(connection.stderr.readline, b''):
                preview[1].log(line)
            connection.stderr.close()

        stdout_thread = threading.Thread(target=enqueue_stdout)
        stdout_thread.daemon = True

        stderr_thread = threading.Thread(target=enqueue_stderr)
        stderr_thread.daemon = True

        stdout_thread.start()
        stderr_thread.start()

        # Change computer overlay
        try:
            shutil.copyfile(self.user_overlay_path.format(user=remote_computer_index+1), self.overlay_path.format(source=preview_index+1))
        except Exception as e:
            # Copying failed, ignore silently
            print(e)
            pass
