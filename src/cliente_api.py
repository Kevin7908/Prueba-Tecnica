import logging
import os
import time

import requests

logger = logging.getLogger(__name__)


# Caso de negocio: la API respondió y dijo que el id no existe (404). Nunca va a cambiar.
class IdNoExiste(Exception):
    pass


# Caso técnico: no pudimos obtener una respuesta útil.
# causa sirve para agrupar en el resumen; reintentable decide si vale la pena volver a intentar.
class ErrorTecnico(Exception):
    def __init__(self, causa, detalle="", reintentable=False):
        super().__init__(f"{causa}: {detalle}")
        self.causa = causa
        self.detalle = detalle
        self.reintentable = reintentable


# Un solo intento. Devuelve el JSON del post o lanza IdNoExiste / ErrorTecnico.
def _intentar(id_cuenta, url_base, timeout):
    try:
        respuesta = requests.get(f"{url_base}/{id_cuenta}", timeout=timeout)
    # Timeout va antes que ConnectionError porque ConnectTimeout hereda de las dos.
    except requests.Timeout as error:
        raise ErrorTecnico("timeout", str(error), reintentable=True)
    except requests.ConnectionError as error:
        raise ErrorTecnico("sin_conexion", str(error), reintentable=True)
    except requests.RequestException as error:
        raise ErrorTecnico("peticion_invalida", str(error))

    if respuesta.status_code == 404:
        raise IdNoExiste(f"El id {id_cuenta} no existe en la API")

    # 5xx: el servidor falló ahora, puede funcionar después.
    if respuesta.status_code >= 500:
        raise ErrorTecnico(f"http_{respuesta.status_code}", respuesta.reason, reintentable=True)

    # Cualquier otra respuesta que no sea 200 no la esperamos y reintentar no la arregla.
    if respuesta.status_code != 200:
        raise ErrorTecnico(f"http_{respuesta.status_code}", respuesta.reason)

    return respuesta.json()


# Consulta con reintentos y espera creciente (espera, espera*factor, espera*factor^2...).
# Solo reintenta los ErrorTecnico reintentables. IdNoExiste sale de inmediato.
# La configuración se lee aquí, al llamar, para no depender del orden en que main carga el .env.
def consultar_cuenta(id_cuenta):
    url_base = os.getenv("API_URL_BASE", "https://jsonplaceholder.typicode.com/posts")
    timeout = float(os.getenv("API_TIMEOUT_SEGUNDOS", "10"))
    intentos = max(1, int(os.getenv("REINTENTOS_MAXIMO", "4")))
    espera = float(os.getenv("REINTENTOS_ESPERA_INICIAL_SEGUNDOS", "1"))
    factor = float(os.getenv("REINTENTOS_FACTOR", "2"))

    for intento in range(1, intentos + 1):
        try:
            return _intentar(id_cuenta, url_base, timeout)
        except ErrorTecnico as error:
            if not error.reintentable or intento == intentos:
                raise
            logger.warning("Id %s: intento %d/%d falló (%s). Reintento en %.1fs",
                           id_cuenta, intento, intentos, error.causa, espera)
            time.sleep(espera)
            espera *= factor
