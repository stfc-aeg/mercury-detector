import logging

import pytest
from unittest.mock import Mock

from mercury.asic_emulator.register_model import MercuryAsicRegisterModel, RegisterMap

@pytest.fixture(scope="class")
def test_register_model():
    """Test fixture for MercuryAsicRegisterModel tests"""
    emulator = Mock()
    log_register_writes = True
    register_model = MercuryAsicRegisterModel(emulator, log_register_writes)
    yield register_model


class TestRegisterModel():
    """Test cases for the MercuryAsicRegisterModel class."""

    @pytest.mark.parametrize("register, index, width, result",
        [
            (0xA5, 0, 8, 0xA5),
            (0xAF, 4, 4, 0xA),
            (0xFF, 0, 1, 0x1),
            (0x0, 32, 8, 0x0),
        ]
    )
    def test_bitfield(self, test_register_model, register, index, width, result):
        assert test_register_model.bitfield(register, index, width) == result

    def test_default_values(self, test_register_model):

        assert test_register_model.page_select == 0

    def test_registers_returns_list(self, test_register_model):

        registers = test_register_model.registers()
        assert type(registers) is list
        assert len(registers) == RegisterMap.size()

    def test_registers_have_default_values(self, test_register_model):

        assert any(test_register_model.registers())

    @pytest.mark.parametrize("transaction, result",
        [
            ([0x0,  0x0],  True),
            ([0x80, 0x0], False),
            ([0x1,  0x0],  True),
            ([0xF3, 0x0], False),
        ]
    )
    def test_is_write_transaction(self, test_register_model, transaction, result):

        assert test_register_model.is_write_transaction(transaction) == result

    @pytest.mark.parametrize("page_select, addr, result",
        [
            (0, 0x00, 0x00),
            (0, 0x10, 0x10),
            (1, 0x00, 0x00),
            (1, 0x02, 0x02),
            (1, 0x10, 0x90),
        ]
    )
    def test_calc_register_addr(self, test_register_model, monkeypatch, page_select, addr, result):

        monkeypatch.setattr(test_register_model, "page_select", page_select)
        assert test_register_model.calc_register_addr(addr) == result

    def test_write_transaction(self, test_register_model):

        transaction = [0x0, 0x1, 0x2, 0x3]
        response = test_register_model.process_transaction(transaction)

        assert response == transaction
        assert test_register_model.registers()[0:3] == transaction[1:]

    def test_read_transaction(self, test_register_model):

        reg_vals = [0x0, 0xde, 0xad, 0xbe, 0xef]
        transaction = [0x0] + reg_vals
        response = test_register_model.process_transaction(transaction)

        transaction = [0x80] + [0x0]*len(reg_vals)
        response = test_register_model.process_transaction(transaction)
        assert response == [0x80] + reg_vals

    def test_log_register_writes(self, test_register_model, caplog):

        with caplog.at_level(logging.DEBUG):
            value = 0x1
            transaction = [RegisterMap.CONFIG1, value]
            test_register_model.process_transaction(transaction)
            assert f"CONFIG1 register: {value:#04x}" in caplog.text

    def test_transaction_error(self, test_register_model, caplog):

        caplog.clear()
        transaction = 0
        test_register_model.process_transaction(transaction)
        assert "Error processing transaction" in caplog.text
