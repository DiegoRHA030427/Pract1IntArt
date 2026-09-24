"""
Paso 1: Descargar el grafo vial (espacio de estados) de la zona norte-centro de CDMX.

Se corre UNA sola vez desde la raíz del proyecto:
    python src/descargar_grafo.py

Modelo formal del grafo:
    - Nodos (V):   intersecciones de calles.
    - Aristas (E): tramos de calle entre dos intersecciones.
    - Pesos (w):   atributo 'length' de cada arista = longitud en metros.
"""

import osmnx as ox

# --- Parámetros de la zona (decididos por el equipo) ---
# Punto medio entre el Zócalo y La Raza: abarca Centro Histórico, Tlatelolco y Guerrero.
CENTRO = (19.450, -99.137)   # (latitud, longitud)
RADIO_METROS = 3000          # 3 km: grafo suficientemente grande pero rápido en Python

# 'drive' = solo calles para autos, y respeta el sentido de circulación.
# Tiene sentido porque nuestro agente es un camión de reparto.
TIPO_RED = "drive"

# Dónde se guarda el grafo para no volver a descargarlo cada vez.
ARCHIVO_GRAFO = "data/grafo_cdmx.graphml"
ARCHIVO_IMAGEN = "data/grafo_cdmx.png"


def main():
    print("Versión de osmnx:", ox.__version__)
    print("Descargando grafo... (puede tardar 1-2 minutos)")

    # graph_from_point descarga de OpenStreetMap todas las calles dentro del radio.
    # El resultado es un grafo DIRIGIDO: una calle de un solo sentido es una sola arista.
    # NOTA: no quitamos zonas desconectadas a propósito, porque la Fase 1 debe
    # poder detectar destinos que NO son alcanzables desde el depósito.
    G = ox.graph_from_point(CENTRO, dist=RADIO_METROS, network_type=TIPO_RED)

    # Resumen para verificar que la descarga salió bien.
    print("Nodos (intersecciones):", G.number_of_nodes())
    print("Aristas (calles):", G.number_of_edges())

    # Guardamos en formato GraphML (texto/XML), que osmnx puede volver a leer después.
    ox.save_graphml(G, filepath=ARCHIVO_GRAFO)
    print("Grafo guardado en:", ARCHIVO_GRAFO)

    # Imagen rápida del mapa para comprobar visualmente la zona descargada.
    ox.plot_graph(G, node_size=0, edge_linewidth=0.5, show=False, close=True,
                  save=True, filepath=ARCHIVO_IMAGEN)
    print("Imagen guardada en:", ARCHIVO_IMAGEN)


# Esta condición hace que main() solo se ejecute si corremos el archivo directamente.
if __name__ == "__main__":
    main()
