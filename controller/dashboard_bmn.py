from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QPushButton, QLabel
)
from PyQt5.QtCore import Qt
import ui.dashboard_bmn as _ui_form
from model.connectiondb import get_db_connection

_ui_name = [n for n in dir(_ui_form) if n.startswith("Ui_")][0]
_UiClass = getattr(_ui_form, _ui_name)
_BaseClass = QMainWindow if _ui_name == "Ui_MainWindow" else QWidget


class DashboardBMNController(_BaseClass):
    def __init__(self, user_data):
        super().__init__()
        self.ui = _UiClass()
        self.ui.setupUi(self)
        self.user = user_data

        # Tampilkan nama petugas BMN di label pojok kanan atas jika ada
        nama_bmn = self.user.get("nama", "Petugas BMN")
        for nama_lbl in ("lblBmn", "lblUser", "label_user", "label_bmn"):
            lbl = getattr(self.ui, nama_lbl, None)
            if isinstance(lbl, QLabel):
                lbl.setText(f"BMN: {nama_bmn}")
                break

        # Konfigurasi Tabel Pengajuan Masuk / Terbaru
        daftar_tbl = self.findChildren(QTableWidget)
        self.tabel = daftar_tbl[0] if daftar_tbl else None
        if self.tabel:
            self.tabel.setColumnCount(6)
            self.tabel.setHorizontalHeaderLabels([
                "ID", "Organisasi (OKI)", "Nama Kegiatan", "Ruang", "Waktu Pinjam", "Status"
            ])
            header = self.tabel.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Organisasi
            header.setSectionResizeMode(2, QHeaderView.Stretch)           # Nama Kegiatan
            header.setSectionResizeMode(3, QHeaderView.Stretch)           # Ruang
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Waktu Pinjam
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Status

            self.tabel.verticalHeader().setVisible(False)
            self.tabel.setWordWrap(True)
            self.tabel.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tabel.setSelectionMode(QAbstractItemView.SingleSelection)
            self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.tabel.doubleClicked.connect(self.buka_verifikasi_atau_detail)

        # Hubungkan tombol aksi & navigasi sidebar BMN secara otomatis
        for btn in self.findChildren(QPushButton):
            teks = btn.text().lower()
            obj = btn.objectName().lower()

            if "dashboard" in teks or "dashboard" in obj:
                btn.clicked.connect(self.load_data)
            elif "verifikasi" in teks or "pengajuan" in teks or "verifikasi" in obj:
                btn.clicked.connect(self.buka_verifikasi_pengajuan)
            elif "ruang" in teks or "ruang" in obj:
                btn.clicked.connect(self.buka_kelola_ruang)
            elif "riwayat" in teks or "laporan" in teks or "riwayat" in obj:
                btn.clicked.connect(self.buka_riwayat_bmn)
            elif "logout" in teks or "keluar" in teks or "logout" in obj:
                btn.clicked.connect(self.logout)

        self.load_data()

    def load_data(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Hitung statistik ringkasan pengajuan untuk kartu BMN
        cursor.execute(
            "SELECT status_pengajuan, COUNT(*) FROM pengajuan_peminjaman GROUP BY status_pengajuan"
        )
        stat = {"Menunggu": 0, "Disetujui": 0, "Ditolak": 0, "Selesai": 0}
        for r in cursor.fetchall() or []:
            stat[r[0]] = r[1]

        jml_menunggu = stat["Menunggu"]
        jml_disetujui = stat["Disetujui"] + stat["Selesai"]
        jml_ditolak = stat["Ditolak"]

        # Isi label kartu statistik (mendukung penamaan khusus maupun bawaan Qt Designer)
        mapping_kartu = [
            (["lblMenunggu", "lblPending", "label_4"], f"Menunggu: {jml_menunggu}", str(jml_menunggu)),
            (["lblDisetujui", "lblApproved", "label_6"], f"Disetujui: {jml_disetujui}", str(jml_disetujui)),
            (["lblDitolak", "lblRejected", "label_8"], f"Ditolak: {jml_ditolak}", str(jml_ditolak)),
        ]
        for kandidat_nama, teks_panjang, angka_saja in mapping_kartu:
            for nama in kandidat_nama:
                lbl = getattr(self.ui, nama, None)
                if isinstance(lbl, QLabel):
                    # Jika label kartu bertipe lblMenunggu/Disetujui/Ditolak, tampilkan label + angka
                    if nama.startswith("lbl"):
                        lbl.setText(teks_panjang)
                    else:
                        lbl.setText(angka_saja)
                    break

        # 2. Ambil daftar pengajuan (prioritaskan status 'Menunggu' di paling atas)
        sql = """
            SELECT p.id_pengajuan, COALESCE(u.nama_organisasi, u.nama), p.nama_kegiatan,
                   r.kode_ruang, r.nama_ruang, p.tanggal_mulai, p.tanggal_selesai, p.status_pengajuan
            FROM pengajuan_peminjaman p
            JOIN ruang r ON p.id_ruang = r.id_ruang
            JOIN pengguna u ON p.id_oki = u.id_pengguna
            ORDER BY FIELD(p.status_pengajuan, 'Menunggu', 'Disetujui', 'Selesai', 'Ditolak'),
                     p.id_pengajuan DESC
        """
        cursor.execute(sql)
        rows = cursor.fetchall() or []
        conn.close()

        if not self.tabel:
            return

        self.tabel.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            waktu = f"{row[5].strftime('%d-%m-%Y %H:%M')} s/d {row[6].strftime('%H:%M')}"
            items = [
                str(row[0]), row[1], row[2],
                f"{row[3]} - {row[4]}", waktu, row[7]
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, row[0])
                if col in (0, 4, 5):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tabel.setItem(idx, col, item)

        self.tabel.resizeRowsToContents()

    def buka_verifikasi_atau_detail(self):
        if not self.tabel:
            return
        row_idx = self.tabel.currentRow()
        if row_idx < 0:
            return
        id_pengajuan = self.tabel.item(row_idx, 0).data(Qt.UserRole)

        try:
            from controller.dialog_verifikasi_pengajuan import DialogVerifikasiPengajuanController
            dialog = DialogVerifikasiPengajuanController(id_pengajuan, self.user, parent=self)
            dialog.exec_()
            self.load_data()
        except Exception:
            from controller.dialog_detail_pengajuan import DialogDetailPengajuanController
            dialog = DialogDetailPengajuanController(id_pengajuan, parent=self)
            dialog.exec_()

    def buka_verifikasi_pengajuan(self):
        # Sesuaikan dengan nama file controller verifikasi BMN milik temanmu
        try:
            from controller.dialog_verifikasi_pengajuan import BmnVerifikasiPengajuanController
            self.win = BmnVerifikasiPengajuanController(self.user)
            self.win.show()
            self.close()
        except ImportError as e:
            QMessageBox.information(self, "Info Navigasi", f"Controller halaman verifikasi belum tersedia:\n{e}")

    def buka_kelola_ruang(self):
        try:
            from controller.bmn_kelola_ruang import BmnKelolaRuangController
            self.win = BmnKelolaRuangController(self.user)
            self.win.show()
            self.close()
        except ImportError as e:
            QMessageBox.information(self, "Info Navigasi", f"Controller halaman kelola ruang belum tersedia:\n{e}")

    def buka_riwayat_bmn(self):
        try:
            from controller.bmn_riwayat_peminjaman import RiwayatPeminjamanBMNController
            self.win = RiwayatPeminjamanBMNController(self.user)
            self.win.show()
            self.close()
        except ImportError as e:
            QMessageBox.information(self, "Info Navigasi", f"Controller halaman riwayat BMN belum tersedia:\n{e}")

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