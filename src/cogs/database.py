import sqlite3


def conectar_db():
    conn = sqlite3.connect("bouken.db")
    return conn


def inicializar_db():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sanciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            motivo TEXT NOT NULL,
            fecha TEXT NOT NULL,
            imagen TEXT,
            estado TEXT NOT NULL DEFAULT 'activa',
            staff TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def guardar_sancion(user_id, motivo, fecha, imagen, estado, staff):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sanciones (user_id, motivo, fecha, imagen, estado, staff)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, motivo, fecha, imagen, estado, staff))
    sancion_id = cursor.lastrowid  # Recuperar el ID generado automáticamente
    conn.commit()
    conn.close()
    return sancion_id


def cargar_sanciones(user_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, motivo, fecha, imagen, estado, staff FROM sanciones WHERE user_id = ?', (user_id,))
    sanciones = cursor.fetchall()
    conn.close()
    return sanciones


def actualizar_sancion_con_imagen(sancion_id, url_imagen):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE sanciones
        SET imagen = ?
        WHERE id = ?
    ''', (url_imagen, sancion_id))
    conn.commit()
    conn.close()