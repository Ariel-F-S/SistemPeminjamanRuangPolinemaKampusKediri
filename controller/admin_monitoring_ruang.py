from PyQt5.QtWidgets import QMainWindow, QMessageBox, QHeaderView, QAbstractItemView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
from ui.data_ruang_admin import Ui_MainWindow
from model.User import User
from model.connectiondb import get_db_connection


class AdminMonitoringRuangController(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.user = user_data
        self.model = User()

        self.ui.lineEdit.setPlaceholderText("Kode / nama ruang...")
        self.ui.comboBox.setStyleSheet("")
        self._load_filter_gedung()

        self.table_model = QStandardItemModel()
        self.ui.tableView.setModel(self.table_model)
        self.ui.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tableView.verticalHeader().setVisible(False)
        self.ui.tableView.setWordWrap(True)

        self.ui.pushButton.clicked.connect(self.buka_dashboard)
        self.ui.pushButton_2.clicked.connect(self.buka_kelola_akun)
        self.ui.pushButton_3.clicked.connect(self.refresh_semua)
        self.ui.pushButton_4.clicked.connect(self.buka_monitoring_pengajuan)
        self.ui.pushButton_5.clicked.connect(self.buka_monitoring_peminjaman)
        self.ui.pushButton_6.clicked.connect(self.logout)

        self.ui.pushButton_7.clicked.connect(self.load_data)
        self.ui.lineEdit.returnPressed.connect(self.load_data)
        self.ui.comboBox.currentTextChanged.connect(self.load_data)

        self.load_data()

    def _load_filter_gedung(self):
        self.ui.comboBox.blockSignals(True)
        self.ui.comboBox.clear()
        self.ui.comboBox.addItem("Semua")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nama_gedung FROM lokasi_gedung ORDER BY nama_gedung ASC")
        gedung_list = [r[0] for r in cursor.fetchall() or []]
        conn.close()

        self.ui.comboBox.addItems(gedung_list)
        self.ui.comboBox.blockSignals(False)

    def refresh_semua(self):
        self.ui.lineEdit.clear()
        self._load_filter_gedung()
        self.load_data()

    def load_data(self):
        keyword = self.ui.lineEdit.text().strip()
        gedung = self.ui.comboBox.currentText()
        rows = self.model.select_data_ruang(keyword=keyword, gedung=gedung) or []

        self.table_model.clear()
        self.table_model.setHorizontalHeaderLabels([
            "Kode Ruang", "Nama Ruang", "Gedung", "Kapasitas", "Fasilitas", "Status"
        ])

        header = self.ui.tableView.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

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
        for r in range(self.table_model.rowCount()):
            if self.ui.tableView.rowHeight(r) < 52:
                self.ui.tableView.setRowHeight(r, 52)

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