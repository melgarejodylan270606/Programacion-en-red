import xmlrpc.client

# Cambia IP_SERVIDOR por la IP real del servidor si están en equipos distintos (ej: "192.168.1.50")
IP_SERVIDOR = "127.0.0.1"
PUERTO = 8000


def main():
    url_servidor = f"http://{IP_SERVIDOR}:{PUERTO}"
    cliente = xmlrpc.client.ServerProxy(url_servidor)

    print("=== SISTEMA DE TURNOS: LA FILA (XML-RPC) ===")
    apodo = input("Ingrese su apodo: ").strip()

    if not apodo:
        print("El apodo no puede estar vacío.")
        return

    try:
        # 1. Solicitar el turno remoto
        mi_turno = cliente.tomar_turno(apodo)
        print(f"\n¡Éxito! Hola {apodo}, tu número de turno es: {mi_turno}")

        # 2. Consultar cuántos turnos van asignados
        total = cliente.cuantos_van()
        print(f"Total de turnos asignados en el sistema: {total}")

    except ConnectionRefusedError:
        print(f"\nError: No se pudo conectar al servidor en {url_servidor}.")
    except Exception as e:
        print(f"\nOcurrió un error inesperado: {e}")


if __name__ == "__main__":
    main()