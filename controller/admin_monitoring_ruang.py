from PyQt5.QtWidgets import QMainWindow, QMessageBox, QHeaderView, QAbstractItemView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
from ui.data_ruang_admin import Ui_MainWindow
from model.User import User


class AdminMonitoringRuangController(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.user = user_data
        self.model = User()

        self.ui.lineEdit.setPlaceholderText("Kode / nama ruang...")
        self.ui.comboBox.clear()
        self.ui.comboBox.addItems(["Semua", "Gedung A", "Gedung B"])

        self.table_model = QStandardItemModel()
        self.ui.tableView.setModel(self.table_model)
        self.ui.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tableView.verticalHeader().setVisible(False)
        self.ui.tableView.setWordWrap(True)

        self.ui.pushButton.clicked.connect(self.buka_dashboard)
        self.ui.pushButton_2.clicked.connect(self.buka_kelola_akun)
        self.ui.pushButton_4.clicked.connect(self.buka_monitoring_pengajuan)
        self.ui.pushButton_5.clicked.connect(self.buka_monitoring_peminjaman)
        self.ui.pushButton_6.clicked.connect(self.logout)

        self.ui.pushButton_7.clicked.connect(self.load_data)
        self.ui.lineEdit.returnPressed.connect(self.load_data)
        self.ui.comboBox.currentTextChanged.connect(self.load_data)

        self.load_data()

    def load_data(self):
        keyword = self.ui.lineEdit.text().strip()
        gedung = self.ui.comboBox.currentText()
        rows = self.model.select_data_ruang(keyword=keyword, gedung=gedung) or []

        self.table_model.clear()
        self.table_model.setHorizontalHeaderLabels([
            "Kode Ruang", "Nama Ruang", "Gedung", "Kapasitas", "Fasilitas", "Status"
        ])

        # Pasang ulang proporsi kolom setiap kali model di-clear
        header = self.ui.tableView.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Kode Ruang
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Nama Ruang
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Gedung
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Kapasitas
        header.setSectionResizeMode(4, QHeaderView.Stretch)           # Fasilitas
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Status

        for row in rows:
            item_kode = QStandardItem(row[0])
            item_kode.setTextAlignment(Qt.AlignCenter)

            item_gedung = QStandardItem(row[2])
            item_gedung.setTextAlignment(Qt.AlignCenter)

            item_kapasitas = QStandardItem(f"{row[3]} Org")
            item_kapasitas.setTextAlignment(Qt.AlignCenter)

            item_status = QStandardItem(row[5])
            item_status.setTextAlignment(Qt.AlignCenter)

            self.table_model.appendRow([
                item_kode,
                QStandardItem(row[1]),
                item_gedung,
                item_kapasitas,
                QStandardItem(row[4] or "-"),
                item_status,
            ])

        self.ui.tableView.resizeRowsToContents()

    def buka_dashboard(self):
        from controller.dashboard_admin import DashboardAdminController
        self.win = DashboardAdminController(self.user)
        self.win.show()
        self.close()

    def buka_kelola_akun(self):
        from controller.admin_kelola_akun import AdminKelolaAkunController
        self.win = AdminKelolaAkunController(self.user)
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