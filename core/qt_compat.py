# -*- coding: utf-8 -*-
"""
Zentrale PySide6/PySide2-Kompatibilitätsweiche.
Alle anderen Module importieren Qt nur noch von hier:

    from qt_compat import QtWidgets, QtCore, QtGui
"""
try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

__all__ = ["QtWidgets", "QtCore", "QtGui"]
