import sqlite3

# Conexión a la base de datos SQLite
def conectar_db():
    conn = sqlite3.connect("bouken.db")
    return conn

# Inicializar la tabla de sanciones
def inicializar_db():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sanciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            motivo TEXT NOT NULL,
            fecha TEXT NOT NULL,
            imagen TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Insertar una sanción en la base de datos
# database.py
def guardar_sancion(user_id, motivo, fecha, imagen):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sanciones (user_id, motivo, fecha, imagen)
        VALUES (?, ?, ?, ?)
    ''', (user_id, motivo, fecha, imagen))
    sancion_id = cursor.lastrowid  # Recuperar el ID generado automáticamente
    conn.commit()
    conn.close()
    return sancion_id

# Obtener sanciones de un usuario
def cargar_sanciones(user_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, motivo, fecha, imagen FROM sanciones WHERE user_id = ?', (user_id,))
    sanciones = cursor.fetchall()
    conn.close()
    return sanciones

# Actualizar la sanción con la URL de la imagen
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