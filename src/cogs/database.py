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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS apelaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sancion_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            razones TEXT NOT NULL,
            evidencia TEXT,
            fecha_apelacion TEXT DEFAULT (strftime('%d-%m-%Y %H:%M', 'now', 'localtime')),
            estado TEXT DEFAULT 'pendiente',
            FOREIGN KEY (sancion_id) REFERENCES sanciones(id),
            FOREIGN KEY (user_id) REFERENCES usuarios(discord_id)
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
    
def guardar_apelacion(sancion_id, user_id, razones, evidencia):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO apelaciones (sancion_id, user_id, razones, evidencia)
        VALUES (?, ?, ?, ?)
    ''', (sancion_id, user_id, razones, evidencia))
    apelacion_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return apelacion_id

def cargar_apelaciones_por_usuario(user_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, sancion_id, razones, evidencia, fecha_apelacion, estado
        FROM apelaciones
        WHERE user_id = ?
    ''', (user_id,))
    apelaciones = cursor.fetchall()
    conn.close()
    return apelaciones


def cargar_apelaciones_por_sancion(sancion_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, razones, evidencia, fecha_apelacion, estado
        FROM apelaciones
        WHERE sancion_id = ?
    ''', (sancion_id,))
    apelaciones = cursor.fetchall()
    conn.close()
    return apelaciones

def actualizar_apelacion_imagen(apelacion_id, url_imagen):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE apelaciones
        SET evidencia = ?
        WHERE id = ?
    ''', (url_imagen, apelacion_id))
    conn.commit()
    conn.close()
    
def actualizar_estado_apelacion(apelacion_id, nuevo_estado):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE apelaciones
        SET estado = ?
        WHERE id = ?
    ''', (nuevo_estado, apelacion_id))
    conn.commit()
    conn.close()