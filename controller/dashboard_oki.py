import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QPushButton

# Ganti 'dashboard_oki' & 'Ui_MainWindow' sesuai nama file di folder ui/ dan kelas UI-nya
try:
    from ui.dashboard_oki import Ui_MainWindow as Ui_DashboardOKI
except ImportError:
    Ui_DashboardOKI = None


def _cari_widget(ui, daftar_nama, tipe):
    for nama in daftar_nama:
        w = getattr(ui, nama, None)
        if isinstance(w, tipe):
            return w
    return None


class DashboardOKIController(QMainWindow):
    def __init__(self, user_data: dict = None, parent=None):
        super().__init__(parent)
        self.user_data = user_data or {
            "id_pengguna": 3,
            "nama": "OKI",
            "nama_organisasi": "Organisasi Kemahasiswaan Intra",
            "role": "OKI",
        }
        self._child_windows = []

        if Ui_DashboardOKI is None:
            raise ImportError(
                "Sesuaikan import UI di bagian atas controller/dashboard_oki.py dengan file di folder ui/."
            )

        self.ui = Ui_DashboardOKI()
        self.ui.setupUi(self)
        self._hubungkan_navigasi()

    def _hubungkan_navigasi(self):
        btn_ruang = _cari_widget(
            self.ui,
            ["pushButton_lihat_ruang", "btn_lihat_ruang", "btnRuang", "pushButton_ruang"],
            QPushButton,
        )
        btn_jadwal = _cari_widget(
            self.ui,
            ["pushButton_jadwal", "btn_jadwal", "btnJadwalDisetujui", "pushButton_jadwal_disetujui"],
            QPushButton,
        )
        btn_ajukan = _cari_widget(
            self.ui,
            ["pushButton_ajukan", "btn_ajukan", "btnAjukanPeminjaman", "pushButton_ajukan_peminjaman"],
            QPushButton,
        )
        btn_riwayat = _cari_widget(
            self.ui,
            ["pushButton_riwayat", "btn_riwayat", "btnRiwayatPengajuan", "pushButton_riwayat_pengajuan"],
            QPushButton,
        )
        btn_logout = _cari_widget(
            self.ui,
            ["pushButton_logout", "btn_logout", "btnKeluar", "pushButton_keluar"],
            QPushButton,
        )

        if btn_ruang:
            btn_ruang.clicked.connect(self.buka_lihat_ruang)
        if btn_jadwal:
            btn_jadwal.clicked.connect(self.buka_jadwal_disetujui)
        if btn_ajukan:
            btn_ajukan.clicked.connect(self.buka_ajukan_peminjaman)
        if btn_riwayat:
            btn_riwayat.clicked.connect(self.buka_riwayat_pengajuan)
        if btn_logout:
            btn_logout.clicked.connect(self.logout)

    def _tampilkan_window(self, controller_cls):
        win = controller_cls(user_data=self.user_data, parent=self)
        self._child_windows.append(win)
        win.show()

    def buka_lihat_ruang(self):
        from controller.oki_lihat_ruang import OKILihatRuangController
        self._tampilkan_window(OKILihatRuangController)

    def buka_jadwal_disetujui(self):
        from controller.oki_jadwal_disetujui import OKIJadwalDisetujuiController
        self._tampilkan_window(OKIJadwalDisetujuiController)

    def buka_ajukan_peminjaman(self):
        from controller.oki_ajukan_peminjaman import OKIAjukanPeminjamanController
        self._tampilkan_window(OKIAjukanPeminjamanController)

    def buka_riwayat_pengajuan(self):
        from controller.oki_riwayat_pengajuan import OKIRiwayatPengajuanController
        self._tampilkan_window(OKIRiwayatPengajuanController)

    def logout(self):
        jawab = QMessageBox.question(
            self,
            "Konfirmasi Logout",
            "Yakin ingin keluar dari akun OKI?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if jawab == QMessageBox.Yes:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DashboardOKIController()
    win.show()
    sys.exit(app.exec_())