import socket
import threading

HOST = "0.0.0.0"
PUERTO = 5000

def atender_cliente(conexion, direccion):
    contador = 0
    try:
        with conexion:
            buffer = ""
            while True:
                datos = conexion.recv(1024)
                if not datos:
                    break
                buffer += datos.decode("utf-8")
                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    contador += 1
                    respuesta = f"{contador}>{linea}\n"
                    conexion.sendall(respuesta.encode("utf-8"))
    except (ConnectionResetError, BrokenPipeError):
        print(f"Cliente {direccion} desconectado abruptamente")
    finally:
        print(f"Conexión cerrada: {direccion} (mensajes procesados: {contador})")

def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        servidor.bind((HOST, PUERTO))
    except OSError:
        print(f"Error: el puerto {PUERTO} ya está en uso.")
        return

    servidor.listen()
    print(f"Servidor de eco con contador escuchando en el puerto {PUERTO}...")
    while True:
        conexion, direccion = servidor.accept()
        hilo = threading.Thread(target=atender_cliente, args=(conexion, direccion), daemon=True)
        hilo.start()

if __name__ == "__main__":
    main()
