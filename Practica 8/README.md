# Práctica 8 · Servidor HTTP en Python: CRUD con JSON en disco

Programación en Red · NRC 19141 · Unidad IV

Servidor HTTP (solo biblioteca estándar) que administra una bitácora de incidencias de seguridad.
Los datos se guardan en `incidencias.json`; los logs y contadores viven en memoria.

## Archivos

| Archivo | Descripción |
|---|---|
| `servidor_bitacora.py` | Servidor HTTP en `http://localhost:8001` |
| `cliente_bitacora.py` | Cliente con `requests` que prueba todo el servicio (OK/FALLO + resumen) |
| `incidencias.json` | Se crea automáticamente con el primer POST |
| `Reporte_Practica8.docx` | Reporte con evidencias |

## Ejecución

```bash
# terminal 1
python3 servidor_bitacora.py

# terminal 2
pip install requests          # solo la primera vez
python3 cliente_bitacora.py
```

## Rutas

| Método | Ruta | Éxito | Errores |
|---|---|---|---|
| GET | `/incidencias?tipo=&estado=` | 200 | 400 (estado inválido) |
| GET | `/incidencias/<id>` | 200 | 400, 404 |
| POST | `/incidencias` | 201 | 400, 404 |
| PUT | `/incidencias/<id>` | 200 | 400, 404 |
| PATCH | `/incidencias/<id>` | 200 | 400, 404 |
| DELETE | `/incidencias/<id>` | 204 | 400, 404 |
| GET | `/logs`, `/contadores` | 200 | — |
| HEAD | `/`, `/incidencias`, `/logs`, `/contadores` | 200 | 404 |

`estado` solo admite `abierta`, `en_proceso` o `resuelta`.

## Ejercicio 2: ¿por qué `/logs` y `/contadores` vuelven a cero?

`incidencias` es la única estructura que se escribe en disco: `guardar()` la vuelca a
`incidencias.json` tras cada POST, PUT, PATCH o DELETE y `cargar()` la lee al arrancar
(de ahí se recupera también el siguiente id con `max(id) + 1`).

`logs` (una lista) y `contadores` (un diccionario) son variables de Python que viven en la RAM
del proceso y se inicializan vacías o en cero cuando se carga el módulo. Al detener el
servidor el proceso termina y su memoria se libera; al arrancar de nuevo se crean otra vez
desde cero. Es deliberado: son una auditoría de la sesión, no datos de negocio.

## Ejercicio 3: ¿por qué el 501 no aparece en `/contadores` ni en `/logs`?

Sin `do_PUT`, quien responde es `BaseHTTPRequestHandler`: busca un método `do_PUT`, no lo
encuentra y llama a su propio `send_error(501)`. Nuestro código nunca se ejecuta y, por tanto,
tampoco `_enviar`, que es el único lugar donde se agrega una entrada a `logs` y se incrementan
los contadores. La petición solo deja una línea en la consola del servidor (vía `log_message`).

## Mejoras sobre el código base

- Escritura atómica del JSON (archivo temporal + `os.replace`).
- El archivo de datos se ubica junto al script, sin depender de la carpeta de ejecución.
- Funciones auxiliares `_id_de_ruta` y `_buscar` (menos código repetido).
- Decorador `_protegido`: una excepción inesperada responde 500.
- HEAD también se registra en logs y contadores.
- `GET /incidencias?estado=<inválido>` responde 400 en vez de una lista vacía.
- Cliente con comprobaciones automáticas, resumen final y código de salida.

## Limitaciones

Servidor de un solo hilo, sin autenticación ni cifrado, y `tipo` acepta cualquier cadena.
