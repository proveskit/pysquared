"""
Solar Panel Hardware Module
==========================

This module provides managers for controlling solar panels on PySquared satellite hardware.
"""

from .xy_panel_manager import XYSolarPanelManager
from .z_panel_manager import ZSolarPanelManager

__all__ = [
    "XYSolarPanelManager",
    "ZSolarPanelManager",
]
