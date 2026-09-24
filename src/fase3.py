"""
Fase 3: Búsqueda local para ordenar las entregas (problema del agente viajero, TSP).

Problema: un camión sale del depósito, visita N entregas y REGRESA al depósito.
¿En qué orden las visita para recorrer la menor distancia total?

Representación (la usan SA y AG):
    - Índice 0 = depósito; índices 1..N = entregas.
    - Una RUTA es una lista con el orden de las entregas, p. ej. [3, 1, 2]
      significa: depósito -> 3 -> 1 -> 2 -> depósito.
    - matriz[i][j] = metros del camino más corto (A*) del punto i al punto j.
"""

import math
import random
import time

from mapa import cargar_grafo, nodo_mas_cercano, DEPOSITO
from fase1 import nodos_alcanzables
from fase2 import a_estrella, h2_haversine
from admisibilidad import invertir_grafo

N_ENTREGAS = 15
SEMILLA = 42   # semilla fija: siempre salen las mismas entregas (resultados repetibles)


# ---------------------------------------------------------------------------
# Definición del problema
# ---------------------------------------------------------------------------

def elegir_entregas(vecinos, deposito, n, semilla):
    """Elige n nodos aleatorios a los que el camión puede IR y de los que puede REGRESAR.

    Como las calles tienen sentido, no basta con poder llegar a un nodo:
    también hay que poder volver al depósito. Si todas las entregas cumplen
    ambas cosas, entre cualquier par de entregas siempre hay camino (pasando
    por el depósito si hace falta), así la matriz de distancias queda completa.
    """
    se_puede_ir = nodos_alcanzables(vecinos, deposito)
    # En el grafo invertido, "alcanzables desde el depósito" = los que pueden regresar a él.
    se_puede_regresar = nodos_alcanzables(invertir_grafo(vecinos), deposito)

    candidatos = sorted((se_puede_ir & se_puede_regresar) - {deposito})
    # sorted() asegura el mismo orden de candidatos siempre, para que la semilla funcione igual.
    random.seed(semilla)
    return random.sample(candidatos, n)


def matriz_distancias(vecinos, coords, puntos):
    """matriz[i][j] = metros del camino más corto de puntos[i] a puntos[j], usando A* (Fase 2).

    No es simétrica: por los sentidos de las calles, ir de i a j puede medir
    distinto que ir de j a i.
    """
    n = len(puntos)
    matriz = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                resultado = a_estrella(vecinos, coords, puntos[i], puntos[j], h2_haversine)
                matriz[i][j] = resultado["metros"]
    return matriz


def distancia_ruta(ruta, matriz):
    """Metros totales de: depósito -> ruta[0] -> ... -> ruta[-1] -> depósito."""
    total = matriz[0][ruta[0]]                  # salida del depósito a la primera entrega
    for i in range(len(ruta) - 1):
        total += matriz[ruta[i]][ruta[i + 1]]    # de cada entrega a la siguiente
    total += matriz[ruta[-1]][0]                 # regreso de la última entrega al depósito
    return total


def preparar_problema(n=N_ENTREGAS, semilla=SEMILLA):
    """Arma todo lo necesario: regresa (puntos, matriz, coords, vecinos).

    puntos[0] es el depósito y puntos[1..n] son las entregas.
    """
    vecinos, coords = cargar_grafo()
    deposito, _ = nodo_mas_cercano(coords, DEPOSITO[0], DEPOSITO[1])
    entregas = elegir_entregas(vecinos, deposito, n, semilla)
    puntos = [deposito] + entregas
    matriz = matriz_distancias(vecinos, coords, puntos)
    return puntos, matriz, coords, vecinos


# ---------------------------------------------------------------------------
# Simulated Annealing (Recocido simulado)
# ---------------------------------------------------------------------------

# Parámetros típicos (explicados):
SA_T0 = 1000        # temperatura inicial. Una ruta 1000 m peor se acepta al inicio con
                    # prob. e^(-1000/1000) = 37%: hay bastante exploración.
SA_ALFA = 0.999     # enfriamiento geométrico: T se multiplica por 0.999 en cada iteración.
SA_T_MIN = 0.1      # cuando T baja de aquí, se detiene (ya casi no acepta rutas peores).
                    # Con estos valores son ~9,200 iteraciones.


def vecino_2opt(ruta):
    """Operador 2-opt: elige dos posiciones i < j e INVIERTE el tramo entre ellas.

    Ejemplo: [1, 2, 3, 4, 5] con i=1, j=3  ->  [1, 4, 3, 2, 5]
    En un mapa, esto "desenreda" dos tramos de la ruta que se cruzan.
    """
    i, j = sorted(random.sample(range(len(ruta)), 2))
    return ruta[:i] + ruta[i:j + 1][::-1] + ruta[j + 1:]


def simulated_annealing(matriz, t0=SA_T0, alfa=SA_ALFA, t_min=SA_T_MIN, semilla=None):
    """Busca un buen orden de entregas imitando cómo se enfría un metal.

    En cada iteración propone una ruta vecina (2-opt):
        - Si es MEJOR, siempre la acepta.
        - Si es PEOR, la acepta con probabilidad e^(-diferencia / T).
    Al inicio T es alta y acepta muchas rutas peores (explora, escapa de mínimos
    locales). Conforme T baja, casi solo acepta mejoras (se enfoca).

    Regresa un diccionario con la mejor ruta y el historial para graficar la convergencia.
    """
    inicio = time.perf_counter()
    if semilla is not None:
        random.seed(semilla)

    # Ruta inicial: las entregas (1..N) en orden aleatorio.
    actual = list(range(1, len(matriz)))
    random.shuffle(actual)
    dist_actual = distancia_ruta(actual, matriz)

    mejor, dist_mejor = actual, dist_actual
    historial_actual = [dist_actual]   # distancia de la ruta actual en cada iteración
    historial_mejor = [dist_mejor]     # mejor distancia encontrada hasta cada iteración

    T = t0
    while T > t_min:
        candidata = vecino_2opt(actual)
        # La matriz NO es simétrica (calles de un sentido): al invertir un tramo,
        # esas calles se recorren al revés. Por eso recalculamos la distancia completa.
        dist_candidata = distancia_ruta(candidata, matriz)
        diferencia = dist_candidata - dist_actual   # negativa = mejora

        if diferencia < 0 or random.random() < math.exp(-diferencia / T):
            actual, dist_actual = candidata, dist_candidata
            if dist_actual < dist_mejor:
                mejor, dist_mejor = actual, dist_actual

        historial_actual.append(dist_actual)
        historial_mejor.append(dist_mejor)
        T *= alfa   # enfriamiento geométrico

    return {
        "ruta": mejor,
        "metros": dist_mejor,
        "iteraciones": len(historial_mejor) - 1,
        "tiempo_ms": (time.perf_counter() - inicio) * 1000,
        "historial_actual": historial_actual,
        "historial_mejor": historial_mejor,
    }


# ---------------------------------------------------------------------------
# Algoritmo Genético (AG)
# ---------------------------------------------------------------------------

# Parámetros típicos (explicados):
AG_POBLACION = 100      # cuántas rutas conviven en cada generación
AG_GENERACIONES = 200   # cuántas veces se renueva la población
AG_PROB_CRUZA = 0.9     # probabilidad de que dos padres se crucen (si no, el hijo es copia)
AG_PROB_MUTACION = 0.2  # probabilidad de que un hijo sufra un intercambio al azar
AG_TORNEO = 3           # cuántas rutas compiten en cada torneo de selección
AG_ELITE = 2            # las 2 mejores rutas pasan intactas a la siguiente generación


def seleccion_torneo(poblacion, distancias, k):
    """Toma k rutas al azar y regresa la más corta (la "ganadora del torneo").

    Así las rutas buenas tienen más probabilidad de ser padres, pero las
    no tan buenas también pueden ganar a veces (se conserva diversidad).
    """
    competidores = random.sample(range(len(poblacion)), k)
    ganador = min(competidores, key=lambda idx: distancias[idx])
    return poblacion[ganador]


def cruza_ox(padre1, padre2):
    """Order Crossover (OX): el hijo hereda un TRAMO del padre1 y el ORDEN del padre2.

    Ejemplo con tramo en posiciones 2..4:
        padre1 = [1, 2, |3, 4, 5|, 6, 7]
        padre2 = [5, 7, 6, 1, 3, 2, 4]
        hijo   = [_, _,  3, 4, 5,  _, _]   <- copia el tramo del padre1
        faltan, en el orden del padre2: 7, 6, 1, 2
        hijo   = [7, 6,  3, 4, 5,  1, 2]

    No se puede cruzar "mitad y mitad" como en otros problemas, porque se
    repetirían entregas; OX garantiza que cada entrega aparezca exactamente una vez.
    """
    n = len(padre1)
    i, j = sorted(random.sample(range(n), 2))

    hijo = [None] * n
    hijo[i:j + 1] = padre1[i:j + 1]

    tramo = set(padre1[i:j + 1])
    faltantes = [gen for gen in padre2 if gen not in tramo]   # en el orden del padre2

    k = 0
    for posicion in range(n):
        if hijo[posicion] is None:
            hijo[posicion] = faltantes[k]
            k += 1
    return hijo


def mutacion_intercambio(ruta):
    """Intercambia dos entregas al azar: [1, 2, 3, 4] -> [1, 4, 3, 2]."""
    ruta = ruta[:]   # copia, para no modificar la ruta original
    i, j = random.sample(range(len(ruta)), 2)
    ruta[i], ruta[j] = ruta[j], ruta[i]
    return ruta


def algoritmo_genetico(matriz, poblacion_tam=AG_POBLACION, generaciones=AG_GENERACIONES,
                       prob_cruza=AG_PROB_CRUZA, prob_mutacion=AG_PROB_MUTACION,
                       torneo=AG_TORNEO, elite=AG_ELITE, semilla=None):
    """Evoluciona una población de rutas: selección -> cruza -> mutación, generación tras generación.

    Regresa un diccionario con la mejor ruta y el historial para graficar la convergencia.
    """
    inicio = time.perf_counter()
    if semilla is not None:
        random.seed(semilla)

    # Población inicial: rutas completamente aleatorias.
    entregas = list(range(1, len(matriz)))
    poblacion = []
    for _ in range(poblacion_tam):
        ruta = entregas[:]
        random.shuffle(ruta)
        poblacion.append(ruta)

    historial_mejor = []     # mejor distancia de cada generación
    historial_promedio = []  # distancia promedio de cada generación (muestra la diversidad)
    evaluaciones = 0

    for _generacion in range(generaciones):
        distancias = [distancia_ruta(ruta, matriz) for ruta in poblacion]
        evaluaciones += len(poblacion)
        historial_mejor.append(min(distancias))
        historial_promedio.append(sum(distancias) / len(distancias))

        # Elitismo: las mejores rutas pasan tal cual, para no perder nunca la mejor solución.
        orden = sorted(range(len(poblacion)), key=lambda idx: distancias[idx])
        nueva = [poblacion[idx] for idx in orden[:elite]]

        # El resto de la nueva generación se forma con hijos.
        while len(nueva) < poblacion_tam:
            padre1 = seleccion_torneo(poblacion, distancias, torneo)
            padre2 = seleccion_torneo(poblacion, distancias, torneo)
            if random.random() < prob_cruza:
                hijo = cruza_ox(padre1, padre2)
            else:
                hijo = padre1[:]
            if random.random() < prob_mutacion:
                hijo = mutacion_intercambio(hijo)
            nueva.append(hijo)

        poblacion = nueva

    # Evaluamos la última generación para quedarnos con la mejor ruta.
    distancias = [distancia_ruta(ruta, matriz) for ruta in poblacion]
    evaluaciones += len(poblacion)
    idx_mejor = min(range(len(poblacion)), key=lambda idx: distancias[idx])
    historial_mejor.append(distancias[idx_mejor])
    historial_promedio.append(sum(distancias) / len(distancias))

    return {
        "ruta": poblacion[idx_mejor],
        "metros": distancias[idx_mejor],
        "generaciones": generaciones,
        "evaluaciones": evaluaciones,
        "tiempo_ms": (time.perf_counter() - inicio) * 1000,
        "historial_mejor": historial_mejor,
        "historial_promedio": historial_promedio,
    }


# ---------------------------------------------------------------------------
# Prueba rápida
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    inicio = time.perf_counter()
    puntos, matriz, coords, vecinos = preparar_problema()
    print(f"Matriz {len(puntos)}x{len(puntos)} calculada en {time.perf_counter() - inicio:.1f} s")

    print("\nEntregas elegidas:")
    for i, nodo in enumerate(puntos):
        etiqueta = "Depósito" if i == 0 else f"Entrega {i}"
        print(f"  {i:2d}. {etiqueta:11s} nodo {nodo}  {coords[nodo]}")

    # Ruta de referencia: visitar las entregas en el orden en que salieron (1, 2, ..., N).
    # SA y AG deben encontrar algo mucho mejor que esto.
    ruta_inicial = list(range(1, len(puntos)))
    print(f"\nRuta en orden 1..{len(puntos) - 1}: {distancia_ruta(ruta_inicial, matriz):.0f} m")

    # Simulated Annealing: lo corremos con 5 semillas porque es aleatorio.
    print("\nSimulated Annealing (5 corridas):")
    for semilla in range(5):
        r = simulated_annealing(matriz, semilla=semilla)
        print(f"  semilla {semilla}: {r['metros']:7.0f} m en {r['iteraciones']} iteraciones "
              f"({r['tiempo_ms']:.0f} ms)  ruta: {r['ruta']}")

    # Algoritmo Genético: también aleatorio, 5 corridas.
    print("\nAlgoritmo Genético (5 corridas):")
    for semilla in range(5):
        r = algoritmo_genetico(matriz, semilla=semilla)
        print(f"  semilla {semilla}: {r['metros']:7.0f} m en {r['evaluaciones']} evaluaciones "
              f"({r['tiempo_ms']:.0f} ms)  ruta: {r['ruta']}")
