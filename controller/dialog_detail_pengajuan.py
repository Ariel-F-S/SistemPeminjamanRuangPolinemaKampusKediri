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

        for lbl in [
            self.ui.label_11, self.ui.label_12, self.ui.label_13, self.ui.label_14,
            self.ui.label_23, self.ui.label_24, self.ui.label_17
        ]:
            lbl.setFixedWidth(210)
        self.ui.label_28.setFixedWidth(200)
        self.ui.label_26.setWordWrap(True)

        self.ui.pushButton.clicked.connect(self.buka_surat)
        self.load_detail()

    def load_detail(self):
        data = self.model.select_detail_pengajuan(self.id_pengajuan)
        if not data:
            QMessageBox.critical(self, "Error", "Detail peminjaman tidak ditemukan.")
            self.reject()
            return

        self.ui.label_11.setText(data[0])
        self.ui.label_12.setText(data[1])
        self.ui.label_13.setText(data[2].strftime("%d-%m-%Y %H:%M"))
        self.ui.label_14.setText(data[3])

        self.ui.label_23.setText(f"{data[4]} - {data[5]}")
        self.ui.label_24.setText(data[6].strftime("%d-%m-%Y"))
        self.ui.label_17.setText(f"{data[6].strftime('%H:%M')} - {data[7].strftime('%H:%M')}")

        catatan = data[9] or "-"
        self.ui.label_26.setText(f"{data[8] or data[1]}\n\nCatatan BMN: {catatan}")

        self.file_surat = data[10] or ""
        self.ui.label_28.setText(os.path.basename(self.file_surat) if self.file_surat else "Tidak ada file")

    def buka_surat(self):
        if not self.file_surat or not os.path.exists(self.file_surat):
            QMessageBox.warning(self, "Berkas Tidak Ditemukan", "File surat pengajuan tidak ditemukan di folder lokal.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(self.file_surat)))