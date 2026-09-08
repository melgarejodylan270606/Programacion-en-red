import socket

PUERTO = 5050
TAMANO = 5

def crear_radar():
    return [["~" for _ in range(TAMANO)] for _ in range(TAMANO)]

def mostrar_radar(radar):
    print("\n--- RADAR DE ATAQUES ---")
    print("  " + " ".join(str(i) for i in range(TAMANO)))
    for i, fila in enumerate(radar):
        print(f"{i} " + " ".join(fila))

def main():
    ip_defensor = input("Ingrese IP del defensor (Enter para localhost): ").strip()
    if not ip_defensor:
        ip_defensor = "127.0.0.1"

    # Atacante es el client: inicia la comunicación con CONNECT
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"[ATACANTE] Conectando al defensor en {ip_defensor}:{PUERTO}...")
    cliente.connect((ip_defensor, PUERTO))
    print("[ATACANTE] ¡Conexión establecida!")

    radar = crear_radar()
    juego_activo = True

    try:
        while juego_activo:
            mostrar_radar(radar)
            
            # Formular el request (petición de ataque)
            print("\n--- TU TURNO DE ATAQUE ---")
            f = int(input("Fila a atacar (0-4): "))
            c = int(input("Columna a atacar (0-4): "))
            
            request = f"{f},{c}"
            
            # SEND = ENCODE (enviar = codificar)
            cliente.send(request.encode('utf-8'))
            print(f"[ATACANTE] Ataque enviado ({request}). Esperando respuesta...")

            # RECEIVE = DECODE (recibir = decodificar) - Operación blocking
            response = cliente.recv(1024).decode('utf-8')
            print(f"[ATACANTE] Respuesta del defensor: {response}")

            if response == "TOCADO":
                radar[f][c] = "X"
                print("\n¡IMPACTO DIRECTO! Has hundido el barco enemigo.")
                mostrar_radar(radar)
                juego_activo = False
            elif response == "AGUA":
                radar[f][c] = "O"
                print("\nDisparo al agua. Intenta de nuevo.")

    finally:
        cliente.close()
        print("[ATACANTE] Socket cerrado.")

if __name__ == "__main__":
    main()