from datetime import datetime
from html import escape

from PyQt5.QtWidgets import (
    QMainWindow, QMessageBox, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter

from ui.riwayat_peminjaman_BMN import Ui_MainWindow
from model.User import User

class RiwayatPeminjamanController(QMainWindow):

    def __init__(self, user=None):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.user = user or {}
        self.model = User()

        self.setup_filter()
        self.setup_table()
        self.connect_signals()
        self.load_data()

    def setup_filter(self):
        bulan = [
            "Semua",
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "November",
            "Desember"
        ]

        self.ui.comboBox.clear()
        self.ui.comboBox.addItems(bulan)

        self.ui.spinBox.setRange(2000, 2100)
        self.ui.spinBox.setValue(datetime.now().year)

        self.ui.comboBox_2.clear()
        self.ui.comboBox_2.addItem("Semua")

        rows = self.model.daftar_ruang()

        for row in rows:
            self.ui.comboBox_2.addItem(str(row[1]))

    def setup_table(self):
        self.ui.tableWidget.setColumnCount(7)

        self.ui.tableWidget.setHorizontalHeaderLabels([
            "ID",
            "Organisasi",
            "Kegiatan",
            "Kode Ruang",
            "Nama Ruang",
            "Waktu Pinjam",
            "Status"
        ])

        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.ui.tableWidget.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.ui.tableWidget.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.ui.tableWidget.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

    def connect_signals(self):
        self.ui.pushButton.clicked.connect(self.menu_dashboard)
        self.ui.pushButton_2.clicked.connect(self.menu_kelola_ruang)
        self.ui.pushButton_3.clicked.connect(self.menu_verifikasi)
        self.ui.pushButton_4.clicked.connect(self.load_data)
        self.ui.pushButton_5.clicked.connect(self.menu_logout)

        self.ui.pushButton_6.clicked.connect(self.load_data)
        self.ui.pushButton_7.clicked.connect(self.aksi_cetak_pdf)

    def ambil_filter(self):
        bulan = self.ui.comboBox.currentIndex()

        tahun = self.ui.spinBox.value()

        ruang = self.ui.comboBox_2.currentText()

        return bulan, tahun, ruang

    def ambil_data(self):
        bulan, tahun, ruang = self.ambil_filter()

        return self.model.riwayat(
            bulan,
            tahun,
            ruang
        )

    def load_data(self):
        try:
            rows = self.ambil_data()

            self.ui.tableWidget.setRowCount(len(rows))

            for i, row in enumerate(rows):

                waktu = (
                    f"{row[5].strftime('%d-%m-%Y %H:%M')} "
                    f"s/d {row[6].strftime('%d-%m-%Y %H:%M')}"
                )

                values = [
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    waktu,
                    row[7]
                ]

                for j, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setData(Qt.UserRole, row[0])
                    self.ui.tableWidget.setItem(i, j, item)

            self.ui.tableWidget.resizeRowsToContents()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Gagal Memuat Riwayat",
                str(e)
            )

    def aksi_cetak_pdf(self):
        try:
            rows = self.ambil_data()

            if not rows:
                QMessageBox.warning(
                    self,
                    "Data Kosong",
                    "Tidak ada riwayat peminjaman untuk dicetak."
                )
                return

            path, _ = QFileDialog.getSaveFileName(
                self,
                "Simpan Riwayat Peminjaman",
                f"Riwayat_Peminjaman_BMN_{datetime.now():%Y%m%d}.pdf",
                "PDF Files (*.pdf)"
            )

            if not path:
                return

            if not path.lower().endswith(".pdf"):
                path += ".pdf"

            body = ""

            for no, row in enumerate(rows, start=1):

                waktu = (
                    f"{row[5].strftime('%d-%m-%Y %H:%M')} "
                    f"s/d {row[6].strftime('%d-%m-%Y %H:%M')}"
                )

                body += f"""
                <tr>
                    <td>{no}</td>
                    <td>{escape(str(row[1]))}</td>
                    <td>{escape(str(row[2]))}</td>
                    <td>{escape(str(row[3]))} - {escape(str(row[4]))}</td>
                    <td>{escape(waktu)}</td>
                    <td>{escape(str(row[7]))}</td>
                </tr>
                """

            html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial;
                        font-size: 10pt;
                    }}

                    h2, h3 {{
                        text-align: center;
                    }}

                    table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}

                    th, td {{
                        border: 1px solid black;
                        padding: 6px;
                        text-align: center;
                    }}

                    th {{
                        background-color: #D9EAF2;
                    }}
                </style>
            </head>

            <body>
                <h2>POLITEKNIK NEGERI MALANG</h2>
                <h3>PSDKU KEDIRI</h3>
                <h3>RIWAYAT PEMINJAMAN RUANG</h3>

                <p>
                    Tanggal Cetak:
                    {datetime.now().strftime('%d-%m-%Y %H:%M')}
                </p>

                <table>
                    <tr>
                        <th>No</th>
                        <th>Organisasi</th>
                        <th>Kegiatan</th>
                        <th>Ruang</th>
                        <th>Waktu Pinjam</th>
                        <th>Status</th>
                    </tr>

                    {body}
                </table>
            </body>
            </html>
            """

            printer = QPrinter(QPrinter.HighResolution)

            printer.setOutputFormat(
                QPrinter.PdfFormat
            )

            printer.setOutputFileName(path)

            document = QTextDocument()
            document.setHtml(html)
            document.print_(printer)

            QMessageBox.information(
                self,
                "Berhasil",
                f"PDF berhasil disimpan:\n{path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Gagal Mencetak PDF",
                str(e)
            )

    def menu_dashboard(self):
        from controller.dashboard_bmn import DashboardBMNController

        self.win = DashboardBMNController(self.user)
        self.win.show()
        self.close()

    def menu_kelola_ruang(self):
        from controller.bmn_kelola_ruang import KelolaDataRuangController

        self.win = KelolaDataRuangController(self.user)
        self.win.show()
        self.close()

    def menu_verifikasi(self):
        from controller.bmn_kelola_pengajuan import VerifikasiAjuanController

        self.win = VerifikasiAjuanController(self.user)
        self.win.show()
        self.close()

    def menu_logout(self):
        reply = QMessageBox.question(
            self,
            "Konfirmasi Logout",
            "Yakin ingin keluar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            from controller.login import LoginController

            self.login_win = LoginController()
            self.login_win.show()
            self.close()