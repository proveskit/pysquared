"""
Test XY Solar Panel Manager
===========================

This module provides unit tests for the XYSolarPanelManager class.
"""

from pysquared.hardware.solar_panel.xy_panel_manager import XYSolarPanelManager
from tests.unit.hardware.solar_panel.test_base_solar_panel import BaseSolarPanelTest


class TestXYSolarPanelManager(BaseSolarPanelTest):
    """Test cases for XYSolarPanelManager."""

    MANAGER_CLASS = XYSolarPanelManager
    PANEL_NAME = "XY"
