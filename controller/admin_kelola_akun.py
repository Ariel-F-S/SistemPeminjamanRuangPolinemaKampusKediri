from PyQt5.QtWidgets import QMainWindow, QMessageBox, QHeaderView, QAbstractItemView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
from ui.kelola_akun_admin import Ui_MainWindow
from model.User import User


class AdminKelolaAkunController(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.user = user_data
        self.model = User()

        self.ui.lineEdit.setPlaceholderText("Cari nama / username...")
        self.ui.comboBox.clear()
        self.ui.comboBox.addItems(["Semua", "Admin", "BMN", "OKI"])

        self.table_model = QStandardItemModel()
        self.ui.tableView.setModel(self.table_model)
        self.ui.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tableView.verticalHeader().setVisible(False)
        self.ui.tableView.setWordWrap(True)

        self.ui.pushButton.clicked.connect(self.buka_dashboard)
        self.ui.pushButton_3.clicked.connect(self.buka_monitoring_ruang)
        self.ui.pushButton_4.clicked.connect(self.buka_monitoring_pengajuan)
        self.ui.pushButton_5.clicked.connect(self.buka_monitoring_peminjaman)
        self.ui.pushButton_6.clicked.connect(self.logout)

        self.ui.pushButton_7.clicked.connect(self.load_data)
        self.ui.lineEdit.returnPressed.connect(self.load_data)
        self.ui.comboBox.currentTextChanged.connect(self.load_data)
        self.ui.pushButton_8.clicked.connect(self.buka_tambah_akun)
        self.ui.pushButton_9.clicked.connect(self.buka_ubah_akun)
        self.ui.pushButton_10.clicked.connect(self.hapus_akun)

        self.load_data()

    def load_data(self):
        keyword = self.ui.lineEdit.text().strip()
        role_filter = self.ui.comboBox.currentText()
        rows = self.model.select_data_tabel(keyword=keyword, role_filter=role_filter)

        self.table_model.clear()
        self.table_model.setHorizontalHeaderLabels([
            "ID", "Username", "Nama/OKI", "No.Wa", "Role", "Status"
        ])

        header = self.ui.tableView.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Username
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Nama/OKI
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # No.Wa
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Role
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Status

        for row in rows:
            item_id = QStandardItem(str(row[0]))
            item_id.setData(row[0], Qt.UserRole)
            item_id.setTextAlignment(Qt.AlignCenter)

            item_no_wa = QStandardItem(row[3] or "-")
            item_no_wa.setTextAlignment(Qt.AlignCenter)

            item_role = QStandardItem(row[4])
            item_role.setTextAlignment(Qt.AlignCenter)

            item_status = QStandardItem(row[5])
            item_status.setTextAlignment(Qt.AlignCenter)

            self.table_model.appendRow([
                item_id,
                QStandardItem(row[1]),
                QStandardItem(row[2]),
                item_no_wa,
                item_role,
                item_status,
            ])

        self.ui.tableView.resizeRowsToContents()

    def _get_selected_id(self):
        indexes = self.ui.tableView.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.table_model.item(indexes[0].row(), 0).data(Qt.UserRole)

    def buka_tambah_akun(self):
        from controller.dialog_tambah_akun import DialogTambahAkunController
        dialog = DialogTambahAkunController(parent=self)
        if dialog.exec_():
            self.load_data()

    def buka_ubah_akun(self):
        id_pengguna = self._get_selected_id()
        if not id_pengguna:
            QMessageBox.warning(self, "Peringatan", "Pilih salah satu akun pada tabel terlebih dahulu!")
            return
        from controller.dialog_ubah_akun import DialogUbahAkunController
        dialog = DialogUbahAkunController(id_pengguna, parent=self)
        if dialog.exec_():
            self.load_data()

    def hapus_akun(self):
        id_pengguna = self._get_selected_id()
        if not id_pengguna:
            QMessageBox.warning(self, "Peringatan", "Pilih akun yang ingin dihapus terlebih dahulu!")
            return
        if id_pengguna == self.user["id_pengguna"]:
            QMessageBox.warning(self, "Peringatan", "Tidak dapat menghapus akun yang sedang digunakan login!")
            return

        reply = QMessageBox.question(
            self, "Konfirmasi Hapus", "Apakah Anda yakin ingin menghapus akun ini?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.model.delete_data(id_pengguna):
                QMessageBox.information(self, "Sukses", "Data akun berhasil dihapus.")
                self.load_data()
            else:
                QMessageBox.critical(
                    self, "Gagal Menghapus",
                    "Akun tidak dapat dihapus karena masih memiliki relasi data pengajuan peminjaman!"
                )

    def buka_dashboard(self):
        from controller.dashboard_admin import DashboardAdminController
        self.win = DashboardAdminController(self.user)
        self.win.show()
        self.close()

    def buka_monitoring_ruang(self):
        from controller.admin_monitoring_ruang import AdminMonitoringRuangController
        self.win = AdminMonitoringRuangController(self.user)
        self.win.show()
        self.close()

    def buka_monitoring_pengajuan(self):
        from controller.admin_monitoring_pengajuan import AdminMonitoringPengajuanController
        self.win = AdminMonitoringPengajuanController(self.user)
        self.win.show()
        self.close()

    def buka_monitoring_peminjaman(self):
        from controller.admin_monitoring_peminjaman import AdminMonitoringPeminjamanController
        self.win = AdminMonitoringPeminjamanController(self.user)
        self.win.show()
        self.close()

    def logout(self):
        reply = QMessageBox.question(
            self, "Konfirmasi Logout", "Apakah Anda yakin ingin keluar dari sistem?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            from controller.login import LoginController
            self.login_win = LoginController()
            self.login_win.show()
            self.close()