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
    # Defensor es el server: espera pasivo
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(('0.0.0.0', PUERTO))
    servidor.listen(1)
    
    print(f"[DEFENSOR] Esperando conexión en el puerto {PUERTO}...")
    
    # Primitiva ACCEPT (blocking)
    conn, addr = servidor.accept()
    print(f"[DEFENSOR] Atacante conectado desde: {addr}")

    tablero_defensor = crear_tablero()
    
    # Posicionar barco del defensor
    print("\n--- CONFIGURACIÓN DEL DEFENSOR ---")
    f = int(input("Fila del barco (0-4): "))
    c = int(input("Columna del barco (0-4): "))
    tablero_defensor[f][c] = "B"
    
    mostrar_tablero(tablero_defensor, "TU TABLERO DE DEFENSA")
    
    barcos_vivos = 1

    try:
        while barcos_vivos > 0:
            print("\n[DEFENSOR] Esperando ataque del cliente (blocking)...")
            
            # RECEIVE = DECODE (recibir = decodificar)
            request = conn.recv(1024).decode('utf-8')
            if not request:
                break
                
            af, ac = map(int, request.split(","))
            print(f"[DEFENSOR] Ataque recibido en coordenada: ({af}, {ac})")

            # Evaluación de la petición (request) y respuesta (response)
            if tablero_defensor[af][ac] == "B":
                response = "TOCADO"
                tablero_defensor[af][ac] = "X"
                barcos_vivos -= 1
            else:
                response = "AGUA"
                tablero_defensor[af][ac] = "O"

            # SEND = ENCODE (enviar = codificar)
            conn.send(response.encode('utf-8'))
            print(f"[DEFENSOR] Respuesta enviada: {response}")
            mostrar_tablero(tablero_defensor, "ESTADO DEL TABLERO")

            if barcos_vivos == 0:
                print("\n[DEFENSOR] ¡Tu barco ha sido destruido! Fin del juego.")
                break

    finally:
        conn.close()
        servidor.close()

if __name__ == "__main__":
    main()