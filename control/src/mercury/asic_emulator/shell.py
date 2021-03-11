"""MercuryAsicEmulatorShell - interactive shell for testing the MERCURY ASIC emulator.

This module implements an interactive shell for testing the behaviour of the MERCURY ASIC
emulator. It allows the user to undertake register read and write commands, which are
executed as transations on a connect emulator server.

Tim Nicholls, STFC Detector Systems Software Group
"""
import asyncio
import cmd
import inspect
import logging

from itertools import zip_longest
from functools import partial, update_wrapper

import click

from mercury.asic_emulator.client import MercuryAsicClient


class MercuryAsicEmulatorShell(cmd.Cmd):
    """
    MERCURY ASIC emulator interactive shell.

    The class implements the interactive command shell for testing the MERCURY ASIC emulator.
    """

    # Set the shell command prompt
    prompt = '> '

    def __init__(self, client):
        """Initialise the command shell.

        :param client: MERCURY ASIC emulator client instance to use
        """
        super().__init__()
        self.client = client

        # Get the asyncio event loop to run client tasks in
        self.loop = asyncio.get_event_loop()

        # Iterate over all the command `do_` methods in this class and generate an equivalent
        # `help_` method that prints a cleaned-up docstring. This avoids the default behaviour
        # where commands get a help method that shows an indented docstring.
        for item in dir(self):
            if item.startswith('do_') and callable(getattr(self, item)):
                cmd_name = item[len('do_'):]
                if cmd_name != 'help':
                    help_name = 'help_' + cmd_name
                    doc_str = inspect.cleandoc(getattr(self, item).__doc__)
                    setattr(self, help_name, lambda doc_str=doc_str: print(doc_str))

    def _parse_args(self, arg_str, *defaults, **kwargs):
        """Parse a command argument string into arguments.

        This internal method parses the single argument string the shell passes to a command
        method into a list of appropriately typed and formatted arguments. Default values for
        arguments can be defined, which also define the type of specified arguments. A default
        type for all arguments can be given.

        :param arg_str: argument string passed by the shell command loop
        :param *defaults: default values for arguments, also used to coerce types of arguments
        :param **kwargs: keyword arguments
        """
        # Extract the default argument type if specified, otherwise fall back to string
        def_type = kwargs.get('def_type', str)

        # Build a list of the parsed and type-coerced arguments
        args = []
        for (arg, default) in zip_longest(arg_str.split(), defaults):
            if arg:
                # If the argument has been specified, use the type of matching default if given
                arg_type = type(default) if default else def_type

                # For integer arguments, update the argtype to allow an integer to be coerced
                # from non-decimal value strings, e.g. hex or binary
                if arg_type == int:
                    arg_type = partial(int, base=0)
                    update_wrapper(arg_type, int)

                # Attempt to coerce the type of the argument accordingly. If this fails, return
                # immediately.
                try:
                    args.append(arg_type(arg))
                except ValueError:
                    print(f"Error parsing argument {arg} into type {arg_type.__name__}")
                    return
            else:
                # If no argument given at this position, append the default
                args.append(default)

        return args

    def _run_task(self, future):
        """Run the specified aysnchronous task.

        This method runs the specified asyncio future in the event loop and returns once complete.

        :param future: asyncio future to run (e.g. an async function)
        :return: return value of the future
        """
        return self.loop.run_until_complete(future)

    def do_quit(self, arg):
        """Quit the client application."""
        return True

    # Bind the cmd shell EOF event to the quit function, allowing 'ctrl-D' to terminate the shell
    do_EOF = do_quit

    def do_read(self, arg):
        """
        Perform a register read transaction.

        Arguments: <addr> <len> <radix>
        where:
          addr  = register address (default=0)
          len   = number of registers to read (default=1)
          radix = radix (base) to display values in: bin, dec or hex (default=hex)
        """
        # Parse the input arguments
        args = self._parse_args(arg, 0, 1, 'hex', def_type=int)
        if not args:
            return

        # Extract the read command address, length and radix from the arguments
        read_addr = args[0]
        read_len = args[1]
        radix = args[2]

        # Decode the radix argument into a format specifier for displaying the result. Falls back
        # gracefully to decimal if the argument isn't recognised
        radix_fmt = {
            'dec': '03d',
            'bin': '#010b',
            'hex': '#04x'
        }.get(radix, '03d')

        # Construct the client transaction based on the read address and length
        transaction = [read_addr, *[0]*read_len]

        # Execute the client read task
        response = self._run_task(self.client.read(transaction))

        # Parse the response into formatted display values
        vals = ' '.join(f"{val:{radix_fmt}}" for val in response[1:])

        # Print the result
        print(f"{read_addr:03d} : {vals}")

    def do_write(self, arg):
        """
        Perform a register write transaction.

        Arguments: <addr>, <val>, [vals....]
        where:
          addr = register adddress
          val  = value to write
          vals = optional additional consecutive registers to write
        """
        # Parse the input arguments
        args = self._parse_args(arg, def_type=int)
        if not args:
            return

        # Construct the client transaction from the arguments, then execute the client write task
        transaction = args
        response = self._run_task(self.client.write(transaction))

        # Parse the response into formatted display values
        vals = ' '.join(f"{val:03d}" for val in response[1:])
        print(f"{response[0]:03d} : {vals}")


@click.command()
@click.option('--addr', default='127.0.0.1', help='Endpoint address')
@click.option('--port', default=5555, help='Endpoint port')
@click.option("--test", is_flag=True, help='Run an automated set of test transactions')
def main(addr, port, test):
    """Run the the ASIC emulator shell.

    This function implements the main entry point for the emulator shell and is defined
    as a click command with appropriate command-line options. A test mode invokes the client
    test loop, which runs and automated set of test teransations, instead of launching the
    interactive shell.

    :param addr: string endpoint IP address or hostname for the emulator server
    :param port: integer endpoint port for the emulator server
    :param test: boolean flag indicating client test mode.
    """
    # Set up message logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    # Create a MERCURY ASIC client at the specified endpoint address and port
    client = MercuryAsicClient(addr, port)

    # If in test mode, start the client test loop, otherwise enter the interactive shell
    if test:
        client.test()
    else:
        MercuryAsicEmulatorShell(client).cmdloop()


if __name__ == '__main__':
    main()
