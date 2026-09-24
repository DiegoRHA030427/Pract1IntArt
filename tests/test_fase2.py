"""
Pruebas unitarias de la Fase 2 (heurísticas, A* y Greedy).

Usamos un grafo pequeño hecho a mano, con coordenadas reales cerca de CDMX.
Las posiciones se definen en METROS respecto a un punto base y se convierten
a (lat, lon), para que las distancias sean fáciles de razonar.

Mapa de prueba (en metros; el destino D está 1000 m al este de O):

        E (600, 600)
        ^           \\
        | 600        \\ 800
        |             v
    O ---600---> A    D (1000, 0)
    |                 ^
    | 400             |
    v                 |
    C (0, -400) --1100+

    F (2000, 2000): nodo aislado, nadie llega a él.

Caminos de O a D:
    - O-A-E-D = 600 + 600 + 800 = 2000 m   <- Greedy cae aquí (A "parece" más cerca)
    - O-C-D   = 400 + 1100      = 1500 m   <- el óptimo, el que debe dar A*
"""

import math

from fase1 import ucs
from fase2 import (h1_euclidiana, h2_haversine, h3_personalizada,
                   a_estrella, greedy, PENALIZACION_GIRO)

LAT_BASE, LON_BASE = 19.45, -99.13
METROS_POR_GRADO = 111195   # metros que mide 1 grado de latitud (R_TIERRA * pi / 180)


def punto(x_metros, y_metros):
    """Convierte (x, y) en metros desde el punto base a (lat, lon)."""
    lat = LAT_BASE + y_metros / METROS_POR_GRADO
    lon = LON_BASE + x_metros / (METROS_POR_GRADO * math.cos(math.radians(LAT_BASE)))
    return (lat, lon)


COORDS = {
    "O": punto(0, 0),
    "A": punto(600, 0),
    "E": punto(600, 600),
    "C": punto(0, -400),
    "D": punto(1000, 0),
    "F": punto(2000, 2000),
}

GRAFO = {
    "O": [("A", 600), ("C", 400)],
    "A": [("E", 600)],
    "E": [("D", 800)],
    "C": [("D", 1100)],
    "D": [],
    "F": [],
}


# --- Heurísticas ---

def test_heuristicas_miden_metros():
    # D está a 1000 m de O: ambas deben dar ~1000 m (tolerancia de 1 m).
    assert abs(h1_euclidiana(COORDS, "O", "D") - 1000) < 1
    assert abs(h2_haversine(COORDS, "O", "D") - 1000) < 1


def test_h1_y_h2_casi_iguales_en_distancias_cortas():
    # En pocos km la curvatura de la Tierra casi no importa.
    assert abs(h1_euclidiana(COORDS, "C", "D") - h2_haversine(COORDS, "C", "D")) < 0.01


def test_heuristicas_valen_cero_en_el_destino():
    for h in (h1_euclidiana, h2_haversine, h3_personalizada):
        assert h(COORDS, "D", "D") == 0


def test_h3_sin_giro_cuando_esta_alineado():
    # De O a D es línea recta al este (0°): no hay giro, h3 = h2.
    assert h3_personalizada(COORDS, "O", "D") == h2_haversine(COORDS, "O", "D")


def test_h3_penaliza_cuando_esta_en_diagonal():
    # De C a D el ángulo es ~22° (más de 20°): cuenta 1 giro, h3 = h2 + penalización.
    esperado = h2_haversine(COORDS, "C", "D") + PENALIZACION_GIRO
    assert abs(h3_personalizada(COORDS, "C", "D") - esperado) < 1e-9


# --- A* y Greedy ---

def test_a_estrella_encuentra_el_optimo():
    for h in (h1_euclidiana, h2_haversine):
        r = a_estrella(GRAFO, COORDS, "O", "D", h)
        assert r["camino"] == ["O", "C", "D"]
        assert r["metros"] == 1500


def test_a_estrella_da_lo_mismo_que_ucs():
    assert a_estrella(GRAFO, COORDS, "O", "D", h2_haversine)["metros"] == ucs(GRAFO, "O", "D")["metros"]


def test_greedy_falla_en_este_grafo():
    # Greedy se va por A porque "parece" más cerca de D, y termina en un camino más largo.
    r = greedy(GRAFO, COORDS, "O", "D", h2_haversine)
    assert r["camino"] == ["O", "A", "E", "D"]
    assert r["metros"] == 2000


def test_inalcanzable_regresa_none():
    assert a_estrella(GRAFO, COORDS, "O", "F", h2_haversine)["camino"] is None
    assert greedy(GRAFO, COORDS, "O", "F", h2_haversine)["camino"] is None


def test_formato_igual_al_de_fase1():
    claves = set(ucs(GRAFO, "O", "D").keys())
    assert set(a_estrella(GRAFO, COORDS, "O", "D", h2_haversine).keys()) == claves
    assert set(greedy(GRAFO, COORDS, "O", "D", h2_haversine).keys()) == claves
