"""
Gráficas de la Fase 3:
    1) Convergencia de SA y AG (cómo baja la distancia iteración tras iteración).
    2) Experimento de temperatura inicial T0 del SA (diversidad de soluciones).

Guarda las imágenes en imagenes/ y muestra una tabla con el experimento de T0.
Se corre desde la raíz del proyecto:
    python src/graficas_fase3.py
"""

import statistics
import matplotlib.pyplot as plt

from fase3 import (preparar_problema, simulated_annealing, algoritmo_genetico,
                   SA_ALFA, SA_T_MIN, AG_POBLACION)

# Colores (paleta accesible para daltonismo)
AZUL = "#2a78d6"      # SA / "mejor"
NARANJA = "#eb6834"   # AG
GRIS = "#9a9a9a"      # series secundarias ("actual" / "promedio")
# Tonos de un mismo azul, de claro a oscuro, para las T0 (de menor a mayor)
AZULES_T0 = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]


def grafica_convergencia(matriz):
    """Tres paneles: SA sola, AG sola y ambas comparadas por número de evaluaciones."""
    sa = simulated_annealing(matriz, semilla=1)
    ag = algoritmo_genetico(matriz, semilla=1)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))

    # Panel 1: SA. La ruta "actual" sube y baja (acepta rutas peores);
    # la "mejor" solo puede bajar.
    ax1.plot(sa["historial_actual"], color=GRIS, linewidth=1, label="Ruta actual")
    ax1.plot(sa["historial_mejor"], color=AZUL, linewidth=2, label="Mejor encontrada")
    ax1.set_title(f"Simulated Annealing (final: {sa['metros']:.0f} m)")
    ax1.set_xlabel("Iteración")
    ax1.set_ylabel("Distancia total (m)")
    ax1.legend()

    # Panel 2: AG. El promedio muestra qué tan diversa es la población.
    ax2.plot(ag["historial_promedio"], color=GRIS, linewidth=1, label="Promedio de la población")
    ax2.plot(ag["historial_mejor"], color=NARANJA, linewidth=2, label="Mejor de la generación")
    ax2.set_title(f"Algoritmo Genético (final: {ag['metros']:.0f} m)")
    ax2.set_xlabel("Generación")
    ax2.set_ylabel("Distancia total (m)")
    ax2.legend()

    # Panel 3: comparación justa. SA evalúa 1 ruta por iteración y AG evalúa
    # toda la población (100 rutas) por generación, así que usamos "rutas evaluadas"
    # como eje X común.
    evals_sa = list(range(len(sa["historial_mejor"])))
    evals_ag = [g * AG_POBLACION for g in range(len(ag["historial_mejor"]))]
    ax3.plot(evals_sa, sa["historial_mejor"], color=AZUL, linewidth=2, label="SA")
    ax3.plot(evals_ag, ag["historial_mejor"], color=NARANJA, linewidth=2, label="AG")
    ax3.set_title("SA vs AG (mejor distancia)")
    ax3.set_xlabel("Rutas evaluadas")
    ax3.set_ylabel("Distancia total (m)")
    ax3.legend()

    for ax in (ax1, ax2, ax3):
        ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig("imagenes/convergencia_sa_ag.png", dpi=120)
    plt.close(fig)
    print("Guardada: imagenes/convergencia_sa_ag.png")


def experimento_t0(matriz):
    """Corre SA con distintas T0 y mide la diversidad de las soluciones.

    Para que la comparación sea justa, TODAS las T0 hacen el mismo número de
    iteraciones: ajustamos alfa para que T baje de T0 hasta T_MIN en N pasos.
        T0 * alfa^N = T_MIN   ->   alfa = (T_MIN / T0) ^ (1 / N)
    """
    valores_t0 = [10, 100, 1000, 10000]
    corridas = 10
    iteraciones = 9206   # las mismas que hace nuestro SA con T0 = 1000

    print(f"\nExperimento de T0 ({corridas} corridas por valor, {iteraciones} iteraciones cada una):")
    print(f"{'T0':>6s} {'Mejor':>8s} {'Promedio':>9s} {'Peor':>8s} {'Desv.est.':>10s} {'Rutas distintas':>16s}")

    historiales = []   # historial "actual" de una corrida por T0, para graficar
    for t0 in valores_t0:
        alfa = (SA_T_MIN / t0) ** (1 / iteraciones)
        distancias = []
        rutas_finales = set()
        for semilla in range(corridas):
            r = simulated_annealing(matriz, t0=t0, alfa=alfa, semilla=semilla)
            distancias.append(r["metros"])
            rutas_finales.add(tuple(r["ruta"]))   # tuple porque las listas no se pueden meter a un set
            if semilla == 0:
                historiales.append(r["historial_actual"])

        print(f"{t0:6d} {min(distancias):8.0f} {statistics.mean(distancias):9.0f} "
              f"{max(distancias):8.0f} {statistics.stdev(distancias):10.0f} "
              f"{len(rutas_finales):>10d} de {corridas}")

    # Gráfica: la ruta "actual" de SA con cada T0. Con T0 alta la línea sube y
    # baja mucho al principio (explora rutas muy distintas); con T0 baja casi
    # no se mueve (solo acepta mejoras desde el inicio).
    fig, paneles = plt.subplots(1, len(valores_t0), figsize=(18, 4.5), sharey=True)
    for ax, t0, historial, color in zip(paneles, valores_t0, historiales, AZULES_T0):
        ax.plot(historial, color=color, linewidth=1)
        ax.set_title(f"T0 = {t0}")
        ax.set_xlabel("Iteración")
        ax.grid(alpha=0.3)
    paneles[0].set_ylabel("Distancia de la ruta actual (m)")
    fig.suptitle("SA: exploración según la temperatura inicial (semilla 0)")
    fig.tight_layout()
    fig.savefig("imagenes/experimento_t0.png", dpi=120)
    plt.close(fig)
    print("Guardada: imagenes/experimento_t0.png")


def main():
    _puntos, matriz, _coords, _vecinos = preparar_problema()
    grafica_convergencia(matriz)
    experimento_t0(matriz)


if __name__ == "__main__":
    main()
