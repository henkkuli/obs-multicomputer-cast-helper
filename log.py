import threading

class Log:
    
    def __init__(self, history_length, queue):
        self.__lock = threading.Lock()
        self.__history = []
        self.__history_length = history_length
        self.__queue = qeueu
        self.__clear_event_handlers = []
        self.__log_event_handlers = []

    def log(self, message):
        self.__lock.acquire()

        self.__history.append(message)

        if len(self.__history) > self.__history_length:
            self.__history = self.__history[len(self.__history) - self.__history_length : ]

        for handler in self.__log_event_handlers:
            queue.put(lambda: handler(message))

        self.__lock.release()


    def clear(self):
        self.__lock.acquire()

        self.__history = []

        for handler in self.__clear_event_handlers:
            queue.put(lambda: handler(message))

        self.__lock.release()

    def get_messages(self):
        self.__lock.acquire()

        messages = self.__history[:]

        self.__lock.release()

        return messages


    
