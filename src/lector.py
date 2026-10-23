import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)

SOLO_DIGITOS = re.compile(r"^\d+$")


# Devuelve dos cosas:
# - cuentas: {id: [líneas del CSV donde apareció]}, sin repetidos y en orden de primera aparición
# - descartados: lista de {"linea", "valor_original", "causa"} con lo que no sirvió
def leer_cuentas(ruta, columna):
    # dtype=str: no dejamos que pandas adivine tipos (por 'abc' y por ' 23').
    # skip_blank_lines=False: la línea vacía llega como fila y la podemos reportar.
    # keep_default_na=False: lo vacío llega como "" en lugar de NaN.
    df = pd.read_csv(ruta, dtype=str, skip_blank_lines=False, keep_default_na=False)

    if columna not in df.columns:
        raise ValueError(f"El CSV no tiene la columna '{columna}'. Columnas: {list(df.columns)}")

    cuentas = {}
    descartados = []

    # La fila 0 del DataFrame es la línea 2 del archivo (la 1 es el encabezado).
    for indice, valor in enumerate(df[columna]):
        linea = indice + 2
        limpio = valor.strip()

        if limpio == "":
            descartados.append({"linea": linea, "valor_original": valor, "causa": "linea_vacia"})
            logger.warning("Línea %d descartada: vacía", linea)
            continue

        if not SOLO_DIGITOS.match(limpio):
            descartados.append({"linea": linea, "valor_original": valor, "causa": "no_numerico"})
            logger.warning("Línea %d descartada: '%s' no es un número", linea, limpio)
            continue

        # se covierte a int ya que como se utilizo dtype=str covierte todo a texto
        id_cuenta = int(limpio)
        # Si el id ya es clave de cuentas, es un repetido. En el log,
        # cuentas[id_cuenta][0] es la primera línea donde apareció (posición 0 de su lista).
        if id_cuenta in cuentas:
            logger.info("Línea %d: id %d repetido, ya aparecía en la línea %d",
                        linea, id_cuenta, cuentas[id_cuenta][0])
        else:
            # crea el diccionario vacio con el id que le llego
            cuentas[id_cuenta] = []
        # inserta el valor en el id anterior
        cuentas[id_cuenta].append(linea)

    logger.info("CSV leído: %d ids únicos válidos, %d líneas descartadas",
                len(cuentas), len(descartados))
    return cuentas, descartados
