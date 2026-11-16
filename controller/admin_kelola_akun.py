from PyQt5 import QtWidgets

import sys
from ui.kelola_akun_admin import Ui_MainWindow as KelolaAkunUI
from model.User import User
from controller import dialog_tambah_akun as TambahAkunUI
from controller import dialog_ubah_akun as UbahAkunUI

class Admin(QtWidgets.QMainWindow, KelolaAkunUI):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.user = User()
        self.filter_dan_cari()
        self.tampil_tabel()
        self.pushButton.clicked.connect(self.dashboard)
        self.pushButton_2.clicked.connect(self.kelola_akun)
        self.pushButton_3.clicked.connect(self.data_ruang)
        self.pushButton_4.clicked.connect(self.pengajuan)
        self.pushButton_5.clicked.connect(self.detail_pengajuan)
        self.pushButton_6.clicked.connect(self.keluar)
        self.pushButton_7.clicked.connect(self.cari)
        self.pushButton_8.clicked.connect(self.tambah_akun)
        self.pushButton_9.clicked.connect(self.ubah_akun)
        self.pushButton_10.clicked.connect(self.hapus_akun)