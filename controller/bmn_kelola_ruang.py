from PyQt5.QtWidgets import (
    QMainWindow, QMessageBox, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt

from ui.kelola_data_ruang_BMN import Ui_MainWindow
from model.User import User

class KelolaDataRuangController(QMainWindow):

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
        self.ui.comboBox.addItem("Semua")
        self.ui.comboBox.addItems(self.model.daftar_gedung())

        self.ui.lineEdit.setPlaceholderText(
            "Kode / nama ruang / fasilitas"
        )

    def setup_table(self):
        self.ui.tableWidget.setColumnCount(6)

        self.ui.tableWidget.setHorizontalHeaderLabels([
            "ID", "Kode Ruang", "Nama Ruang",
            "Gedung", "Kapasitas", "Status"
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
        self.ui.pushButton_2.clicked.connect(self.load_data)
        self.ui.pushButton_3.clicked.connect(self.menu_verifikasi)
        self.ui.pushButton_4.clicked.connect(self.menu_riwayat)
        self.ui.pushButton_5.clicked.connect(self.menu_logout)

        self.ui.pushButton_6.clicked.connect(self.load_data)
        self.ui.pushButton_7.clicked.connect(self.aksi_tambah)
        self.ui.pushButton_8.clicked.connect(self.aksi_ubah)
        self.ui.pushButton_9.clicked.connect(self.aksi_hapus)

        self.ui.lineEdit.returnPressed.connect(self.load_data)
        self.ui.comboBox.currentTextChanged.connect(self.load_data)

    def load_data(self):
        try:
            rows = self.model.daftar_ruang(
                self.ui.lineEdit.text().strip(),
                self.ui.comboBox.currentText()
            )

            self.ui.tableWidget.setRowCount(len(rows))

            for i, row in enumerate(rows):

                values = [
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[6]
                ]

                for j, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setData(Qt.UserRole, row[0])
                    self.ui.tableWidget.setItem(i, j, item)

            self.ui.tableWidget.resizeRowsToContents()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Gagal Memuat Data",
                str(e)
            )

    def selected_id(self):
        row = self.ui.tableWidget.currentRow()

        if row < 0:
            QMessageBox.warning(
                self,
                "Pilih Data",
                "Pilih data ruang pada tabel terlebih dahulu."
            )
            return None

        return self.ui.tableWidget.item(
            row, 0
        ).data(Qt.UserRole)

    def aksi_tambah(self):
        from controller.dialog_tambah_ruang import DialogTambahRuangController

        dialog = DialogTambahRuangController(self)

        if dialog.exec_():
            self.load_data()

    def aksi_ubah(self):
        id_ruang = self.selected_id()

        if id_ruang is None:
            return

        from controller.dialog_ubah_ruang import DialogUbahRuangController

        dialog = DialogUbahRuangController(id_ruang, self)

        if dialog.exec_():
            self.load_data()

    def aksi_hapus(self):
        id_ruang = self.selected_id()

        if id_ruang is None:
            return

        reply = QMessageBox.question(
            self,
            "Konfirmasi Hapus",
            "Apakah kamu yakin ingin menghapus ruang ini?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                hasil = self.model.hapus_ruang(id_ruang)

                if hasil:
                    QMessageBox.information(
                        self,
                        "Berhasil",
                        "Data ruang berhasil dihapus."
                    )
                    self.load_data()
                else:
                    QMessageBox.warning(
                        self,
                        "Gagal",
                        "Data ruang tidak berhasil dihapus."
                    )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Gagal Menghapus",
                    f"Data tidak dapat dihapus.\n{e}"
                )

    def menu_dashboard(self):
        from controller.dashboard_bmn import DashboardBMNController

        self.win = DashboardBMNController(self.user)
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