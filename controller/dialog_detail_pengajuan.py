import os
import tempfile
from PyQt5.QtWidgets import (
    QDialog, QMessageBox, QLabel, QLineEdit, QTextEdit, QPlainTextEdit, QPushButton
)
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl, QPoint
import ui.detail_peminjaman as _ui_form
from model.connectiondb import get_db_connection

_ui_name = [n for n in dir(_ui_form) if n.startswith("Ui_")][0]
_UiClass = getattr(_ui_form, _ui_name)


class DialogDetailPengajuanController(QDialog):
    def __init__(self, id_pengajuan, user_data=None, parent=None):
        if not isinstance(user_data, dict):
            parent = user_data
            user_data = {}

        super().__init__(parent)
        self.ui = _UiClass()
        self.ui.setupUi(self)
        self.id_pengajuan = id_pengajuan
        self.user = user_data

        self.file_surat_path = None
        self.surat_blob = None
        self.nama_file_surat = None

        for btn in self.findChildren(QPushButton):
            teks = btn.text().lower()
            obj = btn.objectName().lower()
            if any(k in teks or k in obj for k in ("surat", "pdf", "berkas", "lampiran", "lihat")):
                btn.clicked.connect(self.buka_surat)
            elif any(k in teks or k in obj for k in ("tutup", "batal", "close", "kembali", "ok")):
                btn.clicked.connect(self.reject)

        self.load_detail()

    def _pos_dialog(self, widget):
        """Mengambil koordinat (x, y) widget relatif terhadap jendela QDialog utama."""
        return widget.mapTo(self, QPoint(0, 0))

    def _isi_field(self, kandidat_nama, nilai):
        for nama in kandidat_nama:
            widget = getattr(self.ui, nama, None)
            if isinstance(widget, QLabel):
                widget.setText(str(nilai))
                return True
            if isinstance(widget, QLineEdit):
                widget.setText(str(nilai))
                widget.setReadOnly(True)
                return True
            if isinstance(widget, (QTextEdit, QPlainTextEdit)):
                widget.setPlainText(str(nilai))
                widget.setReadOnly(True)
                return True
        return False

    def _isi_label_berdasarkan_posisi(self, mapping_sejajar, mapping_bawah):
        semua_label = self.findChildren(QLabel)
        label_nilai = [
            lbl for lbl in semua_label
            if lbl.text().strip().lower() == "textlabel"
        ]

        for lbl_judul in semua_label:
            if lbl_judul in label_nilai:
                continue
            teks_judul = lbl_judul.text().lower().strip()
            pos_judul = self._pos_dialog(lbl_judul)

            for kunci, nilai in mapping_sejajar:
                if kunci in teks_judul:
                    kandidat = [
                        v for v in label_nilai
                        if abs(self._pos_dialog(v).y() - pos_judul.y()) <= 15
                        and self._pos_dialog(v).x() >= pos_judul.x()
                    ]
                    if kandidat:
                        target = min(kandidat, key=lambda v: self._pos_dialog(v).x())
                        target.setText(str(nilai))
                        target.adjustSize()
                        label_nilai.remove(target)
                    break

        for lbl_judul in semua_label:
            if lbl_judul in label_nilai:
                continue
            teks_judul = lbl_judul.text().lower().strip()
            pos_judul = self._pos_dialog(lbl_judul)

            for kunci, nilai in mapping_bawah:
                if kunci in teks_judul:
                    kandidat = [
                        v for v in label_nilai
                        if self._pos_dialog(v).y() > pos_judul.y()
                    ]
                    if kandidat:
                        target = min(kandidat, key=lambda v: self._pos_dialog(v).y())
                        target.setText(str(nilai))
                        target.setWordWrap(True)
                        target.adjustSize()
                        label_nilai.remove(target)
                    break

    def load_detail(self):
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SHOW COLUMNS FROM pengajuan_peminjaman")
            kolom_db = [c[0] for c in cursor.fetchall()]

            select_file = "p.file_surat_pengajuan" if "file_surat_pengajuan" in kolom_db else "NULL"
            select_blob = "p.data_surat_pengajuan" if "data_surat_pengajuan" in kolom_db else "NULL"
            select_tgl_ajukan = "p.tanggal_pengajuan" if "tanggal_pengajuan" in kolom_db else "p.tanggal_mulai"
            select_keperluan = "COALESCE(p.keperluan, '-')" if "keperluan" in kolom_db else "'-'"

            sql = f"""
                SELECT p.id_pengajuan, COALESCE(u.nama_organisasi, u.nama), p.nama_kegiatan,
                       {select_tgl_ajukan}, r.kode_ruang, r.nama_ruang, r.lokasi_gedung,
                       p.tanggal_mulai, p.tanggal_selesai, p.status_pengajuan,
                       {select_keperluan}, COALESCE(p.catatan_verifikasi, '-'),
                       {select_file}, {select_blob}
                FROM pengajuan_peminjaman p
                JOIN ruang r ON p.id_ruang = r.id_ruang
                JOIN pengguna u ON p.id_oki = u.id_pengguna
                WHERE p.id_pengajuan = %s
            """
            cursor.execute(sql, (self.id_pengajuan,))
            row = cursor.fetchone()
        except Exception as e:
            QMessageBox.critical(self, "Error Database", f"Gagal memuat detail pengajuan:\n{e}")
            return
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()

        if not row:
            QMessageBox.warning(self, "Data Tidak Ditemukan", "Detail pengajuan tidak ditemukan.")
            return

        self.file_surat_path = row[12]
        self.surat_blob = row[13]
        self.nama_file_surat = (
            os.path.basename(self.file_surat_path)
            if self.file_surat_path
            else f"Surat_Pengajuan_{row[0]}.pdf"
        )

        teks_nama_surat = (
            self.nama_file_surat
            if (self.file_surat_path or self.surat_blob)
            else "Tidak ada berkas terlampir"
        )

        oki_str = row[1]
        kegiatan_str = row[2]
        tgl_ajukan_str = row[3].strftime("%d-%m-%Y %H:%M") if hasattr(row[3], "strftime") else str(row[3])
        ruang_str = f"{row[4]} - {row[5]} ({row[6]})"
        tanggal_str = row[7].strftime("%d-%m-%Y") if hasattr(row[7], "strftime") else str(row[7])
        waktu_str = (
            f"{row[7].strftime('%H:%M')} - {row[8].strftime('%H:%M')} WIB"
            if hasattr(row[7], "strftime") and hasattr(row[8], "strftime")
            else "-"
        )
        status_str = row[9]
        deskripsi_str = row[10] if row[10] and str(row[10]).strip() else "-"
        catatan_str = row[11] if row[11] and str(row[11]).strip() else "-"

        self._isi_field(["lblOki", "lblOrganisasi"], oki_str)
        self._isi_field(["lblKegiatan", "lblNamaKegiatan"], kegiatan_str)
        self._isi_field(["lblTanggalPengajuan", "lblTglPengajuan"], tgl_ajukan_str)
        self._isi_field(["lblRuang", "lblRuangan"], ruang_str)
        self._isi_field(["lblTanggal", "lblTanggalPinjam"], tanggal_str)
        self._isi_field(["lblWaktu", "lblJam"], waktu_str)
        self._isi_field(["lblStatus"], status_str)
        self._isi_field(["lblDeskripsi", "lblKeperluan", "txtDeskripsi", "txtKeperluan"], deskripsi_str)
        self._isi_field(["lblSurat", "lblNamaSurat", "txtSurat", "txtNamaSurat"], teks_nama_surat)
        self._isi_field(["lblCatatan", "txtCatatan"], catatan_str)

        self._isi_label_berdasarkan_posisi(
            mapping_sejajar=[
                ("organisasi", oki_str),
                ("nama kegiatan", kegiatan_str),
                ("tanggal pengajuan", tgl_ajukan_str),
                ("status", status_str),
                ("ruangan", ruang_str),
                ("tanggal pinjam", tanggal_str),
                ("waktu", waktu_str),
            ],
            mapping_bawah=[
                ("deskripsi", deskripsi_str),
                ("keperluan", deskripsi_str),
                ("surat pengajuan", teks_nama_surat),
            ]
        )

    def buka_surat(self):
        if not self.file_surat_path and not self.surat_blob:
            QMessageBox.information(self, "Lampiran Kosong", "Pengajuan ini tidak memiliki lampiran surat.")
            return

        if isinstance(self.file_surat_path, str) and self.file_surat_path:
            nama_dasar = os.path.basename(self.file_surat_path)
            kandidat_path = [
                self.file_surat_path,
                os.path.join("uploads", nama_dasar),
                os.path.join("ui", "uploads", nama_dasar),
            ]
            for path in kandidat_path:
                if os.path.exists(path):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(path)))
                    return

        if isinstance(self.surat_blob, (bytes, bytearray, memoryview)):
            nama_bersih = os.path.basename(self.nama_file_surat or f"Surat_PGJ_{self.id_pengajuan}.pdf")
            if not nama_bersih.lower().endswith(".pdf"):
                nama_bersih += ".pdf"

            temp_path = os.path.join(tempfile.gettempdir(), nama_bersih)
            with open(temp_path, "wb") as f:
                f.write(bytes(self.surat_blob))
            QDesktopServices.openUrl(QUrl.fromLocalFile(temp_path))
            return

        QMessageBox.warning(
            self,
            "File Tidak Ditemukan",
            f"File surat tidak ditemukan di folder penyimpanan maupun database:\n{self.file_surat_path}"
        )


DetailPengajuanController = DialogDetailPengajuanController
DialogDetailPeminjamanController = DialogDetailPengajuanController