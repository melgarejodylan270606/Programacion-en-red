import socket

# Cambiar por la IP real del servidor al probar entre dos equipos
IP_SERVIDOR = "127.0.0.1"
PUERTO_UDP = 5001


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as cliente:
        cliente.settimeout(3)
        try:
            cliente.sendto("CUANTOS".encode("utf-8"), (IP_SERVIDOR, PUERTO_UDP))
            datos, _ = cliente.recvfrom(1024)
            respuesta = datos.decode("utf-8").strip()
            print(f"Respuesta del servidor: {respuesta}")
        except TimeoutError:
            print("Sin respuesta tras 3 segundos: el servidor no está activo o se perdió el datagrama.")
        except ConnectionResetError:
            print("El puerto UDP del servidor no está disponible.")


if __name__ == "__main__":
    main()
