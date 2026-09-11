from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class KpiCard(QWidget):
    def __init__(self, title: str, value_object_name: str = "KpiValue", parent=None):
        super().__init__(parent)
        self.setObjectName("KpiCard")

        title_label = QLabel(title)
        title_label.setObjectName("KpiTitle")

        self.value_label = QLabel("0")
        self.value_label.setObjectName(value_object_name)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_value(self, text: str):
        self.value_label.setText(text)
