"""
Mapa de la ruta de entregas de la Fase 3.

Dibuja sobre las calles el recorrido completo del camión (depósito -> 15 entregas
-> depósito) en dos paneles:
    - Izquierda: visitando las entregas en el orden en que salieron (1, 2, ..., 15).
    - Derecha:   el orden que encontró Simulated Annealing.

Se corre desde la raíz del proyecto:
    python src/ruta_entregas_fase3.py
"""

import matplotlib.pyplot as plt

from fase2 import a_estrella, h2_haversine
from fase3 import preparar_problema, simulated_annealing, distancia_ruta
from snapshots_fase1 import dibujar_calles   # reutilizamos el fondo de calles de la Fase 1

AZUL = "#2a78d6"
NARANJA = "#eb6834"


def dibujar_recorrido(ax, vecinos, coords, puntos, ruta, color, titulo):
    """Dibuja el recorrido calle por calle y numera las entregas en orden de visita."""
    dibujar_calles(ax, vecinos, coords)

    # Orden completo de puntos: depósito (0) -> entregas -> depósito (0).
    orden = [0] + ruta + [0]
    for k in range(len(orden) - 1):
        # A* nos da las calles exactas entre dos puntos consecutivos.
        r = a_estrella(vecinos, coords, puntos[orden[k]], puntos[orden[k + 1]], h2_haversine)
        xs = [coords[n][1] for n in r["camino"]]   # longitud
        ys = [coords[n][0] for n in r["camino"]]   # latitud
        ax.plot(xs, ys, color=color, linewidth=1.8, alpha=0.8)

    # Depósito en verde; cada entrega con su número de visita (1ª, 2ª, ...).
    lat, lon = coords[puntos[0]]
    ax.scatter([lon], [lat], s=150, c="green", marker="s", zorder=5, label="Depósito")
    for visita, entrega in enumerate(ruta, start=1):
        lat, lon = coords[puntos[entrega]]
        ax.scatter([lon], [lat], s=160, c="white", edgecolors="black", zorder=5)
        ax.text(lon, lat, str(visita), ha="center", va="center", fontsize=7, zorder=6)

    ax.set_title(titulo)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(loc="lower right", fontsize=8)


def main():
    puntos, matriz, coords, vecinos = preparar_problema()

    ruta_inicial = list(range(1, len(puntos)))
    sa = simulated_annealing(matriz, semilla=1)   # semilla 1: la mejor de nuestras 5 corridas

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    dibujar_recorrido(ax1, vecinos, coords, puntos, ruta_inicial, NARANJA,
                      f"Orden 1..15 sin optimizar: {distancia_ruta(ruta_inicial, matriz):.0f} m")
    dibujar_recorrido(ax2, vecinos, coords, puntos, sa["ruta"], AZUL,
                      f"Orden encontrado por SA: {sa['metros']:.0f} m")
    fig.suptitle("Fase 3: recorrido del camión (los números indican el orden de visita)")
    fig.tight_layout(rect=[0, 0, 1, 0.96])   # deja espacio arriba para el título general
    fig.savefig("imagenes/ruta_entregas_sa.png", dpi=120)
    plt.close(fig)
    print("Guardada: imagenes/ruta_entregas_sa.png")


if __name__ == "__main__":
    main()
