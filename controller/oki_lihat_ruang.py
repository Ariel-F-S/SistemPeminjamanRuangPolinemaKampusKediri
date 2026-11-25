import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QHeaderView,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from model.connectiondb import get_db_connection

# Ganti 'oki_lihat_ruang' & 'Ui_MainWindow' sesuai nama file di folder ui/
try:
    from ui.oki_lihat_ruang import Ui_MainWindow as Ui_OKILihatRuang
except ImportError:
    Ui_OKILihatRuang = None


def _cari_widget(ui, daftar_nama, tipe):
    for nama in daftar_nama:
        w = getattr(ui, nama, None)
        if isinstance(w, tipe):
            return w
    return None


class OKILihatRuangController(QMainWindow):
    def __init__(self, user_data: dict = None, parent=None):
        super().__init__(parent)
        self.user_data = user_data or {}

        if Ui_OKILihatRuang is None:
            raise ImportError(
                "Sesuaikan import UI di bagian atas controller/oki_lihat_ruang.py dengan file di folder ui/."
            )

        self.ui = Ui_OKILihatRuang()
        self.ui.setupUi(self)
        self._bind_widgets()
        self._connect_signals()
        self.muat_data_ruang()

    def _bind_widgets(self):
        self.tbl_ruang = _cari_widget(
            self.ui,
            ["tableWidget_ruang", "tbl_ruang", "tableRuang", "tableWidget"],
            QTableWidget,
        )
        self.txt_cari = _cari_widget(
            self.ui,
            ["lineEdit_cari", "txt_cari", "lineEdit_cari_ruang", "txt_cari_ruang"],
            QLineEdit,
        )
        self.cmb_gedung = _cari_widget(
            self.ui,
            ["comboBox_gedung", "cmb_gedung", "cmbGedung"],
            QComboBox,
        )
        self.btn_cari = _cari_widget(
            self.ui,
            ["pushButton_cari", "btn_cari", "pushButton_cari_ruang", "btn_cari_ruang"],
            QPushButton,
        )
        self.btn_refresh = _cari_widget(
            self.ui,
            ["pushButton_refresh", "btn_refresh", "pushButton_reset", "btn_reset"],
            QPushButton,
        )

    def _connect_signals(self):
        if self.btn_cari:
            self.btn_cari.clicked.connect(self.muat_data_ruang)
        if self.txt_cari:
            self.txt_cari.returnPressed.connect(self.muat_data_ruang)
        if self.cmb_gedung:
            if self.cmb_gedung.count() == 0:
                self.cmb_gedung.addItems(["Semua", "Gedung A", "Gedung B", "Gedung C", "Gedung D"])
            self.cmb_gedung.currentTextChanged.connect(self.muat_data_ruang)
        if self.btn_refresh:
            self.btn_refresh.clicked.connect(self.reset_filter)

    def reset_filter(self):
        if self.txt_cari:
            self.txt_cari.clear()
        if self.cmb_gedung:
            self.cmb_gedung.setCurrentIndex(0)
        self.muat_data_ruang()

    def _ambil_ruang_tersedia(self, keyword="", gedung="Semua"):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = """
                SELECT id_ruang, kode_ruang, nama_ruang, lokasi_gedung, kapasitas, fasilitas, status_ruang
                FROM ruang
                WHERE status_ruang = 'Tersedia'
            """
            params = []
            if keyword and keyword.strip():
                sql += " AND (kode_ruang LIKE %s OR nama_ruang LIKE %s OR fasilitas LIKE %s)"
                kw = f"%{keyword.strip()}%"
                params.extend([kw, kw, kw])
            if gedung and gedung != "Semua":
                sql += " AND lokasi_gedung = %s"
                params.append(gedung)
            sql += " ORDER BY kode_ruang ASC"
            cursor.execute(sql, tuple(params))
            return True, "OK", cursor.fetchall() or []
        except Exception as e:
            return False, f"Gagal memuat data ruang: {e}", []
        finally:
            conn.close()

    def muat_data_ruang(self):
        if not self.tbl_ruang:
            return
        kw = self.txt_cari.text() if self.txt_cari else ""
        gedung = self.cmb_gedung.currentText() if self.cmb_gedung else "Semua"
        ok, pesan, rows = self._ambil_ruang_tersedia(keyword=kw, gedung=gedung)
        if not ok:
            QMessageBox.warning(self, "Peringatan", pesan)
            return

        headers = ["ID", "Kode Ruang", "Nama Ruang", "Gedung", "Kapasitas", "Fasilitas", "Status"]
        self.tbl_ruang.setColumnCount(len(headers))
        self.tbl_ruang.setHorizontalHeaderLabels(headers)
        self.tbl_ruang.setRowCount(len(rows))
        self.tbl_ruang.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_ruang.setEditTriggers(QTableWidget.NoEditTriggers)

        for idx, r in enumerate(rows):
            id_ruang, kode_ruang, nama_ruang, lokasi_gedung, kapasitas, fasilitas, status_ruang = r
            vals = [
                str(id_ruang),
                str(kode_ruang),
                str(nama_ruang),
                str(lokasi_gedung or "-"),
                f"{kapasitas} orang",
                str(fasilitas or "-"),
                str(status_ruang),
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if col in (0, 4, 6):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tbl_ruang.setItem(idx, col, item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = OKILihatRuangController()
    win.show()
    sys.exit(app.exec_())