import sys
import threading
from time import sleep

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QMessageBox, QDesktopWidget, \
    QInputDialog
from PyQt5 import QtGui, QtCore
from pymodbus.client.sync import ModbusTcpClient


class WagoGUI(QMainWindow):
    def __init__(self, wago_ip, wago_port):
        super().__init__()

        self.wago_ip = wago_ip
        self.wago_port = wago_port
        self.output_states = [False] * 16

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('PSB UI')
        self.setGeometry(100, 100, 500, 350)
        self.setStyleSheet("background-color: #d9d9d9;")

        self.setWindowIcon(QIcon('icon.png'))

        logo_label = QLabel(self)
        pixmap = QtGui.QPixmap('LOGO.png')
        logo_label.setPixmap(pixmap)
        logo_label.setGeometry(10, 10, pixmap.width(), pixmap.height())

        additional_label = QLabel("750-362", self)
        additional_label.setGeometry(20 + pixmap.width(), 15, 200, 30)

        # self.connecting_status_label = QLabel(self)
        # self.connecting_status_label.setGeometry(110 + pixmap.width(), 300, 200, 30)

        self.connecting_status_label = QLabel(self)
        self.connecting_status_label.setGeometry(160, 300, 230, 30)
        self.connecting_status_label.setAlignment(QtCore.Qt.AlignCenter)
        # self.connecting_status_label.setStyleSheet("background-color: #fff;")

        self.plc_ip_label = QLabel("IP: " + self.wago_ip, self)
        self.plc_ip_label.setGeometry(self.width() - 110, 15, 180, 30)

        self.plc_ip_label = QLabel("IP: " + self.wago_ip, self)
        self.plc_ip_label.setGeometry(self.width() - 200, 15, 180, 30)

        self.update_ip_button = QPushButton('Change IP', self)
        self.update_ip_button.setGeometry(self.width() - 100, 15, 80, 30)
        self.update_ip_button.clicked.connect(self.update_ip_label)

        self.status_label = QLabel(self)
        self.status_label.setGeometry(90, pixmap.height() + 35, 330, 30)
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setStyleSheet("background-color: #fff;")

        self.output_buttons = []
        for i in range(16):
            button = QPushButton(f'#DO {i + 1}', self)
            button.setGeometry(100 + (i % 4) * 80, pixmap.height() + 100 + (i // 4) * 40, 70, 30)
            button.clicked.connect(lambda _, output=i + 1: self.toggle_output(output))
            self.output_buttons.append(button)

        desktop = QDesktopWidget().screenGeometry()
        center_x = desktop.width() // 2 - self.width() // 2
        center_y = desktop.height() // 2 - self.height() // 2
        self.move(center_x, center_y)
        self.setFixedSize(self.size())

    def connect_to_plc(self):
        self.modbus_client = ModbusTcpClient(self.wago_ip, self.wago_port)
        if not self.modbus_client.connect():
            self.connecting_status_label.setText(f"Status: Unable to connect to {self.wago_ip}")
            self.disable_buttons()
        else:
            self.connecting_status_label.setText(f"Status: Connected")
            self.enable_buttons()

    def update_indicators(self, output, is_on):
        if is_on:
            self.status_label.setText(f'DO {output + 1} Turned ON')
        else:
            self.status_label.setText(f'DO {output + 1} Turned OFF')

    def toggle_output(self, output):
        self.current_output = output
        # threading.Thread(target=self.connect_to_plc).start()

        output_address = self.output_buttons.index(self.sender())
        current_state = self.output_states[output_address - 1]
        new_state = not current_state

        self.modbus_client.write_coil(output_address, new_state)
        self.update_indicators(output_address, new_state)

        self.output_states[output_address - 1] = new_state

        self.modbus_client.close()

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            'Exit Confirmation',
            'Are you sure you want to exit?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def disable_buttons(self):
        for button in self.output_buttons:
            button.setEnabled(False)

    def enable_buttons(self):
        for button in self.output_buttons:
            button.setEnabled(True)

    def update_ip_label(self):
        ip_dialog = QInputDialog()
        new_ip, ok = ip_dialog.getText(self, 'WAGO IP', 'Enter the WAGO IP address:')
        if ok and new_ip:
            self.wago_ip = new_ip
            self.plc_ip_label.setText("IP: " + self.wago_ip)
            threading.Thread(target=self.connect_to_plc).start()
        else:
            QMessageBox.warning(self, 'Invalid IP', 'Invalid or empty IP address entered.', QMessageBox.Ok)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WagoGUI("", 502)
    window.show()

    window.update_ip_label()
    WagoGUI.disable_buttons(window)
    sys.exit(app.exec_())
