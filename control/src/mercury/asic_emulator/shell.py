import asyncio
import cmd
import inspect
import logging

from itertools import zip_longest
from functools import partial, update_wrapper

import click

from mercury.asic_emulator.client import MercuryAsicClient

class AsicEmulatorShell(cmd.Cmd):
    prompt = '> '

    def __init__(self, client):

        super().__init__()
        self.client = client
        self.loop = asyncio.get_event_loop()

        for item in dir(self):
            if item.startswith('do_') and callable(getattr(self, item)):
                cmd_name = item[len('do_'):]
                if cmd_name != 'help':
                    help_name = 'help_' + cmd_name
                    doc_str = inspect.cleandoc(getattr(self, item).__doc__)
                    setattr(self, help_name, lambda doc_str=doc_str: print(doc_str))

    def _parse_args(self, arg_str, *defaults, **kwargs):

        def_type = kwargs.get('def_type', str)

        args = []
        for (arg, default) in zip_longest(arg_str.split(), defaults):
            if arg:
                arg_type = type(default) if default else def_type
                if arg_type == int:
                    arg_type = partial(int, base=0)
                    update_wrapper(arg_type, int)
                try:
                    args.append(arg_type(arg))
                except ValueError:
                    print(f"Error parsing argument {arg} into type {arg_type.__name__}")
                    return
            else:
                args.append(default)

        return args

    def _run_task(self, future):
        return self.loop.run_until_complete(future)

    def do_quit(self, arg):
        """
        Quit the client application.
        """
        return True

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
        args = self._parse_args(arg, 0, 1, 'hex', def_type=int)
        if not args:
            return

        read_addr = args[0]
        read_len = args[1]
        radix = args[2]

        radix_fmt = {
            'dec': '03d',
            'bin': '#010b',
            'hex': '#04x'
        }.get(radix, '03d')

        transaction = [read_addr, *[0]*read_len]

        response = self._run_task(self.client.read(transaction))
        vals = ' '.join(f"{val:{radix_fmt}}" for val in response[1:])
        print(f"{read_addr:03d} : {vals}")

    def do_write(self, arg):
        """
        Perform a register write transaction.

        Arguments: <reg>, <val>, [vals....]
        """
        args = self._parse_args(arg, def_type=int)
        if not args:
            return

        transaction = args
        response = self._run_task(self.client.write(transaction))
        print(response)

@click.command()
@click.option('--addr', default='127.0.0.1', help='Endpoint address')
@click.option('--port', default=5555, help='Endpoint port')
@click.option("--test", is_flag=True, help='Run an automated set of test transactions')
def main(addr, port, test):

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    client = MercuryAsicClient(addr, port)

    if test:
        client.run()
    else:
        AsicEmulatorShell(client).cmdloop()

if __name__ == '__main__':
    main()