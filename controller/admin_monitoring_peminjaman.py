from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QPushButton, QFileDialog
)
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtCore import Qt
from ui.dashboard_admin import Ui_MainWindow
from model.User import User


class AdminMonitoringPeminjamanController(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.user = user_data
        self.model = User()

        self.ui.label_2.setText("Akun OKI :")
        self.ui.label_5.setText("Akun BMN :")
        self.ui.label_7.setText("Akun Admin :")
        self.ui.label_11.setText("Monitoring Data Peminjaman Ruang (Disetujui)")

        # Tambahkan tombol Cetak Riwayat PDF otomatis tanpa mengubah file .ui
        self.btnCetakRiwayat = QPushButton("Cetak Riwayat PDF", self.ui.centralwidget)
        self.btnCetakRiwayat.setStyleSheet("""
            QPushButton {
                background-color: #3368A0;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #275280;
            }
        """)
        self.btnCetakRiwayat.adjustSize()
        self.btnCetakRiwayat.setFixedHeight(32)
        # Posisikan rapi di pojok kanan atas tabel
        tbl_geo = self.ui.tableWidget.geometry()
        self.btnCetakRiwayat.move(
            tbl_geo.x() + tbl_geo.width() - self.btnCetakRiwayat.width(),
            tbl_geo.y() - 38
        )
        self.btnCetakRiwayat.clicked.connect(self.cetak_riwayat_pdf)

        self.ui.tableWidget.setColumnCount(6)
        self.ui.tableWidget.setHorizontalHeaderLabels([
            "ID", "Organisasi (OKI)", "Nama Kegiatan", "Ruang", "Waktu Pinjam", "Status"
        ])
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tableWidget.doubleClicked.connect(self.buka_detail_pengajuan)

        self.ui.pushButton.clicked.connect(self.buka_dashboard)
        self.ui.pushButton_2.clicked.connect(self.buka_kelola_akun)
        self.ui.pushButton_3.clicked.connect(self.buka_monitoring_ruang)
        self.ui.pushButton_4.clicked.connect(self.buka_monitoring_pengajuan)
        self.ui.pushButton_5.clicked.connect(self.load_data)
        self.ui.pushButton_6.clicked.connect(self.logout)

        self.load_data()

    def load_data(self):
        stat = self.model.get_statistik_dashboard()
        self.ui.label_4.setText(str(stat["OKI"]))
        self.ui.label_6.setText(str(stat["BMN"]))
        self.ui.label_8.setText(str(stat["Admin"]))
        self.ui.label_10.setText(str(stat["Disetujui"]))

        rows = self.model.select_pengajuan_admin("Disetujui")
        self.ui.tableWidget.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            waktu = f"{row[5].strftime('%d-%m-%Y %H:%M')} s/d {row[6].strftime('%H:%M')}"
            items = [str(row[0]), row[1], row[2], f"{row[3]} - {row[4]}", waktu, row[7]]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, row[0])
                self.ui.tableWidget.setItem(idx, col, item)

    def cetak_riwayat_pdf(self):
        rows = self.model.select_pengajuan_admin("Disetujui")
        if not rows:
            QMessageBox.warning(self, "Data Kosong", "Belum ada data peminjaman yang disetujui untuk dicetak.")
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
        row_idx = self.ui.tableWidget.currentRow()
        if row_idx < 0:
            return
        id_pengajuan = self.ui.tableWidget.item(row_idx, 0).data(Qt.UserRole)
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