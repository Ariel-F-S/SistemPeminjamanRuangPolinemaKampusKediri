import os
import tempfile
from PyQt5.QtWidgets import (
    QDialog, QMessageBox, QLabel, QLineEdit, QTextEdit, QPlainTextEdit, QPushButton
)
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
import ui.detail_dan_verifikasi_pengajuan as _ui_form
from model.connectiondb import get_db_connection

_ui_name = [n for n in dir(_ui_form) if n.startswith("Ui_")][0]
_UiClass = getattr(_ui_form, _ui_name)


class DialogVerifikasiPengajuanController(QDialog):
    def __init__(self, id_pengajuan, user_data, parent=None):
        super().__init__(parent)
        self.ui = _UiClass()
        self.ui.setupUi(self)
        self.id_pengajuan = id_pengajuan
        self.user = user_data
        self.file_surat_path = None
        self.surat_blob = None
        self.nama_file_surat = None

        
        texts = self.findChildren(QTextEdit)
        plains = self.findChildren(QPlainTextEdit)
        line_edits = sorted(self.findChildren(QLineEdit), key=lambda w: w.y())

        self.txt_nama_surat = line_edits[0] if line_edits else None
        if isinstance(self.txt_nama_surat, QLineEdit):
            self.txt_nama_surat.setReadOnly(True)

        self.inp_catatan = (
            texts[0] if texts
            else plains[0] if plains
            else line_edits[-1] if len(line_edits) > 1
            else None
        )

        
        for btn in self.findChildren(QPushButton):
            teks = btn.text().lower()
            obj = btn.objectName().lower()
            if any(k in teks or k in obj for k in ("setuju", "terima", "approve")):
                btn.clicked.connect(lambda: self.simpan_verifikasi("Disetujui"))
            elif any(k in teks or k in obj for k in ("tolak", "reject")):
                btn.clicked.connect(lambda: self.simpan_verifikasi("Ditolak"))
            elif any(k in teks or k in obj for k in ("surat", "pdf", "berkas", "lampiran", "lihat")):
                btn.clicked.connect(self.buka_surat)
            elif any(k in teks or k in obj for k in ("tutup", "batal", "close", "kembali")):
                btn.clicked.connect(self.reject)

        self.load_detail()

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
        return False

    def _isi_textlabel_berdasarkan_posisi(self, mapping_judul_nilai):
        """
        Mencocokkan QLabel judul (misal 'ID Pengajuan:', 'Organisasi:') dengan QLabel
        bernilai 'TextLabel' yang berada di sebelah kanannya pada baris (Y) yang sama.
        """
        semua_label = self.findChildren(QLabel)
        label_nilai = [
            lbl for lbl in semua_label
            if lbl.text().strip().lower() == "textlabel"
        ]

        for lbl_judul in semua_label:
            teks_judul = lbl_judul.text().lower().strip()
            for kunci, nilai in mapping_judul_nilai:
                if kunci in teks_judul and lbl_judul not in label_nilai:
                    
                    if "textlabel" in teks_judul:
                        prefix = lbl_judul.text().split(":")[0]
                        lbl_judul.setText(f"{prefix}: {nilai}")
                        break

                    
                    kandidat = [
                        v for v in label_nilai
                        if abs(v.y() - lbl_judul.y()) <= 15 and v.x() >= lbl_judul.x()
                    ]
                    if kandidat:
                        target = min(kandidat, key=lambda v: v.x())
                        target.setText(str(nilai))
                        target.adjustSize()
                        label_nilai.remove(target)
                    break

    def load_detail(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SHOW COLUMNS FROM pengajuan_peminjaman")
        kolom_db = [c[0] for c in cursor.fetchall()]

        select_file = "p.file_surat_pengajuan" if "file_surat_pengajuan" in kolom_db else "NULL"
        select_blob = "p.data_surat_pengajuan" if "data_surat_pengajuan" in kolom_db else "NULL"

        sql = f"""
            SELECT p.id_pengajuan, COALESCE(u.nama_organisasi, u.nama), p.nama_kegiatan,
                   r.kode_ruang, r.nama_ruang, r.lokasi_gedung,
                   p.tanggal_mulai, p.tanggal_selesai, p.status_pengajuan,
                   COALESCE(p.catatan_verifikasi, ''),
                   {select_file}, {select_blob}
            FROM pengajuan_peminjaman p
            JOIN ruang r ON p.id_ruang = r.id_ruang
            JOIN pengguna u ON p.id_oki = u.id_pengguna
            WHERE p.id_pengajuan = %s
        """
        cursor.execute(sql, (self.id_pengajuan,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            QMessageBox.warning(self, "Data Tidak Ditemukan", "Detail pengajuan tidak ditemukan.")
            return

        self.file_surat_path = row[10]
        self.surat_blob = row[11]
        self.nama_file_surat = (
            os.path.basename(self.file_surat_path)
            if self.file_surat_path
            else f"Surat_Pengajuan_{row[0]}.pdf"
        )

       
        if isinstance(self.txt_nama_surat, QLineEdit):
            if self.file_surat_path or self.surat_blob:
                self.txt_nama_surat.setText(self.nama_file_surat)
            else:
                self.txt_nama_surat.setText("Tidak ada berkas terlampir")

        id_str = f"PGJ-{int(row[0]):04d}" if str(row[0]).isdigit() else str(row[0])
        oki_str = row[1]
        kegiatan_str = row[2]
        ruang_str = f"{row[3]} - {row[4]} ({row[5]})"
        tanggal_str = row[6].strftime("%d-%m-%Y")
        waktu_str = f"{row[6].strftime('%H:%M')} - {row[7].strftime('%H:%M')} WIB"
        status_str = row[8]
        catatan_str = row[9]

        
        terisi = [
            self._isi_field(["lblId", "lblIdPengajuan", "txtId"], id_str),
            self._isi_field(["lblOki", "lblOrganisasi", "txtOki", "txtOrganisasi"], oki_str),
            self._isi_field(["lblKegiatan", "lblNamaKegiatan", "txtKegiatan", "txtNamaKegiatan"], kegiatan_str),
            self._isi_field(["lblRuang", "txtRuang"], ruang_str),
            self._isi_field(["lblTanggal", "txtTanggal"], tanggal_str),
            self._isi_field(["lblWaktu", "lblJam", "txtWaktu"], waktu_str),
            self._isi_field(["lblStatus", "txtStatus"], status_str),
        ]

       
        if not all(terisi):
            self._isi_textlabel_berdasarkan_posisi([
                ("id pengajuan", id_str),
                ("organisasi", oki_str),
                ("nama kegiatan", kegiatan_str),
                ("ruang", ruang_str),
                ("tanggal", tanggal_str),
                ("waktu", waktu_str),
                ("status", status_str),
            ])

        if self.inp_catatan and catatan_str:
            if hasattr(self.inp_catatan, "setPlainText"):
                self.inp_catatan.setPlainText(catatan_str)
            else:
                self.inp_catatan.setText(catatan_str)

    def buka_surat(self):
        if not self.file_surat_path and not self.surat_blob:
            QMessageBox.information(self, "Lampiran Kosong", "Pengajuan ini tidak memiliki lampiran surat.")
            return

        
        if isinstance(self.file_surat_path, str) and os.path.exists(self.file_surat_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(self.file_surat_path)))
            return

        
        if isinstance(self.surat_blob, (bytes, bytearray, memoryview)):
            data_bytes = bytes(self.surat_blob)
            nama_bersih = os.path.basename(self.nama_file_surat or f"Surat_PGJ_{self.id_pengajuan}.pdf")
            if not nama_bersih.lower().endswith(".pdf"):
                nama_bersih += ".pdf"

            temp_path = os.path.join(tempfile.gettempdir(), nama_bersih)
            with open(temp_path, "wb") as f:
                f.write(data_bytes)
            QDesktopServices.openUrl(QUrl.fromLocalFile(temp_path))
            return

        QMessageBox.warning(
            self,
            "File Tidak Ditemukan",
            f"File surat tidak ditemukan di folder lokal maupun database:\n{self.file_surat_path}"
        )

    def simpan_verifikasi(self, status_baru):
        catatan = ""
        if self.inp_catatan:
            catatan = (
                self.inp_catatan.toPlainText().strip()
                if hasattr(self.inp_catatan, "toPlainText")
                else self.inp_catatan.text().strip()
            )

        if not catatan:
            catatan = (
                "Disetujui oleh pihak BMN."
                if status_baru == "Disetujui"
                else "Pengajuan ditolak oleh pihak BMN."
            )

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SHOW COLUMNS FROM pengajuan_peminjaman")
            kolom_db = [c[0] for c in cursor.fetchall()]

            set_parts = ["status_pengajuan = %s", "catatan_verifikasi = %s"]
            params = [status_baru, catatan]

            if "id_bmn" in kolom_db:
                set_parts.append("id_bmn = %s")
                params.append(self.user["id_pengguna"])
            if "tanggal_verifikasi" in kolom_db:
                set_parts.append("tanggal_verifikasi = NOW()")

            params.append(self.id_pengajuan)
            sql = f"UPDATE pengajuan_peminjaman SET {', '.join(set_parts)} WHERE id_pengajuan = %s"

            cursor.execute(sql, tuple(params))
            conn.commit()
            conn.close()

            QMessageBox.information(
                self, "Verifikasi Berhasil",
                f"Pengajuan berhasil diperbarui menjadi '{status_baru}'."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error Database", f"Gagal menyimpan hasil verifikasi:\n{e}")