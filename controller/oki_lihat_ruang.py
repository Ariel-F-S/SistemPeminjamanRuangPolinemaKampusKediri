from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLineEdit, QComboBox, QPushButton, QLabel
)
from PyQt5.QtCore import Qt
import ui.daftar_ruang as ui_form
from model.User import User

_ui_name = [n for n in dir(ui_form) if n.startswith("Ui_")][0]
_UiClass = getattr(ui_form, _ui_name)
_BaseClass = QMainWindow if _ui_name == "Ui_MainWindow" else QWidget


def _cari(ui, kandidat, tipe):
    for nama in kandidat:
        w = getattr(ui, nama, None)
        if isinstance(w, tipe):
            return w
    return None


class OkiLihatRuangController(_BaseClass):
    def __init__(self, user_data):
        super().__init__()
        self.ui = _UiClass()
        self.ui.setupUi(self)
        self.user = user_data
        self.model = User()

        nama_oki = self.user.get("nama_organisasi") or self.user.get("nama", "OKI")
        lbl_oki = _cari(self.ui, ["lblOki", "label_oki"], QLabel)
        if lbl_oki:
            lbl_oki.setText(f"OKI: {nama_oki}")

        self.inp_cari = _cari(self.ui, ["txtCari", "txtSearch", "lineEdit"], QLineEdit)
        if self.inp_cari:
            self.inp_cari.setPlaceholderText("Cari kode / nama ruang / fasilitas...")
            self.inp_cari.returnPressed.connect(self.load_data)

        self.cmb_gedung = _cari(self.ui, ["cmbGedung", "cmbFilter", "comboBox"], QComboBox)
        if self.cmb_gedung:
            self.cmb_gedung.clear()
            self.cmb_gedung.addItems(["Semua", "Gedung A", "Gedung B"])
            self.cmb_gedung.currentTextChanged.connect(self.load_data)

        btn_cari = _cari(self.ui, ["btnCari", "btnFilter", "pushButton_7"], QPushButton)
        if btn_cari:
            btn_cari.clicked.connect(self.load_data)

        self.tabel = _cari(self.ui, ["tblRuang", "tableWidget"], QTableWidget)
        if self.tabel:
            self.tabel.setColumnCount(6)
            self.tabel.setHorizontalHeaderLabels([
                "Kode Ruang", "Nama Ruang", "Gedung", "Kapasitas", "Fasilitas", "Status"
            ])
            header = self.tabel.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.Stretch)
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
            self.tabel.verticalHeader().setVisible(False)
            self.tabel.setWordWrap(True)
            self.tabel.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tabel.setSelectionMode(QAbstractItemView.SingleSelection)
            self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Navigasi Sidebar OKI
        for nama, fungsi in [
            ("btnDashboard", self.buka_dashboard),
            ("btnDaftarRuang", self.load_data),
            ("btnAjukanPinjam", self.buka_ajukan_pinjam),
            ("btnRiwayat", self.buka_riwayat),
            ("btnJadwal", self.buka_jadwal),
            ("btnLogout", self.logout),
        ]:
            btn = getattr(self.ui, nama, None)
            if isinstance(btn, QPushButton):
                btn.clicked.connect(fungsi)

        self.load_data()

    def load_data(self):
        keyword = self.inp_cari.text().strip() if self.inp_cari else ""
        gedung = self.cmb_gedung.currentText() if self.cmb_gedung else "Semua"
        rows = self.model.select_data_ruang(keyword=keyword, gedung=gedung) or []

        if not self.tabel:
            return
        self.tabel.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            items = [row[0], row[1], row[2], f"{row[3]} Org", row[4] or "-", row[5]]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                if col in (0, 2, 3, 5):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tabel.setItem(idx, col, item)
        self.tabel.resizeRowsToContents()

    def buka_dashboard(self):
        from controller.dashboard_oki import DashboardOKIController
        self.win = DashboardOKIController(self.user)
        self.win.show()
        self.close()

    def buka_ajukan_pinjam(self):
        from controller.oki_ajukan_peminjaman import OkiAjukanPeminjamanController
        self.win = OkiAjukanPeminjamanController(self.user)
        self.win.show()
        self.close()

    def buka_riwayat(self):
        from controller.oki_riwayat_pengajuan import OkiRiwayatPengajuanController
        self.win = OkiRiwayatPengajuanController(self.user)
        self.win.show()
        self.close()

    def buka_jadwal(self):
        from controller.oki_jadwal_disetujui import OKIJadwalDisetujuiController
        self.win = OKIJadwalDisetujuiController(self.user)
        self.win.show()
        self.close()

    def logout(self):
        reply = QMessageBox.question(
            self, "Konfirmasi Logout", "Apakah Anda yakin ingin keluar dari sistem?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            from controller.login import LoginController
            self.login_win = LoginController()
            self.login_win.show()
            self.close()