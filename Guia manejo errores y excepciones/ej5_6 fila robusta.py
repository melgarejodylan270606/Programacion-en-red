import socket
import threading
import time

HOST = "0.0.0.0"
PUERTO_TCP = 5000
PUERTO_UDP = 5001
ARCHIVO_LOG = "errores_fila.log"

turno_actual = 0
candado = threading.Lock()

def registrar_error(direccion, descripcion):
    marca = time.strftime("%Y-%m-%d %H:%M:%S")
    linea = f"{marca} {direccion} {descripcion}"
    print(f"[ERROR] {linea}")
    with candado:
        with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
            f.write(linea + "\n")

def tomar_turno(apodo):
    global turno_actual
    with candado:
        turno_actual += 1
        return turno_actual

def total_asignados():
    with candado:
        return turno_actual

def atender_cliente(conexion, direccion):
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
                    mensaje = linea.strip()
                    if mensaje.startswith("TURNO>") and len(mensaje) > 6:
                        apodo = mensaje.split(">", 1)[1].strip()
                        numero = tomar_turno(apodo)
                        print(f"Turno {numero} asignado a '{apodo}' desde {direccion}")
                        conexion.sendall(f"turno>{numero}\n".encode("utf-8"))
                    else:
                        registrar_error(direccion, f"mensaje inválido fuera de protocolo: {mensaje!r}")
                        conexion.sendall(b"error>formato esperado TURNO>apodo\n")
    except ConnectionResetError:
        registrar_error(direccion, "conexión reiniciada por el cliente")
    except BrokenPipeError:
        registrar_error(direccion, "tubería rota al intentar responder")
    except UnicodeDecodeError:
        registrar_error(direccion, "bytes recibidos no son UTF-8 válido")
    finally:
        print(f"Conexión cerrada: {direccion}")

def ciclo_udp():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock_udp:
        sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_udp.bind((HOST, PUERTO_UDP))
        print(f"Servicio UDP activo en puerto {PUERTO_UDP}")
        while True:
            try:
                datos, direccion = sock_udp.recvfrom(1024)
                mensaje = datos.decode("utf-8").strip()
                if mensaje == "CUANTOS":
                    resp = f"van>{total_asignados()}\n"
                else:
                    resp = "error>comando esperado CUANTOS\n"
                sock_udp.sendto(resp.encode("utf-8"), direccion)
            except UnicodeDecodeError:
                registrar_error(direccion, "datagrama UDP no UTF-8")
            except OSError:
                pass

def main():
    threading.Thread(target=ciclo_udp, daemon=True).start()
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        servidor.bind((HOST, PUERTO_TCP))
    except OSError:
        print(f"Error: el puerto {PUERTO_TCP} está ocupado.")
        return

    servidor.listen(10)
    print(f"Servidor LA FILA tolerante a fallos escuchando en puerto {PUERTO_TCP}...")
    try:
        while True:
            conexion, direccion = servidor.accept()
            threading.Thread(target=atender_cliente, args=(conexion, direccion), daemon=True).start()
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario.")
    finally:
        servidor.close()

if __name__ == "__main__":
    main()
