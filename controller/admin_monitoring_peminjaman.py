from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFileDialog, QLabel
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtCore import Qt
from ui.data_peminjaman_admin import Ui_MainWindow
from model.User import User
from model.connectiondb import get_db_connection


class AdminMonitoringPeminjamanController(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.user = user_data
        self.model = User()

        self.setWindowTitle("POLINEMA PSDKU KEDIRI - Data Peminjaman")

        if hasattr(self.ui, "label_11"):
            self.ui.label_11.setText("Data Peminjaman Ruang (Disetujui & Selesai)")

        # Rapikan judul 3 kartu teratas yang sebelumnya duplikat 'Akun OKI :'
        lbl_judul = sorted(
            [lbl for lbl in self.findChildren(QLabel) if "akun oki" in lbl.text().lower()],
            key=lambda w: w.mapToGlobal(w.rect().topLeft()).x()
        )
        if len(lbl_judul) >= 3:
            lbl_judul[0].setText("Akun OKI :")
            lbl_judul[1].setText("Total Ruang :")
            lbl_judul[2].setText("Menunggu :")

        # Simpan referensi 4 QLabel angka ('TextLabel') berurutan dari atas ke bawah, kiri ke kanan
        self.label_angka = sorted(
            [lbl for lbl in self.findChildren(QLabel) if lbl.text().strip().lower() == "textlabel"],
            key=lambda w: (
                round(w.mapToGlobal(w.rect().topLeft()).y() / 15),
                w.mapToGlobal(w.rect().topLeft()).x()
            )
        )

        # Setup tabel (otomatis mendukung tableWidget maupun tableView)
        if hasattr(self.ui, "tableWidget"):
            self.ui.tableWidget.setColumnCount(6)
            self.ui.tableWidget.setHorizontalHeaderLabels([
                "ID", "OKI", "Kegiatan", "Ruang", "Waktu Pinjam", "Status"
            ])
            self._atur_proporsi_kolom(self.ui.tableWidget.horizontalHeader())
            self.ui.tableWidget.verticalHeader().setVisible(False)
            self.ui.tableWidget.setWordWrap(True)
            self.ui.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.ui.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
            self.ui.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.ui.tableWidget.doubleClicked.connect(self.buka_detail_pengajuan)
        elif hasattr(self.ui, "tableView"):
            self.table_model = QStandardItemModel()
            self.ui.tableView.setModel(self.table_model)
            self.ui.tableView.verticalHeader().setVisible(False)
            self.ui.tableView.setWordWrap(True)
            self.ui.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.ui.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
            self.ui.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.ui.tableView.doubleClicked.connect(self.buka_detail_pengajuan)

        # Hubungkan tombol Cetak Riwayat Peminjaman di bawah tabel (pushButton_7)
        if hasattr(self.ui, "pushButton_7"):
            self.ui.pushButton_7.clicked.connect(self.cetak_riwayat_pdf)

        # Navigasi Sidebar Admin
        self.ui.pushButton.clicked.connect(self.buka_dashboard)
        self.ui.pushButton_2.clicked.connect(self.buka_kelola_akun)
        self.ui.pushButton_3.clicked.connect(self.buka_monitoring_ruang)
        self.ui.pushButton_4.clicked.connect(self.buka_monitoring_pengajuan)
        self.ui.pushButton_5.clicked.connect(self.load_data)
        self.ui.pushButton_6.clicked.connect(self.logout)

        self.load_data()

    def _atur_proporsi_kolom(self, header):
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Organisasi (OKI)
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Nama Kegiatan
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Ruang
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Waktu Pinjam
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Status

    def _update_statistik_kartu(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM pengguna WHERE role = 'oki'")
        jml_oki = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM ruang")
        jml_ruang = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM pengajuan_peminjaman WHERE status_pengajuan = 'Menunggu'")
        jml_menunggu = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM pengajuan_peminjaman WHERE status_pengajuan IN ('Disetujui', 'Selesai')"
        )
        jml_disetujui = cursor.fetchone()[0]
        conn.close()

        if len(self.label_angka) >= 4:
            self.label_angka[0].setText(str(jml_oki))
            self.label_angka[1].setText(str(jml_ruang))
            self.label_angka[2].setText(str(jml_menunggu))
            self.label_angka[3].setText(str(jml_disetujui))

    def _ambil_data_peminjaman(self):
        data = (self.model.select_pengajuan_admin("Disetujui") or []) + (
            self.model.select_pengajuan_admin("Selesai") or []
        )
        return sorted(data, key=lambda r: r[0])

    def load_data(self):
        self._update_statistik_kartu()
        rows = self._ambil_data_peminjaman()
        headers = ["ID", "Organisasi (OKI)", "Nama Kegiatan", "Ruang", "Waktu Pinjam", "Status"]

        if hasattr(self.ui, "tableWidget"):
            self.ui.tableWidget.setRowCount(len(rows))
            for idx, row in enumerate(rows):
                waktu = f"{row[5].strftime('%d-%m-%Y %H:%M')} s/d {row[6].strftime('%H:%M')}"
                items = [str(row[0]), row[1], row[2], f"{row[3]} - {row[4]}", waktu, row[7]]
                for col, val in enumerate(items):
                    item = QTableWidgetItem(val)
                    item.setData(Qt.UserRole, row[0])
                    if col in (0, 4, 5):
                        item.setTextAlignment(Qt.AlignCenter)
                    self.ui.tableWidget.setItem(idx, col, item)
            self.ui.tableWidget.resizeRowsToContents()

        elif hasattr(self.ui, "tableView"):
            self.table_model.clear()
            self.table_model.setHorizontalHeaderLabels(headers)
            self._atur_proporsi_kolom(self.ui.tableView.horizontalHeader())

            for row in rows:
                waktu = f"{row[5].strftime('%d-%m-%Y %H:%M')} s/d {row[6].strftime('%H:%M')}"

                item_id = QStandardItem(str(row[0]))
                item_id.setData(row[0], Qt.UserRole)
                item_id.setTextAlignment(Qt.AlignCenter)

                item_waktu = QStandardItem(waktu)
                item_waktu.setTextAlignment(Qt.AlignCenter)

                item_status = QStandardItem(row[7])
                item_status.setTextAlignment(Qt.AlignCenter)

                self.table_model.appendRow([
                    item_id,
                    QStandardItem(row[1]),
                    QStandardItem(row[2]),
                    QStandardItem(f"{row[3]} - {row[4]}"),
                    item_waktu,
                    item_status,
                ])
            self.ui.tableView.resizeRowsToContents()

    def cetak_riwayat_pdf(self):
        rows = self._ambil_data_peminjaman()
        if not rows:
            QMessageBox.warning(self, "Data Kosong", "Belum ada data peminjaman untuk dicetak.")
            return

        default_name = f"Riwayat_Peminjaman_Ruang_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Simpan Laporan Riwayat Peminjaman", default_name, "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        baris_html = ""
        for no, row in enumerate(rows, start=1):
            waktu = f"{row[5].strftime('%d-%m-%Y %H:%M')} s/d {row[6].strftime('%H:%M')}"
            baris_html += f"""
            <tr>
                <td align="center">{no}</td>
                <td>{row[1]}</td>
                <td>{row[2]}</td>
                <td>{row[3]} - {row[4]}</td>
                <td>{waktu}</td>
                <td align="center">{row[7]}</td>
            </tr>
            """

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; font-size: 10pt; }}
                h2, h3 {{ text-align: center; margin: 2px 0; }}
                p.meta {{ text-align: center; font-size: 9pt; color: #555; margin-bottom: 14px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th {{ background-color: #3368A0; color: white; padding: 6px; border: 1px solid #333; }}
                td {{ padding: 6px; border: 1px solid #333; }}
            </style>
        </head>
        <body>
            <h2>POLITEKNIK NEGERI MALANG - PSDKU KEDIRI</h2>
            <h3>LAPORAN RIWAYAT PEMINJAMAN RUANG KAMPUS</h3>
            <p class="meta">Dicetak oleh: {self.user['nama']} (Admin) | Tanggal Cetak: {datetime.now().strftime('%d-%m-%Y %H:%M')}</p>
            <table>
                <thead>
                    <tr>
                        <th width="5%">No</th>
                        <th width="20%">Organisasi (OKI)</th>
                        <th width="25%">Nama Kegiatan</th>
                        <th width="20%">Ruang</th>
                        <th width="20%">Waktu Pinjam</th>
                        <th width="10%">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {baris_html}
                </tbody>
            </table>
        </body>
        </html>
        """

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)

        doc = QTextDocument()
        doc.setHtml(html)
        doc.print_(printer)

        QMessageBox.information(self, "Berhasil", f"Laporan riwayat peminjaman berhasil disimpan di:\n{file_path}")

    def buka_detail_pengajuan(self):
        id_pengajuan = None
        if hasattr(self.ui, "tableWidget"):
            row_idx = self.ui.tableWidget.currentRow()
            if row_idx < 0:
                return
            id_pengajuan = self.ui.tableWidget.item(row_idx, 0).data(Qt.UserRole)
        elif hasattr(self.ui, "tableView"):
            indexes = self.ui.tableView.selectionModel().selectedRows()
            if not indexes:
                return
            id_pengajuan = self.table_model.item(indexes[0].row(), 0).data(Qt.UserRole)

        if id_pengajuan:
            from controller.dialog_detail_pengajuan import DialogDetailPengajuanController
            dialog = DialogDetailPengajuanController(id_pengajuan, parent=self)
            dialog.exec_()

    def buka_dashboard(self):
        from controller.dashboard_admin import DashboardAdminController
        self.win = DashboardAdminController(self.user)
        self.win.show()
        self.close()

    def buka_kelola_akun(self):
        from controller.admin_kelola_akun import AdminKelolaAkunController
        self.win = AdminKelolaAkunController(self.user)
        self.win.show()
        self.close()

    def buka_monitoring_ruang(self):
        from controller.admin_monitoring_ruang import AdminMonitoringRuangController
        self.win = AdminMonitoringRuangController(self.user)
        self.win.show()
        self.close()

    def buka_monitoring_pengajuan(self):
        from controller.admin_monitoring_pengajuan import AdminMonitoringPengajuanController
        self.win = AdminMonitoringPengajuanController(self.user)
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