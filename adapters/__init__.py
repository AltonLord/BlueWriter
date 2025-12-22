"""
BlueWriter Qt Adapters Package.

Provides adapters that bridge framework-agnostic services
to specific UI frameworks (currently Qt/PySide6).
"""
from adapters.qt_adapter import QtEventAdapter

__all__ = ['QtEventAdapter']
