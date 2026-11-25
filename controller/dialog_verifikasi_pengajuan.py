import os

from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

from ui.detail_dan_verifikasi_pengajuan import Ui_Dialog
from model.User import User

class DialogVerifikasiPengajuanController(QDialog):

    def __init__(self, id_pengajuan, user=None, parent=None):
        super().__init__(parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.model = User()
        self.id_pengajuan = id_pengajuan
        self.user = user or {}
        self.file_surat = ""

        self.connect_signals()
        self.load_detail()

    def connect_signals(self):
        self.ui.pushButton.clicked.connect(self.buka_surat)
        self.ui.pushButton_2.clicked.connect(self.reject)
        self.ui.pushButton_3.clicked.connect(self.tolak)
        self.ui.pushButton_4.clicked.connect(self.setujui)

    def load_detail(self):
        try:
            row = self.model.detail_pengajuan(
                self.id_pengajuan
            )

            if not row:
                QMessageBox.warning(
                    self,
                    "Data Tidak Ada",
                    "Detail pengajuan tidak ditemukan."
                )
                self.reject()
                return

            # Informasi pengajuan
            self.ui.label_6.setText(str(row[0]))
            self.ui.label_7.setText(str(row[2]))

            self.ui.label_8.setText(
                f"{row[3]} - {row[4]}"
            )

            waktu = (
                f"{row[6].strftime('%d-%m-%Y %H:%M')} "
                f"s/d {row[7].strftime('%d-%m-%Y %H:%M')}"
            )

            self.ui.label_9.setText(waktu)

            # Informasi organisasi
            self.ui.label_13.setText(str(row[1]))

            self.ui.label_14.setText(
                row[5].strftime("%d-%m-%Y %H:%M")
                if row[5] else "-"
            )

            self.ui.label_15.setText(str(row[10]))

            # Informasi surat
            self.file_surat = row[9] or ""

            self.ui.lineEdit.setText(
                os.path.basename(self.file_surat)
                if self.file_surat
                else "Tidak ada file"
            )

            # Catatan verifikasi
            self.ui.textEdit.setPlainText(
                row[11] or ""
            )

            # Kunci tombol jika sudah diproses
            bisa_verifikasi = row[10] == "Menunggu"

            self.ui.pushButton_3.setEnabled(
                bisa_verifikasi
            )

            self.ui.pushButton_4.setEnabled(
                bisa_verifikasi
            )

            self.ui.textEdit.setReadOnly(
                not bisa_verifikasi
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
                "Surat pengajuan belum tersedia."
            )
            return

        if not os.path.isfile(self.file_surat):
            QMessageBox.warning(
                self,
                "File Tidak Ditemukan",
                "File surat tidak ditemukan di lokasi penyimpanan."
            )
            return

        QDesktopServices.openUrl(
            QUrl.fromLocalFile(
                os.path.abspath(self.file_surat)
            )
        )

    def simpan_verifikasi(self, status):
        catatan = self.ui.textEdit.toPlainText().strip()

        if status == "Ditolak" and not catatan:
            QMessageBox.warning(
                self,
                "Catatan Wajib",
                "Alasan penolakan wajib diisi."
            )
            return

        id_bmn = self.user.get("id_pengguna")

        if not id_bmn:
            QMessageBox.warning(
                self,
                "Akun Tidak Valid",
                "ID pengguna BMN tidak ditemukan. Silakan login kembali."
            )
            return

        try:
            hasil = self.model.verifikasi_pengajuan(
                self.id_pengajuan,
                id_bmn,
                status,
                catatan
            )

            if not hasil:
                QMessageBox.warning(
                    self,
                    "Tidak Dapat Diproses",
                    "Pengajuan sudah diverifikasi atau datanya berubah."
                )
                self.reject()
                return

            QMessageBox.information(
                self,
                "Berhasil",
                f"Pengajuan berhasil {status.lower()}."
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Gagal Menyimpan",
                f"Verifikasi gagal disimpan.\n{e}"
            )

    def setujui(self):
        reply = QMessageBox.question(
            self,
            "Konfirmasi Persetujuan",
            "Apakah kamu yakin ingin menyetujui pengajuan ini?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.simpan_verifikasi("Disetujui")

    def tolak(self):
        reply = QMessageBox.question(
            self,
            "Konfirmasi Penolakan",
            "Apakah kamu yakin ingin menolak pengajuan ini?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.simpan_verifikasi("Ditolak")