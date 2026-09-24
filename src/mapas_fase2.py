"""
Mapas interactivos (folium) de la Fase 2: rutas de A* contra Greedy.

Genera un archivo HTML por destino en mapas/. Se abren con doble clic en el
navegador: se puede hacer zoom, mover el mapa y prender/apagar cada ruta.

Se corre desde la raíz del proyecto:
    python src/mapas_fase2.py
"""

import folium

from mapa import cargar_grafo, pares_origen_destino
from fase2 import a_estrella, greedy, h2_haversine


def agregar_ruta(mapa, coords, resultado, nombre, color):
    """Dibuja una ruta como línea sobre el mapa, dentro de su propia capa."""
    # folium espera una lista de puntos (lat, lon); coords ya tiene ese orden.
    puntos = [coords[n] for n in resultado["camino"]]
    texto = f"{nombre}: {resultado['metros']:.0f} m, {resultado['expandidos']} nodos expandidos"

    # Un FeatureGroup es una "capa": permite prenderla/apagarla con el control de capas.
    capa = folium.FeatureGroup(name=texto)
    folium.PolyLine(puntos, color=color, weight=6, opacity=0.7, tooltip=texto).add_to(capa)
    capa.add_to(mapa)


def crear_mapa(vecinos, coords, nombre_destino, origen, destino):
    """Crea y guarda el mapa de un par origen-destino con las rutas de A* y Greedy."""
    r_astar = a_estrella(vecinos, coords, origen, destino, h2_haversine)
    r_greedy = greedy(vecinos, coords, origen, destino, h2_haversine)

    # Centramos el mapa a la mitad entre el depósito y el destino.
    lat_centro = (coords[origen][0] + coords[destino][0]) / 2
    lon_centro = (coords[origen][1] + coords[destino][1]) / 2
    # Fondo de Esri en vez del de OpenStreetMap: los servidores de OSM bloquean
    # (error 403) los mapas abiertos como archivo local, y Esri no pide clave de API.
    mapa = folium.Map(location=(lat_centro, lon_centro), zoom_start=15, tiles=None)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri",   # crédito obligatorio del proveedor del mapa
        name="Mapa de calles (Esri)",
    ).add_to(mapa)

    # Greedy primero y A* después, para que A* quede dibujada encima.
    agregar_ruta(mapa, coords, r_greedy, "Greedy (h2)", "red")
    agregar_ruta(mapa, coords, r_astar, "A* (h2)", "blue")

    folium.Marker(coords[origen], tooltip="Depósito",
                  icon=folium.Icon(color="green", icon="home")).add_to(mapa)
    folium.Marker(coords[destino], tooltip=nombre_destino,
                  icon=folium.Icon(color="black", icon="flag")).add_to(mapa)

    # Control en la esquina para prender/apagar cada ruta.
    folium.LayerControl(collapsed=False).add_to(mapa)

    # Nombre de archivo sin espacios ni acentos, para evitar problemas en Windows.
    nombre_archivo = (nombre_destino.lower().replace(" ", "_")
                      .replace("ó", "o").replace("á", "a").replace("é", "e"))
    ruta = f"mapas/ruta_{nombre_archivo}.html"
    mapa.save(ruta)

    diferencia = r_greedy["metros"] - r_astar["metros"]
    print(f"{nombre_destino:28s} A*: {r_astar['metros']:6.0f} m | Greedy: {r_greedy['metros']:6.0f} m "
          f"(+{diferencia:.0f} m) -> {ruta}")


def main():
    vecinos, coords = cargar_grafo()
    for nombre, origen, destino in pares_origen_destino(coords):
        crear_mapa(vecinos, coords, nombre, origen, destino)


if __name__ == "__main__":
    main()
