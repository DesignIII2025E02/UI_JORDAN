from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
import serial.tools.list_ports


class PortSelectionDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.selected_port = None
        self.selected_baudrate = None
        self.setWindowTitle("Grue")
        self.init_ui()


    def init_ui(self):
        layout = QVBoxLayout()
        self.port_label = QLabel("Sélectionnez le port UART :")
        self.port_combo = QComboBox()
        self.port_combo.addItems(self.get_available_ports())
        self.baudrate_label = QLabel("Sélectionnez le baudrate :")
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "115200", "230400", "460800"])
        self.baudrate_combo.setCurrentText("115200")
        self.ok_button = QPushButton("Valider")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_combo)
        layout.addWidget(self.baudrate_label)
        layout.addWidget(self.baudrate_combo)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)


    def accept(self):
        self.selected_port = self.port_combo.currentText()
        self.selected_baudrate = int(self.baudrate_combo.currentText())
        super().accept()


    def get_available_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]