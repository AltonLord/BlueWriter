"""
BlueWriter Adapters Package.

Contains UI framework adapters that bridge the event bus to specific UI toolkits.
"""
from adapters.qt_adapter import QtEventAdapter

__all__ = ['QtEventAdapter']
