import random
from entorno import FUEGO, ESTACION, HUMANO, RATA, DUENDE

class Agente:
    def __init__(self, fila_inicial, col_inicial, energia_maxima=100):
        self.fila = int(fila_inicial)
        self.columna = int(col_inicial)
        self.energia_maxima = energia_maxima
        self.energia_actual = energia_maxima
        self.humanos_rescatados = 0
        self.ruta_actual = []
        self.log_callback = None # Función para imprimir en la interfaz
        self.cargando_humano = False # Nueva variable para la Fase 6

    def mover_a(self, fila, columna, entorno):
        """Mueve al agente a una nueva coordenada, gastando energia e interactuando con el entorno."""
        if self.energia_actual <= 0:
            return False
            
        self.fila = int(fila)
        self.columna = int(columna)
        self.energia_actual -= 1
        
        celda_actual = entorno.obtener_celda(self.fila, self.columna)
        
        # Incertidumbre: Probabilidad de dano al pisar fuego
        if celda_actual == FUEGO:
            prob = random.random()
            if prob < 0.70: # 70% de quemadura grave
                dano = 20
                if self.log_callback:
                    self.log_callback("¡Aaaah! Fuego grave (-20 energia)")
            else: # 30% de quemadura leve
                dano = 5
                if self.log_callback:
                    self.log_callback("¡Uf! Fuego leve (-5 energia)")
                    
            self.energia_actual = max(0, self.energia_actual - dano)
            
        # Recargar en estación y dejar al humano a salvo
        elif celda_actual == ESTACION:
            self.recargar_energia()
            if self.cargando_humano:
                self.humanos_rescatados += 1
                self.cargando_humano = False
                if self.log_callback:
                    self.log_callback(f"¡Humano a salvo en el Hospital! (Total: {self.humanos_rescatados})")
            else:
                if self.log_callback:
                    self.log_callback("¡Energia recargada al 100% en la Base!")
            # Decisión: ¿Consumir estación o no? Por ahora, no la consumiremos para que sirva de hospital permanente
            # entorno.agregar_celda(self.fila, self.columna, 0)
            
        # Rescatar humano
        elif celda_actual == HUMANO:
            if not self.cargando_humano:
                self.cargando_humano = True
                entorno.agregar_celda(self.fila, self.columna, 0) # Quitar humano del mapa
                if self.log_callback:
                    self.log_callback("¡Humano asegurado! Buscando Hospital...")
            else:
                if self.log_callback:
                    self.log_callback("Ya estoy cargando a alguien, no puedo llevar más.")
                    
        # Enemigos
        elif celda_actual in [RATA, DUENDE]:
            dano = 50
            if self.log_callback:
                enemigo_str = "Rata" if celda_actual == RATA else "Duende"
                self.log_callback(f"¡Ataque de {enemigo_str}! (-{dano} energia)")
            self.energia_actual = max(0, self.energia_actual - dano)
            entorno.agregar_celda(self.fila, self.columna, 0) # El enemigo muere al chocar
            
        return True

    def establecer_ruta(self, ruta):
        """Asigna una lista de tuplas (fila, col) como la ruta a seguir."""
        self.ruta_actual = ruta

    def avanzar_ruta(self, entorno):
        """Avanza un paso en la ruta actual."""
        if self.ruta_actual:
            siguiente_paso = self.ruta_actual.pop(0)
            return self.mover_a(siguiente_paso[0], siguiente_paso[1], entorno)
        return False

    def recargar_energia(self):
        """Restaura la energia al máximo."""
        self.energia_actual = self.energia_maxima

    def rescatar_humano(self):
        """Incrementa el contador de rescatados."""
        self.humanos_rescatados += 1
