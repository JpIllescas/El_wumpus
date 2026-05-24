import numpy as np

# Constantes para los tipos de celdas
VACIO = 0
MURO = 1
FUEGO = 2
HUMANO = 3
ESTACION = 4
RATA = 5
DUENDE = 6

class Entorno:
    def __init__(self, filas, columnas):
        self.filas = filas
        self.columnas = columnas
        # Inicializar el mapa vacío
        self.mapa = np.zeros((filas, columnas), dtype=int)
        # Lista de enemigos
        self.enemigos = []
    
    def agregar_celda(self, fila, columna, tipo):
        if 0 <= fila < self.filas and 0 <= columna < self.columnas:
            # Si añadimos un enemigo desde el Modo Dios, también lo registramos
            if tipo in [RATA, DUENDE]:
                self.enemigos.append({'tipo': tipo, 'fila': fila, 'columna': columna, 'direccion': 1})
            
            # Si sobrescribimos un enemigo, hay que sacarlo de la lista
            if self.mapa[fila][columna] in [RATA, DUENDE] and tipo not in [RATA, DUENDE]:
                self.enemigos = [e for e in self.enemigos if not (e['fila'] == fila and e['columna'] == columna)]

            self.mapa[fila][columna] = tipo
            
    def obtener_celda(self, fila, columna):
        if 0 <= fila < self.filas and 0 <= columna < self.columnas:
            return self.mapa[fila][columna]
        return MURO # Fuera del mapa cuenta como muro
    
    def limpiar_mapa(self):
        self.mapa = np.zeros((self.filas, self.columnas), dtype=int)
        self.enemigos = []

    def obtener_posiciones_tipo(self, tipo):
        posiciones = np.where(self.mapa == tipo)
        return list(zip(posiciones[0], posiciones[1]))
        
    def actualizar_enemigos(self):
        """Mueve a los enemigos en el mapa de forma lógica."""
        nuevo_mapa = self.mapa.copy()
        
        for enemigo in self.enemigos:
            fila = enemigo['fila']
            col = enemigo['columna']
            tipo = enemigo['tipo']
            
            # Limpiar posición actual (temporalmente)
            if nuevo_mapa[fila][col] == tipo:
                nuevo_mapa[fila][col] = VACIO
                
            # IA Básica de la Rata (Patrullaje simple Izquierda-Derecha)
            if tipo == RATA:
                nueva_col = col + enemigo['direccion']
                
                # Si choca con muro o límite, cambia de dirección
                if nueva_col < 0 or nueva_col >= self.columnas or nuevo_mapa[fila][nueva_col] != VACIO:
                    enemigo['direccion'] *= -1
                    nueva_col = col + enemigo['direccion']
                    
                # Si sigue sin poder moverse, se queda quieta
                if 0 <= nueva_col < self.columnas and nuevo_mapa[fila][nueva_col] == VACIO:
                    enemigo['columna'] = nueva_col
                    
            # IA Básica del Duende (Movimiento aleatorio o hacia jugador si quisiéramos)
            elif tipo == DUENDE:
                direcciones = [(-1,0), (1,0), (0,-1), (0,1)]
                np.random.shuffle(direcciones)
                for df, dc in direcciones:
                    nf, nc = fila + df, col + dc
                    if 0 <= nf < self.filas and 0 <= nc < self.columnas and nuevo_mapa[nf][nc] == VACIO:
                        enemigo['fila'] = nf
                        enemigo['columna'] = nc
                        break

            # Colocar en su nueva posición
            nuevo_mapa[enemigo['fila']][enemigo['columna']] = tipo
            
        self.mapa = nuevo_mapa
