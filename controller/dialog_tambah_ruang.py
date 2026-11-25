from PyQt5.QtWidgets import (
    QDialog, QMessageBox, QComboBox, QSpinBox,
    QPushButton, QLineEdit, QTextEdit
)
from model.connectiondb import get_db_connection
from ui.tambah_ruang_BMN import Ui_Dialog
from model.User import User


def _cari(ui, kandidat, tipe):
    for nama in kandidat:
        w = getattr(ui, nama, None)
        if isinstance(w, tipe):
            return w
    return None


class DialogTambahRuangController(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.model = User()

        self._deteksi_widget()
        self.setup_form()
        self.connect_signals()

    def _deteksi_widget(self):
        
        combos = sorted(self.findChildren(QComboBox), key=lambda w: w.y())

        
        self.cmb_gedung = _cari(self.ui, ["comboGedung", "cmbGedung", "comboBox"], QComboBox)
        if not self.cmb_gedung and len(combos) >= 1:
            self.cmb_gedung = combos[0]

        
        self.cmb_status = _cari(self.ui, ["comboStatus", "cmbStatus", "comboBox_2"], QComboBox)
        if not self.cmb_status and len(combos) >= 2:
            self.cmb_status = combos[1]

        
        spins = self.findChildren(QSpinBox)
        self.spin_kapasitas = (
            _cari(self.ui, ["spinKapasitas", "spinBox"], QSpinBox)
            or (spins[0] if spins else None)
        )

       
        line_edits = sorted(self.findChildren(QLineEdit), key=lambda w: w.y())
        self.txt_kode = _cari(self.ui, ["txtKode", "lineEdit"], QLineEdit) or (line_edits[0] if len(line_edits) > 0 else None)
        self.txt_nama = _cari(self.ui, ["txtNama", "lineEdit_2"], QLineEdit) or (line_edits[1] if len(line_edits) > 1 else None)

       
        text_edits = self.findChildren(QTextEdit)
        self.txt_fasilitas = _cari(self.ui, ["txtFasilitas", "textEdit"], QTextEdit) or (text_edits[0] if text_edits else None)

        
        buttons = self.findChildren(QPushButton)
        self.btn_batal = next((b for b in buttons if "batal" in b.text().lower()), None) or _cari(self.ui, ["btnBatal", "pushButton"], QPushButton)
        self.btn_simpan = next((b for b in buttons if "simpan" in b.text().lower()), None) or _cari(self.ui, ["btnSimpan", "pushButton_2"], QPushButton)

    def _load_data_gedung(self):
        if not isinstance(self.cmb_gedung, QComboBox):
            return

        self.cmb_gedung.blockSignals(True)
        self.cmb_gedung.clear()

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_gedung, nama_gedung FROM lokasi_gedung "
                "WHERE nama_gedung IS NOT NULL AND TRIM(nama_gedung) != '' "
                "ORDER BY id_gedung ASC"
            )
            rows = cursor.fetchall() or []

            if rows:
                for row in rows:
                    if isinstance(row, dict):
                        id_gedung = row.get("id_gedung")
                        nama_gedung = row.get("nama_gedung")
                    else:
                        id_gedung = row[0]
                        nama_gedung = row[1]

                    if nama_gedung:
                        
                        self.cmb_gedung.addItem(str(nama_gedung).strip(), id_gedung)

                self.cmb_gedung.setCurrentIndex(0)
            else:
                self.cmb_gedung.addItem("-- Data Gedung Kosong --", None)

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error Database",
                f"Gagal memuat data dari tabel lokasi_gedung:\n{e}"
            )
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()
            self.cmb_gedung.blockSignals(False)

    def setup_form(self):
        if isinstance(self.cmb_gedung, QComboBox):
            self.cmb_gedung.setStyleSheet("")
            self._load_data_gedung()

        if isinstance(self.cmb_status, QComboBox):
            self.cmb_status.setStyleSheet("")
            self.cmb_status.clear()
            self.cmb_status.addItems(["Tersedia", "Perbaikan"])

        if isinstance(self.spin_kapasitas, QSpinBox):
            self.spin_kapasitas.setRange(1, 10000)
            self.spin_kapasitas.setValue(1)

    def connect_signals(self):
        if isinstance(self.btn_batal, QPushButton):
            self.btn_batal.clicked.connect(self.reject)
        if isinstance(self.btn_simpan, QPushButton):
            self.btn_simpan.clicked.connect(self.simpan)

    def simpan(self):
        kode = self.txt_kode.text().strip() if isinstance(self.txt_kode, QLineEdit) else ""
        nama = self.txt_nama.text().strip() if isinstance(self.txt_nama, QLineEdit) else ""
        gedung = self.cmb_gedung.currentText().strip() if isinstance(self.cmb_gedung, QComboBox) else ""
        kapasitas = self.spin_kapasitas.value() if isinstance(self.spin_kapasitas, QSpinBox) else 0
        fasilitas = self.txt_fasilitas.toPlainText().strip() if isinstance(self.txt_fasilitas, QTextEdit) else ""
        status = self.cmb_status.currentText().strip() if isinstance(self.cmb_status, QComboBox) else "Tersedia"

        if not kode or not nama or not gedung or gedung == "-- Data Gedung Kosong --":
            QMessageBox.warning(
                self,
                "Input Belum Lengkap",
                "Kode ruang, nama ruang, dan lokasi gedung wajib diisi."
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