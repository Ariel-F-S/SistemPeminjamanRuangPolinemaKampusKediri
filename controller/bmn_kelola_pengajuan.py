from PyQt5.QtWidgets import (
    QMainWindow, QMessageBox, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt

from ui.verifikasi_ajuan_BMN import Ui_MainWindow
from model.User import User

class VerifikasiAjuanController(QMainWindow):

    def __init__(self, user=None):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.user = user or {}
        self.model = User()

        self.setup_filter()
        self.setup_table()
        self.connect_signals()
        self.load_data()

    def setup_filter(self):
        self.ui.comboBox.clear()
        self.ui.comboBox.addItems([
            "Menunggu",
            "Disetujui",
            "Ditolak",
            "Semua"
        ])

        self.ui.comboBox.setCurrentText("Menunggu")

        self.ui.lineEdit.setPlaceholderText(
            "Nama OKI / Kegiatan / Ruang"
        )

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

        self.ui.tableWidget.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.ui.tableWidget.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

    def connect_signals(self):
        self.ui.pushButton.clicked.connect(self.menu_dashboard)
        self.ui.pushButton_2.clicked.connect(self.menu_kelola_ruang)
        self.ui.pushButton_3.clicked.connect(self.load_data)
        self.ui.pushButton_4.clicked.connect(self.menu_riwayat)
        self.ui.pushButton_5.clicked.connect(self.menu_logout)

        self.ui.pushButton_6.clicked.connect(self.load_data)
        self.ui.pushButton_7.clicked.connect(self.aksi_verifikasi_detail)

        self.ui.lineEdit.returnPressed.connect(self.load_data)
        self.ui.comboBox.currentTextChanged.connect(self.load_data)

        self.ui.tableWidget.doubleClicked.connect(
            lambda index: self.aksi_verifikasi_detail()
        )

    def load_data(self):
        try:
            status = self.ui.comboBox.currentText()
            keyword = self.ui.lineEdit.text().strip()

            rows = self.model.daftar_pengajuan(
                status,
                keyword
            )

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
                "Gagal Memuat Pengajuan",
                str(e)
            )

    def aksi_verifikasi_detail(self):
        row = self.ui.tableWidget.currentRow()

        if row < 0:
            QMessageBox.warning(
                self,
                "Pilih Pengajuan",
                "Pilih salah satu pengajuan terlebih dahulu."
            )
            return

        id_pengajuan = self.ui.tableWidget.item(
            row, 0
        ).data(Qt.UserRole)

        from controller.dialog_verifikasi_pengajuan import (
            DialogVerifikasiPengajuanController
        )

        dialog = DialogVerifikasiPengajuanController(
            id_pengajuan,
            self.user,
            self
        )

        if dialog.exec_():
            self.load_data()

    def menu_dashboard(self):
        from controller.dashboard_bmn import DashboardBMNController

        self.win = DashboardBMNController(self.user)
        self.win.show()
        self.close()

    def menu_kelola_ruang(self):
        from controller.bmn_kelola_ruang import KelolaDataRuangController

        self.win = KelolaDataRuangController(self.user)
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