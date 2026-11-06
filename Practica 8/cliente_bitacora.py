"""
Práctica 8 · Programación en Red (NRC 19141) · Unidad IV
Cliente de pruebas para el servidor de la bitácora de incidencias.

Recorre el ciclo CRUD completo, los errores 4xx, los filtros combinados y la
auditoría (/logs y /contadores). Cada comprobación imprime OK/FALLO y al final
se muestra un resumen. No depende de ids fijos, así que puede ejecutarse varias
veces contra el mismo incidencias.json.

Uso:  python3 cliente_bitacora.py            (con el servidor ya en marcha)
"""
import sys

import requests

BASE = "http://localhost:8001"
TIMEOUT = 10
ESTADOS = ("abierta", "en_proceso", "resuelta")

resultados = []


def titulo(texto):
    print(f"\n=== {texto} ===")


def verificar(descripcion, condicion):
    """Registra e imprime una comprobación."""
    resultados.append(bool(condicion))
    print(f"  [{'OK' if condicion else 'FALLO'}] {descripcion}")
    return condicion


def crear(tipo, descripcion, **extra):
    return requests.post(f"{BASE}/incidencias",
                         json={"tipo": tipo, "descripcion": descripcion, **extra},
                         timeout=TIMEOUT)


def probar_cliente():
    # 1 ---------------------------------------------------------------------
    titulo("1. Vocabulario controlado y validación (POST)")
    r = crear("alerta", "Intento de login", estado="invalido")
    print(f"  Status: {r.status_code}  Respuesta: {r.json()}")
    verificar("estado inválido -> 400", r.status_code == 400)
    verificar("el mensaje lista los valores válidos",
              all(e in r.json()["error"] for e in ESTADOS))

    r = requests.post(f"{BASE}/incidencias", json={"tipo": "alerta"}, timeout=TIMEOUT)
    print(f"  Status: {r.status_code}  Respuesta: {r.json()}")
    verificar("falta 'descripcion' -> 400", r.status_code == 400)

    r = requests.post(f"{BASE}/incidencias", data="esto no es json", timeout=TIMEOUT)
    print(f"  Status: {r.status_code}  Respuesta: {r.json()}")
    verificar("cuerpo que no es JSON -> 400", r.status_code == 400)

    # 2 ---------------------------------------------------------------------
    titulo("2. Crear incidencias válidas (POST -> 201)")
    inc1 = crear("alerta", "Escaneo de puertos SSH", estado="abierta").json()
    inc2 = crear("vulnerabilidad", "Kernel desactualizado", estado="en_proceso").json()
    inc3 = crear("incidente", "Phishing reportado por un usuario").json()
    for inc in (inc1, inc2, inc3):
        print(f"  Creada: {inc}")
    verificar("las tres tienen id distinto", len({inc1["id"], inc2["id"], inc3["id"]}) == 3)
    verificar("sin 'estado' se asigna 'abierta'", inc3["estado"] == "abierta")

    # 3 ---------------------------------------------------------------------
    titulo("3. Consultas (GET)")
    r = requests.get(f"{BASE}/incidencias/{inc1['id']}", timeout=TIMEOUT)
    print(f"  GET /incidencias/{inc1['id']} -> {r.status_code} {r.json()}")
    verificar("GET por id -> 200", r.status_code == 200 and r.json()["id"] == inc1["id"])

    r = requests.get(f"{BASE}/incidencias/999999", timeout=TIMEOUT)
    print(f"  GET /incidencias/999999 -> {r.status_code} {r.json()}")
    verificar("id inexistente -> 404", r.status_code == 404)

    r = requests.get(f"{BASE}/incidencias/abc", timeout=TIMEOUT)
    print(f"  GET /incidencias/abc -> {r.status_code} {r.json()}")
    verificar("id no entero -> 400", r.status_code == 400)

    # 4 ---------------------------------------------------------------------
    titulo("4. Reemplazo completo (PUT)")
    r = requests.put(f"{BASE}/incidencias/{inc1['id']}",
                     json={"tipo": "incidente", "descripcion": "Servidor comprometido totalmente"},
                     timeout=TIMEOUT)
    print(f"  Status: {r.status_code}  Registro: {r.json()}")
    verificar("PUT -> 200", r.status_code == 200)
    verificar("conserva el id original", r.json()["id"] == inc1["id"])
    verificar("reinicia el estado a 'abierta'", r.json()["estado"] == "abierta")

    r = requests.put(f"{BASE}/incidencias/{inc1['id']}", json={"tipo": "alerta"}, timeout=TIMEOUT)
    print(f"  PUT incompleto -> {r.status_code} {r.json()}")
    verificar("PUT sin 'descripcion' -> 400", r.status_code == 400)

    r = requests.put(f"{BASE}/incidencias/999999",
                     json={"tipo": "alerta", "descripcion": "x"}, timeout=TIMEOUT)
    verificar("PUT a id inexistente -> 404", r.status_code == 404)

    # 5 ---------------------------------------------------------------------
    titulo("5. Modificación parcial (PATCH)")
    r = requests.patch(f"{BASE}/incidencias/{inc1['id']}", json={"estado": "resuelta"}, timeout=TIMEOUT)
    print(f"  Status: {r.status_code}  Registro: {r.json()}")
    verificar("PATCH -> 200 y estado 'resuelta'", r.status_code == 200 and r.json()["estado"] == "resuelta")
    verificar("PATCH no toca los demás campos", r.json()["tipo"] == "incidente")

    r = requests.patch(f"{BASE}/incidencias/{inc1['id']}", json={"estado": "cerrada"}, timeout=TIMEOUT)
    print(f"  PATCH estado inválido -> {r.status_code} {r.json()}")
    verificar("PATCH con estado inválido -> 400", r.status_code == 400)

    r = requests.patch(f"{BASE}/incidencias/999999", json={"estado": "resuelta"}, timeout=TIMEOUT)
    verificar("PATCH a id inexistente -> 404", r.status_code == 404)

    # 6 ---------------------------------------------------------------------
    titulo("6. Filtros combinados (GET ?tipo=&estado=)")
    todas = requests.get(f"{BASE}/incidencias", timeout=TIMEOUT).json()
    tipos = sorted({i["tipo"] for i in todas})
    for tipo in [None] + tipos[:2]:
        for estado in [None] + list(ESTADOS):
            params = {k: v for k, v in (("tipo", tipo), ("estado", estado)) if v}
            r = requests.get(f"{BASE}/incidencias", params=params, timeout=TIMEOUT)
            esperado = [i for i in todas
                        if (tipo is None or i["tipo"] == tipo)
                        and (estado is None or i["estado"] == estado)]
            print(f"  {str(params or '(sin filtros)'):55s} -> {len(r.json())} resultado(s)")
            verificar(f"filtro {params or 'vacío'} coincide con el filtrado local", r.json() == esperado)
    r = requests.get(f"{BASE}/incidencias", params={"estado": "cerrada"}, timeout=TIMEOUT)
    verificar("filtro con estado inválido -> 400", r.status_code == 400)

    # 7 ---------------------------------------------------------------------
    titulo("7. Eliminación (DELETE -> 204)")
    r = requests.delete(f"{BASE}/incidencias/{inc2['id']}", timeout=TIMEOUT)
    print(f"  DELETE -> {r.status_code}  cuerpo={r.text!r}")
    verificar("DELETE -> 204 sin cuerpo", r.status_code == 204 and r.text == "")
    r = requests.delete(f"{BASE}/incidencias/{inc2['id']}", timeout=TIMEOUT)
    print(f"  DELETE repetido -> {r.status_code} {r.json()}")
    verificar("segundo DELETE -> 404", r.status_code == 404)
    r = requests.get(f"{BASE}/incidencias/{inc2['id']}", timeout=TIMEOUT)
    verificar("ya no se puede consultar -> 404", r.status_code == 404)

    # 8 ---------------------------------------------------------------------
    titulo("8. HEAD y ruta desconocida")
    r = requests.head(f"{BASE}/incidencias", timeout=TIMEOUT)
    verificar("HEAD /incidencias -> 200 sin cuerpo", r.status_code == 200 and r.text == "")
    r = requests.get(f"{BASE}/no-existe", timeout=TIMEOUT)
    print(f"  GET /no-existe -> {r.status_code} {r.json()}")
    verificar("ruta desconocida -> 404", r.status_code == 404)

    # 9 ---------------------------------------------------------------------
    titulo("9. Auditoría (/contadores y /logs)")
    cont = requests.get(f"{BASE}/contadores", timeout=TIMEOUT).json()
    print("  Contadores:", cont)
    for fam in ("2xx", "4xx"):
        verificar(f"contador {fam} > 0", cont["por_familia"][fam] > 0)
    for m in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"):
        verificar(f"el método {m} aparece en los contadores", cont["por_metodo"][m] > 0)
    logs = requests.get(f"{BASE}/logs", timeout=TIMEOUT).json()
    print("  Últimos 3 logs:")
    for entrada in logs[-3:]:
        print("   ", entrada)
    verificar("los logs registran las peticiones", len(logs) > 0)


def main():
    try:
        probar_cliente()
    except requests.exceptions.ConnectionError:
        print("Error: el servidor no está ejecutándose en", BASE)
        sys.exit(1)

    ok = sum(resultados)
    print(f"\nRESUMEN: {ok}/{len(resultados)} comprobaciones correctas")
    sys.exit(0 if ok == len(resultados) else 1)


if __name__ == "__main__":
    main()
