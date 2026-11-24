import sys
import os
from PyQt5.QtWidgets import QApplication
from controller.login import LoginController


def main():
    os.makedirs("uploads", exist_ok=True)
    app = QApplication(sys.argv)
    window = LoginController()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
