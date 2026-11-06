"""
Práctica 8 · Programación en Red (NRC 19141) · Unidad IV
Servidor HTTP en Python: pseudo-CRUD con JSON en disco (bitácora de incidencias).

Solo usa la biblioteca estándar. Las incidencias se guardan en incidencias.json
(memoria no volátil); los logs y contadores viven en RAM y se reinician al arrancar.

Rutas:
    GET    /                     índice del servicio
    GET    /incidencias          lista (filtros opcionales: ?tipo=...&estado=...)
    GET    /incidencias/<id>     una incidencia
    POST   /incidencias          crea (201)
    PUT    /incidencias/<id>     reemplazo completo (200)
    PATCH  /incidencias/<id>     modificación parcial (200)
    DELETE /incidencias/<id>     elimina (204)
    GET    /logs                 bitácora de peticiones
    GET    /contadores           contadores de la sesión
"""
import functools
import http.server
import json
import os
import time
import traceback
from urllib.parse import parse_qs, urlparse

# ----------------------------------------------------------------------------
# Configuración
# ----------------------------------------------------------------------------
HOST = "localhost"
PUERTO = 8001
# El archivo se guarda junto al script, sin importar desde dónde se ejecute.
ARCHIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "incidencias.json")

# Ejercicio 1: vocabulario controlado para el campo 'estado'
ESTADOS_VALIDOS = ("abierta", "en_proceso", "resuelta")
CAMPOS_MODIFICABLES = ("tipo", "descripcion", "estado")   # el id jamás cambia
CAMPOS_OBLIGATORIOS = ("tipo", "descripcion")

# ----------------------------------------------------------------------------
# Estado del servidor
# ----------------------------------------------------------------------------
siguiente_id = 1

# Estructuras en RAM: se reinician al apagar el servidor (Ejercicio 2)
logs = []
contadores = {
    "peticiones_totales": 0,
    "por_metodo": {"GET": 0, "POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0, "HEAD": 0},
    "por_familia": {"2xx": 0, "4xx": 0, "5xx": 0},
    "incidencias_por_tipo": {"alerta": 0, "vulnerabilidad": 0, "incidente": 0},
}


def cargar():
    """Lee las incidencias del archivo JSON al arrancar y recupera el siguiente id."""
    global siguiente_id
    try:
        with open(ARCHIVO, encoding="utf-8") as f:
            datos = json.load(f)
        if not isinstance(datos, list):
            return []
        if datos:
            siguiente_id = max(i["id"] for i in datos) + 1
        return datos
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return []  # primera ejecución o archivo corrupto: empezar vacío


def guardar():
    """Reescribe el archivo JSON de forma atómica (temporal + os.replace).

    Si el proceso se interrumpe a la mitad de la escritura, incidencias.json
    nunca queda truncado: o está la versión vieja completa o la nueva completa.
    """
    temporal = ARCHIVO + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump(incidencias, f, ensure_ascii=False, indent=2)
    os.replace(temporal, ARCHIVO)


incidencias = cargar()  # al arrancar, recupera lo que había en disco


def _mensaje_estado_invalido(valor):
    return f"estado inválido '{valor}'. Valores válidos: {list(ESTADOS_VALIDOS)}"


def _protegido(metodo):
    """Decorador: cualquier excepción no prevista responde 500 en vez de cortar la conexión."""
    @functools.wraps(metodo)
    def envoltura(self, *args, **kwargs):
        try:
            metodo(self, *args, **kwargs)
        except Exception:
            traceback.print_exc()
            self._enviar(500, {"error": "error interno del servidor"})
    return envoltura


# ----------------------------------------------------------------------------
# Manejador HTTP
# ----------------------------------------------------------------------------
class Manejador(http.server.BaseHTTPRequestHandler):
    """Hereda de BaseHTTPRequestHandler y sobreescribe do_GET, do_POST, etc."""

    # ---- utilidades ---------------------------------------------------------
    def _leer_json(self):
        """Lee el cuerpo de la petición y lo interpreta como JSON (None si es inválido)."""
        try:
            tam = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(tam).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):  # JSONDecodeError es subclase de ValueError
            return None

    def _enviar(self, codigo, datos=None):
        """Única salida de respuestas: envía JSON y anota la petición en logs y contadores."""
        cuerpo = b"" if datos is None else json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        if self.command != "HEAD":      # HEAD nunca lleva cuerpo
            self.wfile.write(cuerpo)

        logs.append({"hora": time.strftime("%H:%M:%S"),
                     "metodo": self.command, "ruta": self.path, "codigo": codigo})
        contadores["peticiones_totales"] += 1
        por_metodo = contadores["por_metodo"]
        por_metodo[self.command] = por_metodo.get(self.command, 0) + 1
        familia = f"{codigo // 100}xx"
        contadores["por_familia"][familia] = contadores["por_familia"].get(familia, 0) + 1

    def _id_de_ruta(self, url):
        """Devuelve el id entero de /incidencias/<id>; responde 404/400 y devuelve None si no aplica."""
        if not url.path.startswith("/incidencias/"):
            self._enviar(404, {"error": f"ruta no conocida: {url.path}"})
            return None
        try:
            return int(url.path.split("/")[2])
        except ValueError:
            self._enviar(400, {"error": "id debe ser entero"})
            return None

    def _buscar(self, id_buscado):
        for inc in incidencias:
            if inc["id"] == id_buscado:
                return inc
        return None

    def log_message(self, formato, *args):
        """Silencia el log por defecto de consola: usamos nuestra propia bitácora."""

    # ---- HEAD ---------------------------------------------------------------
    @_protegido
    def do_HEAD(self):
        url = urlparse(self.path)
        if url.path in ("/", "/incidencias", "/logs", "/contadores"):
            self._enviar(200)
        else:
            self._enviar(404)

    # ---- GET (Ejercicio 5: filtros combinados tipo + estado) ----------------
    @_protegido
    def do_GET(self):
        url = urlparse(self.path)
        parametros = parse_qs(url.query)   # {"tipo": ["alerta"]}: valores en lista

        if url.path == "/":
            self._enviar(200, {
                "servicio": "Bitácora de incidencias",
                "rutas": [
                    "GET /incidencias", "GET /incidencias/<id>",
                    "POST /incidencias", "PUT /incidencias/<id>",
                    "PATCH /incidencias/<id>", "DELETE /incidencias/<id>",
                    "GET /logs", "GET /contadores",
                ],
            })

        elif url.path == "/incidencias":
            if "estado" in parametros and parametros["estado"][0] not in ESTADOS_VALIDOS:
                self._enviar(400, {"error": _mensaje_estado_invalido(parametros["estado"][0])})
                return
            lista = incidencias
            if "tipo" in parametros:
                lista = [i for i in lista if i["tipo"] == parametros["tipo"][0]]
            if "estado" in parametros:
                lista = [i for i in lista if i["estado"] == parametros["estado"][0]]
            self._enviar(200, lista)

        elif url.path.startswith("/incidencias/"):
            buscado = self._id_de_ruta(url)
            if buscado is None:
                return
            inc = self._buscar(buscado)
            if inc:
                self._enviar(200, inc)
            else:
                self._enviar(404, {"error": f"incidencia {buscado} no encontrada"})

        elif url.path == "/logs":
            self._enviar(200, logs)

        elif url.path == "/contadores":
            self._enviar(200, contadores)

        else:
            self._enviar(404, {"error": f"ruta no conocida: {url.path}"})

    # ---- POST (Ejercicio 1: valida 'estado') --------------------------------
    @_protegido
    def do_POST(self):
        global siguiente_id
        url = urlparse(self.path)
        if url.path != "/incidencias":
            self._enviar(404, {"error": f"ruta no conocida: {url.path}"})
            return

        datos = self._leer_json()
        if not isinstance(datos, dict):
            self._enviar(400, {"error": "el cuerpo debe ser JSON válido"})
            return

        faltan = [c for c in CAMPOS_OBLIGATORIOS if c not in datos]
        if faltan:
            self._enviar(400, {"error": f"faltan campos: {', '.join(faltan)}"})
            return

        estado = datos.get("estado", "abierta")
        if estado not in ESTADOS_VALIDOS:
            self._enviar(400, {"error": _mensaje_estado_invalido(estado)})
            return

        incidencia = {
            "id": siguiente_id,
            "tipo": str(datos["tipo"]),
            "descripcion": str(datos["descripcion"]),
            "estado": estado,
            "hora": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        siguiente_id += 1
        incidencias.append(incidencia)
        por_tipo = contadores["incidencias_por_tipo"]
        por_tipo[incidencia["tipo"]] = por_tipo.get(incidencia["tipo"], 0) + 1
        guardar()                       # <-- aquí se escribe incidencias.json
        self._enviar(201, incidencia)

    # ---- PUT (Ejercicio 4: reemplazo completo) ------------------------------
    @_protegido
    def do_PUT(self):
        url = urlparse(self.path)
        buscado = self._id_de_ruta(url)
        if buscado is None:
            return

        datos = self._leer_json()
        if not isinstance(datos, dict):
            self._enviar(400, {"error": "el cuerpo debe ser JSON válido"})
            return

        faltan = [c for c in CAMPOS_OBLIGATORIOS if c not in datos]
        if faltan:
            self._enviar(400, {"error": f"faltan campos obligatorios para PUT: {', '.join(faltan)}"})
            return

        inc = self._buscar(buscado)
        if inc is None:
            self._enviar(404, {"error": f"incidencia {buscado} no encontrada"})
            return

        # Reemplazo completo: el id se conserva; todo lo demás se reconstruye.
        inc["tipo"] = str(datos["tipo"])
        inc["descripcion"] = str(datos["descripcion"])
        inc["estado"] = "abierta"       # por especificación, PUT reinicia el estado
        inc["hora"] = time.strftime("%Y-%m-%d %H:%M:%S")
        guardar()
        self._enviar(200, inc)

    # ---- PATCH (Ejercicio 1: valida 'estado') -------------------------------
    @_protegido
    def do_PATCH(self):
        url = urlparse(self.path)
        buscado = self._id_de_ruta(url)
        if buscado is None:
            return

        datos = self._leer_json()
        if not isinstance(datos, dict):
            self._enviar(400, {"error": "el cuerpo debe ser JSON válido"})
            return

        if "estado" in datos and datos["estado"] not in ESTADOS_VALIDOS:
            self._enviar(400, {"error": _mensaje_estado_invalido(datos["estado"])})
            return

        inc = self._buscar(buscado)
        if inc is None:
            self._enviar(404, {"error": f"incidencia {buscado} no encontrada"})
            return

        for campo in CAMPOS_MODIFICABLES:
            if campo in datos:
                inc[campo] = str(datos[campo])
        guardar()                       # <-- el cambio queda en el archivo
        self._enviar(200, inc)

    # ---- DELETE -------------------------------------------------------------
    @_protegido
    def do_DELETE(self):
        url = urlparse(self.path)
        buscado = self._id_de_ruta(url)
        if buscado is None:
            return

        inc = self._buscar(buscado)
        if inc is None:
            self._enviar(404, {"error": f"incidencia {buscado} no encontrada"})
            return

        incidencias.remove(inc)
        guardar()                       # <-- el archivo también lo olvida
        self._enviar(204)               # 204 No Content: sin cuerpo


# ----------------------------------------------------------------------------
def main():
    servidor = http.server.HTTPServer((HOST, PUERTO), Manejador)
    print(f"Escuchando en http://{HOST}:{PUERTO}  (datos en {ARCHIVO})")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
