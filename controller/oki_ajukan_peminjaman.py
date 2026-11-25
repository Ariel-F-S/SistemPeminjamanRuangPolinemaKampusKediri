import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QMessageBox, QFileDialog,
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox,
    QDateEdit, QTimeEdit, QDateTimeEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import QDate, QTime, QDateTime, Qt
import ui.ajukan_pinjam as ui_form
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


class OkiAjukanPeminjamanController(_BaseClass):
    def __init__(self, user_data):
        super().__init__()
        self.ui = _UiClass()
        self.ui.setupUi(self)
        self.user = user_data
        self.model = User()
        self.path_surat = ""

        nama_oki = self.user.get("nama_organisasi") or self.user.get("nama", "OKI")
        lbl_oki = _cari(self.ui, ["lblOki", "label_oki"], QLabel)
        if lbl_oki:
            lbl_oki.setText(f"OKI: {nama_oki}")

        # Identifikasi widget input form secara otomatis
        self.inp_kegiatan = _cari(self.ui, ["txtKegiatan", "txtNamaKegiatan", "lineEdit"], QLineEdit)
        self.cmb_ruang = _cari(self.ui, ["cmbRuang", "comboRuang", "comboBox"], QComboBox)
        self.inp_tgl = _cari(self.ui, ["dtTanggal", "dateTanggal", "dateEdit"], QDateEdit)
        self.inp_jam_mulai = _cari(self.ui, ["tmMulai", "timeMulai", "timeEdit"], QTimeEdit)
        self.inp_jam_selesai = _cari(self.ui, ["tmSelesai", "timeSelesai", "timeEdit_2"], QTimeEdit)
        self.dt_mulai = _cari(self.ui, ["dtMulai", "dateTimeEdit"], QDateTimeEdit)
        self.dt_selesai = _cari(self.ui, ["dtSelesai", "dateTimeEdit_2"], QDateTimeEdit)
        self.inp_keperluan = _cari(self.ui, ["txtKeperluan", "textEdit", "plainTextEdit"], (QTextEdit, QPlainTextEdit, QLineEdit))
        self.lbl_file = _cari(self.ui, ["lblFileSurat", "lblNamaFile", "lblFile", "lineEdit_2", "txtFileSurat"], (QLabel, QLineEdit))
        self.lbl_status_cek = _cari(self.ui, ["lblStatusJadwal", "lblStatus", "label_status"], QLabel)
        self.tbl_jadwal = _cari(self.ui, ["tblJadwal", "tableWidget"], QTableWidget)

        if self.inp_tgl:
            self.inp_tgl.setDate(QDate.currentDate())
        if self.inp_jam_mulai:
            self.inp_jam_mulai.setTime(QTime(8, 0))
        if self.inp_jam_selesai:
            self.inp_jam_selesai.setTime(QTime(12, 0))
        if self.dt_mulai:
            self.dt_mulai.setDateTime(QDateTime.currentDateTime())
        if self.dt_selesai:
            self.dt_selesai.setDateTime(QDateTime.currentDateTime().addSecs(3600))

        self._load_daftar_ruang()

        # Hubungkan tombol aksi
        btn_cek = _cari(self.ui, ["btnCekJadwal", "btnCekKetersediaan", "pushButton_7"], QPushButton)
        if btn_cek:
            btn_cek.clicked.connect(self.cek_ketersediaan_jadwal)

        btn_pilih = _cari(self.ui, ["btnPilihFile", "btnUpload", "btnBrowse", "pushButton_8"], QPushButton)
        if btn_pilih:
            btn_pilih.clicked.connect(self.pilih_file_surat)

        btn_reset = _cari(self.ui, ["btnReset", "pushButton_9"], QPushButton)
        if btn_reset:
            btn_reset.clicked.connect(self.reset_form)

        btn_kirim = _cari(self.ui, ["btnKirim", "btnAjukan", "btnSimpan", "pushButton_10"], QPushButton)
        if btn_kirim:
            btn_kirim.clicked.connect(self.simpan_pengajuan)

        # Navigasi Sidebar OKI
        for nama, fungsi in [
            ("btnDashboard", self.buka_dashboard),
            ("btnDaftarRuang", self.buka_daftar_ruang),
            ("btnAjukanPinjam", self.reset_form),
            ("btnRiwayat", self.buka_riwayat),
            ("btnJadwal", self.buka_jadwal),
            ("btnLogout", self.logout),
        ]:
            btn = getattr(self.ui, nama, None)
            if isinstance(btn, QPushButton):
                btn.clicked.connect(fungsi)

    def _load_daftar_ruang(self):
        if not self.cmb_ruang:
            return
        self.cmb_ruang.clear()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id_ruang, kode_ruang, nama_ruang FROM ruang WHERE status_ruang = 'Tersedia' ORDER BY kode_ruang ASC"
        )
        for r in cursor.fetchall() or []:
            self.cmb_ruang.addItem(f"{r[1]} - {r[2]}", r[0])
        conn.close()

    def _ambil_waktu_mulai_selesai(self):
        if self.dt_mulai and self.dt_selesai:
            return self.dt_mulai.dateTime().toPyDateTime(), self.dt_selesai.dateTime().toPyDateTime()
        tgl = self.inp_tgl.date().toPyDate() if self.inp_tgl else datetime.now().date()
        jm = self.inp_jam_mulai.time().toPyTime() if self.inp_jam_mulai else datetime.now().time()
        js = self.inp_jam_selesai.time().toPyTime() if self.inp_jam_selesai else datetime.now().time()
        return datetime.combine(tgl, jm), datetime.combine(tgl, js)

    def cek_ketersediaan_jadwal(self):
        if not self.cmb_ruang or not self.cmb_ruang.currentData():
            return False
        id_ruang = self.cmb_ruang.currentData()
        dt_mulai, dt_selesai = self._ambil_waktu_mulai_selesai()

        if dt_selesai <= dt_mulai:
            QMessageBox.warning(self, "Validasi Waktu", "Jam selesai harus lebih akhir dari jam mulai!")
            return False

        conn = get_db_connection()
        cursor = conn.cursor()
        # Tampilkan daftar jadwal terpakai pada tanggal tersebut ke tabel samping jika ada
        if self.tbl_jadwal:
            cursor.execute(
                """
                SELECT p.nama_kegiatan, p.tanggal_mulai, p.tanggal_selesai, p.status_pengajuan
                FROM pengajuan_peminjaman p
                WHERE p.id_ruang = %s AND DATE(p.tanggal_mulai) = DATE(%s)
                  AND p.status_pengajuan IN ('Menunggu', 'Disetujui')
                ORDER BY p.tanggal_mulai ASC
                """,
                (id_ruang, dt_mulai)
            )
            jadwal_hari_ini = cursor.fetchall() or []
            self.tbl_jadwal.setColumnCount(3)
            self.tbl_jadwal.setHorizontalHeaderLabels(["Kegiatan", "Jam", "Status"])
            self.tbl_jadwal.setRowCount(len(jadwal_hari_ini))
            for idx, j in enumerate(jadwal_hari_ini):
                jam_str = f"{j[1].strftime('%H:%M')} - {j[2].strftime('%H:%M')}"
                self.tbl_jadwal.setItem(idx, 0, QTableWidgetItem(j[0]))
                self.tbl_jadwal.setItem(idx, 1, QTableWidgetItem(jam_str))
                self.tbl_jadwal.setItem(idx, 2, QTableWidgetItem(j[3]))

        # Cek bentrok jam
        cursor.execute(
            """
            SELECT COUNT(*) FROM pengajuan_peminjaman
            WHERE id_ruang = %s
              AND status_pengajuan IN ('Menunggu', 'Disetujui')
              AND (%s < tanggal_selesai AND %s > tanggal_mulai)
            """,
            (id_ruang, dt_mulai, dt_selesai)
        )
        bentrok = cursor.fetchone()[0] > 0
        conn.close()

        if self.lbl_status_cek:
            if bentrok:
                self.lbl_status_cek.setText("Bentrok / Tidak Tersedia!")
                self.lbl_status_cek.setStyleSheet("color: #C0392B; font-weight: bold;")
            else:
                self.lbl_status_cek.setText("Tersedia!")
                self.lbl_status_cek.setStyleSheet("color: #1E8449; font-weight: bold;")
        return not bentrok

    def pilih_file_surat(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Pilih Surat Pengajuan", "", "Dokumen (*.pdf *.jpg *.jpeg *.png)"
        )
        if not file_path:
            return
        if os.path.getsize(file_path) > 10 * 1024 * 1024:
            QMessageBox.warning(self, "Ukuran File", "Maksimal ukuran file surat adalah 10 MB.")
            return
        self.path_surat = file_path
        if self.lbl_file:
            self.lbl_file.setText(os.path.basename(file_path))

    def simpan_pengajuan(self):
        nama_kegiatan = self.inp_kegiatan.text().strip() if self.inp_kegiatan else ""
        id_ruang = self.cmb_ruang.currentData() if self.cmb_ruang else None
        dt_mulai, dt_selesai = self._ambil_waktu_mulai_selesai()

        if isinstance(self.inp_keperluan, (QTextEdit, QPlainTextEdit)):
            keperluan = self.inp_keperluan.toPlainText().strip()
        elif isinstance(self.inp_keperluan, QLineEdit):
            keperluan = self.inp_keperluan.text().strip()
        else:
            keperluan = nama_kegiatan

        if not nama_kegiatan:
            QMessageBox.warning(self, "Validasi", "Nama kegiatan wajib diisi!")
            return
        if not id_ruang:
            QMessageBox.warning(self, "Validasi", "Pilih ruangan terlebih dahulu!")
            return
        if dt_selesai <= dt_mulai:
            QMessageBox.warning(self, "Validasi", "Waktu selesai harus lebih akhir dari waktu mulai!")
            return
        if not self.path_surat or not os.path.exists(self.path_surat):
            QMessageBox.warning(self, "Validasi", "Pilih file surat pengajuan terlebih dahulu!")
            return

        if not self.cek_ketersediaan_jadwal():
            QMessageBox.warning(self, "Jadwal Bentrok", "Ruangan sudah dipakai pada jam tersebut!")
            return

        try:
            nama_file = os.path.basename(self.path_surat)
            with open(self.path_surat, "rb") as f:
                blob_surat = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Error File", f"Gagal membaca file surat:\n{e}")
            return

        sukses = self.model.insert_pengajuan_oki(
            id_oki=self.user["id_pengguna"],
            id_ruang=id_ruang,
            nama_kegiatan=nama_kegiatan,
            tanggal_mulai=dt_mulai,
            tanggal_selesai=dt_selesai,
            keperluan=keperluan,
            nama_file=nama_file,
            blob_surat=blob_surat,
        )
        if sukses:
            QMessageBox.information(self, "Berhasil", "Pengajuan peminjaman ruang berhasil dikirim!")
            self.reset_form()
        else:
            QMessageBox.critical(self, "Gagal", "Gagal menyimpan pengajuan ke database.")

    def reset_form(self):
        if self.inp_kegiatan:
            self.inp_kegiatan.clear()
        if isinstance(self.inp_keperluan, (QTextEdit, QPlainTextEdit, QLineEdit)):
            self.inp_keperluan.clear()
        self.path_surat = ""
        if self.lbl_file:
            self.lbl_file.setText("Belum ada file dipilih")

    def buka_dashboard(self):
        from controller.dashboard_oki import DashboardOKIController
        self.win = DashboardOKIController(self.user)
        self.win.show()
        self.close()

    def buka_daftar_ruang(self):
        from controller.oki_lihat_ruang import OkiLihatRuangController
        self.win = OkiLihatRuangController(self.user)
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