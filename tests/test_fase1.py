"""
Pruebas unitarias de la Fase 1 (BFS, DFS, UCS y accesibilidad).

Usamos un grafo PEQUEÑO hecho a mano en lugar del mapa real, porque:
    - sabemos de antemano cuál es la respuesta correcta,
    - las pruebas corren en milisegundos y no dependen de data/.

Grafo de prueba (dirigido, pesos en metros):

    A --10--> B --1--> D
    |                  ^
    1                  1
    v                  |
    C --1--> E --------+
    ^        |
    +---1----+          (C y E forman un ciclo)

    F --1--> A          (nadie llega a F: es inalcanzable desde A)

Desde A hasta D:
    - Menos saltos: A-B-D  (2 saltos, 11 m)   <- lo que debe dar BFS
    - Menos metros: A-C-E-D (3 saltos, 3 m)   <- lo que debe dar UCS
"""

from fase1 import bfs, dfs, ucs, nodos_alcanzables, verificar_entregas

GRAFO = {
    "A": [("B", 10), ("C", 1)],
    "B": [("D", 1)],
    "C": [("E", 1)],
    "E": [("D", 1), ("C", 1)],
    "D": [],
    "F": [("A", 1)],
}


def es_camino_valido(vecinos, camino):
    """Revisa que cada paso del camino sea una calle que existe en el grafo."""
    for i in range(len(camino) - 1):
        destinos = [v for v, _m in vecinos[camino[i]]]
        if camino[i + 1] not in destinos:
            return False
    return True


def test_bfs_encuentra_menos_saltos():
    r = bfs(GRAFO, "A", "D")
    assert r["camino"] == ["A", "B", "D"]
    assert r["saltos"] == 2
    assert r["metros"] == 11


def test_ucs_encuentra_menos_metros():
    r = ucs(GRAFO, "A", "D")
    assert r["camino"] == ["A", "C", "E", "D"]
    assert r["saltos"] == 3
    assert r["metros"] == 3


def test_dfs_encuentra_camino_valido():
    # DFS no garantiza el mejor camino, solo que sea uno válido.
    # Además comprueba que el ciclo C<->E no lo deja atrapado.
    r = dfs(GRAFO, "A", "D")
    assert r["camino"][0] == "A"
    assert r["camino"][-1] == "D"
    assert es_camino_valido(GRAFO, r["camino"])


def test_destino_inalcanzable_regresa_none():
    for algoritmo in (bfs, dfs, ucs):
        r = algoritmo(GRAFO, "A", "F")
        assert r["camino"] is None


def test_origen_igual_a_destino():
    for algoritmo in (bfs, dfs, ucs):
        r = algoritmo(GRAFO, "A", "A")
        assert r["camino"] == ["A"]
        assert r["metros"] == 0
        assert r["saltos"] == 0


def test_resultado_tiene_formato_comun():
    claves = {"camino", "metros", "saltos", "expandidos",
              "frontera_max", "tiempo_ms", "orden_expansion"}
    for algoritmo in (bfs, dfs, ucs):
        assert set(algoritmo(GRAFO, "A", "D").keys()) == claves


def test_nodos_alcanzables():
    assert nodos_alcanzables(GRAFO, "A") == {"A", "B", "C", "D", "E"}


def test_verificar_entregas():
    assert verificar_entregas(GRAFO, "A", ["D", "F"]) == {"D": True, "F": False}
