from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.tambah_ruang_BMN import Ui_Dialog
from model.User import User

class DialogTambahRuangController(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.model = User()

        self.setup_form()
        self.connect_signals()

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
            hasil = self.model.tambah_ruang(
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
                    "Data ruang berhasil ditambahkan."
                )
                self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Gagal Menyimpan",
                f"Data ruang gagal disimpan.\n{e}"
            )