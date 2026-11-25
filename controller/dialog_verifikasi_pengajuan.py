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
        self.surat_data = None
        self.nama_file_surat = None

        # Deteksi otomatis input catatan verifikasi (QTextEdit / QPlainTextEdit / QLineEdit)
        texts = self.findChildren(QTextEdit)
        plains = self.findChildren(QPlainTextEdit)
        lines = [inp for inp in self.findChildren(QLineEdit) if not inp.isReadOnly()]
        self.inp_catatan = (
            texts[0] if texts
            else plains[0] if plains
            else lines[-1] if lines
            else None
        )

        # Hubungkan tombol Setujui, Tolak, Lihat Surat, dan Tutup secara otomatis
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

    def load_detail(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SHOW COLUMNS FROM pengajuan_peminjaman")
        kolom_db = [c[0] for c in cursor.fetchall()]

        kolom_surat = next(
            (k for k in kolom_db if any(w in k.lower() for w in ("file_surat", "surat_blob", "dokumen", "surat"))),
            None
        )
        kolom_nama_surat = next(
            (k for k in kolom_db if "nama" in k.lower() and "surat" in k.lower()),
            None
        )

        select_surat = f"p.{kolom_surat}" if kolom_surat else "NULL"
        select_nama_surat = f"p.{kolom_nama_surat}" if kolom_nama_surat else "NULL"

        sql = f"""
            SELECT p.id_pengajuan, COALESCE(u.nama_organisasi, u.nama), p.nama_kegiatan,
                   r.kode_ruang, r.nama_ruang, r.lokasi_gedung,
                   p.tanggal_mulai, p.tanggal_selesai, p.status_pengajuan,
                   COALESCE(p.catatan_verifikasi, ''),
                   {select_surat}, {select_nama_surat}
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

        self.surat_data = row[10]
        self.nama_file_surat = row[11] or f"Surat_Pengajuan_{row[0]}.pdf"

        oki_str = row[1]
        kegiatan_str = row[2]
        ruang_str = f"{row[3]} - {row[4]} ({row[5]})"
        tanggal_str = row[6].strftime("%d-%m-%Y")
        waktu_str = f"{row[6].strftime('%H:%M')} - {row[7].strftime('%H:%M')} WIB"
        status_str = row[8]
        catatan_str = row[9]

        # Isi berdasarkan nama objek widget jika sesuai
        terisi = [
            self._isi_field(["lblOki", "lblOrganisasi", "txtOki", "txtOrganisasi"], oki_str),
            self._isi_field(["lblKegiatan", "lblNamaKegiatan", "txtKegiatan", "txtNamaKegiatan"], kegiatan_str),
            self._isi_field(["lblRuang", "txtRuang"], ruang_str),
            self._isi_field(["lblTanggal", "txtTanggal"], tanggal_str),
            self._isi_field(["lblWaktu", "lblJam", "txtWaktu"], waktu_str),
            self._isi_field(["lblStatus", "txtStatus"], status_str),
        ]

        # Fallback jika label nilai memakai nama default Qt Designer (label_2, label_4, dst.)
        if not any(terisi):
            ringkasan = [
                ("organisasi", oki_str),
                ("oki", oki_str),
                ("kegiatan", kegiatan_str),
                ("ruang", ruang_str),
                ("tanggal", tanggal_str),
                ("waktu", waktu_str),
                ("jam", waktu_str),
                ("status", status_str),
            ]
            semua_label = self.findChildren(QLabel)
            for idx, lbl in enumerate(semua_label):
                teks_lbl = lbl.text().lower().strip()
                for kunci, val in ringkasan:
                    if teks_lbl.startswith(kunci) and ":" in teks_lbl:
                        lbl.setText(f"{lbl.text().split(':')[0]}: {val}")
                        break
                    elif teks_lbl == kunci and idx + 1 < len(semua_label):
                        semua_label[idx + 1].setText(val)
                        break

        if self.inp_catatan and catatan_str:
            if hasattr(self.inp_catatan, "setPlainText"):
                self.inp_catatan.setPlainText(catatan_str)
            else:
                self.inp_catatan.setText(catatan_str)

    def buka_surat(self):
        if not self.surat_data:
            QMessageBox.information(self, "Lampiran Kosong", "Pengajuan ini tidak memiliki lampiran surat.")
            return

        # Jika tersimpan sebagai path file lokal di database
        if isinstance(self.surat_data, str):
            if os.path.exists(self.surat_data):
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(self.surat_data)))
            else:
                QMessageBox.warning(self, "File Tidak Ditemukan", f"File surat tidak ditemukan:\n{self.surat_data}")
            return

        # Jika tersimpan sebagai bytes / LONGBLOB PDF di database
        if isinstance(self.surat_data, (bytes, bytearray)):
            temp_path = os.path.join(tempfile.gettempdir(), os.path.basename(self.nama_file_surat))
            if not temp_path.lower().endswith(".pdf"):
                temp_path += ".pdf"
            with open(temp_path, "wb") as f:
                f.write(self.surat_data)
            QDesktopServices.openUrl(QUrl.fromLocalFile(temp_path))

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