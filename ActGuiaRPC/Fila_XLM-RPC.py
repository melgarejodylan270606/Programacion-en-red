import threading
import time
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

HOST = "0.0.0.0"
PUERTO = 8000

# ---- Estado compartido ----
turno_actual = 0
candado = threading.Lock()


def registrar(texto):
    print(f"{time.strftime('%H:%M:%S')} | {texto}")


def tomar_turno(apodo):
    """
    Asigna el siguiente turno de forma segura entre peticiones concurrentes.
    Devuelve el número de turno asignado.
    """
    global turno_actual
    with candado:
        turno_actual += 1
        numero = turno_actual

    registrar(f"Turno {numero} asignado a '{apodo}'")
    return numero


def cuantos_van():
    """Devuelve el total de turnos asignados hasta el momento."""
    with candado:
        total = turno_actual

    registrar(f"Consulta de total de turnos: {total}")
    return total


# Clase para silenciar/personalizar los logs HTTP por defecto en la consola
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/RPC2",)


if __name__ == "__main__":
    # Creamos el servidor XML-RPC
    with SimpleXMLRPCServer(
        (HOST, PUERTO), requestHandler=RequestHandler, allow_none=True
    ) as servidor:
        # Registrar funciones remotas
        servidor.register_function(tomar_turno, "tomar_turno")
        servidor.register_function(cuantos_van, "cuantos_van")

        registrar(
            f"Servidor XML-RPC 'LA FILA' escuchando en http://{HOST}:{PUERTO}"
        )
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            registrar(
                f"\nServidor detenido. Total de turnos asignados: {cuantos_van()}"
            )