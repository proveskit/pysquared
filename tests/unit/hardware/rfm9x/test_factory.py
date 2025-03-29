import math
from unittest.mock import MagicMock, patch

import pytest

from mocks.adafruit_rfm.rfm9x import RFM9x
from mocks.adafruit_rfm.rfm9xfsk import RFM9xFSK
from pysquared.config.radio import FSKConfig, LORAConfig, RadioConfig
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.rfm9x.factory import RFM9xFactory
from pysquared.hardware.rfm9x.modulation import RFM9xModulation


@pytest.fixture
def mock_spi():
    return MagicMock()


@pytest.fixture
def mock_chip_select():
    return MagicMock()


@pytest.fixture
def mock_reset():
    return MagicMock()


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_fsk_config():
    return FSKConfig(
        {"broadcast_address": 255, "node_address": 1, "modulation_type": 0}
    )


@pytest.fixture
def mock_lora_config():
    return LORAConfig(
        {
            "ack_delay": 0.2,
            "coding_rate": 5,
            "cyclic_redundancy_check": True,
            "max_output": True,
            "spreading_factor": 7,
            "transmit_power": 23,
        }
    )


@pytest.fixture
def mock_radio_config():
    return RadioConfig(
        {
            "sender_id": 1,
            "receiver_id": 2,
            "transmit_frequency": 915,
            "start_time": 0,
            "fsk": {"broadcast_address": 255, "node_address": 1, "modulation_type": 0},
            "lora": {
                "ack_delay": 0.2,
                "coding_rate": 5,
                "cyclic_redundancy_check": True,
                "max_output": True,
                "spreading_factor": 7,
                "transmit_power": 23,
            },
        }
    )


def test_create_fsk_radio(mock_spi, mock_chip_select, mock_reset, mock_fsk_config):
    frequency = 915
    radio = RFM9xFactory.create_fsk_radio(
        mock_spi, mock_chip_select, mock_reset, frequency, mock_fsk_config
    )
    assert isinstance(radio, RFM9xFSK)
    assert radio.fsk_broadcast_address == 255
    assert radio.fsk_node_address == 1
    assert radio.modulation_type == 0


def test_create_lora_radio(mock_spi, mock_chip_select, mock_reset, mock_lora_config):
    frequency = 915
    radio = RFM9xFactory.create_lora_radio(
        mock_spi,
        mock_chip_select,
        mock_reset,
        frequency,
        mock_lora_config,
    )
    assert isinstance(radio, RFM9x)
    assert math.isclose(radio.ack_delay, 0.2)
    assert radio.enable_crc
    assert radio.max_output
    assert radio.spreading_factor == 7
    assert radio.tx_power == 23


def test_create_lora_radio_high_sf(mock_spi, mock_chip_select, mock_reset):
    frequency = 915
    high_sf_config = LORAConfig(
        {
            "ack_delay": 0.2,
            "coding_rate": 5,
            "cyclic_redundancy_check": True,
            "max_output": True,
            "spreading_factor": 10,
            "transmit_power": 23,
        }
    )

    radio = RFM9xFactory.create_lora_radio(
        mock_spi,
        mock_chip_select,
        mock_reset,
        frequency,
        high_sf_config,
    )
    assert isinstance(radio, RFM9x)
    assert radio.preamble_length == 10
    assert radio.low_datarate_optimize == 1


def test_create_fsk(
    mock_spi, mock_chip_select, mock_reset, mock_logger, mock_radio_config
):
    factory = RFM9xFactory(mock_spi, mock_chip_select, mock_reset, mock_radio_config)

    radio = factory.create(
        mock_logger,
        RFM9xModulation.FSK,
    )
    assert isinstance(radio, RFM9xFSK)
    assert radio.node == mock_radio_config.sender_id
    assert radio.destination == mock_radio_config.receiver_id


def test_create_lora(
    mock_spi, mock_chip_select, mock_reset, mock_logger, mock_radio_config
):
    factory = RFM9xFactory(mock_spi, mock_chip_select, mock_reset, mock_radio_config)

    radio = factory.create(
        mock_logger,
        RFM9xModulation.LORA,
    )
    assert isinstance(radio, RFM9x)
    assert radio.node == mock_radio_config.sender_id
    assert radio.destination == mock_radio_config.receiver_id


def test_get_instance_modulation():
    mock_fsk_radio = RFM9xFSK(None, None, None, 915)
    mock_lora_radio = RFM9x(None, None, None, 915)

    assert RFM9xFactory.get_instance_modulation(mock_fsk_radio) == RFM9xModulation.FSK
    assert RFM9xFactory.get_instance_modulation(mock_lora_radio) == RFM9xModulation.LORA


@pytest.mark.slow
@patch("pysquared.hardware.rfm9x.factory.RFM9xFactory.create_fsk_radio")
def test_create_with_retries_fsk(
    mock_create_fsk_radio,
    mock_spi,
    mock_chip_select,
    mock_reset,
    mock_logger,
    mock_radio_config,
):
    mock_create_fsk_radio.side_effect = Exception("Simulated FSK failure")

    factory = RFM9xFactory(mock_spi, mock_chip_select, mock_reset, mock_radio_config)

    with pytest.raises(HardwareInitializationError):
        factory.create(
            mock_logger,
            RFM9xModulation.FSK,
        )
    assert mock_create_fsk_radio.call_count == 3


@pytest.mark.slow
@patch("pysquared.hardware.rfm9x.factory.RFM9xFactory.create_lora_radio")
def test_create_with_retries_lora(
    mock_create_lora_radio,
    mock_spi,
    mock_chip_select,
    mock_reset,
    mock_logger,
    mock_radio_config,
):
    mock_create_lora_radio.side_effect = Exception("Simulated LoRa failure")

    factory = RFM9xFactory(mock_spi, mock_chip_select, mock_reset, mock_radio_config)

    with pytest.raises(HardwareInitializationError):
        factory.create(
            mock_logger,
            RFM9xModulation.LORA,
        )
    assert mock_create_lora_radio.call_count == 3
