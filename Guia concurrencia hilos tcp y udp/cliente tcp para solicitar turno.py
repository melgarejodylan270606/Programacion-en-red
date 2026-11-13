import socket

# Cambiar por la IP real del servidor al probar entre dos equipos
IP_SERVIDOR = "127.0.0.1"
PUERTO_TCP = 5000


def main():
    apodo = input("Ingrese su apodo para tomar turno: ").strip()
    if not apodo:
        print("El apodo no puede estar vacío.")
        return

    try:
        with socket.create_connection((IP_SERVIDOR, PUERTO_TCP), timeout=5) as conexion:
            mensaje = f"TURNO>{apodo}\n"
            conexion.sendall(mensaje.encode("utf-8"))

            buffer = ""
            while "\n" not in buffer:
                datos = conexion.recv(1024)
                if not datos:
                    break
                buffer += datos.decode("utf-8")

            respuesta, _ = buffer.split("\n", 1)
            print(f"Respuesta del servidor: {respuesta}")
    except ConnectionRefusedError:
        print(f"No se pudo conectar al servidor en {IP_SERVIDOR}:{PUERTO_TCP}")
    except TimeoutError:
        print("Tiempo de espera agotado al comunicarse con el servidor.")


if __name__ == "__main__":
    main()
