from PyQt5 import QtWidgets

import sys
from ui.dashboard_admin import Ui_MainWindow as AdminUI
from model.User import User

class  HalamanAdmin(QtWidgets.QMainWindow, AdminUI):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.user = User()
        self.pushButton.clicked.connect(self.dashboard)
        self.pushButton_2.clicked.connect(self.kelola_akun)
        self.pushButton_3.clicked.connect(self.data_ruang)
        self.pushButton_4.clicked.connect(self.pengajuan)
        self.pushButton_5.clicked.connect(self.detail_pengajuan)
        self.pushButton_6.clicked.connect(self.keluar)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(["Nama", "Password", "level"])
        self.tampil_tabel()

    def tampil_tabel(self):
        data = self.user.select_data_tabel()
        self.tableWidget.setRowCount(0)
        for row_data in data:
            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            for col, val in enumerate(row_data):
                self.tableWidget.setItem(row, col, QtWidgets.QTableWidgetItem(str(val)))        