"""
Pruebas unitarias de la Fase 3 (TSP con Simulated Annealing y Algoritmo Genético).

Usamos una matriz PEQUEÑA hecha a mano en lugar del mapa real.
Depósito y 4 entregas sobre una línea recta, a 100 m entre sí:

    0 ---100--- 1 ---100--- 2 ---100--- 3 ---100--- 4
  (depósito)

La mejor ruta cerrada es ir hasta el final y regresar: 0-1-2-3-4-0 (o al revés),
que mide 100 + 100 + 100 + 100 + 400 = 800 m. Cualquier otro orden da más.
"""

import random

from fase3 import (distancia_ruta, vecino_2opt, cruza_ox, mutacion_intercambio,
                   simulated_annealing, algoritmo_genetico, elegir_entregas)

# matriz[i][j] = 100 * |i - j|   (distancia sobre la línea)
MATRIZ_LINEA = [[100 * abs(i - j) for j in range(5)] for i in range(5)]
OPTIMO = 800


def es_permutacion(ruta, n):
    """True si la ruta tiene cada entrega de 1 a n exactamente una vez."""
    return sorted(ruta) == list(range(1, n + 1))


# --- Distancia de una ruta ---

def test_distancia_ruta_incluye_salida_y_regreso():
    assert distancia_ruta([1, 2, 3, 4], MATRIZ_LINEA) == 800
    # 0->1 (100) + 1->3 (200) + 3->2 (100) + 2->4 (200) + 4->0 (400) = 1000
    assert distancia_ruta([1, 3, 2, 4], MATRIZ_LINEA) == 1000


def test_distancia_ruta_respeta_matriz_asimetrica():
    # Ir de 0 a 1 cuesta 10, pero de 1 a 0 cuesta 50 (como una calle de un sentido).
    matriz = [[0, 10],
              [50, 0]]
    assert distancia_ruta([1], matriz) == 60


# --- Operadores ---

def test_2opt_genera_permutacion_valida():
    random.seed(0)
    ruta = [1, 2, 3, 4, 5, 6]
    for _ in range(100):
        assert es_permutacion(vecino_2opt(ruta), 6)


def test_2opt_invierte_un_tramo():
    random.seed(0)
    ruta = [1, 2, 3, 4, 5, 6]
    nueva = vecino_2opt(ruta)
    # Las posiciones que cambiaron deben formar un tramo invertido.
    cambiadas = [k for k in range(6) if nueva[k] != ruta[k]]
    i, j = cambiadas[0], cambiadas[-1]
    assert nueva[i:j + 1] == ruta[i:j + 1][::-1]


def test_cruza_ox_genera_permutacion_valida():
    random.seed(0)
    padre1 = [1, 2, 3, 4, 5, 6, 7]
    padre2 = [5, 7, 6, 1, 3, 2, 4]
    for _ in range(100):
        assert es_permutacion(cruza_ox(padre1, padre2), 7)


def test_mutacion_intercambia_exactamente_dos():
    random.seed(0)
    ruta = [1, 2, 3, 4, 5]
    mutada = mutacion_intercambio(ruta)
    assert es_permutacion(mutada, 5)
    assert sum(1 for k in range(5) if mutada[k] != ruta[k]) == 2
    assert ruta == [1, 2, 3, 4, 5]   # la original no se modifica


# --- Algoritmos completos ---

def test_sa_encuentra_el_optimo_en_la_linea():
    r = simulated_annealing(MATRIZ_LINEA, semilla=0)
    assert es_permutacion(r["ruta"], 4)
    assert r["metros"] == OPTIMO


def test_ag_encuentra_el_optimo_en_la_linea():
    r = algoritmo_genetico(MATRIZ_LINEA, semilla=0)
    assert es_permutacion(r["ruta"], 4)
    assert r["metros"] == OPTIMO


def test_historial_mejor_nunca_empeora():
    # La "mejor distancia encontrada" solo puede bajar o quedarse igual.
    for r in (simulated_annealing(MATRIZ_LINEA, semilla=0),
              algoritmo_genetico(MATRIZ_LINEA, semilla=0)):
        h = r["historial_mejor"]
        assert all(h[k + 1] <= h[k] for k in range(len(h) - 1))


# --- Elección de entregas ---

def test_elegir_entregas_solo_ida_y_vuelta():
    # D <-> A (se puede ir y regresar);  D -> B (solo ida);  C -> D (solo regreso)
    grafo = {
        "D": [("A", 1), ("B", 1)],
        "A": [("D", 1)],
        "B": [],
        "C": [("D", 1)],
    }
    assert elegir_entregas(grafo, "D", 1, semilla=0) == ["A"]
