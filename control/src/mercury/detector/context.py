"""SyncContext - synchronous context for device operations.

This class implements a synchronous context that can be used to allow async device
functions to be executed synchronously in command sequence operations. Functions or
attribtes added to the context will, if returning an async coroutine, be run in
a thread-safe manner in the appropriate event loop.

Tim Nicholls, STFC Detector Systems Software Group
"""

import asyncio
from functools import wraps
import logging


class SyncContext:
    """
    Synchronous execution context.
    """
    def __init__(self):
        """Initialise the synchronous context.

        The current async event loop is stored as an attribute of the object.
        """
        self.__dict__["loop"] = asyncio.get_event_loop()
        logging.debug(f"SyncContext has event loop {self.loop} {id(self.loop)}")

    def _run_sync(self, func):
        """Run a function synchronously.

        This method wraps the specified function in a wrapper that ensures it is run
        synchronously. The wrapper determines if the function returns an async coroutine and
        runs it in a thread-safe manner on the current event loop if necessary. Non-async
        functions are called normally and their result returned.

        param func: function to run synchronously
        return: result of the function
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrap the function to run synchronously."""
            # Call the function
            result = func(*args, **kwargs)

            # If function returns a coroutine, run it synchronously on the event loop.
            if asyncio.iscoroutine(result):
                logging.debug(
                    f"Running {func.__name__} in ioloop {self.loop} {id(self.loop)}"
                )
                result = asyncio.run_coroutine_threadsafe(result, self.loop).result()

            # Return the result
            return result

        return wrapper

    def __setattr__(self, name, attr):
        """Assign an instance attribute of the object.

        This method overrides the default attribute assignment mechanism and causes
        all direct assignments to wrapped in the sync run method.

        param name: attribute name
        param attr: attribute value - usually a function in this context
        """
        self.__dict__[name] = self._run_sync(attr)

    def setattr(self, name, attr, wrap=True):
        """Explicitly assign an attribute of the object.

        This method provides an explicit attribute assignment mechanism, allowing the
        caller to decide if the attribute will be wrapped in the sync run method.

        param name: attribute name
        param attr: attribute value
        param wrap: wrap attribute in sync run method if true
        """
        if wrap:
            self.__dict__[name] = self._run_sync(attr)
        else:
            self.__dict__[name] = attr
