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

    # Primitiva SOCKET: Crear socket UDP
    cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    direccion_defensor = (ip_defensor, PUERTO)

    radar = crear_radar()
    juego_activo = True

    try:
        while juego_activo:
            mostrar_radar(radar)
            
            print("\n--- TU TURNO DE ATAQUE ---")
            f = int(input("Fila a atacar (0-4): "))
            c = int(input("Columna a atacar (0-4): "))
            
            request = f"{f},{c}"
            
            # Primitiva SENDTO: Envía el datagrama especificando la dirección de destino
            cliente.sendto(request.encode('utf-8'), direccion_defensor)
            print(f"[ATACANTE] Ataque sent ({request}) enviado a {direccion_defensor}. Esperando respuesta...")

            # Primitiva RECVFROM: Recibe la respuesta en modo bloqueante
            response_bytes, _ = cliente.recvfrom(1024)
            response = response_bytes.decode('utf-8')
            print(f"[ATACANTE] Respuesta recibida: {response}")

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

if __name__ == "__main__":
    main()