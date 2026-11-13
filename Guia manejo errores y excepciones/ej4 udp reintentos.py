import socket
import time

def consultar(servidor, mensaje, reintentos=3):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as cliente:
        cliente.settimeout(2)
        for intento in range(1, reintentos + 1):
            try:
                cliente.sendto((mensaje + "\n").encode("utf-8"), servidor)
                datos, _ = cliente.recvfrom(1024)
                return datos.decode("utf-8").strip()
            except TimeoutError:
                espera = 2 ** (intento - 1)
                print(f"Intento {intento}/{reintentos}: sin respuesta. Esperando {espera}s...")
                if intento < reintentos:
                    time.sleep(espera)
            except ConnectionResetError:
                espera = 2 ** (intento - 1)
                print(f"Intento {intento}/{reintentos}: puerto inalcanzable. Esperando {espera}s...")
                if intento < reintentos:
                    time.sleep(espera)
    return None

if __name__ == "__main__":
    respuesta = consultar(("127.0.0.1", 5001), "CUANTOS")
    if respuesta:
        print(f"Estado de la fila: {respuesta}")
    else:
        print("No se obtuvo respuesta del servidor tras 3 intentos.")
