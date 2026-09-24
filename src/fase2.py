"""
Fase 2: Búsqueda informada (usa coordenadas para guiarse hacia el destino).

Las búsquedas de esta fase reciben lo mismo que en la Fase 1, más:
    coords     = {nodo: (lat, lon)}              (ver mapa.py)
    heuristica = función h(coords, nodo, destino) que estima los metros que faltan

Y regresan el MISMO diccionario que la Fase 1 (reutilizamos armar_resultado),
así se pueden comparar directamente con BFS, DFS y UCS.
"""

import math
import time
import heapq

from mapa import haversine
from fase1 import armar_resultado

R_TIERRA = 6371000  # radio medio de la Tierra en metros (el mismo que usa haversine)


# ---------------------------------------------------------------------------
# Heurísticas: todas regresan METROS, para poder sumarse con g(n) (que también son metros)
# ---------------------------------------------------------------------------

def h1_euclidiana(coords, nodo, destino):
    """Distancia en línea recta sobre un PLANO (ignora que la Tierra es curva).

    Primero convertimos la diferencia de lat/lon a metros:
        - 1 grado de latitud mide lo mismo en todos lados: R * (radianes).
        - 1 grado de longitud se "encoge" al alejarse del ecuador: se multiplica
          por cos(latitud). Usamos la latitud promedio de los dos puntos.
    Luego aplicamos Pitágoras: sqrt(dx² + dy²).
    """
    lat1, lon1 = coords[nodo]
    lat2, lon2 = coords[destino]
    lat_promedio = math.radians((lat1 + lat2) / 2)
    dx = R_TIERRA * math.radians(lon2 - lon1) * math.cos(lat_promedio)
    dy = R_TIERRA * math.radians(lat2 - lat1)
    return math.sqrt(dx ** 2 + dy ** 2)


def h2_haversine(coords, nodo, destino):
    """Distancia en línea recta sobre la ESFERA terrestre (considera la curvatura)."""
    lat1, lon1 = coords[nodo]
    lat2, lon2 = coords[destino]
    return haversine(lat1, lon1, lat2, lon2)


# Parámetros de h3 (decididos por el equipo)
PENALIZACION_GIRO = 50   # metros extra por cada giro estimado (~media cuadra)
TOLERANCIA_GRADOS = 20   # si el destino está a menos de 20° de un eje N-S/E-O, "va derecho"


def h3_personalizada(coords, nodo, destino):
    """Haversine + una penalización si probablemente hay que dar vuelta.

    Idea: en una cuadrícula de calles, si el destino está en línea recta hacia
    el norte, sur, este u oeste, podrías llegar sin doblar (0 giros). Si está
    en diagonal, tienes que doblar al menos una vez (1 giro).

    OJO: el costo real (g) solo cuenta metros, NO giros. Por eso esta
    penalización puede hacer que h3 SOBREESTIME en algunos nodos, es decir,
    que no sea admisible. Lo medimos en la validación de admisibilidad.
    """
    lat1, lon1 = coords[nodo]
    lat2, lon2 = coords[destino]

    # Dirección hacia el destino, en metros sobre el plano (igual que en h1).
    lat_promedio = math.radians((lat1 + lat2) / 2)
    dx = R_TIERRA * math.radians(lon2 - lon1) * math.cos(lat_promedio)
    dy = R_TIERRA * math.radians(lat2 - lat1)

    # atan2 da el ángulo de la dirección (de -180° a 180°).
    angulo = abs(math.degrees(math.atan2(dy, dx)))
    # Cuántos grados se aleja del eje más cercano (0° = alineado, 45° = diagonal pura).
    resto = angulo % 90
    desviacion = min(resto, 90 - resto)

    giros_estimados = 1 if desviacion > TOLERANCIA_GRADOS else 0
    return haversine(lat1, lon1, lat2, lon2) + PENALIZACION_GIRO * giros_estimados


# ---------------------------------------------------------------------------
# A* (A-Star)
# ---------------------------------------------------------------------------

def a_estrella(vecinos, coords, origen, destino, heuristica):
    """Camino de menor distancia, guiado por la heurística.

    Es igual que UCS, pero la prioridad en la cola es:
        f(n) = g(n) + h(n)
        g(n) = metros reales recorridos desde el origen hasta n
        h(n) = metros estimados desde n hasta el destino
    Así prefiere los nodos que "van hacia el destino" y expande menos nodos que UCS.
    Si h nunca sobreestima (es admisible), el camino sigue siendo el óptimo.
    """
    inicio = time.perf_counter()

    # En la cola guardamos (f, nodo); heapq siempre saca el de menor f.
    frontera = [(heuristica(coords, origen, destino), origen)]

    # g[n] = el menor costo real con el que hemos llegado a n hasta ahora.
    g = {origen: 0.0}
    padres = {origen: None}
    visitados = set()

    expandidos = 0
    frontera_max = 1
    orden_expansion = []
    encontrado = False

    while frontera:
        _f, actual = heapq.heappop(frontera)

        # Igual que en UCS: ignoramos copias viejas de un nodo ya expandido.
        if actual in visitados:
            continue
        visitados.add(actual)
        expandidos += 1
        orden_expansion.append(actual)

        if actual == destino:
            encontrado = True
            break

        for vecino, metros in vecinos[actual]:
            nuevo_g = g[actual] + metros
            if vecino not in g or nuevo_g < g[vecino]:
                g[vecino] = nuevo_g
                padres[vecino] = actual
                f = nuevo_g + heuristica(coords, vecino, destino)
                heapq.heappush(frontera, (f, vecino))

        frontera_max = max(frontera_max, len(frontera))

    return armar_resultado(vecinos, padres, destino, encontrado, expandidos,
                           frontera_max, inicio, orden_expansion)


# ---------------------------------------------------------------------------
# Greedy Best-First (Búsqueda voraz)
# ---------------------------------------------------------------------------

def greedy(vecinos, coords, origen, destino, heuristica):
    """Va directo hacia el destino SIN fijarse en los metros ya recorridos.

    La prioridad en la cola es solo f(n) = h(n): siempre expande el nodo que
    "parece" más cercano al destino. Suele ser muy rápido, pero NO garantiza
    el camino más corto, porque ignora g(n) (lo que ya costó llegar ahí).
    """
    inicio = time.perf_counter()

    frontera = [(heuristica(coords, origen, destino), origen)]

    # Como Greedy no compara costos, basta con registrar cada nodo la primera vez
    # que se descubre (igual que en BFS): padres también funciona como "visitados".
    padres = {origen: None}

    expandidos = 0
    frontera_max = 1
    orden_expansion = []
    encontrado = False

    while frontera:
        _h, actual = heapq.heappop(frontera)   # sale el que parece más cercano al destino
        expandidos += 1
        orden_expansion.append(actual)

        if actual == destino:
            encontrado = True
            break

        for vecino, _metros in vecinos[actual]:   # Greedy ignora los metros
            if vecino not in padres:
                padres[vecino] = actual
                heapq.heappush(frontera, (heuristica(coords, vecino, destino), vecino))

        frontera_max = max(frontera_max, len(frontera))

    return armar_resultado(vecinos, padres, destino, encontrado, expandidos,
                           frontera_max, inicio, orden_expansion)


# ---------------------------------------------------------------------------
# Prueba rápida: compara UCS, A* y Greedy
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from mapa import cargar_grafo, pares_origen_destino
    from fase1 import ucs

    vecinos, coords = cargar_grafo()
    pares = pares_origen_destino(coords)

    # Para UCS usamos una función "envoltura" (lambda) que ignora coords y heurística,
    # así podemos correr todos los algoritmos con el mismo ciclo.
    algoritmos = [
        ("UCS", lambda o, d: ucs(vecinos, o, d)),
        ("A*-h1", lambda o, d: a_estrella(vecinos, coords, o, d, h1_euclidiana)),
        ("A*-h2", lambda o, d: a_estrella(vecinos, coords, o, d, h2_haversine)),
        ("A*-h3", lambda o, d: a_estrella(vecinos, coords, o, d, h3_personalizada)),
        ("Gr-h2", lambda o, d: greedy(vecinos, coords, o, d, h2_haversine)),
    ]

    print(f"{'Alg':6s} {'Destino':28s} {'Metros':>8s} {'Saltos':>7s} {'Expand.':>8s} {'Front.max':>9s} {'ms':>7s}")
    for nombre, origen, destino in pares:
        for nombre_alg, funcion in algoritmos:
            r = funcion(origen, destino)
            print(f"{nombre_alg:6s} {nombre:28s} {r['metros']:8.0f} {r['saltos']:7d} {r['expandidos']:8d} "
                  f"{r['frontera_max']:9d} {r['tiempo_ms']:7.2f}")
        print()
