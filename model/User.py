from model.connectiondb import get_db_connection

class User:
    def __init__(self):
        pass

    def login(self, username, password):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("select level from user where username = %s and password = %s", (username, password))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return None

    def select_data_tabel(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("select username, level from user")
        result = cursor.fetchall()
        conn.close()
        return result

    def insert_data(self, username, password, level):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("insert into user (username, password, level) values (%s, %s, %s)"
                       (username, password, level))
        conn.commit()
        conn.close()

    def update_data(self, username, password, level):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("update user set username = %s, password = %s, level=%s where username = %s")
        conn.commit()
        conn.close()

    def delete_data(self, username):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user WHERE username = %s", (username,))
        conn.commit()
        conn.close() 