from PyQt5.QtWidgets import QDialog, QMessageBox, QLineEdit
from ui.tambah_akun_admin import Ui_Dialog
from model.User import User


class DialogTambahAkunController(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.model = User()

        self.ui.lineEdit_3.setEchoMode(QLineEdit.Password)
        self.ui.radioButton_2.setChecked(True)

        self.ui.pushButton.clicked.connect(self.simpan_akun)
        self.ui.pushButton_2.clicked.connect(self.reject)

    def simpan_akun(self):
        username = self.ui.lineEdit.text().strip()
        nama = self.ui.lineEdit_2.text().strip()
        password = self.ui.lineEdit_3.text().strip()
        no_wa = self.ui.lineEdit_4.text().strip()
        role = "BMN" if self.ui.radioButton.isChecked() else "OKI"

        if not username or not nama or not password or not no_wa:
            QMessageBox.warning(self, "Validasi Gagal", "Semua field wajib diisi!")
            return
        if not no_wa.isdigit() or len(no_wa) < 10:
            QMessageBox.warning(self, "Validasi Gagal", "Nomor WhatsApp harus berupa angka minimal 10 digit!")
            return
        if self.model.cek_username_ada(username):
            QMessageBox.warning(self, "Peringatan", f"Username '{username}' sudah digunakan!")
            return

        if self.model.insert_data(nama, username, password, no_wa, role):
            QMessageBox.information(self, "Sukses", "Akun baru berhasil ditambahkan!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Gagal menyimpan akun ke database.")