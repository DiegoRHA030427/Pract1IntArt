"""
Validación empírica de admisibilidad de las heurísticas (Fase 2).

Una heurística h es ADMISIBLE si nunca sobreestima:  h(n) <= h*(n)  para todo nodo n,
donde h*(n) = costo real (metros) del camino más corto de n al destino.

Para cada destino calculamos h*(n) de TODOS los nodos que pueden llegar a él,
y contamos cuántas veces cada heurística se pasa del valor real.

Se corre desde la raíz del proyecto:
    python src/admisibilidad.py
"""

import heapq

from mapa import cargar_grafo, pares_origen_destino
from fase2 import h1_euclidiana, h2_haversine, h3_personalizada


def invertir_grafo(vecinos):
    """Voltea el sentido de todas las calles: si había u -> v, ahora hay v -> u.

    Truco: la distancia más corta de CUALQUIER nodo n hacia el destino es igual
    a la distancia del destino hacia n en el grafo invertido. Así, con UNA sola
    búsqueda desde el destino obtenemos h*(n) para todos los nodos a la vez.
    """
    invertido = {nodo: [] for nodo in vecinos}
    for u in vecinos:
        for v, metros in vecinos[u]:
            invertido[v].append((u, metros))
    return invertido


def distancias_desde(vecinos, origen):
    """UCS/Dijkstra SIN destino: regresa {nodo: metros mínimos desde origen}.

    Es el mismo algoritmo que ucs() de la Fase 1, pero no se detiene al encontrar
    un destino: sigue hasta vaciar la cola para tener la distancia a todos.
    """
    distancia = {origen: 0.0}
    visitados = set()
    frontera = [(0.0, origen)]
    while frontera:
        costo, actual = heapq.heappop(frontera)
        if actual in visitados:
            continue
        visitados.add(actual)
        for vecino, metros in vecinos[actual]:
            nuevo = costo + metros
            if vecino not in distancia or nuevo < distancia[vecino]:
                distancia[vecino] = nuevo
                heapq.heappush(frontera, (nuevo, vecino))
    return distancia


def main():
    vecinos, coords = cargar_grafo()
    invertido = invertir_grafo(vecinos)
    pares = pares_origen_destino(coords)

    # Además de h1, h2 y h3 probamos h2 multiplicada por k > 1
    # para responder: "si multiplicas h por k > 1, ¿sigue siendo admisible?"
    heuristicas = [
        ("h1 Euclidiana", h1_euclidiana),
        ("h2 Haversine", h2_haversine),
        ("h3 Personalizada", h3_personalizada),
        ("h2 x 1.2", lambda c, n, d: 1.2 * h2_haversine(c, n, d)),
        ("h2 x 1.5", lambda c, n, d: 1.5 * h2_haversine(c, n, d)),
        ("h2 x 2.0", lambda c, n, d: 2.0 * h2_haversine(c, n, d)),
    ]

    # Acumuladores por heurística, juntando los 6 destinos.
    revisados = {nombre: 0 for nombre, _h in heuristicas}
    sobreestima = {nombre: 0 for nombre, _h in heuristicas}
    peor_exceso = {nombre: 0.0 for nombre, _h in heuristicas}
    suma_proporcion = {nombre: 0.0 for nombre, _h in heuristicas}

    for _nombre_destino, _origen, destino in pares:
        h_real = distancias_desde(invertido, destino)   # h*(n) para cada nodo n
        for nodo, real in h_real.items():
            if nodo == destino:
                continue   # en el destino h* = 0 y todas dan 0; no aporta nada
            for nombre, h in heuristicas:
                estimado = h(coords, nodo, destino)
                revisados[nombre] += 1
                suma_proporcion[nombre] += estimado / real
                # Tolerancia de 1 mm por redondeos de punto flotante.
                if estimado > real + 0.001:
                    sobreestima[nombre] += 1
                    peor_exceso[nombre] = max(peor_exceso[nombre], estimado - real)

    print(f"{'Heurística':18s} {'Revisados':>10s} {'Sobreestima':>12s} {'%':>7s} "
          f"{'Peor exceso (m)':>16s} {'h/h* prom.':>11s}  Admisible")
    for nombre, _h in heuristicas:
        porcentaje = 100 * sobreestima[nombre] / revisados[nombre]
        promedio = suma_proporcion[nombre] / revisados[nombre]
        admisible = "SÍ" if sobreestima[nombre] == 0 else "NO"
        print(f"{nombre:18s} {revisados[nombre]:10d} {sobreestima[nombre]:12d} {porcentaje:6.2f}% "
              f"{peor_exceso[nombre]:16.1f} {promedio:11.3f}  {admisible}")


if __name__ == "__main__":
    main()
