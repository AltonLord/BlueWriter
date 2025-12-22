"""
BlueWriter Service Layer.

This package contains UI-agnostic business logic services.
Services handle all database operations and emit events for state changes.
"""
from services.base import BaseService

__all__ = ['BaseService']
