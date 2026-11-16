from PyQt5 import QtWidgets

import sys
from ui.dashboard_admin import Ui_MainWindow as AdminUI
from model.User import User

class  HalamanAdmin(QtWidgets.QMainWindow, AdminUI):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.user = User()
        self.tableWidget.setColumnCount()