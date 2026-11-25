from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
from ui.pengajuan_admin import Ui_MainWindow
from model.User import User


class AdminMonitoringPengajuanController(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.user = user_data
        self.model = User()

        # Setup filter & pencarian jika ada di pengajuan_admin.ui
        if hasattr(self.ui, "lineEdit"):
            self.ui.lineEdit.setPlaceholderText("Cari kegiatan / organisasi / ruang...")
            self.ui.lineEdit.returnPressed.connect(self.load_data)

        if hasattr(self.ui, "comboBox"):
            self.ui.comboBox.clear()
            self.ui.comboBox.addItems(["Semua", "Menunggu", "Disetujui", "Ditolak", "Selesai"])
            self.ui.comboBox.setCurrentText("Menunggu")
            self.ui.comboBox.currentTextChanged.connect(self.load_data)

        if hasattr(self.ui, "pushButton_7"):
            self.ui.pushButton_7.clicked.connect(self.load_data)

        # Setup tabel (otomatis mendukung tableView maupun tableWidget)
        if hasattr(self.ui, "tableView"):
            self.table_model = QStandardItemModel()
            self.ui.tableView.setModel(self.table_model)
            self.ui.tableView.verticalHeader().setVisible(False)
            self.ui.tableView.setWordWrap(True)
            self.ui.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.ui.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
            self.ui.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.ui.tableView.doubleClicked.connect(self.buka_detail_pengajuan)
        elif hasattr(self.ui, "tableWidget"):
            self.ui.tableWidget.setColumnCount(6)
            self.ui.tableWidget.setHorizontalHeaderLabels([
                "ID", "Organisasi (OKI)", "Nama Kegiatan", "Ruang", "Waktu Pinjam", "Status"
            ])
            self._atur_proporsi_kolom(self.ui.tableWidget.horizontalHeader())
            self.ui.tableWidget.verticalHeader().setVisible(False)
            self.ui.tableWidget.setWordWrap(True)
            self.ui.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.ui.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
            self.ui.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.ui.tableWidget.doubleClicked.connect(self.buka_detail_pengajuan)

        # Tombol Detail jika ada di UI (misal pushButton_8)
        if hasattr(self.ui, "pushButton_8"):
            self.ui.pushButton_8.clicked.connect(self.buka_detail_pengajuan)

        # Navigasi Sidebar Admin
        self.ui.pushButton.clicked.connect(self.buka_dashboard)
        self.ui.pushButton_2.clicked.connect(self.buka_kelola_akun)
        self.ui.pushButton_3.clicked.connect(self.buka_monitoring_ruang)
        self.ui.pushButton_4.clicked.connect(self.load_data)
        self.ui.pushButton_5.clicked.connect(self.buka_monitoring_peminjaman)
        self.ui.pushButton_6.clicked.connect(self.logout)

        self.load_data()

    def _atur_proporsi_kolom(self, header):
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Organisasi (OKI)
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Nama Kegiatan
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Ruang
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Waktu Pinjam
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Status

    def load_data(self):
        status_filter = self.ui.comboBox.currentText() if hasattr(self.ui, "comboBox") else "Menunggu"
        keyword = self.ui.lineEdit.text().strip().lower() if hasattr(self.ui, "lineEdit") else ""

        rows = self.model.select_pengajuan_admin(status_filter) or []
        if keyword:
            rows = [
                r for r in rows
                if keyword in str(r[1]).lower()
                or keyword in str(r[2]).lower()
                or keyword in str(r[3]).lower()
                or keyword in str(r[4]).lower()
            ]

        headers = ["ID", "OKI", "Kegiatan", "Ruang", "Waktu Pinjam", "Status"]

        if hasattr(self.ui, "tableView"):
            self.table_model.clear()
            self.table_model.setHorizontalHeaderLabels(headers)
            self._atur_proporsi_kolom(self.ui.tableView.horizontalHeader())

            for row in rows:
                waktu = f"{row[5].strftime('%d-%m-%Y %H:%M')} s/d {row[6].strftime('%H:%M')}"

                item_id = QStandardItem(str(row[0]))
                item_id.setData(row[0], Qt.UserRole)
                item_id.setTextAlignment(Qt.AlignCenter)

                item_waktu = QStandardItem(waktu)
                item_waktu.setTextAlignment(Qt.AlignCenter)

                item_status = QStandardItem(row[7])
                item_status.setTextAlignment(Qt.AlignCenter)

                self.table_model.appendRow([
                    item_id,
                    QStandardItem(row[1]),
                    QStandardItem(row[2]),
                    QStandardItem(f"{row[3]} - {row[4]}"),
                    item_waktu,
                    item_status,
                ])
            self.ui.tableView.resizeRowsToContents()

        elif hasattr(self.ui, "tableWidget"):
            self.ui.tableWidget.setRowCount(len(rows))
            for idx, row in enumerate(rows):
                waktu = f"{row[5].strftime('%d-%m-%Y %H:%M')} s/d {row[6].strftime('%H:%M')}"
                items = [str(row[0]), row[1], row[2], f"{row[3]} - {row[4]}", waktu, row[7]]
                for col, val in enumerate(items):
                    item = QTableWidgetItem(val)
                    item.setData(Qt.UserRole, row[0])
                    if col in (0, 4, 5):
                        item.setTextAlignment(Qt.AlignCenter)
                    self.ui.tableWidget.setItem(idx, col, item)
            self.ui.tableWidget.resizeRowsToContents()

    def buka_detail_pengajuan(self):
        id_pengajuan = None
        if hasattr(self.ui, "tableView"):
            indexes = self.ui.tableView.selectionModel().selectedRows()
            if not indexes:
                QMessageBox.warning(self, "Peringatan", "Pilih salah satu pengajuan terlebih dahulu!")
                return
            id_pengajuan = self.table_model.item(indexes[0].row(), 0).data(Qt.UserRole)
        elif hasattr(self.ui, "tableWidget"):
            row_idx = self.ui.tableWidget.currentRow()
            if row_idx < 0:
                QMessageBox.warning(self, "Peringatan", "Pilih salah satu pengajuan terlebih dahulu!")
                return
            id_pengajuan = self.ui.tableWidget.item(row_idx, 0).data(Qt.UserRole)

        if id_pengajuan:
            from controller.dialog_detail_pengajuan import DialogDetailPengajuanController
            dialog = DialogDetailPengajuanController(id_pengajuan, parent=self)
            dialog.exec_()

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

    def buka_monitoring_ruang(self):
        from controller.admin_monitoring_ruang import AdminMonitoringRuangController
        self.win = AdminMonitoringRuangController(self.user)
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