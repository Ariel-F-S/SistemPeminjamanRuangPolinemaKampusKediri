from PyQt5.QtWidgets import (
    QMainWindow, QMessageBox, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt

from ui.dashboard_bmn import Ui_MainWindow
from model.User import User

class DashboardBMNController(QMainWindow):

    def __init__(self, user=None):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.user = user or {}
        self.model = User()

        self.setWindowTitle("Dashboard BMN - POLINEMA PSDKU KEDIRI")

        self.setup_table()
        self.connect_signals()
        self.load_data()

    def setup_table(self):
        self.ui.tableWidget.setColumnCount(6)
        self.ui.tableWidget.setHorizontalHeaderLabels([
            "ID", "Organisasi", "Kegiatan",
            "Ruang", "Waktu Pinjam", "Status"
        ])

        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.ui.tableWidget.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.ui.tableWidget.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

    def connect_signals(self):
        self.ui.pushButton.clicked.connect(self.load_data)
        self.ui.pushButton_2.clicked.connect(self.menu_kelola_ruang)
        self.ui.pushButton_3.clicked.connect(self.menu_verifikasi)
        self.ui.pushButton_4.clicked.connect(self.menu_riwayat)
        self.ui.pushButton_5.clicked.connect(self.menu_logout)

    def load_data(self):
        try:
            menunggu, tersedia, terpakai = self.model.ringkasan()

            self.ui.label_4.setText(str(menunggu))
            self.ui.label_6.setText(str(tersedia))
            self.ui.label_8.setText(str(terpakai))

            rows = self.model.daftar_pengajuan("Menunggu")

            self.ui.tableWidget.setRowCount(len(rows))

            for i, row in enumerate(rows):

                waktu = (
                    f"{row[5].strftime('%d-%m-%Y %H:%M')} "
                    f"s/d {row[6].strftime('%H:%M')}"
                )

                values = [
                    row[0],
                    row[1],
                    row[2],
                    f"{row[3]} - {row[4]}",
                    waktu,
                    row[7]
                ]

                for j, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setData(Qt.UserRole, row[0])
                    self.ui.tableWidget.setItem(i, j, item)

            self.ui.tableWidget.resizeRowsToContents()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Gagal Memuat Dashboard",
                str(e)
            )

    def menu_kelola_ruang(self):
        from controller.bmn_kelola_ruang import KelolaDataRuangController

        self.win = KelolaDataRuangController(self.user)
        self.win.show()
        self.close()

    def menu_verifikasi(self):
        from controller.bmn_kelola_pengajuan import VerifikasiAjuanController

        self.win = VerifikasiAjuanController(self.user)
        self.win.show()
        self.close()

    def menu_riwayat(self):
        from controller.bmn_riwayat_peminjaman import RiwayatPeminjamanController

        self.win = RiwayatPeminjamanController(self.user)
        self.win.show()
        self.close()

    def menu_logout(self):
        reply = QMessageBox.question(
            self,
            "Konfirmasi Logout",
            "Yakin ingin keluar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            from controller.login import LoginController

            self.login_win = LoginController()
            self.login_win.show()
            self.close()