# Consulta de cuentas médicas — Reto técnico RPA Developer

Proceso batch en Python que lee el CSV diario de cuentas médicas, consulta cada
identificador en un sistema externo y deja un Excel consolidado para auditoría.
Está pensado para correr solo, de madrugada.

## Qué hace

1. Lee `cuentas.csv` tal como llega (sin arreglarlo a mano).
2. Por cada id válido y único consulta `https://jsonplaceholder.typicode.com/posts/{id}`.
3. Guarda el resultado de cada id en una base SQLite (`salida/estado.db`).
4. Reconstruye `salida/resultado.xlsx` (hoja `Resultados`) desde esa base.
5. Escribe un resumen al final y un log en `logs/proceso.log`.

Un id que falla nunca detiene a los demás.

## Qué necesita

- Python 3.12 (es con el que se probó).
- Acceso a internet hacia `jsonplaceholder.typicode.com`.
- Dependencias de `requirements.txt`: pandas, requests, python-dotenv, openpyxl.

## Cómo se ejecuta

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # ajustar valores si hace falta
python src/main.py          # siempre desde la raíz del proyecto
```

## Configuración (`.env`)

Nada de esto está en el código. `.env.example` es la plantilla y se sube al
repositorio; `.env` no.

| Variable | Para qué sirve | Valor por defecto |
|---|---|---|
| `ARCHIVO_CSV` | CSV de entrada | `cuentas.csv` |
| `COLUMNA_ID` | Columna con los ids | `id_cuenta` |
| `API_URL_BASE` | URL base de la API | `https://jsonplaceholder.typicode.com/posts` |
| `API_TIMEOUT_SEGUNDOS` | Tiempo máximo de espera por intento | `10` |
| `REINTENTOS_MAXIMO` | Total de intentos por id (el primero cuenta) | `4` |
| `REINTENTOS_ESPERA_INICIAL_SEGUNDOS` | Espera antes del primer reintento | `1` |
| `REINTENTOS_FACTOR` | Cuánto crece la espera en cada reintento | `2` |
| `ARCHIVO_EXCEL` | Excel de salida | `salida/resultado.xlsx` |
| `ARCHIVO_ESTADO` | Base SQLite con el estado | `salida/estado.db` |
| `ARCHIVO_LOG` | Archivo de log | `logs/proceso.log` |
| `NIVEL_LOG` | Nivel de log | `INFO` |

Con los valores por defecto la espera entre intentos es 1 s, 2 s, 4 s.

## Cómo se maneja el CSV

El CSV trae basura a propósito y el programa la resuelve al leerlo
(`src/lector.py`):

| Caso del CSV | Qué hace el programa |
|---|---|
| ` 23` (con espacio) | Se limpia con `strip` y vale `23` |
| `"42"` (entre comillas) | El lector de CSV quita las comillas, vale `42` |
| Línea vacía | Se descarta (`linea_vacia`), queda en log y resumen |
| `abc` | Se descarta (`no_numerico`), queda en log y resumen |
| `0` | Es numérico, así que se consulta; la API dice que no existe |
| Ids repetidos | Ver la siguiente sección |

Los descartados no van al Excel ni a la base: no son cuentas, son basura de
entrada. Solo quedan en el log y en el resumen, con su número de línea.

## Decisión: identificadores repetidos

**Decidí consultar cada id una sola vez y conservar el rastro de cuántas veces
apareció.**

En el CSV el 7 aparece 3 veces y el 12 dos veces. Lo que se hace:

- Se consulta una vez por id único.
- El Excel tiene **una fila por id**, con las columnas `apariciones` (cuántas
  veces vino) y `lineas_csv` (en qué líneas), para que auditoría vea que se repitió.

Por qué:

- La consulta es de solo lectura sobre un dato que no cambia entre una línea y
  otra del mismo archivo. Repetirla daría la misma respuesta y gastaría llamadas.
- El archivo es una lista de cuentas radicadas. Un número repetido es casi seguro
  un error de la clínica (doble digitación), no dos hechos distintos.
- Si la clínica ya mandó el mismo número dos veces, auditoría necesita saberlo.
  Por eso no se descarta en silencio: queda el conteo y las líneas.

Alternativa que descarté: una fila por cada aparición. Solo tendría sentido si
cada línea fuera un evento distinto (por ejemplo con una fecha o un valor propio).
El CSV solo trae el número, así que no hay nada que distinga una línea de otra.

Si la clínica me dijera que cada línea es un evento distinto, cambiaría esto.

## Errores y reintentos: dónde está la frontera

Hay dos clases de error y se tratan distinto (`src/cliente_api.py`):

- **Negocio:** la API responde `404`, el id no existe. Es una respuesta válida:
  se guarda como `no_existe` y no se reintenta, porque preguntar de nuevo
  daría lo mismo.
- **Técnico:** no se obtuvo una respuesta útil.

| Situación | ¿Se reintenta? | Causa en el resumen |
|---|---|---|
| Timeout | Sí | `timeout` |
| Sin conexión / red cortada | Sí | `sin_conexion` |
| Error 5xx del servidor | Sí | `http_500`, `http_503`... |
| 404 | **No** (negocio) | `id_no_existe` |
| Cualquier otro código distinto de 200 | **No** | `http_<código>` |
| Petición mal formada | **No** | `peticion_invalida` |

**La frontera:** reintento lo que puede cambiar si espero (la red, un servidor
saturado o caído un momento) y no reintento lo que ya es una respuesta
definitiva. Un 404 no va a dejar de ser 404 en dos segundos; reintentarlo solo
retrasa el proceso y castiga a la API.

Los reintentos usan espera creciente (1 s, 2 s, 4 s con los valores por
defecto). Si se agotan los intentos, el id queda como `error_tecnico`.

Lo dejé corto a propósito. No traté `408`, `429` ni respuestas con JSON inválido
como casos especiales porque el enunciado no los pide; irían bajo "Mejoras
posibles".

## Re-ejecución y reanudación

Cada resultado se guarda en SQLite con un commit por id (`src/estado.py`).

| Estado | Significado | ¿Se vuelve a consultar? |
|---|---|---|
| `ok` | Resuelto | No |
| `no_existe` | La API dijo 404 | No |
| `error_tecnico` | Falló por causa técnica | **Sí**, en la siguiente corrida |

- **Correrlo dos veces seguidas:** la segunda no consulta nada ya resuelto y el
  Excel queda igual, sin filas duplicadas. El Excel se reconstruye completo
  desde la base cada vez, así que no puede duplicar.
- **Si se cae a la mitad:** lo ya guardado queda guardado. Al relanzar, retoma
  con los ids que faltan o que fallaron por causa técnica.
- El Excel se escribe a un archivo temporal y luego se renombra, así que si el
  proceso muere escribiéndolo, el Excel anterior no queda corrupto.

Para forzar una consulta desde cero, borrar `salida/estado.db`.

## Resumen y log

Al final de cada ejecución se imprime en pantalla y en el log:

```
===== RESUMEN =====
Ya resueltos en corridas anteriores (omitidos): N
Resueltos: N
Fallaron por causa:
  id_no_existe         N
  timeout              N
  linea_vacia          N (línea del CSV)
  no_numerico          N (línea del CSV)
```

El log (`logs/proceso.log`) trae cada reintento, cada línea descartada, cada
repetido y los errores inesperados con su traza.

## Runbook: me llaman a las 3 a.m.

**1. ¿Corrió?** Mirar el final del log:

```bash
tail -n 40 logs/proceso.log
```

Buscar `Inicio de ejecución` y `Fin de ejecución` de la corrida de hoy.

**2. Según lo que se vea:**

| Síntoma | Qué significa | Qué hacer |
|---|---|---|
| Aparece `Falla fatal` y el proceso salió con código 1 | No se pudo completar (CSV ausente, columna que no existe, base o Excel no se pueden escribir) | Leer la traza justo debajo. Revisar que exista `cuentas.csv`, que tenga la columna `id_cuenta` y que haya permisos y espacio en `salida/` |
| Resumen con muchos `timeout`, `sin_conexion` o `http_5xx` | La API o la red están mal; los ids quedaron como `error_tecnico` | Comprobar con `curl -I https://jsonplaceholder.typicode.com/posts/1`. Cuando responda, **volver a ejecutar** `python src/main.py`: solo reintenta lo pendiente |
| Resumen con `id_no_existe` | Es normal: son cuentas que la API no conoce | Nada que arreglar; auditoría lo ve en el Excel como `no_existe` |
| `linea_vacia` o `no_numerico` | Basura en el CSV de la clínica | No bloquea nada. Avisar a la clínica si es frecuente |
| `inesperado` | Error no previsto en un id | Buscar `Error inesperado con el id` en el log y leer la traza. El id se reintenta en la siguiente corrida |
| El Excel no se actualizó | Puede estar abierto en otro programa | Cerrarlo y volver a ejecutar; los datos están en la base |

**3. Volver a correr es seguro.** No duplica filas ni repite lo ya resuelto:

```bash
python src/main.py
```

**4. Cuánto puede tardar con la API caída.** Con los valores por defecto cada id
puede tardar hasta unos 47 s (4 intentos de hasta 10 s más esperas de 1+2+4 s).
Con 16 ids únicos, unos 12 minutos. No es un cuelgue.

**Cosas que conviene saber:**

- El proceso termina con código 0 aunque queden ids en `error_tecnico`; el código 1
  es solo para una falla fatal. Por eso hay que mirar el resumen, no solo el
  código de salida.
- No hay candado contra dos ejecuciones simultáneas. Si hay una en marcha, esperar
  a que termine.

## Estructura

```
src/main.py          orquesta: lee, consulta, guarda, genera Excel, resume
src/lector.py        lee y limpia el CSV, detecta repetidos y descartados
src/cliente_api.py   consulta la API, clasifica errores, reintenta
src/estado.py        base SQLite con el estado de cada id
src/reporte.py       genera el Excel desde la base
.env.example         plantilla de configuración
BITACORA.md          uso de IA durante el reto
```
