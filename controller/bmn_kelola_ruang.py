from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLineEdit, QComboBox, QSpinBox, QTextEdit,
    QPushButton, QLabel
)
from PyQt5.QtCore import Qt
import ui.kelola_data_ruang_BMN as _ui_form
import ui.tambah_ruang_BMN as _ui_tambah_ruang
import ui.ubah_data_ruang_BMN as _ui_ubah_ruang
from model.connectiondb import get_db_connection

_ui_name = [n for n in dir(_ui_form) if n.startswith("Ui_")][0]
_UiClass = getattr(_ui_form, _ui_name)
_BaseClass = QMainWindow if _ui_name == "Ui_MainWindow" else QWidget


def _ambil_daftar_gedung():
    """Mengambil seluruh nama_gedung dari tabel lokasi_gedung."""
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
        rows = cursor.fetchall() or []
        return [
            (r["nama_gedung"] if isinstance(r, dict) else r[0]).strip()
            for r in rows
            if (r["nama_gedung"] if isinstance(r, dict) else r[0])
        ]
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


class _DialogTambahRuangBMN(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_cls = getattr(_ui_tambah_ruang, [n for n in dir(_ui_tambah_ruang) if n.startswith("Ui_")][0])
        self.ui = ui_cls()
        self.ui.setupUi(self)

        self.inputs = self.findChildren(QLineEdit)
        self.spins = self.findChildren(QSpinBox)
        self.texts = self.findChildren(QTextEdit)

        # Isi dropdown Gedung (self.ui.comboBox) langsung dari tabel lokasi_gedung
        self.cmb_gedung = getattr(self.ui, "comboBox", None)
        if isinstance(self.cmb_gedung, QComboBox):
            self.cmb_gedung.clear()
            try:
                gedung_db = _ambil_daftar_gedung()
                self.cmb_gedung.addItems(gedung_db if gedung_db else ["-- Data Gedung Kosong --"])
            except Exception as e:
                QMessageBox.warning(self, "Error Database", f"Gagal memuat data lokasi_gedung:\n{e}")

        # Isi dropdown Status (self.ui.comboBox_2)
        self.cmb_status = getattr(self.ui, "comboBox_2", None)
        if isinstance(self.cmb_status, QComboBox):
            self.cmb_status.clear()
            self.cmb_status.addItems(["Tersedia", "Perbaikan", "Tidak Tersedia"])

        for btn in self.findChildren(QPushButton):
            teks = btn.text().lower()
            if any(k in teks for k in ("simpan", "tambah", "save", "ok")):
                btn.clicked.connect(self.simpan)
            elif any(k in teks for k in ("batal", "tutup", "cancel")):
                btn.clicked.connect(self.reject)

    def simpan(self):
        kode = self.inputs[0].text().strip() if len(self.inputs) > 0 else ""
        nama = self.inputs[1].text().strip() if len(self.inputs) > 1 else ""
        gedung = (
            self.cmb_gedung.currentText().strip()
            if isinstance(self.cmb_gedung, QComboBox)
            else (self.inputs[2].text().strip() if len(self.inputs) > 2 else "")
        )
        kapasitas = (
            self.spins[0].value() if self.spins
            else int(self.inputs[2].text().strip() or 30) if len(self.inputs) > 2 and self.inputs[2].text().strip().isdigit()
            else 30
        )
        fasilitas = (
            self.texts[0].toPlainText().strip() if self.texts
            else self.inputs[-1].text().strip() if len(self.inputs) > 2
            else "-"
        )
        status = (
            self.cmb_status.currentText()
            if isinstance(self.cmb_status, QComboBox)
            else "Tersedia"
        )

        if not kode or not nama or not gedung or gedung == "-- Data Gedung Kosong --":
            QMessageBox.warning(self, "Validasi", "Kode ruang, nama ruang, dan lokasi gedung wajib diisi!")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ruang (kode_ruang, nama_ruang, lokasi_gedung, kapasitas, fasilitas, status_ruang)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (kode, nama, gedung, kapasitas, fasilitas or "-", status)
            )
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Berhasil", "Data ruang baru berhasil ditambahkan.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error Database", f"Gagal menambah ruang:\n{e}")


class _DialogUbahRuangBMN(QDialog):
    def __init__(self, id_ruang, parent=None):
        super().__init__(parent)
        self.id_ruang = id_ruang
        ui_cls = getattr(_ui_ubah_ruang, [n for n in dir(_ui_ubah_ruang) if n.startswith("Ui_")][0])
        self.ui = ui_cls()
        self.ui.setupUi(self)

        self.inputs = self.findChildren(QLineEdit)
        self.spins = self.findChildren(QSpinBox)
        self.texts = self.findChildren(QTextEdit)

        # Isi dropdown Gedung (self.ui.comboBox) langsung dari tabel lokasi_gedung
        self.cmb_gedung = getattr(self.ui, "comboBox", None)
        if isinstance(self.cmb_gedung, QComboBox):
            self.cmb_gedung.clear()
            try:
                gedung_db = _ambil_daftar_gedung()
                self.cmb_gedung.addItems(gedung_db if gedung_db else ["-- Data Gedung Kosong --"])
            except Exception as e:
                QMessageBox.warning(self, "Error Database", f"Gagal memuat data lokasi_gedung:\n{e}")

        # Isi dropdown Status (self.ui.comboBox_2)
        self.cmb_status = getattr(self.ui, "comboBox_2", None)
        if isinstance(self.cmb_status, QComboBox):
            self.cmb_status.clear()
            self.cmb_status.addItems(["Tersedia", "Perbaikan", "Tidak Tersedia"])

        for btn in self.findChildren(QPushButton):
            teks = btn.text().lower()
            if any(k in teks for k in ("simpan", "ubah", "update", "save", "ok")):
                btn.clicked.connect(self.simpan)
            elif any(k in teks for k in ("batal", "tutup", "cancel")):
                btn.clicked.connect(self.reject)

        self._load_detail()

    def _load_detail(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT kode_ruang, nama_ruang, lokasi_gedung, kapasitas, fasilitas, status_ruang FROM ruang WHERE id_ruang = %s",
            (self.id_ruang,)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return

        if len(self.inputs) > 0:
            self.inputs[0].setText(row[0] or "")
        if len(self.inputs) > 1:
            self.inputs[1].setText(row[1] or "")
        if isinstance(self.cmb_gedung, QComboBox):
            idx_g = self.cmb_gedung.findText(row[2] or "")
            if idx_g >= 0:
                self.cmb_gedung.setCurrentIndex(idx_g)
            elif row[2]:
                self.cmb_gedung.addItem(row[2])
                self.cmb_gedung.setCurrentText(row[2])
        elif len(self.inputs) > 2:
            self.inputs[2].setText(row[2] or "")

        if self.spins:
            self.spins[0].setValue(int(row[3] or 30))
        elif len(self.inputs) > 2:
            self.inputs[2].setText(str(row[3] or 30))

        if self.texts:
            self.texts[0].setPlainText(row[4] or "")
        elif len(self.inputs) > 3:
            self.inputs[3].setText(row[4] or "")

        if isinstance(self.cmb_status, QComboBox):
            idx_s = self.cmb_status.findText(row[5] or "Tersedia")
            if idx_s >= 0:
                self.cmb_status.setCurrentIndex(idx_s)

    def simpan(self):
        kode = self.inputs[0].text().strip() if len(self.inputs) > 0 else ""
        nama = self.inputs[1].text().strip() if len(self.inputs) > 1 else ""
        gedung = (
            self.cmb_gedung.currentText().strip()
            if isinstance(self.cmb_gedung, QComboBox)
            else (self.inputs[2].text().strip() if len(self.inputs) > 2 else "")
        )
        kapasitas = (
            self.spins[0].value() if self.spins
            else int(self.inputs[2].text().strip() or 30) if len(self.inputs) > 2 and self.inputs[2].text().strip().isdigit()
            else 30
        )
        fasilitas = (
            self.texts[0].toPlainText().strip() if self.texts
            else self.inputs[-1].text().strip() if len(self.inputs) > 2
            else "-"
        )
        status = (
            self.cmb_status.currentText()
            if isinstance(self.cmb_status, QComboBox)
            else "Tersedia"
        )

        if not kode or not nama or not gedung or gedung == "-- Data Gedung Kosong --":
            QMessageBox.warning(self, "Validasi", "Kode ruang, nama ruang, dan lokasi gedung wajib diisi!")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE ruang
                SET kode_ruang = %s, nama_ruang = %s, lokasi_gedung = %s,
                    kapasitas = %s, fasilitas = %s, status_ruang = %s
                WHERE id_ruang = %s
                """,
                (kode, nama, gedung, kapasitas, fasilitas or "-", status, self.id_ruang)
            )
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Berhasil", "Data ruang berhasil diperbarui.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error Database", f"Gagal mengubah data ruang:\n{e}")


class BmnKelolaRuangController(_BaseClass):
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
            self.inp_cari.setPlaceholderText("Cari kode / nama ruang / fasilitas...")
            self.inp_cari.returnPressed.connect(self.load_data)

        # Dropdown Gedung langsung dari self.ui.comboBox
        self.cmb_gedung = getattr(self.ui, "comboBox", None)
        if isinstance(self.cmb_gedung, QComboBox):
            self._load_filter_gedung()
            self.cmb_gedung.currentIndexChanged.connect(self.load_data)

        daftar_tbl = self.findChildren(QTableWidget)
        self.tabel = daftar_tbl[0] if daftar_tbl else None
        if self.tabel:
            self.tabel.setColumnCount(7)
            self.tabel.setHorizontalHeaderLabels([
                "ID", "Kode Ruang", "Nama Ruang", "Gedung", "Kapasitas", "Fasilitas", "Status"
            ])
            header = self.tabel.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.Stretch)
            header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
            self.tabel.verticalHeader().setVisible(False)
            self.tabel.setWordWrap(True)
            self.tabel.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tabel.setSelectionMode(QAbstractItemView.SingleSelection)
            self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.tabel.doubleClicked.connect(self.ubah_ruang)

        for btn in self.findChildren(QPushButton):
            teks = btn.text().lower()
            if "dashboard" in teks:
                btn.clicked.connect(self.buka_dashboard)
            elif "kelola ruang" in teks:
                btn.clicked.connect(self.load_data)
            elif "verifikasi" in teks or "ajuan" in teks or "pengajuan" in teks:
                btn.clicked.connect(self.buka_kelola_pengajuan)
            elif "riwayat" in teks:
                btn.clicked.connect(self.buka_riwayat_bmn)
            elif "logout" in teks:
                btn.clicked.connect(self.logout)
            elif "cari" in teks:
                btn.clicked.connect(self.load_data)
            elif "tambah" in teks:
                btn.clicked.connect(self.tambah_ruang)
            elif "ubah" in teks or "edit" in teks:
                btn.clicked.connect(self.ubah_ruang)
            elif "hapus" in teks:
                btn.clicked.connect(self.hapus_ruang)

        self.load_data()

    def _load_filter_gedung(self):
        if not isinstance(self.cmb_gedung, QComboBox):
            return
        pilihan_sebelumnya = self.cmb_gedung.currentData()
        self.cmb_gedung.blockSignals(True)
        self.cmb_gedung.clear()
        self.cmb_gedung.addItem("Semua Gedung", None)

        try:
            for gedung in _ambil_daftar_gedung():
                self.cmb_gedung.addItem(gedung, gedung)
        except Exception as e:
            QMessageBox.warning(self, "Error Database", f"Gagal memuat filter lokasi_gedung:\n{e}")

        if pilihan_sebelumnya:
            idx = self.cmb_gedung.findData(pilihan_sebelumnya)
            if idx >= 0:
                self.cmb_gedung.setCurrentIndex(idx)
        self.cmb_gedung.blockSignals(False)

    def load_data(self):
        keyword = self.inp_cari.text().strip() if self.inp_cari else ""
        gedung = self.cmb_gedung.currentData() if isinstance(self.cmb_gedung, QComboBox) else None

        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT id_ruang, kode_ruang, nama_ruang, lokasi_gedung, kapasitas, fasilitas, status_ruang
            FROM ruang WHERE 1=1
        """
        params = []
        if gedung:
            sql += " AND lokasi_gedung = %s"
            params.append(gedung)
        if keyword:
            sql += " AND (kode_ruang LIKE %s OR nama_ruang LIKE %s OR lokasi_gedung LIKE %s OR fasilitas LIKE %s OR status_ruang LIKE %s)"
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw, kw, kw])
        sql += " ORDER BY id_ruang ASC"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall() or []
        conn.close()

        if not self.tabel:
            return
        self.tabel.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            items = [
                str(row[0]), row[1], row[2], row[3],
                f"{row[4]} Org", row[5] or "-", row[6]
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, row[0])
                if col in (0, 1, 3, 4, 6):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tabel.setItem(idx, col, item)
        self.tabel.resizeRowsToContents()

    def tambah_ruang(self):
        dialog = _DialogTambahRuangBMN(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._load_filter_gedung()
            self.load_data()

    def ubah_ruang(self):
        if not self.tabel or self.tabel.currentRow() < 0:
            QMessageBox.warning(self, "Pilih Ruang", "Pilih baris ruang yang ingin diubah terlebih dahulu!")
            return
        id_ruang = self.tabel.item(self.tabel.currentRow(), 0).data(Qt.UserRole)
        dialog = _DialogUbahRuangBMN(id_ruang, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._load_filter_gedung()
            self.load_data()

    def hapus_ruang(self):
        if not self.tabel or self.tabel.currentRow() < 0:
            QMessageBox.warning(self, "Pilih Ruang", "Pilih baris ruang yang ingin dihapus terlebih dahulu!")
            return
        row_idx = self.tabel.currentRow()
        id_ruang = self.tabel.item(row_idx, 0).data(Qt.UserRole)
        nama_ruang = f"{self.tabel.item(row_idx, 1).text()} - {self.tabel.item(row_idx, 2).text()}"

        reply = QMessageBox.question(
            self, "Konfirmasi Hapus", f"Hapus ruangan {nama_ruang}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ruang WHERE id_ruang = %s", (id_ruang,))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Berhasil", "Ruangan berhasil dihapus.")
                self._load_filter_gedung()
                self.load_data()
            except Exception as e:
                if "1451" in str(e):
                    nonaktif = QMessageBox.question(
                        self,
                        "Ruang Memiliki Riwayat",
                        f"Ruangan {nama_ruang} tidak bisa dihapus permanen karena sudah memiliki riwayat peminjaman.\n\n"
                        "Ubah status ruangan menjadi 'Tidak Tersedia' agar tidak bisa dipinjam lagi?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    if nonaktif == QMessageBox.Yes:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE ruang SET status_ruang = 'Tidak Tersedia' WHERE id_ruang = %s", (id_ruang,))
                        conn.commit()
                        conn.close()
                        QMessageBox.information(self, "Berhasil", "Status ruangan diubah menjadi 'Tidak Tersedia'.")
                        self.load_data()
                else:
                    QMessageBox.warning(self, "Gagal Hapus", f"Gagal menghapus ruangan:\n{e}")

    def buka_dashboard(self):
        from controller.dashboard_bmn import DashboardBMNController
        self.win = DashboardBMNController(self.user)
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