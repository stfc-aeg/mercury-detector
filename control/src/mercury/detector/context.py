import asyncio
from functools import wraps
import logging


class SyncContext():

    def __init__(self):

        self.__dict__['loop'] = asyncio.get_event_loop()
        logging.debug(f"SyncContext has event loop {self.loop} {id(self.loop)}")

    def _run_sync(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                logging.debug(f"Running {func.__name__} in ioloop {self.loop} {id(self.loop)}")
                result = asyncio.run_coroutine_threadsafe(result, self.loop).result()
            return result
        return wrapper

    def __setattr__(self, name, func):
        self.__dict__[name] = self._run_sync(func)
