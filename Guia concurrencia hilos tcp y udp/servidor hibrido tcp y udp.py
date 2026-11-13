import socket
import threading
import time

HOST = "0.0.0.0"
PUERTO_TCP = 5000
PUERTO_UDP = 5001

# Estado compartido entre hilos
turno_actual = 0
candado = threading.Lock()


def registrar(texto):
    print(f"{time.strftime('%H:%M:%S')} | {texto}")


def tomar_turno():
    """Incrementa y devuelve el siguiente turno de forma segura."""
    global turno_actual
    with candado:
        turno_actual += 1
        return turno_actual


def total_asignados():
    """Devuelve el total de turnos asignados hasta el momento."""
    with candado:
        return turno_actual


def atender_cliente_tcp(conexion, direccion):
    """Atiende a un cliente TCP en su propio hilo."""
    registrar(f"Cliente TCP conectado desde {direccion}")
    buffer = ""
    try:
        with conexion:
            while True:
                datos = conexion.recv(1024)
                if not datos:
                    break
                buffer += datos.decode("utf-8")
                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    mensaje = linea.strip()
                    comando, separador, apodo = mensaje.partition(">")
                    if comando == "TURNO" and separador and apodo.strip():
                        numero = tomar_turno()
                        registrar(f"Turno {numero} asignado a '{apodo.strip()}'")
                        conexion.sendall(f"turno>{numero}\n".encode("utf-8"))
                    else:
                        conexion.sendall(b"error>formato esperado TURNO>apodo\n")
    except (ConnectionResetError, BrokenPipeError):
        registrar(f"Cliente TCP {direccion} se desconectó abruptamente")
    finally:
        registrar(f"Conexión TCP cerrada: {direccion}")


def atender_consultas_udp():
    """Atiende consultas UDP sin conexión en un hilo dedicado."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock_udp:
        sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_udp.bind((HOST, PUERTO_UDP))
        registrar(f"Servidor UDP escuchando en el puerto {PUERTO_UDP}")

        while True:
            try:
                datos, direccion = sock_udp.recvfrom(1024)
                mensaje = datos.decode("utf-8").strip()
                if mensaje == "CUANTOS":
                    total = total_asignados()
                    respuesta = f"van>{total}\n"
                    registrar(f"Consulta UDP de {direccion} -> {respuesta.strip()}")
                else:
                    respuesta = "error>comando esperado CUANTOS\n"
                sock_udp.sendto(respuesta.encode("utf-8"), direccion)
            except OSError:
                pass


def main():
    # Hilo secundario para consultas UDP
    hilo_udp = threading.Thread(target=atender_consultas_udp, daemon=True)
    hilo_udp.start()

    # Hilo principal para aceptar clientes TCP
    servidor_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor_tcp.bind((HOST, PUERTO_TCP))
    servidor_tcp.listen(10)
    registrar(f"Servidor TCP escuchando en el puerto {PUERTO_TCP} (LA FILA abierta)")

    try:
        while True:
            conexion, direccion = servidor_tcp.accept()
            hilo_cliente = threading.Thread(
                target=atender_cliente_tcp,
                args=(conexion, direccion),
                daemon=True
            )
            hilo_cliente.start()
    except KeyboardInterrupt:
        registrar(f"Servidor detenido. Turnos totales asignados: {total_asignados()}")
    finally:
        servidor_tcp.close()


if __name__ == "__main__":
    main()
