"""
Test Z Solar Panel Manager
==========================

This module provides unit tests for the ZSolarPanelManager class.
"""

from pysquared.hardware.solar_panel.z_panel_manager import ZSolarPanelManager
from tests.unit.hardware.solar_panel.test_base_solar_panel import BaseSolarPanelTest


class TestZSolarPanelManager(BaseSolarPanelTest):
    """Test cases for ZSolarPanelManager."""

    MANAGER_CLASS = ZSolarPanelManager
    PANEL_NAME = "Z"
