from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QPlainTextEdit


class MultipleCommandDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.commands = None
        self.setWindowTitle("Commands")
        self.init_ui()


    def init_ui(self):
        layout = QVBoxLayout()
        self.commands_label = QLabel("Envoye une serie de commande :")
        self.command_text = QPlainTextEdit(self)
        self.ok_button = QPushButton("Valider")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.commands_label)
        layout.addWidget(self.command_text)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)


    def accept(self):
        self.commands = self.command_text.toPlainText()
        super().accept()

