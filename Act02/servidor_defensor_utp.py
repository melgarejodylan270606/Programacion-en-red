import socket

PUERTO = 5050
TAMANO = 5

def crear_tablero():
    return [["~" for _ in range(TAMANO)] for _ in range(TAMANO)]

def mostrar_tablero(tablero, titulo):
    print(f"\n--- {titulo} ---")
    print("  " + " ".join(str(i) for i in range(TAMANO)))
    for i, fila in enumerate(tablero):
        print(f"{i} " + " ".join(fila))

def main():
    # Primitiva SOCKET: Crear socket UDP (SOCK_DGRAM)
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Primitiva BIND: Asignar puerto de escucha
    servidor.bind(('0.0.0.0', PUERTO))
    print(f"[DEFENSOR UDP] Escuchando peticiones en el puerto {PUERTO}...")

    tablero_defensor = crear_tablero()
    
    print("\n--- CONFIGURACIÓN DEL DEFENSOR ---")
    f = int(input("Fila del barco (0-4): "))
    c = int(input("Columna del barco (0-4): "))
    tablero_defensor[f][c] = "B"
    
    mostrar_tablero(tablero_defensor, "TU TABLERO DE DEFENSA")
    barcos_vivos = 1

    try:
        while barcos_vivos > 0:
            print("\n[DEFENSOR] Esperando datagrama de ataque (blocking)...")
            
            # Primitiva RECVFROM: Recibe datos y obtiene la dirección (IP, puerto) del cliente
            request_bytes, addr = servidor.recvfrom(1024)
            request = request_bytes.decode('utf-8')
            
            af, ac = map(int, request.split(","))
            print(f"[DEFENSOR] Ataque recibido desde {addr} en la coordenada: ({af}, {ac})")

            # Evaluación de la petición
            if tablero_defensor[af][ac] == "B":
                response = "TOCADO"
                tablero_defensor[af][ac] = "X"
                barcos_vivos -= 1
            else:
                response = "AGUA"
                tablero_defensor[af][ac] = "O"

            # Primitiva SENDTO: Responde enviando un datagrama a la dirección específica
            servidor.sendto(response.encode('utf-8'), addr)
            print(f"[DEFENSOR] Respuesta '{response}' enviada a {addr}")
            mostrar_tablero(tablero_defensor, "ESTADO DEL TABLERO")

            if barcos_vivos == 0:
                print("\n[DEFENSOR] ¡Tu barco ha sido destruido! Fin del juego.")
                break

    finally:
        servidor.close()

if __name__ == "__main__":
    main()