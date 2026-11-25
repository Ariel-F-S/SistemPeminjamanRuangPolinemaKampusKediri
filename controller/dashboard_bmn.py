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

        nama_bmn = self.user.get("nama", "Petugas BMN")
        for nama_lbl in ("lblBmn", "lblUser", "label_user", "label_bmn"):
            lbl = getattr(self.ui, nama_lbl, None)
            if isinstance(lbl, QLabel):
                lbl.setText(f"BMN: {nama_bmn}")
                break

        # Simpan referensi 3 QLabel angka ('TextLabel') dari kiri ke kanan sekali saat init
        self.label_angka = sorted(
            [lbl for lbl in self.findChildren(QLabel) if lbl.text().strip().lower() == "textlabel"],
            key=lambda w: w.mapToGlobal(w.rect().topLeft()).x()
        )

        # Pengaturan lebar kolom tabel agar proporsional dan terbaca utuh
        daftar_tbl = self.findChildren(QTableWidget)
        self.tabel = daftar_tbl[0] if daftar_tbl else None
        if self.tabel:
            self.tabel.setColumnCount(6)
            self.tabel.setHorizontalHeaderLabels([
                "ID", "Organisasi (OKI)", "Nama Kegiatan", "Ruang", "Waktu Pinjam", "Status"
            ])
            header = self.tabel.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Interactive)
            header.setStretchLastSection(True)

            self.tabel.setColumnWidth(0, 42)   # ID
            self.tabel.setColumnWidth(1, 135)  # Organisasi (OKI)
            self.tabel.setColumnWidth(2, 185)  # Nama Kegiatan
            self.tabel.setColumnWidth(3, 165)  # Ruang
            self.tabel.setColumnWidth(4, 120)  # Waktu Pinjam (2 baris)
            self.tabel.setColumnWidth(5, 90)   # Status

            self.tabel.verticalHeader().setVisible(False)
            self.tabel.setWordWrap(True)
            self.tabel.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tabel.setSelectionMode(QAbstractItemView.SingleSelection)
            self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.tabel.doubleClicked.connect(self.buka_dialog_verifikasi)

        for btn in self.findChildren(QPushButton):
            teks = btn.text().lower()
            if "dashboard" in teks:
                btn.clicked.connect(self.load_data)
            elif "ruang" in teks:
                btn.clicked.connect(self.buka_kelola_ruang)
            elif "verifikasi" in teks or "ajuan" in teks or "pengajuan" in teks:
                btn.clicked.connect(self.buka_kelola_pengajuan)
            elif "riwayat" in teks:
                btn.clicked.connect(self.buka_riwayat_bmn)
            elif "logout" in teks:
                btn.clicked.connect(self.logout)

        self.load_data()

    def load_data(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM pengajuan_peminjaman WHERE status_pengajuan = 'Menunggu'")
        jml_menunggu = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM ruang WHERE status_ruang = 'Tersedia'")
        jml_ruang_siap = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*) FROM pengajuan_peminjaman
            WHERE status_pengajuan = 'Disetujui' AND DATE(tanggal_mulai) = CURDATE()
            """
        )
        jml_terpakai_hari_ini = cursor.fetchone()[0]

        if len(self.label_angka) >= 3:
            self.label_angka[0].setText(str(jml_menunggu))
            self.label_angka[1].setText(str(jml_ruang_siap))
            self.label_angka[2].setText(str(jml_terpakai_hari_ini))

        sql = """
            SELECT p.id_pengajuan, COALESCE(u.nama_organisasi, u.nama), p.nama_kegiatan,
                   r.kode_ruang, r.nama_ruang, p.tanggal_mulai, p.tanggal_selesai, p.status_pengajuan
            FROM pengajuan_peminjaman p
            JOIN ruang r ON p.id_ruang = r.id_ruang
            JOIN pengguna u ON p.id_oki = u.id_pengguna
            ORDER BY p.id_pengajuan ASC
        """
        cursor.execute(sql)
        rows = cursor.fetchall() or []
        conn.close()

        if not self.tabel:
            return

        self.tabel.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            waktu = f"{row[5].strftime('%d-%m-%Y')}\n{row[5].strftime('%H:%M')} - {row[6].strftime('%H:%M')}"
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
        for r in range(self.tabel.rowCount()):
            if self.tabel.rowHeight(r) < 50:
                self.tabel.setRowHeight(r, 50)

    def buka_dialog_verifikasi(self):
        if not self.tabel or self.tabel.currentRow() < 0:
            return
        id_pengajuan = self.tabel.item(self.tabel.currentRow(), 0).data(Qt.UserRole)
        from controller.dialog_verifikasi_pengajuan import DialogVerifikasiPengajuanController
        dialog = DialogVerifikasiPengajuanController(id_pengajuan, self.user, parent=self)
        dialog.exec_()
        self.load_data()

    def buka_kelola_ruang(self):
        from controller.bmn_kelola_ruang import BmnKelolaRuangController
        self.win = BmnKelolaRuangController(self.user)
        self.win.show()
        self.close()

    def buka_kelola_pengajuan(self):
        from controller.bmn_kelola_pengajuan import BmnKelolaPengajuanController
        self.win = BmnKelolaPengajuanController(self.user)
        self.win.show()
        self.close()

    def buka_riwayat_bmn(self):
        from controller.bmn_riwayat_peminjaman import RiwayatPeminjamanBMNController
        self.win = RiwayatPeminjamanBMNController(self.user)
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