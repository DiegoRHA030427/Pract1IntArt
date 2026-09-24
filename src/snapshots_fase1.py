"""
Snapshots de la Fase 1: muestra cómo avanza la frontera de BFS, DFS y UCS.

Genera una imagen por algoritmo en imagenes/, cada una con 3 paneles
(25%, 50% y 100% de la búsqueda). Se corre desde la raíz del proyecto:
    python src/snapshots_fase1.py

Cómo se reconstruye cada momento de la búsqueda a partir de "orden_expansion":
    - Expandidos en el paso k = los primeros k nodos de orden_expansion.
    - Frontera en el paso k   = vecinos de esos nodos que todavía no se expanden
      (son los nodos "descubiertos" que esperan su turno).
"""

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

from mapa import cargar_grafo, pares_origen_destino
from fase1 import bfs, dfs, ucs

DESTINO_ELEGIDO = "La Raza"      # el destino más lejano en metros de nuestros pares
PORCENTAJES = [0.25, 0.50, 1.00]  # momentos de la búsqueda que se dibujan


def dibujar_calles(ax, vecinos, coords):
    """Dibuja todas las calles en gris claro como fondo del mapa.

    LineCollection dibuja miles de segmentos de una sola vez; hacer un plt.plot
    por cada calle (11 mil) sería muy lento.
    """
    segmentos = []
    for u in vecinos:
        for v, _metros in vecinos[u]:
            lat1, lon1 = coords[u]
            lat2, lon2 = coords[v]
            # En un mapa, el eje X es la longitud y el eje Y es la latitud.
            segmentos.append([(lon1, lat1), (lon2, lat2)])
    ax.add_collection(LineCollection(segmentos, colors="lightgray", linewidths=0.4))


def dibujar_nodos(ax, nodos, coords, color, tamano, etiqueta):
    """Dibuja un conjunto de nodos como puntos del color indicado."""
    xs = [coords[n][1] for n in nodos]   # longitudes
    ys = [coords[n][0] for n in nodos]   # latitudes
    ax.scatter(xs, ys, s=tamano, c=color, label=etiqueta, zorder=3)


def snapshot(ax, vecinos, coords, resultado, origen, destino, porcentaje):
    """Dibuja un panel: calles, expandidos y frontera en un momento de la búsqueda."""
    orden = resultado["orden_expansion"]
    k = max(1, int(len(orden) * porcentaje))
    expandidos = set(orden[:k])

    # Frontera: vecinos de los expandidos que aún no se expanden.
    frontera = set()
    for n in expandidos:
        for vecino, _metros in vecinos[n]:
            if vecino not in expandidos:
                frontera.add(vecino)

    dibujar_calles(ax, vecinos, coords)
    dibujar_nodos(ax, expandidos, coords, "tab:blue", 2, "Expandidos")
    dibujar_nodos(ax, frontera, coords, "tab:orange", 6, "Frontera")

    # Al 100% también dibujamos el camino encontrado.
    if porcentaje == 1.00 and resultado["camino"] is not None:
        xs = [coords[n][1] for n in resultado["camino"]]
        ys = [coords[n][0] for n in resultado["camino"]]
        ax.plot(xs, ys, color="red", linewidth=2, label="Camino", zorder=4)

    dibujar_nodos(ax, [origen], coords, "green", 60, "Depósito")
    dibujar_nodos(ax, [destino], coords, "black", 60, "Destino")

    ax.set_title(f"{int(porcentaje * 100)}%: {k} expandidos, frontera {len(frontera)}")
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def main():
    vecinos, coords = cargar_grafo()

    # Buscamos el par del destino elegido.
    origen = destino = None
    for nombre, o, d in pares_origen_destino(coords):
        if nombre == DESTINO_ELEGIDO:
            origen, destino = o, d

    algoritmos = [("BFS", bfs), ("DFS", dfs), ("UCS", ucs)]
    for nombre_alg, funcion in algoritmos:
        resultado = funcion(vecinos, origen, destino)

        # 1 fila con 3 paneles (uno por porcentaje).
        fig, paneles = plt.subplots(1, 3, figsize=(18, 6.5))
        for ax, porcentaje in zip(paneles, PORCENTAJES):
            snapshot(ax, vecinos, coords, resultado, origen, destino, porcentaje)

        paneles[2].legend(loc="lower right", fontsize=8)
        fig.suptitle(f"{nombre_alg}: Depósito -> {DESTINO_ELEGIDO}  "
                     f"({resultado['metros']:.0f} m, {resultado['saltos']} saltos)", fontsize=14)
        fig.tight_layout()

        archivo = f"imagenes/snapshot_{nombre_alg.lower()}.png"
        fig.savefig(archivo, dpi=120)
        plt.close(fig)   # liberamos memoria antes de la siguiente figura
        print("Guardada:", archivo)


if __name__ == "__main__":
    main()
