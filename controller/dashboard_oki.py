from PyQt5.QtWidgets import QWidget, QMessageBox, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5.QtCore import Qt
from ui.dashboard_oki import Ui_DashboardOKI
from model.connectiondb import get_db_connection


class DashboardOKIController(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.ui = Ui_DashboardOKI()
        self.ui.setupUi(self)
        self.user = user_data

        
        nama_oki = self.user.get("nama_organisasi") or self.user.get("nama", "OKI")
        self.ui.lblOki.setText(f"OKI: {nama_oki}")

        
        self.ui.tableWidget.setColumnCount(5)
        self.ui.tableWidget.setHorizontalHeaderLabels([
            "ID", "Nama Kegiatan", "Ruang", "Waktu Pinjam", "Status"
        ])
        header = self.ui.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)   
        header.setSectionResizeMode(1, QHeaderView.Stretch)           
        header.setSectionResizeMode(2, QHeaderView.Stretch)            
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)   
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  

        self.ui.tableWidget.verticalHeader().setVisible(False)
        self.ui.tableWidget.setWordWrap(True)
        self.ui.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tableWidget.doubleClicked.connect(self.buka_detail_pengajuan)

        
        self.ui.btnDashboard.clicked.connect(self.load_data)
        self.ui.btnDaftarRuang.clicked.connect(self.buka_daftar_ruang)
        self.ui.btnAjukanPinjam.clicked.connect(self.buka_ajukan_pinjam)
        self.ui.btnRiwayat.clicked.connect(self.buka_riwayat)
        self.ui.btnJadwal.clicked.connect(self.buka_jadwal)
        self.ui.btnLogout.clicked.connect(self.logout)

        self.load_data()

    def load_data(self):
        id_oki = self.user["id_pengguna"]
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT status_pengajuan, COUNT(*) FROM pengajuan_peminjaman WHERE id_oki = %s GROUP BY status_pengajuan",
            (id_oki,)
        )
        stat = {"Menunggu": 0, "Disetujui": 0, "Ditolak": 0, "Selesai": 0}
        for r in cursor.fetchall():
            stat[r[0]] = r[1]

        self.ui.lblDiajukan.setText(f"Diajukan: {sum(stat.values())}")
        self.ui.lblDisetujui.setText(f"Disetujui: {stat['Disetujui'] + stat['Selesai']}")
        self.ui.lblDitolak.setText(f"Ditolak: {stat['Ditolak']}")

        sql = """
            SELECT p.id_pengajuan, p.nama_kegiatan, r.kode_ruang, r.nama_ruang,
                   p.tanggal_mulai, p.tanggal_selesai, p.status_pengajuan
            FROM pengajuan_peminjaman p
            JOIN ruang r ON p.id_ruang = r.id_ruang
            WHERE p.id_oki = %s
            ORDER BY p.id_pengajuan ASC
        """
        cursor.execute(sql, (id_oki,))
        rows = cursor.fetchall() or []
        conn.close()

        self.ui.tableWidget.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            waktu = f"{row[4].strftime('%d-%m-%Y %H:%M')} s/d {row[5].strftime('%H:%M')}"
            items = [str(row[0]), row[1], f"{row[2]} - {row[3]}", waktu, row[6]]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, row[0])
                if col in (0, 3, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                self.ui.tableWidget.setItem(idx, col, item)

        self.ui.tableWidget.resizeRowsToContents()

    def buka_detail_pengajuan(self):
        row_idx = self.ui.tableWidget.currentRow()
        if row_idx < 0:
            return
        id_pengajuan = self.ui.tableWidget.item(row_idx, 0).data(Qt.UserRole)
        from controller.dialog_detail_pengajuan import DialogDetailPengajuanController
        dialog = DialogDetailPengajuanController(id_pengajuan, parent=self)
        dialog.exec_()

    def buka_daftar_ruang(self):
        from controller.oki_lihat_ruang import OkiLihatRuangController
        self.win = OkiLihatRuangController(self.user)
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