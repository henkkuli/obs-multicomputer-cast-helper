import threading

class Log:
    
    def __init__(self, history_length, queue):
        self.__lock = threading.Lock()
        self.__history = []
        self.__history_length = history_length
        self.__queue = queue
        self.__clear_event_handlers = []
        self.__log_event_handlers = []

    def onClear(self, handler):
        self.__lock.acquire()

        self.__clear_event_handlers.append(handler)

        self.__lock.release()

    def onMessage(self, handler):
        self.__lock.acquire()

        self.__log_event_handlers.append(handler)

        self.__lock.release()


    def log(self, message):
        self.__lock.acquire()

        self.__history.append(message)

        if len(self.__history) > self.__history_length:
            self.__history = self.__history[len(self.__history) - self.__history_length : ]

        for handler in self.__log_event_handlers:
            self.__queue.put(lambda message=message: handler(message))

        self.__lock.release()


    def clear(self):
        self.__lock.acquire()

        self.__history = []

        for handler in self.__clear_event_handlers:
            self.__queue.put(lambda: handler)

        self.__lock.release()

    def get_messages(self):
        self.__lock.acquire()

        messages = self.__history[:]

        self.__lock.release()

        return messages


    
