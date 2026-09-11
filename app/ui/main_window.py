from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QLabel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Offline Inventory Management System")
        self.resize(1024, 700)
        label = QLabel("Environment OK — ready for Step 1 (data layer).")
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)
