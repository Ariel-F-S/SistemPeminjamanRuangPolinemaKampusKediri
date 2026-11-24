from PyQt5.QtWidgets import QDialog, QMessageBox, QLineEdit
from ui.ubah_akun_admin import Ui_Dialog
from model.User import User


class DialogUbahAkunController(QDialog):
    def __init__(self, id_pengguna, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.id_pengguna = id_pengguna
        self.model = User()

        self.ui.lineEdit_3.setEchoMode(QLineEdit.Password)
        self.ui.lineEdit_3.setPlaceholderText("Kosongkan jika password tidak diubah")

        self.ui.pushButton.clicked.connect(self.simpan_perubahan)
        self.ui.pushButton_2.clicked.connect(self.reject)

        self.load_detail()

    def load_detail(self):
        data = self.model.cari_by_id(self.id_pengguna)
        if not data:
            QMessageBox.critical(self, "Error", "Data akun tidak ditemukan.")
            self.reject()
            return

        self.ui.lineEdit.setText(data[1])
        self.ui.lineEdit_2.setText(data[2])
        self.ui.lineEdit_4.setText(data[3] or "")
        if data[4] == "BMN":
            self.ui.radioButton.setChecked(True)
        else:
            self.ui.radioButton_2.setChecked(True)

    def simpan_perubahan(self):
        username = self.ui.lineEdit.text().strip()
        nama = self.ui.lineEdit_2.text().strip()
        password = self.ui.lineEdit_3.text().strip()
        no_wa = self.ui.lineEdit_4.text().strip()
        role = "BMN" if self.ui.radioButton.isChecked() else "OKI"

        if not username or not nama or not no_wa:
            QMessageBox.warning(self, "Validasi Gagal", "Username, Nama, dan No. WhatsApp wajib diisi!")
            return
        if not no_wa.isdigit() or len(no_wa) < 10:
            QMessageBox.warning(self, "Validasi Gagal", "Nomor WhatsApp harus berupa angka minimal 10 digit!")
            return
        if self.model.cek_username_ada(username, exclude_id=self.id_pengguna):
            QMessageBox.warning(self, "Peringatan", f"Username '{username}' sudah digunakan akun lain!")
            return

        if self.model.update_data(self.id_pengguna, nama, username, password, no_wa, role):
            QMessageBox.information(self, "Sukses", "Data akun berhasil diperbarui!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Gagal memperbarui data akun.")