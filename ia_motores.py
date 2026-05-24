import heapq
from collections import deque
import random
from entorno import MURO, FUEGO, HUMANO, ESTACION, RATA, DUENDE
import time

class BaseConocimiento:
    def __init__(self, filas, columnas):
        self.filas = filas
        self.columnas = columnas
        # -1 = Desconocido, resto = Valores del entorno
        self.mapa_conocido = [[-1 for _ in range(columnas)] for _ in range(filas)]
        
    def percibir_entorno(self, entorno, fila, col):
        """El agente percibe la celda actual y las adyacentes."""
        direcciones = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for df, dc in direcciones:
            nf, nc = int(fila) + df, int(col) + dc
            if 0 <= nf < self.filas and 0 <= nc < self.columnas:
                self.mapa_conocido[nf][nc] = entorno.obtener_celda(nf, nc)

class MotorInferencia:
    base_conocimiento = set()

    @staticmethod
    def inferir_riesgo(entorno, fila, col):
        """
        Lógica Proposicional:
        Evalúa las celdas adyacentes a (fila, col) y actualiza la Base de Conocimiento.
        Reglas:
        - Si percibo FUEGO adyacente (humo), entonces hay RIESGO de quemarse cerca.
        Devuelve un nivel de riesgo (0 a 4) basado en cuántos fuegos hay alrededor.
        """
        riesgo = 0
        direcciones = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        # Limpiar inferencias posicionales antiguas de peligro inminente para esta celda
        MotorInferencia.base_conocimiento = {h for h in MotorInferencia.base_conocimiento if not h.startswith(f"PeligroInminente_({fila},{col})")}
        
        for df, dc in direcciones:
            n_fila, n_col = fila + df, col + dc
            if entorno.obtener_celda(n_fila, n_col) == FUEGO:
                # Inferencia lógica formal: percibimos fuego, deducimos peligro
                MotorInferencia.base_conocimiento.add(f"FuegoDetectado_({n_fila},{n_col})")
                MotorInferencia.base_conocimiento.add(f"PeligroInminente_({fila},{col})")
                riesgo += 1
                
        return riesgo

class TomaDeDecision:
    @staticmethod
    def funcion_utilidad(agente, objetivo_coord, tipo_objetivo, ruta):
        """
        Evalúa la utilidad de dirigirse a un objetivo específico.
        Utilidad = Recompensa - Costo de Camino - Riesgo Estimado
        """
        if not ruta:
            return -9999 # Imposible llegar
            
        distancia = len(ruta)
        costo_energia = distancia
        
        # Recompensas base
        recompensa = 0
        if agente.cargando_humano:
            if tipo_objetivo == ESTACION:
                recompensa = 1000 # Prioridad máxima: ir al hospital a dejarlo
            else:
                return -9999 # Ignorar humanos u otros objetivos si ya cargamos uno
        else:
            if tipo_objetivo == HUMANO:
                recompensa = 100
            elif tipo_objetivo == ESTACION:
                # La estación vale mucho más si la energía es baja
                factor_necesidad = (agente.energia_maxima - agente.energia_actual) / agente.energia_maxima
                recompensa = 150 * factor_necesidad
            
        # Considerar el riesgo (si hay poco margen de error en la energía, el costo se siente peor)
        margen = agente.energia_actual - costo_energia
        if margen < 10:
            recompensa -= 50 # Penalizar rutas que lo dejen casi en cero
            
        utilidad = recompensa - costo_energia
        return utilidad

    @staticmethod
    def decidir_mejor_accion(agente, entorno, interfaz, algoritmo="A_STAR"):
        """Elige el mejor objetivo disponible evaluando humanos y estaciones."""
        humanos = entorno.obtener_posiciones_tipo(HUMANO)
        estaciones = entorno.obtener_posiciones_tipo(ESTACION)
        
        objetivos = [(h, HUMANO) for h in humanos] + [(e, ESTACION) for e in estaciones]
        
        if not objetivos:
            interfaz.log("No hay tareas pendientes.")
            return None, None
            
        mejor_utilidad = -float('inf')
        mejor_objetivo = None
        mejor_ruta = None
        
        inicio = (agente.fila, agente.columna)
        
        # 1. Filtro rápido con distancia Manhattan
        objetivos_filtrados = []
        for coord, tipo in objetivos:
            coord_int = (int(coord[0]), int(coord[1]))
            distancia_estimada = Busqueda.heuristica(inicio, coord_int)
            
            recompensa_estimada = 0
            if agente.cargando_humano and tipo == ESTACION:
                recompensa_estimada = 1000
            elif not agente.cargando_humano and tipo == HUMANO:
                recompensa_estimada = 100
            elif not agente.cargando_humano and tipo == ESTACION:
                factor = (agente.energia_maxima - agente.energia_actual) / agente.energia_maxima
                recompensa_estimada = 150 * factor
                
            utilidad_estimada = recompensa_estimada - distancia_estimada
            objetivos_filtrados.append((utilidad_estimada, coord_int, tipo))
            
        # Ordenar de mayor a menor utilidad estimada y tomar los top 3
        objetivos_filtrados.sort(key=lambda x: x[0], reverse=True)
        top_objetivos = objetivos_filtrados[:3]
        
        # 2. Búsqueda pesada (A* o BFS) solo en los mejores candidatos
        for _, coord_int, tipo in top_objetivos:
            if algoritmo == "A_STAR":
                ruta, _, _ = Busqueda.a_estrella(entorno, inicio, coord_int)
            else:
                ruta, _, _ = Busqueda.bfs(entorno, inicio, coord_int)
                
            utilidad = TomaDeDecision.funcion_utilidad(agente, coord_int, tipo, ruta)
            
            if utilidad > mejor_utilidad:
                mejor_utilidad = utilidad
                mejor_objetivo = (coord_int, tipo)
                mejor_ruta = ruta
                
        if mejor_objetivo:
            tipo_str = "Humano" if mejor_objetivo[1] == HUMANO else "Estación"
            interfaz.log(f"Decisión ({algoritmo}): Ir a {tipo_str} en {mejor_objetivo[0]}")
            interfaz.log(f"Utilidad calculada: {mejor_utilidad:.1f}")
            return mejor_ruta, mejor_objetivo[0]
        else:
            interfaz.log("Ningún objetivo es alcanzable.")
            return None, None

class Busqueda:
    @staticmethod
    def obtener_vecinos(entorno, fila, col):
        """Devuelve las celdas adyacentes válidas (no muros)."""
        vecinos = []
        direcciones = [(-1, 0), (1, 0), (0, -1), (0, 1)] # Arriba, Abajo, Izquierda, Derecha
        
        for df, dc in direcciones:
            n_fila, n_col = fila + df, col + dc
            # Cast a int para evitar np.int64 bugs
            n_fila, n_col = int(n_fila), int(n_col)
            
            if entorno.obtener_celda(n_fila, n_col) != MURO:
                vecinos.append((n_fila, n_col))
        return vecinos

    @staticmethod
    def heuristica(a, b):
        """Distancia Manhattan para A*."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    @staticmethod
    def costo_movimiento(entorno, fila, col):
        """Fuego cuesta más que espacio vacío (evasión preferente)."""
        celda = entorno.obtener_celda(fila, col)
        if celda == FUEGO:
            return 5 # El agente prefiere evitar fuego
        elif celda in [RATA, DUENDE]:
            return 100 # Evitar enemigos a toda costa
        return 1

    @staticmethod
    def a_estrella(entorno, inicio, objetivo):
        inicio = (int(inicio[0]), int(inicio[1]))
        objetivo = (int(objetivo[0]), int(objetivo[1]))
        
        inicio_tiempo = time.time()
        frontera = []
        heapq.heappush(frontera, (0, inicio))
        
        costo_acumulado = {inicio: 0}
        padres = {inicio: None}
        nodos_explorados = 0

        while frontera:
            _, actual = heapq.heappop(frontera)
            nodos_explorados += 1

            if actual == objetivo:
                break

            for vecino in Busqueda.obtener_vecinos(entorno, actual[0], actual[1]):
                nuevo_costo = costo_acumulado[actual] + Busqueda.costo_movimiento(entorno, vecino[0], vecino[1])
                
                if vecino not in costo_acumulado or nuevo_costo < costo_acumulado[vecino]:
                    costo_acumulado[vecino] = nuevo_costo
                    prioridad = nuevo_costo + Busqueda.heuristica(vecino, objetivo)
                    heapq.heappush(frontera, (prioridad, vecino))
                    padres[vecino] = actual

        tiempo_fin = time.time()
        
        ruta = []
        actual = objetivo
        if actual in padres:
            while actual != inicio:
                ruta.append(actual)
                actual = padres[actual]
            ruta.reverse()
            
        return ruta, nodos_explorados, round(tiempo_fin - inicio_tiempo, 5)

    @staticmethod
    def bfs(entorno, inicio, objetivo):
        inicio = (int(inicio[0]), int(inicio[1]))
        objetivo = (int(objetivo[0]), int(objetivo[1]))
        
        inicio_tiempo = time.time()
        frontera = deque([inicio])
        padres = {inicio: None}
        visitados = set([inicio])
        nodos_explorados = 0

        while frontera:
            actual = frontera.popleft()
            nodos_explorados += 1

            if actual == objetivo:
                break

            for vecino in Busqueda.obtener_vecinos(entorno, actual[0], actual[1]):
                if vecino not in visitados:
                    visitados.add(vecino)
                    frontera.append(vecino)
                    padres[vecino] = actual

        tiempo_fin = time.time()

        ruta = []
        actual = objetivo
        if actual in padres:
            while actual != inicio:
                ruta.append(actual)
                actual = padres[actual]
            ruta.reverse()

        return ruta, nodos_explorados, round(tiempo_fin - inicio_tiempo, 5)

class QLearning:
    def __init__(self, entorno, alpha=0.5, gamma=0.9, epsilon=0.1):
        self.entorno = entorno
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = {}  # (estado, accion) -> valor Q
        # Acciones: 0: Arriba, 1: Abajo, 2: Izquierda, 3: Derecha
        self.acciones = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def obtener_q(self, estado, accion):
        return self.q_table.get((estado, accion), 0.0)

    def actualizar_q(self, estado, accion, recompensa, proximo_estado):
        max_q_proximo = max([self.obtener_q(proximo_estado, a) for a in range(4)], default=0.0)
        q_actual = self.obtener_q(estado, accion)
        self.q_table[(estado, accion)] = q_actual + self.alpha * (recompensa + self.gamma * max_q_proximo - q_actual)

    def entrenar(self, inicio, objetivo, episodios=500):
        inicio_tiempo = time.time()
        for _ in range(episodios):
            estado = inicio
            pasos = 0
            while estado != objetivo and pasos < 100:
                if random.random() < self.epsilon:
                    accion = random.choice(range(4))
                else:
                    valores_q = [self.obtener_q(estado, a) for a in range(4)]
                    max_q = max(valores_q)
                    mejores_acciones = [a for a, q in enumerate(valores_q) if q == max_q]
                    accion = random.choice(mejores_acciones)

                df, dc = self.acciones[accion]
                proximo_estado = (estado[0] + df, estado[1] + dc)

                if 0 <= proximo_estado[0] < self.entorno.filas and 0 <= proximo_estado[1] < self.entorno.columnas:
                    celda = self.entorno.obtener_celda(proximo_estado[0], proximo_estado[1])
                    if celda == MURO:
                        recompensa = -10
                        proximo_estado = estado
                    elif celda == FUEGO:
                        recompensa = -50
                    elif celda in [RATA, DUENDE]:
                        recompensa = -500
                    elif proximo_estado == objetivo:
                        recompensa = 1000
                    else:
                        recompensa = -1

                    self.actualizar_q(estado, accion, recompensa, proximo_estado)
                    estado = proximo_estado
                else:
                    self.actualizar_q(estado, accion, -10, estado)
                    
                pasos += 1
        return round(time.time() - inicio_tiempo, 5)

    def obtener_ruta(self, inicio, objetivo):
        # Aprendizaje continuo: Entrenar en segundo plano antes de actuar
        # Esto permite adaptarse a cambios dinámicos (muros o fuegos nuevos)
        self.entrenar(inicio, objetivo, episodios=50)
        
        ruta = []
        estado = inicio
        visitados = set([inicio])
        pasos = 0
        while estado != objetivo and pasos < 100:
            valores_q = [self.obtener_q(estado, a) for a in range(4)]
            max_q = max(valores_q)
            if max_q == 0.0 and len(set(valores_q)) == 1:
                break
                
            mejores_acciones = [a for a, q in enumerate(valores_q) if q == max_q]
            accion = random.choice(mejores_acciones)

            df, dc = self.acciones[accion]
            proximo_estado = (estado[0] + df, estado[1] + dc)

            if proximo_estado in visitados or not (0 <= proximo_estado[0] < self.entorno.filas and 0 <= proximo_estado[1] < self.entorno.columnas) or self.entorno.obtener_celda(proximo_estado[0], proximo_estado[1]) == MURO:
                break
                
            ruta.append(proximo_estado)
            visitados.add(proximo_estado)
            estado = proximo_estado
            pasos += 1

        if estado != objetivo:
            return None
        return ruta
