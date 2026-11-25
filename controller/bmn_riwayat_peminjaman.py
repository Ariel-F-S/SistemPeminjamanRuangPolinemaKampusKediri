import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QComboBox, QSpinBox, QPushButton, QLabel, QFileDialog
)
from PyQt5.QtGui import QTextDocument, QDesktopServices
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtCore import Qt, QUrl, QDate
import ui.riwayat_peminjaman_BMN as _ui_form
from model.connectiondb import get_db_connection

_ui_name = [n for n in dir(_ui_form) if n.startswith("Ui_")][0]
_UiClass = getattr(_ui_form, _ui_name)
_BaseClass = QMainWindow if _ui_name == "Ui_MainWindow" else QWidget

_COMBO_STYLE = """
QComboBox {
    background-color: #FFFFFF;
    color: #1E293B;
    border: 1px solid #66A3BF;
    border-radius: 4px;
    padding: 2px 22px 2px 6px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #66A3BF;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #1E293B;
    selection-background-color: #3368A0;
    selection-color: #FFFFFF;
}
"""


class BmnRiwayatPeminjamanController(_BaseClass):
    def __init__(self, user_data):
        super().__init__()
        self.ui = _UiClass()
        self.ui.setupUi(self)
        self.user = user_data
        self.data_terakhir = []
        self.pakai_filter = False

        nama_bmn = self.user.get("nama", "Petugas BMN")
        for nama_lbl in ("lblBmn", "lblUser", "label_user", "label_bmn"):
            lbl = getattr(self.ui, nama_lbl, None)
            if isinstance(lbl, QLabel):
                lbl.setText(f"BMN: {nama_bmn}")
                break

        # Dropdown Bulan (comboBox) dan Ruang (comboBox_2)
        # Dropdown Bulan (comboBox) dan Ruang (comboBox_2)
        self.cmb_bulan = getattr(self.ui, "comboBox", None)
        self.cmb_ruang = getattr(self.ui, "comboBox_2", None)

        if isinstance(self.cmb_bulan, QComboBox):
            self.cmb_bulan.setStyleSheet("")
            self.cmb_bulan.blockSignals(True)
            self.cmb_bulan.clear()
            daftar_bulan = [
                ("Semua", None),
                ("Januari", 1), ("Februari", 2), ("Maret", 3), ("April", 4),
                ("Mei", 5), ("Juni", 6), ("Juli", 7), ("Agustus", 8),
                ("September", 9), ("Oktober", 10), ("November", 11), ("Desember", 12)
            ]
            for teks, angka in daftar_bulan:
                self.cmb_bulan.addItem(teks, angka)
            self.cmb_bulan.blockSignals(False)

        if isinstance(self.cmb_ruang, QComboBox):
            self.cmb_ruang.setStyleSheet("")
            self._load_filter_ruang()

        daftar_spin = self.findChildren(QSpinBox)
        self.spin_tahun = daftar_spin[0] if daftar_spin else None
        if self.spin_tahun:
            self.spin_tahun.setValue(QDate.currentDate().year())

        # Pengaturan lebar kolom tabel agar proporsional dan tidak terpotong
        daftar_tbl = self.findChildren(QTableWidget)
        self.tabel = daftar_tbl[0] if daftar_tbl else None
        if self.tabel:
            self.tabel.setColumnCount(7)
            self.tabel.setHorizontalHeaderLabels([
                "ID", "Organisasi", "Nama Kegiatan", "Ruang", "Waktu Pinjam", "Status", "Catatan BMN"
            ])
            header = self.tabel.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Interactive)
            header.setStretchLastSection(True)

            self.tabel.setColumnWidth(0, 38)   # ID
            self.tabel.setColumnWidth(1, 115)  # Organisasi
            self.tabel.setColumnWidth(2, 145)  # Nama Kegiatan
            self.tabel.setColumnWidth(3, 130)  # Ruang
            self.tabel.setColumnWidth(4, 110)  # Waktu Pinjam
            self.tabel.setColumnWidth(5, 78)   # Status
            self.tabel.setColumnWidth(6, 135)  # Catatan BMN

            self.tabel.verticalHeader().setVisible(False)
            self.tabel.setWordWrap(True)
            self.tabel.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tabel.setSelectionMode(QAbstractItemView.SingleSelection)
            self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.tabel.doubleClicked.connect(self.buka_detail)

        for btn in self.findChildren(QPushButton):
            teks = btn.text().lower()
            if "dashboard" in teks:
                btn.clicked.connect(self.buka_dashboard)
            elif "kelola ruang" in teks:
                btn.clicked.connect(self.buka_kelola_ruang)
            elif "verifikasi" in teks or "ajuan" in teks or "pengajuan" in teks:
                btn.clicked.connect(self.buka_kelola_pengajuan)
            elif "riwayat pinjam" in teks:
                btn.clicked.connect(self.reset_dan_muat_semua)
            elif "logout" in teks:
                btn.clicked.connect(self.logout)
            elif "tampilkan" in teks or "cari" in teks or "filter" in teks:
                btn.clicked.connect(self.terapkan_filter)
            elif "cetak" in teks or "pdf" in teks:
                btn.clicked.connect(self.cetak_laporan_pdf)

        self.load_data()

    def _load_filter_ruang(self):
        self.cmb_ruang.blockSignals(True)
        self.cmb_ruang.clear()
        self.cmb_ruang.addItem("Semua Ruang", None)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_ruang, kode_ruang, nama_ruang FROM ruang ORDER BY kode_ruang ASC")
        for r in cursor.fetchall() or []:
            self.cmb_ruang.addItem(f"{r[1]} - {r[2]}", r[0])
        conn.close()
        self.cmb_ruang.blockSignals(False)

    def terapkan_filter(self):
        self.pakai_filter = True
        self.load_data()

    def reset_dan_muat_semua(self):
        self.pakai_filter = False
        if isinstance(self.cmb_bulan, QComboBox):
            self.cmb_bulan.setCurrentIndex(0)
        if isinstance(self.cmb_ruang, QComboBox):
            self.cmb_ruang.setCurrentIndex(0)
        self.load_data()

    def load_data(self):
        bulan = self.cmb_bulan.currentData() if isinstance(self.cmb_bulan, QComboBox) else None
        id_ruang = self.cmb_ruang.currentData() if isinstance(self.cmb_ruang, QComboBox) else None
        tahun = self.spin_tahun.value() if (self.spin_tahun and self.pakai_filter) else None

        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT p.id_pengajuan, COALESCE(u.nama_organisasi, u.nama), p.nama_kegiatan,
                   r.kode_ruang, r.nama_ruang, p.tanggal_mulai, p.tanggal_selesai,
                   p.status_pengajuan, COALESCE(p.catatan_verifikasi, '-')
            FROM pengajuan_peminjaman p
            JOIN ruang r ON p.id_ruang = r.id_ruang
            JOIN pengguna u ON p.id_oki = u.id_pengguna
            WHERE 1=1
        """
        params = []
        if bulan:
            sql += " AND MONTH(p.tanggal_mulai) = %s"
            params.append(bulan)
        if tahun:
            sql += " AND YEAR(p.tanggal_mulai) = %s"
            params.append(tahun)
        if id_ruang:
            sql += " AND p.id_ruang = %s"
            params.append(id_ruang)

        sql += " ORDER BY p.id_pengajuan ASC"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall() or []
        conn.close()
        self.data_terakhir = rows

        if not self.tabel:
            return
        self.tabel.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            waktu = f"{row[5].strftime('%d-%m-%Y')}\n{row[5].strftime('%H:%M')} - {row[6].strftime('%H:%M')}"
            items = [
                str(row[0]), row[1], row[2],
                f"{row[3]} - {row[4]}", waktu, row[7], row[8]
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, row[0])
                if col in (0, 4, 5):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tabel.setItem(idx, col, item)

        self.tabel.resizeRowsToContents()
        for r in range(self.tabel.rowCount()):
            if self.tabel.rowHeight(r) < 48:
                self.tabel.setRowHeight(r, 48)

    def buka_detail(self):
        if not self.tabel or self.tabel.currentRow() < 0:
            return
        id_pengajuan = self.tabel.item(self.tabel.currentRow(), 0).data(Qt.UserRole)
        from controller.dialog_detail_pengajuan import DialogDetailPengajuanController
        dialog = DialogDetailPengajuanController(id_pengajuan, parent=self)
        dialog.exec_()

    def cetak_laporan_pdf(self):
        if not self.data_terakhir:
            QMessageBox.warning(self, "Data Kosong", "Tidak ada data riwayat peminjaman untuk dicetak.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Simpan Laporan Riwayat BMN", "Laporan_Peminjaman_Ruang_BMN.pdf", "PDF Files (*.pdf)"
        )
        if not save_path:
            return

        baris_html = ""
        for idx, r in enumerate(self.data_terakhir, start=1):
            waktu = f"{r[5].strftime('%d-%m-%Y %H:%M')} s/d {r[6].strftime('%H:%M')}"
            baris_html += f"""
            <tr>
                <td style="border: 1px solid #999; padding: 6px; text-align: center;">{idx}</td>
                <td style="border: 1px solid #999; padding: 6px;">{r[1]}</td>
                <td style="border: 1px solid #999; padding: 6px;">{r[2]}</td>
                <td style="border: 1px solid #999; padding: 6px;">{r[3]} - {r[4]}</td>
                <td style="border: 1px solid #999; padding: 6px; text-align: center;">{waktu}</td>
                <td style="border: 1px solid #999; padding: 6px; text-align: center;">{r[7]}</td>
                <td style="border: 1px solid #999; padding: 6px;">{r[8]}</td>
            </tr>
            """

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="text-align: center; border-bottom: 2px solid #3368A0; padding-bottom: 8px;">
                <h2 style="margin: 0; color: #3368A0;">POLITEKNIK NEGERI MALANG - PSDKU KEDIRI</h2>
                <h3 style="margin: 4px 0;">LAPORAN RIWAYAT PEMINJAMAN RUANG (BMN)</h3>
            </div>
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 11px;">
                <thead>
                    <tr style="background-color: #3368A0; color: #FFFFFF;">
                        <th style="border: 1px solid #999; padding: 6px;">No</th>
                        <th style="border: 1px solid #999; padding: 6px;">Organisasi</th>
                        <th style="border: 1px solid #999; padding: 6px;">Kegiatan</th>
                        <th style="border: 1px solid #999; padding: 6px;">Ruang</th>
                        <th style="border: 1px solid #999; padding: 6px;">Waktu</th>
                        <th style="border: 1px solid #999; padding: 6px;">Status</th>
                        <th style="border: 1px solid #999; padding: 6px;">Catatan BMN</th>
                    </tr>
                </thead>
                <tbody>{baris_html}</tbody>
            </table>
        </body>
        </html>
        """

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(save_path)
        doc = QTextDocument()
        doc.setHtml(html)
        doc.print_(printer)

        QMessageBox.information(self, "Berhasil", f"Laporan berhasil dicetak ke:\n{save_path}")
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(save_path)))

    def buka_dashboard(self):
        from controller.dashboard_bmn import DashboardBMNController
        self.win = DashboardBMNController(self.user)
        self.win.show()
        self.close()

    def buka_kelola_ruang(self):
        from controller.bmn_kelola_ruang import BmnKelolaRuangController
        self.win = BmnKelolaRuangController(self.user)
        self.win.show()
        self.close()

    def buka_kelola_pengajuan(self):
        from controller.bmn_kelola_pengajuan import BmnKelolaPengajuanController
        self.win = BmnKelolaPengajuanController(self.user)
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


RiwayatPeminjamanBMNController = BmnRiwayatPeminjamanController