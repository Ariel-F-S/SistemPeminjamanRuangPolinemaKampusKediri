from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLineEdit, QComboBox, QSpinBox,
    QPushButton, QLabel
)
from PyQt5.QtCore import Qt
import ui.daftar_ruang as _ui_form
from model.connectiondb import get_db_connection

_ui_name = [n for n in dir(_ui_form) if n.startswith("Ui_")][0]
_UiClass = getattr(_ui_form, _ui_name)
_BaseClass = QMainWindow if _ui_name == "Ui_MainWindow" else QWidget


class OkiLihatRuangController(_BaseClass):
    def __init__(self, user_data):
        super().__init__()
        self.ui = _UiClass()
        self.ui.setupUi(self)
        self.user = user_data

        # Tampilkan nama OKI di pojok kanan atas
        nama_oki = self.user.get("nama_organisasi") or self.user.get("nama", "OKI")
        for lbl in self.findChildren(QLabel):
            teks = lbl.text().lower()
            obj = lbl.objectName().lower()
            if "oki:" in teks or any(k in obj for k in ("lbloki", "lbluser", "label_oki", "label_user")):
                lbl.setText(f"OKI: {nama_oki}")
                break

        # Deteksi QLineEdit berdasarkan posisi (atas ke bawah, kiri ke kanan)
        # agar kotak Fasilitas di bawah tidak tertukar dengan Min. Kapasitas di atas
        line_edits = sorted(self.findChildren(QLineEdit), key=lambda w: (w.y(), w.x()))

        self.txt_fasilitas = next(
            (w for w in line_edits if "fasilitas" in w.placeholderText().lower()),
            line_edits[-1] if line_edits else None
        )
        if self.txt_fasilitas:
            self.txt_fasilitas.setReadOnly(True)

        atas_edits = [w for w in line_edits if w is not self.txt_fasilitas]
        self.inp_cari = next(
            (w for w in atas_edits if "cari" in w.placeholderText().lower() or "ketik" in w.placeholderText().lower()),
            atas_edits[0] if len(atas_edits) > 0 else None
        )
        if self.inp_cari:
            self.inp_cari.returnPressed.connect(self.load_data)

        # Deteksi Min. Kapasitas (bisa berupa QSpinBox atau QLineEdit di kanan atas)
        spins = self.findChildren(QSpinBox)
        self.spin_kapasitas = spins[0] if spins else None
        self.inp_kapasitas = None
        if not self.spin_kapasitas:
            sisa_atas = [w for w in atas_edits if w is not self.inp_cari]
            self.inp_kapasitas = sisa_atas[0] if sisa_atas else None
            if self.inp_kapasitas:
                self.inp_kapasitas.returnPressed.connect(self.load_data)

        # Dropdown Gedung -> ambil langsung dari tabel lokasi_gedung
        combos = self.findChildren(QComboBox)
        self.cmb_gedung = getattr(self.ui, "comboBox", None) or (combos[0] if combos else None)
        if isinstance(self.cmb_gedung, QComboBox):
            self._load_filter_gedung()
            self.cmb_gedung.currentIndexChanged.connect(self.load_data)

        # Pengaturan Tabel Informasi Ruang Kampus
        tables = self.findChildren(QTableWidget)
        self.tabel = tables[0] if tables else None
        if self.tabel:
            self.tabel.setColumnCount(6)
            self.tabel.setHorizontalHeaderLabels([
                "Kode Ruang", "Nama Ruang", "Gedung", "Kapasitas", "Fasilitas", "Status"
            ])
            header = self.tabel.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.Stretch)
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

            self.tabel.verticalHeader().setVisible(False)
            self.tabel.setWordWrap(True)
            self.tabel.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tabel.setSelectionMode(QAbstractItemView.SingleSelection)
            self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers)

            # Saat baris ruangan diklik atau dipilih dengan panah keyboard, tampilkan fasilitasnya
            self.tabel.itemSelectionChanged.connect(self.tampilkan_fasilitas)
            self.tabel.cellClicked.connect(lambda r, c: self.tampilkan_fasilitas())

        # Hubungkan semua tombol navigasi & aksi
        for btn in self.findChildren(QPushButton):
            teks = btn.text().lower()
            if "dashboard" in teks:
                btn.clicked.connect(self.buka_dashboard)
            elif "daftar ruang" in teks:
                btn.clicked.connect(self.load_data)
            elif "ajukan" in teks:
                btn.clicked.connect(self.buka_ajukan_peminjaman)
            elif "riwayat" in teks:
                btn.clicked.connect(self.buka_riwayat)
            elif "jadwal" in teks:
                btn.clicked.connect(self.buka_jadwal)
            elif "logout" in teks:
                btn.clicked.connect(self.logout)
            elif "cari" in teks:
                btn.clicked.connect(self.load_data)

        self.load_data()

    def _load_filter_gedung(self):
        if not isinstance(self.cmb_gedung, QComboBox):
            return
        self.cmb_gedung.blockSignals(True)
        self.cmb_gedung.clear()
        self.cmb_gedung.addItem("Semua", None)

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT nama_gedung FROM lokasi_gedung "
                "WHERE nama_gedung IS NOT NULL AND TRIM(nama_gedung) != '' "
                "ORDER BY id_gedung ASC"
            )
            for (gedung,) in cursor.fetchall() or []:
                self.cmb_gedung.addItem(gedung, gedung)
        except Exception:
            pass
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()
            self.cmb_gedung.blockSignals(False)

    def _get_min_kapasitas(self):
        if isinstance(self.spin_kapasitas, QSpinBox):
            return self.spin_kapasitas.value()
        if isinstance(self.inp_kapasitas, QLineEdit):
            teks = self.inp_kapasitas.text().strip()
            return int(teks) if teks.isdigit() else 0
        return 0

    def load_data(self):
        keyword = self.inp_cari.text().strip() if self.inp_cari else ""
        gedung = self.cmb_gedung.currentData() if isinstance(self.cmb_gedung, QComboBox) else None
        min_kap = self._get_min_kapasitas()

        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT id_ruang, kode_ruang, nama_ruang, lokasi_gedung, kapasitas, fasilitas, status_ruang
            FROM ruang
            WHERE 1=1
        """
        params = []
        if gedung:
            sql += " AND lokasi_gedung = %s"
            params.append(gedung)
        if min_kap > 0:
            sql += " AND kapasitas >= %s"
            params.append(min_kap)
        if keyword:
            sql += " AND (kode_ruang LIKE %s OR nama_ruang LIKE %s OR fasilitas LIKE %s)"
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw])

        sql += " ORDER BY kode_ruang ASC"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall() or []
        conn.close()

        if not self.tabel:
            return

        self.tabel.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            fasilitas_str = row[5] if row[5] and str(row[5]).strip() else "-"
            items = [
                str(row[1]),
                str(row[2]),
                str(row[3]),
                f"{row[4]} Org",
                fasilitas_str,
                str(row[6]),
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, row[0])
                if col in (0, 2, 3, 5):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tabel.setItem(idx, col, item)

        self.tabel.resizeRowsToContents()
        if self.txt_fasilitas:
            self.txt_fasilitas.clear()

    def tampilkan_fasilitas(self):
        if not self.tabel or not self.txt_fasilitas:
            return
        row = self.tabel.currentRow()
        if row < 0:
            self.txt_fasilitas.clear()
            return
        item_fasilitas = self.tabel.item(row, 4)
        self.txt_fasilitas.setText(item_fasilitas.text() if item_fasilitas else "-")

    def buka_ajukan_peminjaman(self):
        id_ruang_terpilih = None
        if self.tabel and self.tabel.currentRow() >= 0:
            item_kode = self.tabel.item(self.tabel.currentRow(), 0)
            if item_kode:
                id_ruang_terpilih = item_kode.data(Qt.UserRole)

        from controller.oki_ajukan_peminjaman import OkiAjukanPeminjamanController
        try:
            self.win = OkiAjukanPeminjamanController(self.user, id_ruang=id_ruang_terpilih)
        except TypeError:
            self.win = OkiAjukanPeminjamanController(self.user)
        self.win.show()
        self.close()

    def buka_dashboard(self):
        from controller.dashboard_oki import DashboardOkiController
        self.win = DashboardOkiController(self.user)
        self.win.show()
        self.close()

    def buka_riwayat(self):
        from controller.oki_riwayat_pengajuan import OkiRiwayatPengajuanController
        self.win = OkiRiwayatPengajuanController(self.user)
        self.win.show()
        self.close()

    def buka_jadwal(self):
        from controller.oki_jadwal_disetujui import OkiJadwalDisetujuiController
        self.win = OkiJadwalDisetujuiController(self.user)
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