import os

from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

from ui.detail_peminjaman import Ui_Dialog
from model.User import User


class DialogDetailPengajuanController(QDialog):

    def __init__(self, id_pengajuan, parent=None):
        super().__init__(parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.id_pengajuan = id_pengajuan
        self.model = User()
        self.file_surat = ""

        self.setup_tampilan()
        self.connect_signals()
        self.load_detail()

    def setup_tampilan(self):
        self.ui.label_11.setMinimumWidth(210)
        self.ui.label_12.setMinimumWidth(210)
        self.ui.label_13.setMinimumWidth(210)
        self.ui.label_14.setMinimumWidth(210)

        self.ui.label_23.setMinimumWidth(210)
        self.ui.label_24.setMinimumWidth(210)
        self.ui.label_17.setMinimumWidth(210)

        self.ui.label_28.setMinimumWidth(200)
        self.ui.label_26.setWordWrap(True)

    def connect_signals(self):
        self.ui.pushButton.clicked.connect(
            self.buka_surat
        )

    def load_detail(self):
        try:
            data = self.model.select_detail_pengajuan(
                self.id_pengajuan
            )

            if not data:
                QMessageBox.warning(
                    self,
                    "Data Tidak Ditemukan",
                    "Detail peminjaman tidak ditemukan."
                )
                self.reject()
                return

            # Informasi peminjaman
            self.ui.label_11.setText(str(data[0]))
            self.ui.label_12.setText(str(data[1]))

            self.ui.label_13.setText(
                data[2].strftime("%d-%m-%Y %H:%M")
                if data[2] else "-"
            )

            self.ui.label_14.setText(str(data[3]))

            # Informasi pengajuan
            self.ui.label_23.setText(
                f"{data[4]} - {data[5]}"
            )

            self.ui.label_24.setText(
                data[6].strftime("%d-%m-%Y")
                if data[6] else "-"
            )

            self.ui.label_17.setText(
                f"{data[6].strftime('%H:%M')} - "
                f"{data[7].strftime('%H:%M')}"
                if data[6] and data[7] else "-"
            )

            # Deskripsi kegiatan
            catatan = data[9] or "-"

            self.ui.label_26.setText(
                f"{data[8] or '-'}\n\n"
                f"Catatan BMN: {catatan}"
            )

            # File surat pengajuan
            self.file_surat = data[10] or ""

            self.ui.label_28.setText(
                os.path.basename(self.file_surat)
                if self.file_surat
                else "Tidak ada file"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Gagal Memuat Detail",
                str(e)
            )
            self.reject()

    def buka_surat(self):
        if not self.file_surat:
            QMessageBox.warning(
                self,
                "Surat Tidak Tersedia",
                "File surat pengajuan belum tersedia."
            )
            return

        if not os.path.isfile(self.file_surat):
            QMessageBox.warning(
                self,
                "File Tidak Ditemukan",
                "File surat tidak ditemukan di folder penyimpanan."
            )
            return

        QDesktopServices.openUrl(
            QUrl.fromLocalFile(
                os.path.abspath(self.file_surat)
            )
        )