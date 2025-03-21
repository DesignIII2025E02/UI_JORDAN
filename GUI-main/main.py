import sys
from PyQt5.QtWidgets import QApplication, QDialog
from window.live_plot import LivePlot
from window.port_selection_dialog import PortSelectionDialog
from manager.data_manager import DataManager


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = PortSelectionDialog()
    if dialog.exec_() == QDialog.Accepted:
        selected_port = dialog.selected_port
        selected_baudrate = dialog.selected_baudrate

        data_manager = DataManager(selected_port, selected_baudrate, simulate_stm=False, simulate_prehenseur=False, dev_mode=True)
        data_manager.start()

        window = LivePlot(data_manager)
        window.setWindowTitle("Grue")
        window.showMaximized()

    sys.exit(app.exec_())
