from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5.QtCore import Qt
from ui.dashboard_admin import Ui_MainWindow
from model.User import User


class DashboardAdminController(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.user = user_data
        self.model = User()

        self.ui.label_2.setText("Akun OKI :")
        self.ui.label_5.setText("Akun BMN :")
        self.ui.label_7.setText("Akun Admin :")

        self.ui.tableWidget.setColumnCount(6)
        self.ui.tableWidget.setHorizontalHeaderLabels([
            "ID", "Organisasi (OKI)", "Nama Kegiatan", "Ruang", "Waktu Pinjam", "Status"
        ])
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tableWidget.doubleClicked.connect(self.buka_detail_pengajuan)

        self.ui.pushButton.clicked.connect(self.load_data)
        self.ui.pushButton_2.clicked.connect(self.buka_kelola_akun)
        self.ui.pushButton_3.clicked.connect(self.buka_monitoring_ruang)
        self.ui.pushButton_4.clicked.connect(self.buka_monitoring_pengajuan)
        self.ui.pushButton_5.clicked.connect(self.buka_monitoring_peminjaman)
        self.ui.pushButton_6.clicked.connect(self.logout)

        self.load_data()

    def load_data(self):
        stat = self.model.get_statistik_dashboard()
        self.ui.label_4.setText(str(stat["OKI"]))
        self.ui.label_6.setText(str(stat["BMN"]))
        self.ui.label_8.setText(str(stat["Admin"]))
        self.ui.label_10.setText(str(stat["Disetujui"]))
        self.ui.label_11.setText("Aktivitas Pengajuan Terbaru")

        rows = self.model.select_pengajuan_admin("Semua")
        self.ui.tableWidget.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            waktu = f"{row[5].strftime('%d-%m-%Y %H:%M')} s/d {row[6].strftime('%H:%M')}"
            items = [str(row[0]), row[1], row[2], f"{row[3]} - {row[4]}", waktu, row[7]]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, row[0])
                self.ui.tableWidget.setItem(idx, col, item)

    def buka_detail_pengajuan(self):
        row_idx = self.ui.tableWidget.currentRow()
        if row_idx < 0:
            return
        id_pengajuan = self.ui.tableWidget.item(row_idx, 0).data(Qt.UserRole)
        from controller.dialog_detail_pengajuan import DialogDetailPengajuanController
        dialog = DialogDetailPengajuanController(id_pengajuan, parent=self)
        dialog.exec_()

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