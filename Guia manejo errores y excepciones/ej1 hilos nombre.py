import threading
import time

def saludar(nombre, veces):
    for i in range(1, veces + 1):
        print(f"{nombre}: saludo {i} de {veces}")
        time.sleep(0.2)

def main():
    tareas = [("Ana", 3), ("Beto", 5), ("Cora", 2)]
    hilos = []

    for nombre, veces in tareas:
        hilo = threading.Thread(target=saludar, args=(nombre, veces), name=nombre)
        hilos.append(hilo)
        hilo.start()

    for hilo in hilos:
        hilo.join()

    print("Todos los hilos han terminado su ejecución.")

if __name__ == "__main__":
    main()
