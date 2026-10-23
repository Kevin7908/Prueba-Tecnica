import os
import sqlite3
from datetime import datetime

ESTADOS_FINALES = ("ok", "no_existe")


def abrir(ruta):
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    conn = sqlite3.connect(ruta)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resultados (
            id_cuenta   INTEGER PRIMARY KEY,
            estado      TEXT NOT NULL,
            causa       TEXT,
            user_id     INTEGER,
            titulo      TEXT,
            cuerpo      TEXT,
            apariciones INTEGER NOT NULL,
            lineas_csv  TEXT NOT NULL,
            actualizado TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def ids_resueltos(conn):
    filas = conn.execute(
        "SELECT id_cuenta FROM resultados WHERE estado IN (?, ?)", ESTADOS_FINALES
    )
    return {fila[0] for fila in filas}


# Guarda (o reemplaza) el resultado de un id. El commit por id es lo que permite retomar.
def guardar(conn, id_cuenta, estado, lineas, causa=None, datos=None):
    datos = datos or {}
    with conn:
        conn.execute("""
            INSERT INTO resultados
                (id_cuenta, estado, causa, user_id, titulo, cuerpo, apariciones, lineas_csv, actualizado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id_cuenta) DO UPDATE SET
                estado=excluded.estado, causa=excluded.causa, user_id=excluded.user_id,
                titulo=excluded.titulo, cuerpo=excluded.cuerpo,
                apariciones=excluded.apariciones, lineas_csv=excluded.lineas_csv,
                actualizado=excluded.actualizado
        """, (
            id_cuenta, estado, causa, datos.get("userId"), datos.get("title"), datos.get("body"),
            len(lineas), ",".join(map(str, lineas)), datetime.now().isoformat(timespec="seconds"),
        ))

