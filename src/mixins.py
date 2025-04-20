import threading

class concurent_safe_dict(dict):
    def __init__(self, *args, **kwargs):
        self.lock = threading.Lock()
        super(concurent_safe_dict, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        self.lock.acquire()
        super(concurent_safe_dict, self).__setitem__(key, value)
        self.lock.release()

    def keys(self):
        self.lock.acquire()
        keys = super(concurent_safe_dict, self).keys()
        self.lock.release()
        return keys

    def values(self):
        with self.lock:
            values = super(concurent_safe_dict, self).values()
            return values

    def __contains__(self, key):
        with self.lock:
            contains = super(concurent_safe_dict, self).__contains__(key)
            return contains

    def __getitem__(self, key):
        with self.lock:
            item = super(concurent_safe_dict, self).__getitem__(key)
            return item

    def __delitem__(self, key):
        with self.lock:
            super(concurent_safe_dict, self).__delitem__(key)
    def pop(self, __key):
        with self.lock:
            pop = super(concurent_safe_dict, self).pop(__key)
            return pop
    def __len__(self):
        with self.lock:
            length = super(concurent_safe_dict, self).__len__()
            return length
