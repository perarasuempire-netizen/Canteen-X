import mysql.connector

def get_db_connection():
    conn = mysql.connector.connect(
        host="maglev.proxy.rlwy.net",
        port=41955,
        user="root",
        password="mFMSJGsxIfgCUCxuMWXBXivqIwZncnpX",
        database="railway"
    )
    return conn
