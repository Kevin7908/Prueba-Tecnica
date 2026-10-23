import logging
import os

import pandas as pd

logger = logging.getLogger(__name__)


# El Excel se reconstruye completo desde la base de datos en cada corrida.
# Por eso nunca hay filas duplicadas y siempre refleja el estado más reciente.
def generar_excel(conn, ruta):
    df = pd.read_sql_query("""
        SELECT id_cuenta, estado, causa, user_id, titulo, cuerpo,
               apariciones, lineas_csv, actualizado
        FROM resultados
        ORDER BY id_cuenta
    """, conn)

    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)

    # Se escribe a un temporal y se renombra: si el proceso muere a mitad,
    # el Excel anterior queda intacto en vez de quedar corrupto.
    # (la extensión .xlsx se conserva porque pandas la valida)
    nombre, extension = os.path.splitext(ruta)
    temporal = f"{nombre}.tmp{extension}"
    df.to_excel(temporal, sheet_name="Resultados", index=False, engine="openpyxl")
    os.replace(temporal, ruta)

    logger.info("Excel generado: %s (%d filas)", ruta, len(df))
