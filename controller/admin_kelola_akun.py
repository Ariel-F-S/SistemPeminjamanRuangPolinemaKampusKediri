from PyQt5 import QtWidgets

from ui.kelola_akun_admin import Ui_MainWindow as KelolaAkunUI
from model.User import User
from controller.dashboard_admin import HalamanAdmin
from controller.admin_monitoring_ruang import AdminMonitoringRuang
from controller.admin_monitoring_pengajuan import AdminMonitoringPengajuan
from controller.admin_monitoring_peminjaman import AdminMonitoringPeminjaman


class AdminKelolaAkun(QtWidgets.QMainWindow, KelolaAkunUI):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.user = User()

        # tombol
        self.pushButton.clicked.connect(self.dashboard)
        self.pushButton_2.clicked.connect(self.kelola_akun)
        self.pushButton_3.clicked.connect(self.data_ruang)
        self.pushButton_4.clicked.connect(self.pengajuan)
        self.pushButton_5.clicked.connect(self.data_peminjaman)
        self.pushButton_6.clicked.connect(self.keluar)
        self.pushButton_8.clicked.connect(self.tambah_akun)
        self.pushButton_9.clicked.connect(self.ubah_akun)
        self.pushButton_10.clicked.connect(self.hapus_akun)

    def dashboard(self):
        self.halaman = HalamanAdmin()
        self.halaman.show()
        self.close()

    def data_ruang(self):
        self.halaman = AdminMonitoringRuang()
        self.halaman.show()
        self.close()

    def pengajuan(self):
        self.halaman = AdminMonitoringPengajuan()
        self.halaman.show()
        self.close()

    def data_peminjaman(self):
        self.halaman = AdminMonitoringPeminjaman()
        self.halaman.show()
        self.close()