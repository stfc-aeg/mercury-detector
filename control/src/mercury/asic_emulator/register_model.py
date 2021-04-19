"""MercuryAsicRegisterModel - SPI register model for ASIC emulation.

This module implements a model of the MERCURY SPI register space for use in the
MERCURY ASIC emulation. Registers are initialised with their default values and
can be read and written. The page select mechanism is implemented and callbacks
provided to allow the behaviour of the emulator to be modified based on changes
to the registers.

Tim Nicholls, STFC Detector Systems Software Group
"""
import logging

from mercury.asic.registers import RegisterMap


class MercuryAsicRegisterModel:
    """
    MERCURY ASIC Register model class.

    This class implemetnts the SPI register model for the MERCURY ASIC
    emulation.
    """

    # Common constants for register transactions
    REGISTER_RW_MASK = 0x80
    REGISTER_ADDR_MASK = 0x7F
    REGISTER_READ_TRANSACTION = 0x80
    REGISTER_WRITE_TRANSACTION = 0x0
    REGISTER_PAGE_SIZE = 128

    REGISTER_SR_CAL_SIZE = 20
    REGISTER_SR_TEST_SIZE = 480

    @staticmethod
    def bitfield(register, index, width=1):
        """Return a bit field from a register value.

        :param register: register value
        :param index: start bix index for bitfield
        :param width: width of bitfield in bytes
        :return: a right-shifted value from the appropriate bitfield
        """
        return (register >> index) & ((2 ** width) - 1)

    def __init__(self, emulator, log_register_writes):
        """Initialise the register model.

        This constructor initialises the default state of the register model, setting
        default values for all registers and defining a set of callback functions that
        execute when a register is written to.

        :param emulator: reference to emulator instance that can be used in callbacks
        :param log_register_writes: boolean option to emit logging messages for register writes
        """
        self.emulator = emulator
        self.log_register_writes = log_register_writes

        # Create registers and set default values
        self._registers = bytearray(RegisterMap.size())
        self._registers[RegisterMap.CONFIG1] = 0b01010000
        self._registers[RegisterMap.GLOB1] = 0b00000000
        self._registers[RegisterMap.GLOB2] = 0b00000000
        self._registers[RegisterMap.GLOB_VAL1] = 0b00000000
        self._registers[RegisterMap.GLOB_VAL2] = 0b00000000
        self._registers[RegisterMap.FRM_LNGTH] = 200
        self._registers[RegisterMap.INT_TIME] = 1
        self._registers[RegisterMap.TEST_SR] = 0b00000000
        self._registers[RegisterMap.SER_BIAS] = 0b10001000
        self._registers[RegisterMap.TDC_BIAS] = 0b10001000

        # Create shift registers for calibration and test
        self._shift_registers = {
            RegisterMap.SR_CAL: bytearray(self.REGISTER_SR_CAL_SIZE),
            RegisterMap.SR_TEST: bytearray(self.REGISTER_SR_TEST_SIZE),
        }

        # Initialise internal state of register model
        self.page_select = 0

        # Define register-specific callbacks that run when a register is modified
        self._callbacks = {RegisterMap.CONFIG1: self._do_config1}

        # Execute all the callbacks to initialise state of model
        for callback in self._callbacks.values():
            callback()

    def registers(self):
        """Return a list of current register values."""
        return list(self._registers)

    def process_transaction(self, transaction):
        """Process a register transaction.

        This method processes in incoming register read or write transaction, updating the
        values of the registers and executing callbacks for any modified registers. Transactions
        take account of the register page select defined in CONFIG1. Burst read and write
        transactions are supported.

        :param transaction: iterable of transaction values, representing the bytes in an SPI
                            transaction
        :return: list of output bytes representing the response of the ASIC to an SPI transaction
        """
        try:
            # Extract the register address from the first byte of the transaction and determine
            # the length
            register_addr = int(transaction[0]) & self.REGISTER_ADDR_MASK
            transaction_len = len(transaction[1:])

            # If this is a write transaction, handle accordingly, updating register values and
            # executing any registered callbacks for modified registers
            if self.is_write_transaction(transaction):
                logging.debug(
                    f"Write transaction to register {register_addr} length {transaction_len}"
                )
                # Loop over the payload of the transaction
                for idx in range(transaction_len):

                    # Calcuate the address, taking into account the page select state
                    addr = self.calc_register_addr(register_addr + idx)

                    # Intercept shift-register writes where a burst mode transaction doesn't
                    # increment the register address
                    if addr in self._shift_registers:
                        print("This is a shift register")
                        print(len(self._shift_registers[addr]))
                        print(len(transaction[1 + idx :]))
                        sr_write_len = min(
                            len(self._shift_registers[addr]),
                            len(transaction[1 + idx :])
                        )
                        print(f"SR write to addr {addr} len {sr_write_len}")
                        break

                    else:
                        # Update the register value accordingly
                        self._registers[addr] = transaction[1 + idx]

                        # Execute a callback if defined for this register
                        if addr in self._callbacks:
                            self._callbacks[addr]()

                        # Log the register write if enabled
                        if self.log_register_writes:
                            self.log_register_write(addr)

            # Otherwise handle a read transaction.
            else:
                logging.debug(
                    f"Read transaction from register {register_addr} length {transaction_len}"
                )
                # Loop over the payload of the transaction, copying the relevant register
                # values into the response.
                for idx in range(transaction_len):
                    addr = self.calc_register_addr(register_addr + idx)
                    transaction[1 + idx] = self._registers[addr]

        except Exception as err:
            logging.error(f"Error processing transaction: {type(err)} {err}")

        return transaction

    def is_write_transaction(self, transaction):
        """Determine if a transaction is a write.

        This method inspects the first address byte of a transaction to determine if it is a write,
        based on the RW bit.

        :param transaction: transaction to check
        :return: boolean, true if this is a write transaction.
        """
        return (
            transaction[0] & self.REGISTER_RW_MASK
        ) == self.REGISTER_WRITE_TRANSACTION

    def calc_register_addr(self, addr):
        """Calculate the true register address based on the current page select.

        This method maps the incoming register address to the 'true' address based on
        the page select bit in the CONFIG1 register. If page 1 is selected, the calculated
        address is offset by the page size.

        :param addr: raw address from the transaction
        :return: true register address
        """
        if self.page_select and addr > 2:
            addr += self.REGISTER_PAGE_SIZE
        return addr

    def log_register_write(self, addr):
        """Log register write operations.

        This method emits a debug log message for register write operations.

        :param addr: address of the register written to
        """
        reg_name = RegisterMap(addr).name
        logging.debug(f"{reg_name} register: {self._registers[addr]:#04x}")

    def _do_config1(self):
        """Execute callback for CONFIG1 register writes.

        This callback is executed on writes to the CONFIG1 register.
        """
        # Determine if the page select is being changed by this write and, if so, update the
        # value and emit a debug message.
        page_select = self.bitfield(self._registers[RegisterMap.CONFIG1], 0, 1)
        if page_select != self.page_select:
            logging.debug(f"Register page select is now {page_select}")
            self.page_select = page_select
