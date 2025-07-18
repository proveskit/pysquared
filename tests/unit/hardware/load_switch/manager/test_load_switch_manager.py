"""
Test Load Switch Manager
=======================

This module provides unit tests for the LoadSwitchManager class.
"""

from unittest.mock import Mock

import pytest

from pysquared.hardware.load_switch.manager.load_switch import LoadSwitchManager
from pysquared.logger import Logger


class TestLoadSwitchManager:
    """Test cases for LoadSwitchManager."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return Mock(spec=Logger)

    @pytest.fixture
    def mock_switches(self):
        """Create mock load switches for testing."""
        switches = {}
        for name in ["radio", "imu", "camera"]:
            mock_switch = Mock()
            mock_switch.value = False
            switches[name] = mock_switch
        return switches

    @pytest.fixture
    def load_switch_manager(self, mock_logger, mock_switches):
        """Create a LoadSwitchManager instance for testing."""
        return LoadSwitchManager(mock_logger, mock_switches, enable_logic=True)

    def test_initialization(self, mock_logger, mock_switches):
        """Test LoadSwitchManager initialization."""
        manager = LoadSwitchManager(mock_logger, mock_switches, enable_logic=True)

        assert manager.switch_states == {"radio": False, "imu": False, "camera": False}
        assert len(manager.get_switch_names()) == 3

    def test_turn_on_switch(self, load_switch_manager, mock_switches):
        """Test turning on a specific switch."""
        result = load_switch_manager.turn_on("radio")

        assert result is True
        assert load_switch_manager.switch_states["radio"] is True
        assert mock_switches["radio"].value is True

    def test_turn_off_switch(self, load_switch_manager, mock_switches):
        """Test turning off a specific switch."""
        # First turn on the switch
        load_switch_manager.turn_on("radio")

        # Then turn it off
        result = load_switch_manager.turn_off("radio")

        assert result is True
        assert load_switch_manager.switch_states["radio"] is False
        mock_switches["radio"].value = False

    def test_turn_on_nonexistent_switch(self, load_switch_manager):
        """Test turning on a switch that doesn't exist."""
        result = load_switch_manager.turn_on("nonexistent")

        assert result is False

    def test_turn_all_on(self, load_switch_manager, mock_switches):
        """Test turning on all switches."""
        result = load_switch_manager.turn_all_on()

        assert result is True
        assert all(load_switch_manager.switch_states.values())
        for switch in mock_switches.values():
            assert switch.value is True

    def test_turn_all_off(self, load_switch_manager, mock_switches):
        """Test turning off all switches."""
        # First turn all on
        load_switch_manager.turn_all_on()

        # Then turn all off
        result = load_switch_manager.turn_all_off()

        assert result is True
        assert not any(load_switch_manager.switch_states.values())
        for switch in mock_switches.values():
            assert switch.value is False

    def test_get_switch_state(self, load_switch_manager):
        """Test getting the state of a specific switch."""
        # Initially all switches are off
        state = load_switch_manager.get_switch_state("radio")
        assert state is False

        # Turn on the switch
        load_switch_manager.turn_on("radio")
        state = load_switch_manager.get_switch_state("radio")
        assert state is True

    def test_get_switch_state_nonexistent(self, load_switch_manager):
        """Test getting the state of a nonexistent switch."""
        state = load_switch_manager.get_switch_state("nonexistent")
        assert state is None

    def test_get_all_states(self, load_switch_manager):
        """Test getting all switch states."""
        states = load_switch_manager.get_all_states()
        expected = {"radio": False, "imu": False, "camera": False}
        assert states == expected

        # Turn on one switch and check again
        load_switch_manager.turn_on("radio")
        states = load_switch_manager.get_all_states()
        expected["radio"] = True
        assert states == expected

    def test_add_switch(self, load_switch_manager):
        """Test adding a new switch."""
        mock_new_switch = Mock()
        mock_new_switch.value = False

        result = load_switch_manager.add_switch("new_switch", mock_new_switch)

        assert result is True
        assert "new_switch" in load_switch_manager.get_switch_names()
        assert load_switch_manager.switch_states["new_switch"] is False

    def test_add_duplicate_switch(self, load_switch_manager):
        """Test adding a switch that already exists."""
        mock_new_switch = Mock()

        result = load_switch_manager.add_switch("radio", mock_new_switch)

        assert result is False

    def test_remove_switch(self, load_switch_manager):
        """Test removing a switch."""
        result = load_switch_manager.remove_switch("radio")

        assert result is True
        assert "radio" not in load_switch_manager.get_switch_names()
        assert "radio" not in load_switch_manager.switch_states

    def test_remove_nonexistent_switch(self, load_switch_manager):
        """Test removing a switch that doesn't exist."""
        result = load_switch_manager.remove_switch("nonexistent")

        assert result is False

    def test_get_switch_names(self, load_switch_manager):
        """Test getting all switch names."""
        names = load_switch_manager.get_switch_names()
        expected = ["radio", "imu", "camera"]
        assert sorted(names) == sorted(expected)

    def test_enable_logic_false(self, mock_logger, mock_switches):
        """Test LoadSwitchManager with enable_logic=False."""
        manager = LoadSwitchManager(mock_logger, mock_switches, enable_logic=False)

        # Turn on a switch
        result = manager.turn_on("radio")
        assert result is True
        assert manager.switch_states["radio"] is True
        # With enable_logic=False, the pin should be set to False to turn on
        assert mock_switches["radio"].value is False
