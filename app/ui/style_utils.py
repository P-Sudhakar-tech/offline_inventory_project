from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget


def apply_card_shadow(widget: QWidget, blur: int = 24, y_offset: int = 6, alpha: int = 35) -> None:
    """QSS has no box-shadow; a real QGraphicsDropShadowEffect gives cards
    actual depth instead of relying on a flat border alone."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y_offset)
    effect.setColor(QColor(15, 23, 42, alpha))
    widget.setGraphicsEffect(effect)


def apply_shadows_to_cards(root: QWidget) -> None:
    for object_name in ("Card", "KpiCard"):
        for widget in root.findChildren(QWidget, object_name):
            apply_card_shadow(widget)
