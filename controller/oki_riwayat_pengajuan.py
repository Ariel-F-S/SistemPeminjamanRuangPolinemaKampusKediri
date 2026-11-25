import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QComboBox, QPushButton, QLabel, QFileDialog
)
from PyQt5.QtGui import QTextDocument, QDesktopServices
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtCore import Qt, QUrl
from model.connectiondb import get_db_connection

try:
    import ui.riwayat_saya as ui_form
except ImportError:
    import ui.riwayat_saya as ui_form

_ui_name = [n for n in dir(ui_form) if n.startswith("Ui_")][0]
_UiClass = getattr(ui_form, _ui_name)
_BaseClass = QMainWindow if _ui_name == "Ui_MainWindow" else QWidget


class OkiRiwayatPengajuanController(_BaseClass):
    def __init__(self, user_data):
        super().__init__()
        self.ui = _UiClass()
        self.ui.setupUi(self)
        self.user = user_data

        nama_oki = self.user.get("nama_organisasi") or self.user.get("nama", "OKI")
        lbl_oki = getattr(self.ui, "lblOki", None)
        if isinstance(lbl_oki, QLabel):
            lbl_oki.setText(f"OKI: {nama_oki}")

        # Deteksi otomatis ComboBox Status
        daftar_cmb = self.findChildren(QComboBox)
        self.cmb_status = daftar_cmb[0] if daftar_cmb else None
        if self.cmb_status:
            self.cmb_status.clear()
            self.cmb_status.addItems(["Semua", "Menunggu", "Disetujui", "Ditolak", "Selesai"])
            self.cmb_status.currentTextChanged.connect(self.load_data)

        # Deteksi otomatis tombol Cetak Bukti Peminjaman berdasarkan teks tombolnya
        for btn in self.findChildren(QPushButton):
            if "cetak" in btn.text().lower():
                btn.clicked.connect(self.cetak_bukti_peminjaman)
                break

        # Konfigurasi Tabel Riwayat Pengajuan
        daftar_tbl = self.findChildren(QTableWidget)
        self.tabel = daftar_tbl[0] if daftar_tbl else None
        if self.tabel:
            self.tabel.setColumnCount(6)
            self.tabel.setHorizontalHeaderLabels([
                "ID", "Nama Kegiatan", "Ruang", "Waktu Pinjam", "Status", "Catatan BMN"
            ])
            header = self.tabel.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.Stretch)
            self.tabel.verticalHeader().setVisible(False)
            self.tabel.setWordWrap(True)
            self.tabel.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tabel.setSelectionMode(QAbstractItemView.SingleSelection)
            self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.tabel.doubleClicked.connect(self.buka_detail_pengajuan)

        # Navigasi Sidebar OKI
        for nama, fungsi in [
            ("btnDashboard", self.buka_dashboard),
            ("btnDaftarRuang", self.buka_daftar_ruang),
            ("btnAjukanPinjam", self.buka_ajukan_pinjam),
            ("btnRiwayat", self.load_data),
            ("btnJadwal", self.buka_jadwal),
            ("btnLogout", self.logout),
        ]:
            btn = getattr(self.ui, nama, None)
            if isinstance(btn, QPushButton):
                btn.clicked.connect(fungsi)

        self.load_data()

    def load_data(self):
        id_oki = self.user["id_pengguna"]
        status_filter = self.cmb_status.currentText() if self.cmb_status else "Semua"

        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT p.id_pengajuan, p.nama_kegiatan, r.kode_ruang, r.nama_ruang,
                   p.tanggal_mulai, p.tanggal_selesai, p.status_pengajuan, p.catatan_verifikasi
            FROM pengajuan_peminjaman p
            JOIN ruang r ON p.id_ruang = r.id_ruang
            WHERE p.id_oki = %s
        """
        params = [id_oki]
        if status_filter and status_filter != "Semua":
            sql += " AND p.status_pengajuan = %s"
            params.append(status_filter)
        sql += " ORDER BY p.id_pengajuan DESC"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall() or []
        conn.close()

        if not self.tabel:
            return
        self.tabel.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            waktu = f"{row[4].strftime('%d-%m-%Y %H:%M')} s/d {row[5].strftime('%H:%M')}"
            items = [
                str(row[0]), row[1], f"{row[2]} - {row[3]}",
                waktu, row[6], row[7] or "-"
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, row[0])
                if col in (0, 3, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tabel.setItem(idx, col, item)
        self.tabel.resizeRowsToContents()

    def buka_detail_pengajuan(self):
        if not self.tabel:
            return
        row_idx = self.tabel.currentRow()
        if row_idx < 0:
            return
        id_pengajuan = self.tabel.item(row_idx, 0).data(Qt.UserRole)
        from controller.dialog_detail_pengajuan import DialogDetailPengajuanController
        dialog = DialogDetailPengajuanController(id_pengajuan, parent=self)
        dialog.exec_()

    def cetak_bukti_peminjaman(self):
        if not self.tabel:
            return
        row_idx = self.tabel.currentRow()
        if row_idx < 0:
            QMessageBox.warning(self, "Pilih Data", "Silakan klik/pilih baris peminjaman di tabel terlebih dahulu!")
            return

        id_pengajuan = self.tabel.item(row_idx, 0).data(Qt.UserRole)
        status_pengajuan = self.tabel.item(row_idx, 4).text()

        if status_pengajuan not in ("Disetujui", "Selesai"):
            QMessageBox.warning(
                self, "Belum Disetujui",
                f"Bukti peminjaman hanya dapat dicetak untuk pengajuan yang berstatus 'Disetujui' atau 'Selesai' (status saat ini: {status_pengajuan})."
            )
            return

        # Ambil detail lengkap peminjaman dari database
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT p.id_pengajuan, COALESCE(u.nama_organisasi, u.nama), p.nama_kegiatan,
                   r.kode_ruang, r.nama_ruang, r.lokasi_gedung, p.tanggal_mulai,
                   p.tanggal_selesai, p.tanggal_pengajuan, p.status_pengajuan,
                   COALESCE(p.catatan_verifikasi, '-'), COALESCE(b.nama, 'Admin / BMN')
            FROM pengajuan_peminjaman p
            JOIN ruang r ON p.id_ruang = r.id_ruang
            JOIN pengguna u ON p.id_oki = u.id_pengguna
            LEFT JOIN pengguna b ON p.id_bmn = b.id_pengguna
            WHERE p.id_pengajuan = %s
        """
        cursor.execute(sql, (id_pengajuan,))
        data = cursor.fetchone()
        conn.close()

        if not data:
            QMessageBox.critical(self, "Error", "Data pengajuan tidak ditemukan.")
            return

        default_nama = f"Bukti_Peminjaman_Ruang_{data[0]}_{data[3]}.pdf"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Simpan Bukti Peminjaman PDF", default_nama, "PDF Files (*.pdf)"
        )
        if not save_path:
            return

        html_bukti = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 30px; color: #222;">
            <div style="text-align: center; border-bottom: 2px solid #3368A0; padding-bottom: 10px;">
                <h2 style="margin: 0; color: #3368A0;">POLITEKNIK NEGERI MALANG</h2>
                <h3 style="margin: 4px 0; color: #3368A0;">PSDKU KEDIRI</h3>
                <p style="margin: 2px 0; font-size: 12px;">Sistem Informasi Peminjaman Ruang Kampus</p>
            </div>
            <h3 style="text-align: center; margin-top: 20px; text-decoration: underline;">
                BUKTI PERSETUJUAN PEMINJAMAN RUANG
            </h3>
            <p style="text-align: center; font-size: 12px; color: #555;">Nomor Registrasi: #PINJAM-{data[0]:04d}</p>

            <table style="width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px;">
                <tr>
                    <td style="padding: 8px; width: 35%; font-weight: bold;">Organisasi / Peminjam</td>
                    <td style="padding: 8px;">: {data[1]}</td>
                </tr>
                <tr style="background-color: #F4F7FA;">
                    <td style="padding: 8px; font-weight: bold;">Nama Kegiatan</td>
                    <td style="padding: 8px;">: {data[2]}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Ruangan</td>
                    <td style="padding: 8px;">: {data[3]} - {data[4]} ({data[5]})</td>
                </tr>
                <tr style="background-color: #F4F7FA;">
                    <td style="padding: 8px; font-weight: bold;">Tanggal Penggunaan</td>
                    <td style="padding: 8px;">: {data[6].strftime('%d-%m-%Y')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Waktu Penggunaan</td>
                    <td style="padding: 8px;">: {data[6].strftime('%H:%M')} - {data[7].strftime('%H:%M')} WIB</td>
                </tr>
                <tr style="background-color: #F4F7FA;">
                    <td style="padding: 8px; font-weight: bold;">Tanggal Pengajuan</td>
                    <td style="padding: 8px;">: {data[8].strftime('%d-%m-%Y %H:%M')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Status Verifikasi</td>
                    <td style="padding: 8px; color: #1E8449; font-weight: bold;">: {data[9].upper()}</td>
                </tr>
                <tr style="background-color: #F4F7FA;">
                    <td style="padding: 8px; font-weight: bold;">Catatan BMN</td>
                    <td style="padding: 8px;">: {data[10]}</td>
                </tr>
            </table>

            <div style="margin-top: 40px; width: 100%;">
                <table style="width: 100%; font-size: 13px;">
                    <tr>
                        <td style="width: 55%;"></td>
                        <td style="text-align: center;">
                            Kediri, {data[6].strftime('%d-%m-%Y')}<br>
                            Mengetahui / Verifikator BMN,<br><br><br><br>
                            <b><u>{data[11]}</u></b>
                        </td>
                    </tr>
                </table>
            </div>
            <p style="margin-top: 30px; font-size: 11px; color: #666; border-top: 1px dashed #ccc; padding-top: 8px;">
                * Dokumen ini dicetak secara otomatis melalui Sistem Peminjaman Ruang POLINEMA PSDKU Kediri dan sah digunakan sebagai bukti izin pemakaian ruang.
            </p>
        </body>
        </html>
        """

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(save_path)

        doc = QTextDocument()
        doc.setHtml(html_bukti)
        doc.print_(printer)

        QMessageBox.information(self, "Berhasil", f"Bukti peminjaman berhasil dicetak ke:\n{save_path}")
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(save_path)))

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

    def buka_ajukan_pinjam(self):
        from controller.oki_ajukan_peminjaman import OkiAjukanPeminjamanController
        self.win = OkiAjukanPeminjamanController(self.user)
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