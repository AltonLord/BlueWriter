import sys
print("Python version:", sys.version)

try:
    from PySide6 import QtWidgets
    print("✓ QtWidgets imported successfully")
    
    try:
        from PySide6.QtWidgets import QApplication, QWidget, QAction
        print("✓ All required modules imported successfully")
    except ImportError as e:
        print("✗ Import error:", e)
        
except ImportError as e:
    print("✗ Failed to import PySide6:", e)
