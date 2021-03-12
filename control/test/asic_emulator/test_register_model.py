import pytest
from unittest.mock import Mock

from mercury.asic_emulator.register_model import MercuryAsicRegisterModel, RegisterMap

@pytest.fixture(scope="class")
def test_register_model():
    """Test fixture for MercuryAsicRegisterModel tests"""
    emulator = Mock()
    log_register_writes = False
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
