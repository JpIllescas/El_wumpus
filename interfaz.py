import pygame
from entorno import VACIO, MURO, FUEGO, HUMANO, ESTACION, RATA, DUENDE

# Colores
COLOR_VACIO = (200, 200, 200)
COLOR_MURO = (100, 100, 100)
COLOR_FUEGO = (255, 50, 50)
COLOR_HUMANO = (50, 255, 50)
COLOR_ESTACION = (255, 255, 50)
COLOR_AGENTE = (50, 50, 255)
COLOR_TEXTO = (255, 255, 255)
COLOR_FONDO_PANEL = (30, 30, 30)

class Interfaz:
    def __init__(self, entorno, ancho_celda=40, ancho_panel=300):
        pygame.init()
        self.entorno = entorno
        self.ancho_celda = ancho_celda
        self.ancho_panel = ancho_panel
        self.alto_barra = 60
        
        self.ancho_mapa = entorno.columnas * ancho_celda
        self.alto_mapa = entorno.filas * ancho_celda
        
        self.ancho_ventana = self.ancho_mapa + ancho_panel
        self.alto_ventana = self.alto_mapa + self.alto_barra
        
        self.pantalla = pygame.display.set_mode((self.ancho_ventana, self.alto_ventana))
        pygame.display.set_caption("Agente de Rescate - Modo Sandbox")
        
        self.fuente = pygame.font.SysFont("Arial", 16)
        self.mensajes_log = []
        
        # Cargar sprite de la llama animada
        self.img_agente_frames = []
        self.frame_actual = 0
        self.tiempo_ultimo_frame = 0
        self.retraso_animacion = 150 # ms por frame
        
        try:
            spritesheet = pygame.image.load("assets/llama_animada.png").convert_alpha()
            # La imagen tiene 6 columnas y 1 fila. El ancho total se divide entre 6.
            ancho_frame = spritesheet.get_width() // 6
            alto_frame = spritesheet.get_height()
            
            for i in range(6):
                rect = pygame.Rect(i * ancho_frame, 0, ancho_frame, alto_frame)
                frame_crudo = spritesheet.subsurface(rect)
                tamano_sprite = int(self.ancho_celda * 1.25) # Hacerlo 25% más grande
                frame_escalado = pygame.transform.scale(frame_crudo, (tamano_sprite, tamano_sprite))
                self.img_agente_frames.append(frame_escalado)
        except Exception as e:
            print(f"No se pudo cargar llama_animada.png: {e}")
            self.img_agente_frames = []
            
        # Cargar sprites del entorno
        self.sprites = {}
        self.sprites_animados = {}
        self.tiempo_ultimo_frame_entorno = 0
        
        def cargar_spritesheet_horizontal(img_path, num_frames=1):
            try:
                img_completa = pygame.image.load(img_path).convert_alpha()
                ancho_frame = img_completa.get_width() // num_frames
                alto_frame = img_completa.get_height()
                frames = []
                for i in range(num_frames):
                    rect = pygame.Rect(i * ancho_frame, 0, ancho_frame, alto_frame)
                    frame_crudo = img_completa.subsurface(rect)
                    # Forzar al tamaño de celda exacto
                    frames.append(pygame.transform.scale(frame_crudo, (self.ancho_celda, self.ancho_celda)))
                return frames
            except Exception as e:
                print(f"Error cargando {img_path}: {e}")
                return None

        # Fuego.png es 128x16 -> 8 frames
        frames_fuego = cargar_spritesheet_horizontal("assets/fuego.png", num_frames=8)
        if frames_fuego: self.sprites_animados[FUEGO] = frames_fuego

        # Humano (Human_walk.png) es 192x32 -> 6 frames
        frames_humano = cargar_spritesheet_horizontal("assets/humano.png", num_frames=6)
        if frames_humano: self.sprites_animados[HUMANO] = frames_humano

        # Estacion (cofre.png) es 64x24 -> 4 frames
        frames_estacion = cargar_spritesheet_horizontal("assets/estacion.png", num_frames=4)
        if frames_estacion: self.sprites_animados[ESTACION] = frames_estacion

        # Rata (rata.png) es 192x32 -> 6 frames
        frames_rata = cargar_spritesheet_horizontal("assets/rata.png", num_frames=6)
        if frames_rata: self.sprites_animados[RATA] = frames_rata

        # Duende (duende.png) es 192x32 -> 6 frames
        frames_duende = cargar_spritesheet_horizontal("assets/duende.png", num_frames=6)
        if frames_duende: self.sprites_animados[DUENDE] = frames_duende
        
        # Herramientas del Modo Dios
        self.herramienta_actual = MURO
        self.colores_herramientas = {
            VACIO: COLOR_VACIO,
            MURO: COLOR_MURO,
            FUEGO: COLOR_FUEGO,
            HUMANO: COLOR_HUMANO,
            ESTACION: COLOR_ESTACION,
            RATA: (150, 50, 150),
            DUENDE: (50, 150, 150)
        }
        
    def log(self, mensaje):
        self.mensajes_log.append(mensaje)
        if len(self.mensajes_log) > 20:
            self.mensajes_log.pop(0)

    def dibujar_entorno(self):
        # Actualizar timer global de animación para el entorno
        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - self.tiempo_ultimo_frame_entorno > 200: # Velocidad de animacion del entorno
            self.tiempo_ultimo_frame_entorno = tiempo_actual
            self.frame_entorno_idx = (getattr(self, 'frame_entorno_idx', 0) + 1) % 4
            
        for fila in range(self.entorno.filas):
            for col in range(self.entorno.columnas):
                tipo = self.entorno.obtener_celda(fila, col)
                color = self.colores_herramientas.get(tipo, COLOR_VACIO)
                
                rect = pygame.Rect(col * self.ancho_celda, fila * self.ancho_celda, self.ancho_celda, self.ancho_celda)
                
                if hasattr(self, 'sprites_animados') and tipo in self.sprites_animados:
                    pygame.draw.rect(self.pantalla, COLOR_VACIO, rect) # Fondo gris limpio primero
                    frames = self.sprites_animados[tipo]
                    frame_a_dibujar = frames[getattr(self, 'frame_entorno_idx', 0) % len(frames)]
                    self.pantalla.blit(frame_a_dibujar, rect)
                elif hasattr(self, 'sprites') and tipo in self.sprites:
                    pygame.draw.rect(self.pantalla, COLOR_VACIO, rect)
                    self.pantalla.blit(self.sprites[tipo], rect)
                else:
                    pygame.draw.rect(self.pantalla, color, rect)
                    
                pygame.draw.rect(self.pantalla, (50, 50, 50), rect, 1) # Borde
                
    def dibujar_agente(self, x, y):
        if self.img_agente_frames:
            # Actualizar animación
            tiempo_actual = pygame.time.get_ticks()
            if tiempo_actual - self.tiempo_ultimo_frame > self.retraso_animacion:
                self.frame_actual = (self.frame_actual + 1) % len(self.img_agente_frames)
                self.tiempo_ultimo_frame = tiempo_actual
                
            # Calcular offset para centrar el sprite que es un poco más grande
            offset = (self.img_agente_frames[0].get_width() - self.ancho_celda) // 2
            self.pantalla.blit(self.img_agente_frames[self.frame_actual], (x - offset, y - offset))
        else:
            rect = pygame.Rect(x, y, self.ancho_celda, self.ancho_celda)
            pygame.draw.circle(self.pantalla, COLOR_AGENTE, rect.center, self.ancho_celda // 2 - 4)
        
    def dibujar_panel_registro(self):
        rect_panel = pygame.Rect(self.ancho_mapa, 0, self.ancho_panel, self.alto_ventana)
        pygame.draw.rect(self.pantalla, COLOR_FONDO_PANEL, rect_panel)
        
        titulo = self.fuente.render("Panel de Registro", True, COLOR_TEXTO)
        self.pantalla.blit(titulo, (self.ancho_mapa + 10, 50))
        
        y = 70
        for msg in self.mensajes_log:
            texto = self.fuente.render(msg, True, COLOR_TEXTO)
            self.pantalla.blit(texto, (self.ancho_mapa + 10, y))
            y += 20
            
    def dibujar_barra_herramientas(self):
        rect_barra = pygame.Rect(0, self.alto_mapa, self.ancho_mapa, self.alto_barra)
        pygame.draw.rect(self.pantalla, (60, 60, 60), rect_barra)
        
        # Dibujar opciones
        x = 10
        for tipo, color in self.colores_herramientas.items():
            rect_btn = pygame.Rect(x, self.alto_mapa + 10, 40, 40)
            
            # Dibujar icono en el boton si es posible, sino color solido
            if hasattr(self, 'sprites_animados') and tipo in self.sprites_animados:
                pygame.draw.rect(self.pantalla, COLOR_VACIO, rect_btn)
                frame = self.sprites_animados[tipo][0]
                self.pantalla.blit(frame, rect_btn)
            elif hasattr(self, 'sprites') and tipo in self.sprites:
                pygame.draw.rect(self.pantalla, COLOR_VACIO, rect_btn)
                self.pantalla.blit(self.sprites[tipo], rect_btn)
            else:
                pygame.draw.rect(self.pantalla, color, rect_btn)
                
            if self.herramienta_actual == tipo:
                pygame.draw.rect(self.pantalla, (255, 255, 255), rect_btn, 3)
            x += 60

    def dibujar_todo(self, agente_x=None, agente_y=None):
        self.pantalla.fill((0, 0, 0))
        self.dibujar_entorno()
        if agente_x is not None and agente_y is not None:
            self.dibujar_agente(agente_x, agente_y)
        self.dibujar_barra_herramientas()
        self.dibujar_panel_registro()
        pygame.display.flip()

    def procesar_clic(self, pos):
        x, y = pos
        # Clic en barra de herramientas
        if y >= self.alto_mapa and x < self.ancho_mapa:
            btn_idx = (x - 10) // 60
            if 0 <= btn_idx < len(self.colores_herramientas):
                tipos = list(self.colores_herramientas.keys())
                self.herramienta_actual = tipos[btn_idx]
                self.log(f"Herramienta: {self.herramienta_actual}")
        # Clic en mapa
        elif x < self.ancho_mapa and y < self.alto_mapa:
            col = x // self.ancho_celda
            fila = y // self.ancho_celda
            self.entorno.agregar_celda(fila, col, self.herramienta_actual)
            self.log(f"Celda ({fila},{col}) -> {self.herramienta_actual}")
