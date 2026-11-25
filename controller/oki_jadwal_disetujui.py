from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QComboBox, QDateEdit, QPushButton, QLabel
)
from PyQt5.QtCore import Qt, QDate
from model.connectiondb import get_db_connection

try:
    import ui.jadwal_kampus as _ui_form
except ImportError:
    import ui.jadwal_kampus as _ui_form

_ui_name = [n for n in dir(_ui_form) if n.startswith("Ui_")][0]
_UiClass = getattr(_ui_form, _ui_name)
_BaseClass = QMainWindow if _ui_name == "Ui_MainWindow" else QWidget


class OKIJadwalDisetujuiController(_BaseClass):
    def __init__(self, user_data):
        super().__init__()
        self.ui = _UiClass()
        self.ui.setupUi(self)
        self.user = user_data
        self.pakai_filter_tanggal = False

        nama_oki = self.user.get("nama_organisasi") or self.user.get("nama", "OKI")
        lbl_oki = getattr(self.ui, "lblOki", None)
        if isinstance(lbl_oki, QLabel):
            lbl_oki.setText(f"OKI: {nama_oki}")

       
        daftar_cmb = self.findChildren(QComboBox)
        self.cmb_ruang = daftar_cmb[0] if daftar_cmb else None
        if self.cmb_ruang:
            self._load_filter_ruang()

        
        daftar_dt = self.findChildren(QDateEdit)
        self.dt_filter = daftar_dt[0] if daftar_dt else None
        if self.dt_filter:
            self.dt_filter.setDate(QDate.currentDate())
            self.dt_filter.dateChanged.connect(self._aktifkan_filter_tanggal)

       
        for btn in self.findChildren(QPushButton):
            if "cari" in btn.text().lower():
                btn.clicked.connect(self.cari_jadwal)
                break

        
        daftar_tbl = self.findChildren(QTableWidget)
        self.tabel = daftar_tbl[0] if daftar_tbl else None
        if self.tabel:
            self.tabel.setColumnCount(6)
            self.tabel.setHorizontalHeaderLabels([
                "Tanggal", "Waktu", "Ruang", "Organisasi (OKI)", "Nama Kegiatan", "Status"
            ])
            header = self.tabel.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.Stretch)
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

            self.tabel.verticalHeader().setVisible(False)
            self.tabel.setWordWrap(True)
            self.tabel.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tabel.setSelectionMode(QAbstractItemView.SingleSelection)
            self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers)

        
        for nama, fungsi in [
            ("btnDashboard", self.buka_dashboard),
            ("btnDaftarRuang", self.buka_daftar_ruang),
            ("btnAjukanPinjam", self.buka_ajukan_pinjam),
            ("btnRiwayat", self.buka_riwayat),
            ("btnJadwal", self.reset_dan_muat_semua),
            ("btnLogout", self.logout),
        ]:
            btn = getattr(self.ui, nama, None)
            if isinstance(btn, QPushButton):
                btn.clicked.connect(fungsi)

        self.load_data()

    def _load_filter_ruang(self):
        self.cmb_ruang.clear()
        self.cmb_ruang.addItem("Semua Ruang", None)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_ruang, kode_ruang, nama_ruang FROM ruang ORDER BY kode_ruang ASC")
        for r in cursor.fetchall() or []:
            self.cmb_ruang.addItem(f"{r[1]} - {r[2]}", r[0])
        conn.close()

    def _aktifkan_filter_tanggal(self):
        self.pakai_filter_tanggal = True

    def cari_jadwal(self):
        self.pakai_filter_tanggal = True
        self.load_data()

    def reset_dan_muat_semua(self):
        self.pakai_filter_tanggal = False
        if self.cmb_ruang:
            self.cmb_ruang.setCurrentIndex(0)
        self.load_data()

    def load_data(self):
        id_ruang = self.cmb_ruang.currentData() if self.cmb_ruang else None
        tgl_pilih = self.dt_filter.date().toPyDate() if (self.dt_filter and self.pakai_filter_tanggal) else None

        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT p.tanggal_mulai, p.tanggal_selesai, r.kode_ruang, r.nama_ruang,
                   COALESCE(u.nama_organisasi, u.nama), p.nama_kegiatan, p.status_pengajuan
            FROM pengajuan_peminjaman p
            JOIN ruang r ON p.id_ruang = r.id_ruang
            JOIN pengguna u ON p.id_oki = u.id_pengguna
            WHERE p.status_pengajuan IN ('Disetujui', 'Selesai')
        """
        params = []
        if id_ruang:
            sql += " AND p.id_ruang = %s"
            params.append(id_ruang)
        if tgl_pilih:
            sql += " AND DATE(p.tanggal_mulai) = %s"
            params.append(tgl_pilih)

        sql += " ORDER BY p.tanggal_mulai ASC"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall() or []
        conn.close()

        if not self.tabel:
            return

        self.tabel.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            tgl_str = row[0].strftime("%d-%m-%Y")
            jam_str = f"{row[0].strftime('%H:%M')} - {row[1].strftime('%H:%M')}"
            ruang_str = f"{row[2]} - {row[3]}"
            items = [tgl_str, jam_str, ruang_str, row[4], row[5], row[6]]

            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                if col in (0, 1, 5):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tabel.setItem(idx, col, item)

        self.tabel.resizeRowsToContents()

    def buka_dashboard(self):
        from controller.dashboard_oki import DashboardOKIController
        self.win = DashboardOKIController(self.user)
        self.win.show()
        self.close()

    def buka_daftar_ruang(self):
        from controller.oki_lihat_ruang import OkiLihatRuangController
        self.win = OkiLihatRuangController(self.user)
        self.win.show()
        self.close()

    def buka_ajukan_pinjam(self):
        from controller.oki_ajukan_peminjaman import OkiAjukanPeminjamanController
        self.win = OkiAjukanPeminjamanController(self.user)
        self.win.show()
        self.close()

    def buka_riwayat(self):
        from controller.oki_riwayat_pengajuan import OkiRiwayatPengajuanController
        self.win = OkiRiwayatPengajuanController(self.user)
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