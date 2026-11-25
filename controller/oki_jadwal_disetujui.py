import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QHeaderView,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from model.connectiondb import get_db_connection

# Ganti 'oki_jadwal_disetujui' & 'Ui_MainWindow' sesuai nama file di folder ui/
try:
    from ui.oki_jadwal_disetujui import Ui_MainWindow as Ui_OKIJadwalDisetujui
except ImportError:
    Ui_OKIJadwalDisetujui = None


def _cari_widget(ui, daftar_nama, tipe):
    for nama in daftar_nama:
        w = getattr(ui, nama, None)
        if isinstance(w, tipe):
            return w
    return None


class OKIJadwalDisetujuiController(QMainWindow):
    def __init__(self, user_data: dict = None, parent=None):
        super().__init__(parent)
        self.user_data = user_data or {}

        if Ui_OKIJadwalDisetujui is None:
            raise ImportError(
                "Sesuaikan import UI di bagian atas controller/oki_jadwal_disetujui.py dengan file di folder ui/."
            )

        self.ui = Ui_OKIJadwalDisetujui()
        self.ui.setupUi(self)
        self._bind_widgets()
        self._connect_signals()
        self.muat_jadwal()

    def _bind_widgets(self):
        self.tbl_jadwal = _cari_widget(
            self.ui,
            ["tableWidget_jadwal", "tbl_jadwal", "tableJadwal", "tableWidget"],
            QTableWidget,
        )
        self.txt_cari = _cari_widget(
            self.ui,
            ["lineEdit_cari", "txt_cari", "lineEdit_cari_jadwal"],
            QLineEdit,
        )
        self.btn_cari = _cari_widget(
            self.ui,
            ["pushButton_cari", "btn_cari", "pushButton_cari_jadwal"],
            QPushButton,
        )
        self.btn_refresh = _cari_widget(
            self.ui,
            ["pushButton_refresh", "btn_refresh", "pushButton_muat_ulang"],
            QPushButton,
        )

    def _connect_signals(self):
        if self.btn_cari:
            self.btn_cari.clicked.connect(self.muat_jadwal)
        if self.txt_cari:
            self.txt_cari.returnPressed.connect(self.muat_jadwal)
        if self.btn_refresh:
            self.btn_refresh.clicked.connect(self._reset_dan_muat)

    def _reset_dan_muat(self):
        if self.txt_cari:
            self.txt_cari.clear()
        self.muat_jadwal()

    def _ambil_jadwal_disetujui(self, keyword=""):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = """
                SELECT p.id_pengajuan, r.kode_ruang, r.nama_ruang,
                       COALESCE(u.nama_organisasi, u.nama), p.nama_kegiatan,
                       p.tanggal_mulai, p.tanggal_selesai, p.status_pengajuan
                FROM pengajuan_peminjaman p
                JOIN ruang r ON p.id_ruang = r.id_ruang
                JOIN pengguna u ON p.id_oki = u.id_pengguna
                WHERE p.status_pengajuan = 'Disetujui'
            """
            params = []
            if keyword and keyword.strip():
                sql += " AND (r.kode_ruang LIKE %s OR r.nama_ruang LIKE %s OR p.nama_kegiatan LIKE %s OR COALESCE(u.nama_organisasi, u.nama) LIKE %s)"
                kw = f"%{keyword.strip()}%"
                params.extend([kw, kw, kw, kw])
            sql += " ORDER BY p.tanggal_mulai ASC"
            cursor.execute(sql, tuple(params))
            return True, "OK", cursor.fetchall() or []
        except Exception as e:
            return False, f"Gagal memuat jadwal disetujui: {e}", []
        finally:
            conn.close()

    def muat_jadwal(self):
        if not self.tbl_jadwal:
            return
        kw = self.txt_cari.text() if self.txt_cari else ""
        ok, pesan, rows = self._ambil_jadwal_disetujui(keyword=kw)
        if not ok:
            QMessageBox.warning(self, "Peringatan", pesan)
            return

        headers = ["ID", "Ruang", "Organisasi", "Kegiatan", "Waktu Mulai", "Waktu Selesai", "Status"]
        self.tbl_jadwal.setColumnCount(len(headers))
        self.tbl_jadwal.setHorizontalHeaderLabels(headers)
        self.tbl_jadwal.setRowCount(len(rows))
        self.tbl_jadwal.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_jadwal.setEditTriggers(QTableWidget.NoEditTriggers)

        for idx, r in enumerate(rows):
            id_pengajuan, kode_ruang, nama_ruang, org, kegiatan, tgl_mulai, tgl_selesai, status = r
            vals = [
                str(id_pengajuan),
                f"{kode_ruang} - {nama_ruang}",
                str(org or "-"),
                str(kegiatan or "-"),
                str(tgl_mulai),
                str(tgl_selesai),
                str(status),
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if col in (0, 6):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tbl_jadwal.setItem(idx, col, item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = OKIJadwalDisetujuiController()
    win.show()
    sys.exit(app.exec_())