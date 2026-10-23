import logging
import os
import sys
# Counter y no un dict con claves fijas: las causas de error no son una lista cerrada
# (ej. http_{status_code} depende de lo que responda la API) y Counter devuelve 0 en
# claves nuevas en vez de lanzar KeyError dentro de un except.
from collections import Counter

from dotenv import load_dotenv

import estado
import reporte
from lector import leer_cuentas
from cliente_api import consultar_cuenta, IdNoExiste, ErrorTecnico

load_dotenv()

# Logger propio de este módulo: los mensajes salen con el nombre "main"
logger = logging.getLogger("main")


def configurar_logs():
    # Busca una variable de entorno llamada ARCHIVO_LOG si no entonces se pone por defecto
    ruta_log = os.getenv("ARCHIVO_LOG", "logs/proceso.log")
    # El "." es la carpeta actual: si la ruta no trae carpeta, dirname da "" y makedirs fallaría
    # Algo a tener en cuenta es que exist_ok solo perdona carpeta si hay un archivo con el mismo nombre falla
    os.makedirs(os.path.dirname(ruta_log) or ".", exist_ok=True)
    #Se configura una sola vez los loggers del programa
    logging.basicConfig(
        # Lee NIVEL_LOG de el env y no existe usa INFO
        level=os.getenv("NIVEL_LOG", "INFO").upper(),
        #La plantilla de cada linea: fecha, nivel, nombre, y mensaje
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        # Cada mensaje sale por dos destinos: el archivo (queda guardado) y la consola (se ve en vivo)
        handlers=[logging.FileHandler(ruta_log), logging.StreamHandler()],
    )


def imprimir_resumen(contadores, descartados, saltados):
    logger.info("===== RESUMEN =====")
    logger.info("Ya resueltos en corridas anteriores (omitidos): %d", saltados)
    logger.info("Resueltos: %d", contadores["ok"])
    logger.info("Fallaron por causa:")
    for causa, cantidad in contadores.items():
        if causa != "ok":
            logger.info("  %-20s %d", causa, cantidad)
    # La generadora saca la causa de cada descartado, Counter las cuenta
    # y el for imprime un par (causa, cantidad) por línea
    for causa, cantidad in Counter(d["causa"] for d in descartados).items():
        logger.info("  %-20s %d (línea del CSV)", causa, cantidad)


def main():
    configurar_logs()
    logger.info("Inicio de ejecución")

    cuentas, descartados = leer_cuentas(os.getenv("ARCHIVO_CSV", "cuentas.csv"),
                                        os.getenv("COLUMNA_ID", "id_cuenta"))
    conn = estado.abrir(os.getenv("ARCHIVO_ESTADO", "salida/estado.db"))

    resueltos = estado.ids_resueltos(conn)
    pendientes = {i: l for i, l in cuentas.items() if i not in resueltos}
    saltados = len(cuentas) - len(pendientes)

    contadores = Counter()
    for id_cuenta, lineas in pendientes.items():
        try:
            datos = consultar_cuenta(id_cuenta)
            estado.guardar(conn, id_cuenta, "ok", lineas, datos=datos)
            contadores["ok"] += 1
        except IdNoExiste:
            estado.guardar(conn, id_cuenta, "no_existe", lineas, causa="id_no_existe")
            contadores["id_no_existe"] += 1
        except ErrorTecnico as error:
            estado.guardar(conn, id_cuenta, "error_tecnico", lineas, causa=error.causa)
            contadores[error.causa] += 1
        except Exception:
            # Red de seguridad: un error inesperado en un id no detiene a los demás
            logger.exception("Error inesperado con el id %s", id_cuenta)
            estado.guardar(conn, id_cuenta, "error_tecnico", lineas, causa="inesperado")
            contadores["inesperado"] += 1

    reporte.generar_excel(conn, os.getenv("ARCHIVO_EXCEL", "salida/resultado.xlsx"))
    imprimir_resumen(contadores, descartados, saltados)
    conn.close()
    logger.info("Fin de ejecución")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Falla fatal, el proceso no pudo completarse")
        sys.exit(1)
