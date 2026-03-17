import threading


class AtomicCounter:
    def __init__(self):
        self.count = 0
        self.lock = threading.Lock()

    def new_value(self, by: int = 1):
        """ Atomically increments the counter. """
        with self.lock:
            count = self.count
            self.count = count + by
            return count

    def current_value(self):
        """ Atomically reads the counter value. """
        with self.lock:
            return self.count
