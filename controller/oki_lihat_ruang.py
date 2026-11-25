from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLineEdit, QComboBox, QSpinBox, QPushButton, QLabel
)
from PyQt5.QtCore import Qt
import ui.daftar_ruang as ui_form
from model.User import User
from model.connectiondb import get_db_connection

_ui_name = [n for n in dir(ui_form) if n.startswith("Ui_")][0]
_UiClass = getattr(ui_form, _ui_name)
_BaseClass = QMainWindow if _ui_name == "Ui_MainWindow" else QWidget


def _cari(ui, kandidat, tipe):
    for nama in kandidat:
        w = getattr(ui, nama, None)
        if isinstance(w, tipe):
            return w
    return None


class OkiLihatRuangController(_BaseClass):
    def __init__(self, user_data):
        super().__init__()
        self.ui = _UiClass()
        self.ui.setupUi(self)
        self.user = user_data
        self.model = User()

        nama_oki = self.user.get("nama_organisasi") or self.user.get("nama", "OKI")
        lbl_oki = _cari(self.ui, ["lblOki", "label_oki"], QLabel)
        if lbl_oki:
            lbl_oki.setText(f"OKI: {nama_oki}")

        # Input Cari Ruang & Kolom Fasilitas (otomatis mendeteksi QLineEdit di form)
        self.inp_cari = _cari(self.ui, ["txtCari", "txtSearch", "inputCari", "lineEdit"], QLineEdit)
        line_edits = self.findChildren(QLineEdit)
        if not self.inp_cari and line_edits:
            self.inp_cari = next(
                (le for le in line_edits if not le.isReadOnly() and "fasilitas" not in le.placeholderText().lower()),
                line_edits[0]
            )
        if self.inp_cari:
            self.inp_cari.returnPressed.connect(self.load_data)
            self.inp_cari.textChanged.connect(self.load_data)

        self.inp_fasilitas = _cari(self.ui, ["txtFasilitas", "inputFasilitas", "lineEdit_2"], QLineEdit)
        if not self.inp_fasilitas:
            self.inp_fasilitas = next((le for le in line_edits if le != self.inp_cari), None)
        if self.inp_fasilitas:
            self.inp_fasilitas.setReadOnly(True)

        # SpinBox Min. Kapasitas
        self.spin_kapasitas = _cari(self.ui, ["spinKapasitas", "spinBox"], QSpinBox)
        if not self.spin_kapasitas:
            spins = self.findChildren(QSpinBox)
            self.spin_kapasitas = spins[0] if spins else None
        if self.spin_kapasitas:
            self.spin_kapasitas.valueChanged.connect(self.load_data)

        # Dropdown Gedung (comboGedung) -> ambil langsung dari tabel lokasi_gedung
        self.cmb_gedung = _cari(self.ui, ["comboGedung", "cmbGedung", "cmbFilter", "comboBox"], QComboBox)
        if not self.cmb_gedung:
            combos = self.findChildren(QComboBox)
            self.cmb_gedung = combos[0] if combos else None
        if self.cmb_gedung:
            self.cmb_gedung.setStyleSheet("")
            self._load_filter_gedung()
            self.cmb_gedung.currentIndexChanged.connect(self.load_data)

        # Hubungkan tombol Cari & Ajukan Peminjaman Ruang Ini
        btn_cari = _cari(self.ui, ["btnCari", "btnFilter", "pushButton_7"], QPushButton)
        if btn_cari:
            btn_cari.clicked.connect(self.load_data)

        for btn in self.findChildren(QPushButton):
            teks = btn.text().lower()
            if "cari" in teks and btn != btn_cari:
                btn.clicked.connect(self.load_data)
            elif "ajukan peminjaman ruang ini" in teks:
                btn.clicked.connect(self.ajukan_ruang_terpilih)

        # Tabel Ruang
        self.tabel = _cari(self.ui, ["tblRuang", "tableRuang", "tableWidget"], QTableWidget)
        if not self.tabel:
            tables = self.findChildren(QTableWidget)
            self.tabel = tables[0] if tables else None
        if self.tabel:
            self.tabel.setColumnCount(6)
            self.tabel.setHorizontalHeaderLabels([
                "Kode Ruang", "Nama Ruang", "Gedung", "Kapasitas", "Fasilitas", "Status"
            ])
            header = self.tabel.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.Stretch)
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
            self.tabel.verticalHeader().setVisible(False)
            self.tabel.setWordWrap(True)
            self.tabel.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tabel.setSelectionMode(QAbstractItemView.SingleSelection)
            self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.tabel.itemSelectionChanged.connect(self.tampilkan_fasilitas)
            self.tabel.doubleClicked.connect(self.ajukan_ruang_terpilih)

        # Navigasi Sidebar OKI
        for nama, fungsi in [
            ("btnDashboard", self.buka_dashboard),
            ("btnDaftarRuang", self.reset_filter),
            ("btnAjukanPinjam", self.buka_ajukan_pinjam),
            ("btnRiwayat", self.buka_riwayat),
            ("btnJadwal", self.buka_jadwal),
            ("btnLogout", self.logout),
        ]:
            btn = getattr(self.ui, nama, None)
            if isinstance(btn, QPushButton):
                btn.clicked.connect(fungsi)

        self.load_data()

    def _load_filter_gedung(self):
        if not self.cmb_gedung:
            return
        self.cmb_gedung.blockSignals(True)
        self.cmb_gedung.clear()
        self.cmb_gedung.addItem("Semua")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nama_gedung FROM lokasi_gedung ORDER BY nama_gedung ASC")
        gedung_list = [r[0] for r in cursor.fetchall() or []]
        conn.close()

        self.cmb_gedung.addItems(gedung_list)
        self.cmb_gedung.blockSignals(False)

    def reset_filter(self):
        if self.inp_cari:
            self.inp_cari.clear()
        if self.spin_kapasitas:
            self.spin_kapasitas.setValue(0)
        if self.cmb_gedung:
            self.cmb_gedung.setCurrentIndex(0)
        self.load_data()

    def load_data(self):
        keyword = self.inp_cari.text().strip() if self.inp_cari else ""
        gedung = self.cmb_gedung.currentText() if self.cmb_gedung else "Semua"
        min_kapasitas = self.spin_kapasitas.value() if self.spin_kapasitas else 0

        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT kode_ruang, nama_ruang, lokasi_gedung, kapasitas, fasilitas, status_ruang, id_ruang
            FROM ruang
            WHERE 1=1
        """
        params = []
        if keyword:
            sql += " AND (kode_ruang LIKE %s OR nama_ruang LIKE %s OR fasilitas LIKE %s)"
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw])
        if gedung and gedung != "Semua":
            sql += " AND lokasi_gedung = %s"
            params.append(gedung)
        if min_kapasitas > 0:
            sql += " AND kapasitas >= %s"
            params.append(min_kapasitas)
        sql += " ORDER BY kode_ruang ASC"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall() or []
        conn.close()

        if not self.tabel:
            return
        self.tabel.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            items = [row[0], row[1], row[2], f"{row[3]} Org", row[4] or "-", row[5]]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, row[6])
                if col in (0, 2, 3, 5):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tabel.setItem(idx, col, item)
        self.tabel.resizeRowsToContents()

    def tampilkan_fasilitas(self):
        if not self.tabel or not self.inp_fasilitas:
            return
        row_idx = self.tabel.currentRow()
        if row_idx >= 0:
            self.inp_fasilitas.setText(self.tabel.item(row_idx, 4).text())

    def ajukan_ruang_terpilih(self):
        id_ruang = None
        kode_ruang = None
        if self.tabel and self.tabel.currentRow() >= 0:
            row_idx = self.tabel.currentRow()
            status = self.tabel.item(row_idx, 5).text()
            if status != "Tersedia":
                QMessageBox.warning(
                    self, "Ruang Tidak Tersedia",
                    f"Ruangan ini sedang berstatus '{status}' sehingga tidak dapat dipinjam."
                )
                return
            kode_ruang = self.tabel.item(row_idx, 0).text()
            id_ruang = self.tabel.item(row_idx, 0).data(Qt.UserRole)
        self.buka_ajukan_pinjam(id_ruang=id_ruang, kode_ruang=kode_ruang)

    def buka_ajukan_pinjam(self, id_ruang=None, kode_ruang=None):
        from controller.oki_ajukan_peminjaman import OkiAjukanPeminjamanController
        self.win = OkiAjukanPeminjamanController(
            self.user,
            id_ruang_terpilih=id_ruang,
            kode_ruang_terpilih=kode_ruang
        )
        self.win.show()
        self.close()

    def buka_dashboard(self):
        from controller.dashboard_oki import DashboardOKIController
        self.win = DashboardOKIController(self.user)
        self.win.show()
        self.close()

    def buka_riwayat(self):
        from controller.oki_riwayat_pengajuan import OkiRiwayatPengajuanController
        self.win = OkiRiwayatPengajuanController(self.user)
        self.win.show()
        self.close()

    def buka_jadwal(self):
        from controller.oki_jadwal_disetujui import OKIJadwalDisetujuiController
        self.win = OKIJadwalDisetujuiController(self.user)
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