"""
Módulo común: carga el grafo y lo convierte a estructuras simples de Python.

Todas las fases usan este módulo. Los algoritmos NO usan funciones de búsqueda
de networkx/osmnx; solo trabajan con diccionarios y listas.

Estructuras que regresa cargar_grafo():
    vecinos = {nodo: [(vecino, metros), (vecino, metros), ...], ...}
    coords  = {nodo: (latitud, longitud), ...}

Se usa desde la raíz del proyecto (por la ruta relativa a data/):
    python src/mapa.py
"""

import math
import osmnx as ox

ARCHIVO_GRAFO = "data/grafo_cdmx.graphml"

# Depósito = punto de salida del camión. Es el centro de la zona descargada (Tlatelolco).
DEPOSITO = (19.450, -99.137)

# Lugares conocidos para los pares origen-destino (coordenadas aproximadas).
# Se eligen sitios reconocibles para poder explicar las rutas en la demo.
LUGARES = {
    "Bellas Artes": (19.4352, -99.1413),
    "Garibaldi": (19.4406, -99.1395),
    "Monumento a la Revolución": (19.4362, -99.1547),
    "La Raza": (19.4695, -99.1365),
    "Tepito": (19.4424, -99.1237),
    "Zócalo": (19.4326, -99.1332),
}


def haversine(lat1, lon1, lat2, lon2):
    """Distancia en metros entre dos puntos (lat, lon) sobre la superficie de la Tierra."""
    R = 6371000  # radio medio de la Tierra en metros
    # Las funciones trigonométricas de Python trabajan en radianes.
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def cargar_grafo(ruta=ARCHIVO_GRAFO):
    """Lee el grafo guardado y regresa (vecinos, coords) como diccionarios simples."""
    G = ox.load_graphml(ruta)

    # 1) Coordenadas de cada nodo. En osmnx: 'y' = latitud, 'x' = longitud.
    #    También creamos la lista de vecinos vacía para TODOS los nodos,
    #    así un nodo sin calles de salida existe con lista vacía (no da KeyError).
    coords = {}
    vecinos = {}
    for nodo, datos in G.nodes(data=True):
        coords[nodo] = (datos["y"], datos["x"])
        vecinos[nodo] = []

    # 2) Aristas. El grafo de osmnx puede tener varias calles paralelas entre
    #    los mismos dos nodos (aristas paralelas). Nos quedamos con la MÁS CORTA,
    #    porque un camión siempre tomaría esa.
    mas_corta = {}  # (u, v) -> metros
    for u, v, datos in G.edges(data=True):
        if u == v:
            continue  # un ciclo a sí mismo no sirve para llegar a ningún lado
        metros = float(datos["length"])
        if (u, v) not in mas_corta or metros < mas_corta[(u, v)]:
            mas_corta[(u, v)] = metros

    for (u, v), metros in mas_corta.items():
        vecinos[u].append((v, metros))

    return vecinos, coords


def nodo_mas_cercano(coords, lat, lon):
    """Regresa (nodo, distancia_en_metros) del nodo más cercano a (lat, lon).

    Búsqueda lineal: revisamos los ~5 mil nodos uno por uno. Es suficientemente
    rápido y evita instalar scikit-learn (que osmnx pediría para esto).
    """
    mejor_nodo = None
    mejor_dist = float("inf")
    for nodo, (nlat, nlon) in coords.items():
        d = haversine(lat, lon, nlat, nlon)
        if d < mejor_dist:
            mejor_nodo = nodo
            mejor_dist = d
    return mejor_nodo, mejor_dist


def pares_origen_destino(coords):
    """Lista de pares para la Fase 1: (nombre, nodo_deposito, nodo_destino)."""
    deposito, _ = nodo_mas_cercano(coords, DEPOSITO[0], DEPOSITO[1])
    pares = []
    for nombre, (lat, lon) in LUGARES.items():
        destino, _ = nodo_mas_cercano(coords, lat, lon)
        pares.append((nombre, deposito, destino))
    return pares


# Prueba rápida: muestra un resumen del grafo y de los lugares elegidos.
if __name__ == "__main__":
    vecinos, coords = cargar_grafo()
    total_aristas = sum(len(lista) for lista in vecinos.values())
    sin_salida = sum(1 for lista in vecinos.values() if len(lista) == 0)
    print("Nodos:", len(vecinos))
    print("Aristas (sin paralelas):", total_aristas)
    print("Nodos sin calles de salida:", sin_salida)

    nodo, dist = nodo_mas_cercano(coords, DEPOSITO[0], DEPOSITO[1])
    print(f"\nDepósito -> nodo {nodo} (a {dist:.0f} m del punto pedido)")
    for nombre, (lat, lon) in LUGARES.items():
        nodo, dist = nodo_mas_cercano(coords, lat, lon)
        print(f"{nombre:28s} -> nodo {nodo} (a {dist:.0f} m)")
