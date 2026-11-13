import requests

BASE = "http://localhost:8001"


def main():
    print("1. Creando incidencias (POST)...")
    r1 = requests.post(
        f"{BASE}/incidencias",
        json={"tipo": "alerta", "descripcion": "Escaneo de puertos detectado"},
        timeout=10,
    )
    print("POST 1:", r1.status_code, r1.json())
    id_creada = r1.json()["id"]

    r2 = requests.post(
        f"{BASE}/incidencias",
        json={"tipo": "vulnerabilidad", "descripcion": "SSH con contraseña débil", "estado": "en_proceso"},
        timeout=10,
    )
    print("POST 2:", r2.status_code, r2.json())

    print("\n2. Probando validación de estado inválido (400)...")
    r_err = requests.post(
        f"{BASE}/incidencias",
        json={"tipo": "alerta", "descripcion": "Prueba", "estado": "inventado"},
        timeout=10,
    )
    print("POST inválido:", r_err.status_code, r_err.json())

    print("\n3. Consultando con filtros combinados (GET)...")
    r_filtro = requests.get(
        f"{BASE}/incidencias",
        params={"tipo": "alerta", "estado": "abierta"},
        timeout=10,
    )
    print("GET filtrado:", r_filtro.status_code, r_filtro.json())

    print("\n4. Actualizando parcialmente con PATCH...")
    r_patch = requests.patch(
        f"{BASE}/incidencias/{id_creada}",
        json={"estado": "resuelta"},
        timeout=10,
    )
    print("PATCH:", r_patch.status_code, r_patch.json())

    print("\n5. Reemplazando registro completo con PUT...")
    r_put = requests.put(
        f"{BASE}/incidencias/{id_creada}",
        json={"tipo": "incidente", "descripcion": "Fuga de credenciales confirmada"},
        timeout=10,
    )
    print("PUT:", r_put.status_code, r_put.json())

    print("\n6. Eliminando incidencia con DELETE...")
    r_del = requests.delete(f"{BASE}/incidencias/{id_creada}", timeout=10)
    print("DELETE:", r_del.status_code)

    print("\n7. Consultando auditoría del servidor (/contadores y /logs)...")
    print("Contadores:", requests.get(f"{BASE}/contadores", timeout=10).json())
    print("Logs:", requests.get(f"{BASE}/logs", timeout=10).json())


if __name__ == "__main__":
    main()
