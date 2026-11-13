import socket
import sys

PUERTO = 5000

def main():
    ip_servidor = input("Ingrese la IP del servidor: ").strip()
    if not ip_servidor:
        print("Error: debe ingresar una dirección IP o nombre de host.")
        sys.exit(1)

    try:
        conexion = socket.create_connection((ip_servidor, PUERTO), timeout=5)
    except socket.gaierror:
        print(f"Error: la dirección '{ip_servidor}' no es válida o no se pudo resolver.")
        sys.exit(1)
    except ConnectionRefusedError:
        print("Error: conexión rechazada (el servidor está apagado o el puerto cerrado).")
        sys.exit(1)
    except TimeoutError:
        print("Error: tiempo de espera agotado al intentar conectar con el servidor.")
        sys.exit(1)
    except OSError as e:
        print(f"Error de red al conectar: {e}")
        sys.exit(1)

    with conexion:
        conexion.settimeout(5)
        try:
            for mensaje in ["hola", "prueba"]:
                conexion.sendall((mensaje + "\n").encode("utf-8"))
                datos = conexion.recv(1024)
                if not datos:
                    print("Error: el servidor cerró la conexión a media conversación.")
                    sys.exit(1)
                print(f"Respuesta del servidor: {datos.decode('utf-8').strip()}")
        except TimeoutError:
            print("Error: el servidor tardó demasiado en responder.")
            sys.exit(1)
        except (ConnectionResetError, BrokenPipeError):
            print("Error: se perdió la conexión con el servidor durante el intercambio.")
            sys.exit(1)

if __name__ == "__main__":
    main()
