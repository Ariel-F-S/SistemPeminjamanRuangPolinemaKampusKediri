from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.ubah_data_ruang_BMN import Ui_Dialog
from model.User import User

class DialogUbahRuangController(QDialog):

    def __init__(self, id_ruang, parent=None):
        super().__init__(parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.model = User()
        self.id_ruang = id_ruang

        self.setup_form()
        self.connect_signals()
        self.ambil_data()

    def setup_form(self):
        self.ui.comboBox.clear()
        self.ui.comboBox.setEditable(True)
        self.ui.comboBox.addItems(
            self.model.daftar_gedung()
        )

        self.ui.comboBox_2.clear()
        self.ui.comboBox_2.addItems([
            "Tersedia",
            "Perbaikan"
        ])

        self.ui.spinBox.setMinimum(1)

    def connect_signals(self):
        self.ui.pushButton.clicked.connect(self.reject)
        self.ui.pushButton_2.clicked.connect(self.simpan)

    def ambil_data(self):
        try:
            row = self.model.detail_ruang(self.id_ruang)

            if not row:
                QMessageBox.warning(
                    self,
                    "Data Tidak Ada",
                    "Data ruang tidak ditemukan."
                )
                self.reject()
                return

            self.ui.lineEdit.setText(str(row[1]))
            self.ui.lineEdit_2.setText(str(row[2]))

            if self.ui.comboBox.findText(str(row[3])) < 0:
                self.ui.comboBox.addItem(str(row[3]))

            self.ui.comboBox.setCurrentText(str(row[3]))
            self.ui.spinBox.setValue(int(row[4]))
            self.ui.textEdit.setPlainText(row[5] or "")
            self.ui.comboBox_2.setCurrentText(str(row[6]))

        except Exception as e:
            QMessageBox.critical(
                self,
                "Gagal Mengambil Data",
                str(e)
            )
            self.reject()

    def simpan(self):
        kode = self.ui.lineEdit.text().strip()
        nama = self.ui.lineEdit_2.text().strip()
        gedung = self.ui.comboBox.currentText().strip()
        kapasitas = self.ui.spinBox.value()
        fasilitas = self.ui.textEdit.toPlainText().strip()
        status = self.ui.comboBox_2.currentText()

        if not kode or not nama or not gedung:
            QMessageBox.warning(
                self,
                "Input Belum Lengkap",
                "Kode ruang, nama ruang, dan gedung wajib diisi."
            )
            return

        try:
            hasil = self.model.ubah_ruang(
                self.id_ruang,
                kode,
                nama,
                gedung,
                kapasitas,
                fasilitas,
                status
            )

            if hasil:
                QMessageBox.information(
                    self,
                    "Berhasil",
                    "Data ruang berhasil diperbarui."
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Gagal",
                    "Tidak ada perubahan data yang tersimpan."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Gagal Memperbarui",
                f"Data ruang gagal diperbarui.\n{e}"
            )