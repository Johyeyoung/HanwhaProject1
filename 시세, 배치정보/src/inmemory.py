from cacheout import Cache
import time


class Cache:
    def __init__(self):
        self.cache = Cache(maxsize=256, ttl=0, timer=time.time, default=None)  # defaults
        return self.cache

    def checkCache(self):
        self.cache.set_many({'a': 1, 'b': 2, 'c': 3})
        assert self.cache.get_many(['a', 'b', 'c']) == {'a': 1, 'b': 2, 'c': 3}
        self.cache.delete_many(['a', 'b', 'c'])
        assert self.cache.count() == 0


class Memory:
    def __init__(self):
        pass


if __name__ == "__main__":
    cache = Cache()