from PyQt5.QtWidgets import QMainWindow, QMessageBox, QLineEdit
from ui.login import Ui_MainWindow
from model.User import User


class LoginController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.model = User()

        self.ui.lineEdit.setPlaceholderText("Masukkan username...")
        self.ui.lineEdit_2.setPlaceholderText("Masukkan password...")

        self.ui.checkBox.toggled.connect(self.toggle_password)
        self.ui.pushButton.clicked.connect(self.proses_login)
        self.ui.lineEdit_2.returnPressed.connect(self.proses_login)

    def toggle_password(self, checked):
        self.ui.lineEdit_2.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    def proses_login(self):
        username = self.ui.lineEdit.text().strip()
        password = self.ui.lineEdit_2.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Peringatan", "Username dan password tidak boleh kosong!")
            return

        user = self.model.login(username, password)
        if not user:
            QMessageBox.critical(self, "Login Gagal", "Username atau password salah, atau akun tidak aktif!")
            return

        role = user["role"]
        if role == "Admin":
            from controller.dashboard_admin import DashboardAdminController
            self.next_win = DashboardAdminController(user)
        elif role == "BMN":
            from controller.dashboard_bmn import DashboardBMNController
            self.next_win = DashboardBMNController(user)
        elif role == "OKI":
            from controller.dashboard_oki import DashboardOKIController
            self.next_win = DashboardOKIController(user)
        else:
            QMessageBox.warning(self, "Error", f"Role '{role}' tidak dikenali.")
            return

        self.next_win.show()
        self.close()