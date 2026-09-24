"""
Fase 1: Búsqueda a ciegas (sin usar coordenadas).

Todas las búsquedas reciben:
    vecinos = {nodo: [(vecino, metros), ...]}   (ver mapa.py)
    origen, destino = ids de nodo

Y regresan un diccionario con el MISMO formato (así las tablas comparativas salen parejas):
    "camino":          lista de nodos de origen a destino, o None si no se puede llegar
    "metros":          longitud total del camino en metros
    "saltos":          número de calles recorridas (len(camino) - 1)
    "expandidos":      cuántos nodos se sacaron de la frontera para revisarlos
    "frontera_max":    tamaño máximo que alcanzó la frontera
    "tiempo_ms":       tiempo de ejecución en milisegundos
    "orden_expansion": lista de nodos en el orden en que se expandieron (para los snapshots)
"""

import time
import heapq
from collections import deque


# ---------------------------------------------------------------------------
# Funciones de apoyo (las comparten BFS, DFS y UCS)
# ---------------------------------------------------------------------------

def reconstruir_camino(padres, destino):
    """Recorre el diccionario de padres hacia atrás desde el destino hasta el origen."""
    camino = [destino]
    while padres[camino[-1]] is not None:   # el origen es el único con padre None
        camino.append(padres[camino[-1]])
    camino.reverse()                        # lo armamos al revés, lo volteamos
    return camino


def metros_del_camino(vecinos, camino):
    """Suma la longitud de cada calle del camino."""
    total = 0.0
    for i in range(len(camino) - 1):
        u, v = camino[i], camino[i + 1]
        for vecino, metros in vecinos[u]:
            if vecino == v:
                total += metros
                break
    return total


def armar_resultado(vecinos, padres, destino, encontrado, expandidos,
                    frontera_max, inicio, orden_expansion):
    """Arma el diccionario de salida común a todas las búsquedas."""
    tiempo_ms = (time.perf_counter() - inicio) * 1000
    if encontrado:
        camino = reconstruir_camino(padres, destino)
        metros = metros_del_camino(vecinos, camino)
        saltos = len(camino) - 1
    else:
        camino, metros, saltos = None, 0.0, 0
    return {
        "camino": camino,
        "metros": metros,
        "saltos": saltos,
        "expandidos": expandidos,
        "frontera_max": frontera_max,
        "tiempo_ms": tiempo_ms,
        "orden_expansion": orden_expansion,
    }


# ---------------------------------------------------------------------------
# BFS: Búsqueda en Anchura
# ---------------------------------------------------------------------------

def bfs(vecinos, origen, destino):
    """Encuentra el camino con MENOS SALTOS (calles), sin importar los metros.

    Usa una cola FIFO: primero revisa todos los nodos a 1 salto, luego a 2, etc.
    Por eso el primer camino que llega al destino es el de menos saltos.
    """
    inicio = time.perf_counter()

    # deque permite sacar del frente en O(1); con una lista normal (pop(0)) sería lento.
    frontera = deque([origen])

    # padres[n] = de qué nodo llegamos a n. También sirve como "visitados":
    # si un nodo ya está en padres, ya fue descubierto y no lo volvemos a meter.
    padres = {origen: None}

    expandidos = 0
    frontera_max = 1
    orden_expansion = []
    encontrado = False

    while frontera:
        actual = frontera.popleft()         # FIFO: sale el más antiguo
        expandidos += 1
        orden_expansion.append(actual)

        # Revisamos la meta al SACAR el nodo (igual que en UCS), para que
        # el conteo de "expandidos" sea comparable entre los tres algoritmos.
        if actual == destino:
            encontrado = True
            break

        for vecino, _metros in vecinos[actual]:   # BFS ignora los metros
            if vecino not in padres:
                padres[vecino] = actual
                frontera.append(vecino)

        frontera_max = max(frontera_max, len(frontera))

    return armar_resultado(vecinos, padres, destino, encontrado, expandidos,
                           frontera_max, inicio, orden_expansion)


# ---------------------------------------------------------------------------
# DFS: Búsqueda en Profundidad (versión iterativa)
# ---------------------------------------------------------------------------

def dfs(vecinos, origen, destino):
    """Encuentra ALGÚN camino, metiéndose lo más profundo posible antes de regresar.

    Usa una pila LIFO (una lista de Python con append/pop): el último nodo que
    entra es el primero que se revisa. NO garantiza el camino más corto.

    Es iterativa (no recursiva) porque con miles de nodos la recursión podría
    rebasar el límite de llamadas de Python (RecursionError).
    """
    inicio = time.perf_counter()

    # En la pila guardamos parejas (nodo, de_qué_nodo_venimos).
    # Guardamos el padre junto al nodo porque un nodo puede entrar varias veces
    # a la pila desde distintos vecinos; el padre válido es el de la vez que se expande.
    pila = [(origen, None)]

    # visitados: nodos que YA se expandieron. Es obligatorio en un mapa de calles,
    # porque hay ciclos (dar vuelta a la manzana) y sin esto DFS daría vueltas infinitas.
    visitados = set()
    padres = {}

    expandidos = 0
    frontera_max = 1
    orden_expansion = []
    encontrado = False

    while pila:
        actual, padre = pila.pop()          # LIFO: sale el más reciente

        if actual in visitados:
            continue                        # ya lo expandimos por otro camino, lo saltamos
        visitados.add(actual)
        padres[actual] = padre
        expandidos += 1
        orden_expansion.append(actual)

        if actual == destino:
            encontrado = True
            break

        for vecino, _metros in vecinos[actual]:   # DFS también ignora los metros
            if vecino not in visitados:
                pila.append((vecino, actual))

        frontera_max = max(frontera_max, len(pila))

    return armar_resultado(vecinos, padres, destino, encontrado, expandidos,
                           frontera_max, inicio, orden_expansion)


# ---------------------------------------------------------------------------
# UCS: Búsqueda de Costo Uniforme
# ---------------------------------------------------------------------------

def ucs(vecinos, origen, destino):
    """Encuentra el camino de MENOR DISTANCIA en metros.

    Usa una cola de prioridad (heapq): siempre expande el nodo con el menor
    costo acumulado g(n) desde el origen. Cuando el destino sale de la cola,
    ya no puede existir un camino más barato, porque todos los que quedan
    en la cola cuestan igual o más (y las calles nunca miden negativo).
    """
    inicio = time.perf_counter()

    # heapq trabaja sobre una lista normal y siempre deja el MENOR elemento al frente.
    # Guardamos tuplas (costo, nodo): Python compara primero el costo.
    frontera = [(0.0, origen)]

    # mejor_costo[n] = el menor costo con el que hemos llegado a n hasta ahora.
    mejor_costo = {origen: 0.0}
    padres = {origen: None}
    visitados = set()   # nodos ya expandidos: su costo es definitivo

    expandidos = 0
    frontera_max = 1
    orden_expansion = []
    encontrado = False

    while frontera:
        costo, actual = heapq.heappop(frontera)   # sale el de menor costo

        # Un nodo puede estar varias veces en la cola con costos distintos
        # (si después encontramos un camino más barato). Solo vale la primera
        # vez que sale, que es la más barata; las demás copias se ignoran.
        if actual in visitados:
            continue
        visitados.add(actual)
        expandidos += 1
        orden_expansion.append(actual)

        if actual == destino:
            encontrado = True
            break

        for vecino, metros in vecinos[actual]:
            nuevo_costo = costo + metros
            # Solo lo metemos si es la primera vez que lo vemos o si encontramos
            # un camino más barato que el que teníamos.
            if vecino not in mejor_costo or nuevo_costo < mejor_costo[vecino]:
                mejor_costo[vecino] = nuevo_costo
                padres[vecino] = actual
                heapq.heappush(frontera, (nuevo_costo, vecino))

        frontera_max = max(frontera_max, len(frontera))

    return armar_resultado(vecinos, padres, destino, encontrado, expandidos,
                           frontera_max, inicio, orden_expansion)


# ---------------------------------------------------------------------------
# Verificar accesibilidad
# ---------------------------------------------------------------------------

def nodos_alcanzables(vecinos, origen):
    """Regresa el conjunto de TODOS los nodos a los que se puede llegar desde origen.

    Es un BFS sin destino: sigue hasta que la cola se vacía, o sea, hasta
    agotar todo lo alcanzable. Como el grafo es dirigido (calles de un sentido),
    que A llegue a B no significa que B llegue a A.
    """
    alcanzados = {origen}
    cola = deque([origen])
    while cola:
        actual = cola.popleft()
        for vecino, _metros in vecinos[actual]:
            if vecino not in alcanzados:
                alcanzados.add(vecino)
                cola.append(vecino)
    return alcanzados


def verificar_entregas(vecinos, deposito, destinos):
    """Para cada destino dice si es alcanzable desde el depósito: {destino: True/False}.

    Calculamos los alcanzables UNA sola vez y luego cada consulta es
    una búsqueda en un set (instantánea), en vez de correr un BFS por destino.
    """
    alcanzables = nodos_alcanzables(vecinos, deposito)
    return {destino: (destino in alcanzables) for destino in destinos}


# ---------------------------------------------------------------------------
# Prueba rápida: corre BFS en los pares origen-destino
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from mapa import cargar_grafo, pares_origen_destino, nodo_mas_cercano, DEPOSITO

    vecinos, coords = cargar_grafo()
    pares = pares_origen_destino(coords)

    # Lista de (nombre, función) para correr todos los algoritmos con el mismo código.
    algoritmos = [("BFS", bfs), ("DFS", dfs), ("UCS", ucs)]

    print(f"{'Alg':4s} {'Destino':28s} {'Metros':>8s} {'Saltos':>7s} {'Expand.':>8s} {'Front.max':>9s} {'ms':>7s}")
    for nombre, origen, destino in pares:
        for nombre_alg, funcion in algoritmos:
            r = funcion(vecinos, origen, destino)
            if r["camino"] is None:
                print(f"{nombre_alg:4s} {nombre:28s} INALCANZABLE (expandidos: {r['expandidos']})")
            else:
                print(f"{nombre_alg:4s} {nombre:28s} {r['metros']:8.0f} {r['saltos']:7d} {r['expandidos']:8d} "
                      f"{r['frontera_max']:9d} {r['tiempo_ms']:7.2f}")
        print()

    # --- Verificación de accesibilidad desde el depósito ---
    deposito, _ = nodo_mas_cercano(coords, DEPOSITO[0], DEPOSITO[1])
    alcanzables = nodos_alcanzables(vecinos, deposito)
    no_alcanzables = [n for n in vecinos if n not in alcanzables]
    print("Accesibilidad desde el depósito:")
    print("  Alcanzables:", len(alcanzables), "de", len(vecinos), "nodos")
    print("  NO alcanzables:", len(no_alcanzables))

    # Los destinos de los pares (lugares conocidos) deben ser todos alcanzables.
    destinos = [destino for _nombre, _origen, destino in pares]
    resultado = verificar_entregas(vecinos, deposito, destinos)
    for nombre, _origen, destino in pares:
        print(f"  {nombre:28s} alcanzable: {resultado[destino]}")

    # Ejemplo de un destino inalcanzable: UCS debe regresar camino None.
    if no_alcanzables:
        ejemplo = no_alcanzables[0]
        r = ucs(vecinos, deposito, ejemplo)
        print(f"\n  Ejemplo inalcanzable: nodo {ejemplo} en {coords[ejemplo]}")
        print(f"  UCS -> camino: {r['camino']}, expandidos: {r['expandidos']}")
