from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QComboBox, QLineEdit, QPushButton, QLabel
)
from PyQt5.QtCore import Qt
import ui.verifikasi_ajuan_BMN as _ui_form
from model.connectiondb import get_db_connection

_ui_name = [n for n in dir(_ui_form) if n.startswith("Ui_")][0]
_UiClass = getattr(_ui_form, _ui_name)
_BaseClass = QMainWindow if _ui_name == "Ui_MainWindow" else QWidget


class BmnKelolaPengajuanController(_BaseClass):
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

        daftar_inp = self.findChildren(QLineEdit)
        self.inp_cari = daftar_inp[0] if daftar_inp else None
        if self.inp_cari:
            self.inp_cari.setPlaceholderText("Cari kegiatan / OKI / ruang...")
            self.inp_cari.returnPressed.connect(self.load_data)

        self.cmb_oki = getattr(self.ui, "comboBox", None)
        if not isinstance(self.cmb_oki, QComboBox):
            daftar_cmb = self.findChildren(QComboBox)
            self.cmb_oki = daftar_cmb[0] if daftar_cmb else None

        if isinstance(self.cmb_oki, QComboBox):
            self.cmb_oki.setStyleSheet("")
            self._load_filter_oki()
            self.cmb_oki.currentIndexChanged.connect(self.load_data)

        daftar_tbl = self.findChildren(QTableWidget)
        self.tabel = daftar_tbl[0] if daftar_tbl else None
        if self.tabel:
            self.tabel.setColumnCount(7)
            self.tabel.setHorizontalHeaderLabels([
                "ID", "Organisasi (OKI)", "Nama Kegiatan", "Ruang", "Waktu Pinjam", "Surat", "Status"
            ])
            header = self.tabel.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Interactive)
            header.setStretchLastSection(True)

            self.tabel.setColumnWidth(0, 38)  
            self.tabel.setColumnWidth(1, 125) 
            self.tabel.setColumnWidth(2, 165)   
            self.tabel.setColumnWidth(3, 145)   
            self.tabel.setColumnWidth(4, 115)   
            self.tabel.setColumnWidth(5, 78)    
            self.tabel.setColumnWidth(6, 85)    

            self.tabel.verticalHeader().setVisible(False)
            self.tabel.setWordWrap(True)
            self.tabel.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tabel.setSelectionMode(QAbstractItemView.SingleSelection)
            self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.tabel.doubleClicked.connect(self.buka_dialog_verifikasi)

        for btn in self.findChildren(QPushButton):
            teks = btn.text().lower()
            if "dashboard" in teks:
                btn.clicked.connect(self.buka_dashboard)
            elif "kelola ruang" in teks:
                btn.clicked.connect(self.buka_kelola_ruang)
            elif "verifikasi ajuan" in teks or "kelola pengajuan" in teks:
                btn.clicked.connect(self.load_data)
            elif "riwayat" in teks:
                btn.clicked.connect(self.buka_riwayat_bmn)
            elif "logout" in teks:
                btn.clicked.connect(self.logout)
            elif "cari" in teks:
                btn.clicked.connect(self.load_data)
            elif any(k in teks for k in ("verifikasi", "proses", "periksa", "detail", "tindak")):
                btn.clicked.connect(self.buka_dialog_verifikasi)

        self.load_data()

    def _load_filter_oki(self):
        if not isinstance(self.cmb_oki, QComboBox):
            return
        self.cmb_oki.blockSignals(True)
        self.cmb_oki.clear()
        self.cmb_oki.addItem("Semua OKI", None)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT u.id_pengguna, COALESCE(u.nama_organisasi, u.nama) AS nama_oki
            FROM pengguna u
            JOIN pengajuan_peminjaman p ON p.id_oki = u.id_pengguna
            ORDER BY nama_oki ASC
        """)
        for id_oki, nama_oki in cursor.fetchall() or []:
            self.cmb_oki.addItem(nama_oki, id_oki)
        conn.close()
        self.cmb_oki.blockSignals(False)

    def load_data(self):
        id_oki = self.cmb_oki.currentData() if isinstance(self.cmb_oki, QComboBox) else None
        keyword = self.inp_cari.text().strip() if self.inp_cari else ""

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SHOW COLUMNS FROM pengajuan_peminjaman")
        kolom_db = [c[0] for c in cursor.fetchall()]
        kolom_surat = next(
            (k for k in kolom_db if any(kata in k.lower() for kata in ("surat", "file", "dokumen", "lampiran", "berkas"))),
            None
        )
        select_surat = (
            "CASE WHEN (p.file_surat_pengajuan IS NOT NULL AND p.file_surat_pengajuan != '') "
            "OR p.data_surat_pengajuan IS NOT NULL THEN 'Terlampir' ELSE '-' END"
        )

        sql = f"""
            SELECT p.id_pengajuan, COALESCE(u.nama_organisasi, u.nama), p.nama_kegiatan,
                   r.kode_ruang, r.nama_ruang, p.tanggal_mulai, p.tanggal_selesai,
                   {select_surat}, p.status_pengajuan
            FROM pengajuan_peminjaman p
            JOIN ruang r ON p.id_ruang = r.id_ruang
            JOIN pengguna u ON p.id_oki = u.id_pengguna
            WHERE 1=1
        """
        params = []
        if id_oki:
            sql += " AND p.id_oki = %s"
            params.append(id_oki)
        if keyword:
            sql += " AND (p.nama_kegiatan LIKE %s OR u.nama_organisasi LIKE %s OR r.kode_ruang LIKE %s OR r.nama_ruang LIKE %s OR p.status_pengajuan LIKE %s)"
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw, kw, kw])
        sql += " ORDER BY p.id_pengajuan ASC"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall() or []
        conn.close()

        if not self.tabel:
            return
        self.tabel.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            waktu = f"{row[5].strftime('%d-%m-%Y')}\n{row[5].strftime('%H:%M')} - {row[6].strftime('%H:%M')}"
            items = [
                str(row[0]), row[1], row[2],
                f"{row[3]} - {row[4]}", waktu, row[7], row[8]
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, row[0])
                if col in (0, 4, 5, 6):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tabel.setItem(idx, col, item)

        self.tabel.resizeRowsToContents()
        for r in range(self.tabel.rowCount()):
            if self.tabel.rowHeight(r) < 50:
                self.tabel.setRowHeight(r, 50)

    def buka_dialog_verifikasi(self):
        if not self.tabel or self.tabel.currentRow() < 0:
            QMessageBox.warning(self, "Pilih Pengajuan", "Silakan pilih salah satu baris pengajuan terlebih dahulu!")
            return

        id_pengajuan = self.tabel.item(self.tabel.currentRow(), 0).data(Qt.UserRole)
        from controller.dialog_verifikasi_pengajuan import DialogVerifikasiPengajuanController
        dialog = DialogVerifikasiPengajuanController(id_pengajuan, self.user, parent=self)
        dialog.exec_()
        self._load_filter_oki()
        self.load_data()

    def buka_dashboard(self):
        from controller.dashboard_bmn import DashboardBMNController
        self.win = DashboardBMNController(self.user)
        self.win.show()
        self.close()

    def buka_kelola_ruang(self):
        from controller.bmn_kelola_ruang import BmnKelolaRuangController
        self.win = BmnKelolaRuangController(self.user)
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