
from model.connectiondb import get_db_connection


class User:
    def __init__(self):
        pass

    # --- LOGIN ---
    def login(self, username, password):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id_pengguna, nama, username, role, nama_organisasi
                FROM pengguna
                WHERE username = %s
                AND password = %s
                AND status_aktif = 'Aktif'
                """,
                (username, password)
            )

            result = cursor.fetchone()

            if result:
                return {
                    "id_pengguna": result[0],
                    "nama": result[1],
                    "username": result[2],
                    "role": result[3],
                    "nama_organisasi": result[4]
                }

            return None

        finally:
            conn.close()

    # --- CRUD AKUN (ADMIN) ---
    def select_data_tabel(self, keyword="", role_filter="Semua"):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            sql = """
                SELECT id_pengguna, username, nama, no_telepon,
                       role, status_aktif
                FROM pengguna
                WHERE 1=1
            """

            params = []

            if keyword:
                sql += """
                    AND (
                        nama LIKE %s
                        OR username LIKE %s
                        OR no_telepon LIKE %s
                    )
                """
                kw = f"%{keyword}%"
                params.extend([kw, kw, kw])

            if role_filter and role_filter != "Semua":
                sql += " AND role = %s"
                params.append(role_filter)

            sql += " ORDER BY id_pengguna ASC"

            cursor.execute(sql, tuple(params))
            return cursor.fetchall()

        finally:
            conn.close()

    def cari_by_id(self, id_pengguna):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id_pengguna, username, nama, no_telepon, role
                FROM pengguna
                WHERE id_pengguna = %s
                """,
                (id_pengguna,)
            )
            return cursor.fetchone()

        finally:
            conn.close()

    def cek_username_ada(self, username, exclude_id=None):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            if exclude_id:
                cursor.execute(
                    """
                    SELECT id_pengguna FROM pengguna
                    WHERE username = %s AND id_pengguna != %s
                    """,
                    (username, exclude_id)
                )
            else:
                cursor.execute(
                    "SELECT id_pengguna FROM pengguna WHERE username = %s",
                    (username,)
                )

            return cursor.fetchone() is not None

        finally:
            conn.close()

    def insert_data(self, nama, username, password, no_telepon, role):
        nama_org = nama if role == "OKI" else None

        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO pengguna
                (nama, username, password, no_telepon, role,
                 nama_organisasi, status_aktif)
                VALUES (%s, %s, %s, %s, %s, %s, 'Aktif')
                """,
                (nama, username, password, no_telepon, role, nama_org)
            )

            conn.commit()
            return True

        except Exception as e:
            print(f"[SQL Error] {e}")
            conn.rollback()
            return False

        finally:
            conn.close()

    def update_data(
        self, id_pengguna, nama, username,
        password, no_telepon, role
    ):
        nama_org = nama if role == "OKI" else None

        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            if password and password.strip() != "":
                cursor.execute(
                    """
                    UPDATE pengguna
                    SET nama = %s, username = %s, password = %s,
                        no_telepon = %s, role = %s, nama_organisasi = %s
                    WHERE id_pengguna = %s
                    """,
                    (
                        nama, username, password, no_telepon,
                        role, nama_org, id_pengguna
                    )
                )
            else:
                cursor.execute(
                    """
                    UPDATE pengguna
                    SET nama = %s, username = %s, no_telepon = %s,
                        role = %s, nama_organisasi = %s
                    WHERE id_pengguna = %s
                    """,
                    (
                        nama, username, no_telepon,
                        role, nama_org, id_pengguna
                    )
                )

            conn.commit()
            return True

        except Exception as e:
            print(f"[SQL Error] {e}")
            conn.rollback()
            return False

        finally:
            conn.close()

    def delete_data(self, id_pengguna):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM pengguna WHERE id_pengguna = %s",
                (id_pengguna,)
            )

            conn.commit()
            return True

        except Exception as e:
            print(f"[SQL Error] {e}")
            conn.rollback()
            return False

        finally:
            conn.close()

    # --- MONITORING DASHBOARD ADMIN ---
    def get_statistik_dashboard(self):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT role, COUNT(*) FROM pengguna GROUP BY role"
            )

            rows = cursor.fetchall()

            stat = {
                "Admin": 0,
                "BMN": 0,
                "OKI": 0,
                "Disetujui": 0
            }

            for r in rows:
                stat[r[0]] = r[1]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM pengajuan_peminjaman
                WHERE status_pengajuan IN ('Disetujui', 'Selesai')
                """
            )

            res = cursor.fetchone()
            stat["Disetujui"] = res[0] if res else 0

            return stat

        finally:
            conn.close()

    # --- DATA PENGAJUAN ADMIN ---
    def select_pengajuan_admin(self, status_filter="Semua"):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            sql = """
                SELECT p.id_pengajuan,
                       COALESCE(u.nama_organisasi, u.nama),
                       p.nama_kegiatan,
                       r.kode_ruang,
                       r.nama_ruang,
                       p.tanggal_mulai,
                       p.tanggal_selesai,
                       p.status_pengajuan
                FROM pengajuan_peminjaman p
                JOIN ruang r ON p.id_ruang = r.id_ruang
                JOIN pengguna u ON p.id_oki = u.id_pengguna
                WHERE 1=1
            """

            params = []

            if status_filter and status_filter != "Semua":
                sql += " AND p.status_pengajuan = %s"
                params.append(status_filter)

            sql += " ORDER BY p.id_pengajuan ASC"

            cursor.execute(sql, tuple(params))
            return cursor.fetchall()

        finally:
            conn.close()

    # --- DETAIL PENGAJUAN ---
    def select_detail_pengajuan(self, id_pengajuan):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            sql = """
                SELECT COALESCE(u.nama_organisasi, u.nama),
                       p.nama_kegiatan,
                       p.tanggal_pengajuan,
                       p.status_pengajuan,
                       r.kode_ruang,
                       r.nama_ruang,
                       p.tanggal_mulai,
                       p.tanggal_selesai,
                       p.keperluan,
                       p.catatan_verifikasi,
                       p.file_surat_pengajuan
                FROM pengajuan_peminjaman p
                JOIN ruang r ON p.id_ruang = r.id_ruang
                JOIN pengguna u ON p.id_oki = u.id_pengguna
                WHERE p.id_pengajuan = %s
            """

            cursor.execute(sql, (id_pengajuan,))
            return cursor.fetchone()

        finally:
            conn.close()

    # --- AMBIL FILE SURAT ---
    def get_file_surat(self, id_pengajuan):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT file_surat_pengajuan, data_surat_pengajuan
                FROM pengajuan_peminjaman
                WHERE id_pengajuan = %s
                """,
                (id_pengajuan,)
            )

            return cursor.fetchone()

        finally:
            conn.close()

    # --- PENGAJUAN PEMINJAMAN OKI ---
    def insert_pengajuan_oki(
        self, id_oki, id_ruang, nama_kegiatan,
        tanggal_mulai, tanggal_selesai, keperluan,
        nama_file, blob_surat
    ):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            sql = """
                INSERT INTO pengajuan_peminjaman
                (
                    id_oki, id_ruang, nama_kegiatan,
                    tanggal_mulai, tanggal_selesai,
                    keperluan, file_surat_pengajuan,
                    data_surat_pengajuan, status_pengajuan
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Menunggu')
            """

            cursor.execute(
                sql,
                (
                    id_oki, id_ruang, nama_kegiatan,
                    tanggal_mulai, tanggal_selesai,
                    keperluan, nama_file, blob_surat
                )
            )

            conn.commit()
            return True

        except Exception as e:
            print(f"[SQL Error] {e}")
            conn.rollback()
            return False

        finally:
            conn.close()

    # --- DATA RUANG ---
    def select_data_ruang(self, keyword="", gedung="Semua"):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            sql = """
                SELECT kode_ruang, nama_ruang, lokasi_gedung,
                       kapasitas, fasilitas, status_ruang
                FROM ruang
                WHERE 1=1
            """

            params = []

            if keyword:
                sql += """
                    AND (
                        kode_ruang LIKE %s
                        OR nama_ruang LIKE %s
                        OR fasilitas LIKE %s
                    )
                """

                kw = f"%{keyword}%"
                params.extend([kw, kw, kw])

            if gedung and gedung != "Semua":
                sql += " AND lokasi_gedung = %s"
                params.append(gedung)

            sql += " ORDER BY kode_ruang ASC"

            cursor.execute(sql, tuple(params))
            return cursor.fetchall() or []

        finally:
            conn.close()

    
    # --- STATISTIK DASHBOARD BMN ---
    def get_statistik_bmn(self):
        # Menghitung jumlah pengajuan yang masih menunggu
        data_pengajuan = self.ringkasan()
        menunggu = data_pengajuan.get("Menunggu", 0)

        # Mengambil seluruh data ruang
        data_ruang = self.select_data_ruang()

        # Menghitung jumlah ruang yang tersedia dan terpakai
        tersedia = sum(
            1 for ruang in data_ruang
            if str(ruang[5]).strip().lower() == "tersedia"
        )

        terpakai = sum(
            1 for ruang in data_ruang
            if str(ruang[5]).strip().lower() == "terpakai"
        )

        return menunggu, tersedia, terpakai

    # --- RINGKASAN DASHBOARD BMN ---
    def ringkasan(self):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT status_pengajuan, COUNT(*)
                FROM pengajuan_peminjaman
                GROUP BY status_pengajuan
                """
            )

            rows = cursor.fetchall() or []

            hasil = {
                "Menunggu": 0,
                "Disetujui": 0,
                "Ditolak": 0,
                "Selesai": 0,
                "Total": 0
            }

            for r in rows:
                hasil[r[0]] = r[1]
                hasil["Total"] += r[1]

            return hasil

        finally:
            conn.close()
