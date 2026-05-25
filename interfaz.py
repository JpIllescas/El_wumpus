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
COLOR_FONDO_PANEL = (15, 14, 12) # Marrón muy oscuro (GOW style)

class Interfaz:
    def __init__(self, entorno, ancho_celda=40, ancho_panel=350):
        pygame.init()
        self.entorno = entorno
        self.ancho_celda = ancho_celda
        self.ancho_panel = ancho_panel
        
        # Dimensiones de las áreas
        self.alto_hud = 60
        self.alto_barra_herramientas = 70
        
        self.ancho_mapa = entorno.columnas * ancho_celda
        self.alto_mapa = entorno.filas * ancho_celda
        
        self.ancho_ventana = self.ancho_mapa + ancho_panel
        self.alto_ventana = self.alto_hud + self.alto_mapa + self.alto_barra_herramientas
        
        self.pantalla = pygame.display.set_mode((self.ancho_ventana, self.alto_ventana), pygame.RESIZABLE | pygame.SCALED)
        pygame.display.set_caption("Rescue Agent: Ollama")
        
        try:
            icono = pygame.image.load("assets/icon.png").convert_alpha()
            pygame.display.set_icon(icono)
        except Exception as e:
            print("No se pudo cargar el icono de la ventana:", e)
        
        # Inicializar sonidos de interfaz (silenciosos si no existen)
        try:
            self.snd_hover = pygame.mixer.Sound("assets/hover.wav")
            self.snd_hover.set_volume(0.2)
        except Exception:
            self.snd_hover = None
            
        try:
            self.snd_clic = pygame.mixer.Sound("assets/click.wav")
            self.snd_clic.set_volume(0.5)
        except Exception:
            self.snd_clic = None
            
        self.btn_hover_anterior = None # Para rastrear cuando el ratón entra a un botón nuevo
        
        try:
            self.fuente_grande = pygame.font.Font("assets/font.otf", 24)
            self.fuente_media = pygame.font.Font("assets/font.otf", 18)
            # Cambiamos fuente_pequena a Consolas para el log para mejor legibilidad estilo terminal/pixel
            self.fuente_pequena = pygame.font.SysFont("Consolas", 11, bold=True)
            self.fuente_botones = pygame.font.Font("assets/font.otf", 14)
            self.fuente_hud_vol = pygame.font.SysFont("Segoe UI", 24, bold=True)
        except Exception:
            self.fuente_grande = pygame.font.SysFont("Segoe UI", 24, bold=True)
            self.fuente_media = pygame.font.SysFont("Segoe UI", 18, bold=True)
            self.fuente_pequena = pygame.font.SysFont("Consolas", 12)
            self.fuente_botones = pygame.font.SysFont("Segoe UI", 14, bold=True)
            self.fuente_hud_vol = pygame.font.SysFont("Segoe UI", 24, bold=True)
        
        self.mensajes_log = []
        
        # Botones de Acción (UI)
        self.botones_ui = {
            'TOGGLE_SIM': pygame.Rect(self.ancho_mapa + 20, self.alto_hud + 360, 310, 40),
            'A_STAR': pygame.Rect(self.ancho_mapa + 20, self.alto_hud + 410, 150, 35),
            'BFS': pygame.Rect(self.ancho_mapa + 180, self.alto_hud + 410, 150, 35),
            'COMPARAR': pygame.Rect(self.ancho_mapa + 20, self.alto_hud + 455, 310, 35),
            'TRAIN_Q': pygame.Rect(self.ancho_mapa + 20, self.alto_hud + 500, 150, 35),
            'EXEC_Q': pygame.Rect(self.ancho_mapa + 180, self.alto_hud + 500, 150, 35),
            'AUTO_GEN': pygame.Rect(self.ancho_mapa + 20, self.alto_hud + 545, 310, 35),
            'REINICIAR': pygame.Rect(self.ancho_mapa + 20, self.alto_hud + 590, 310, 35),
            'LOGS': pygame.Rect(self.ancho_ventana - 140, 20, 30, 30),
            'VOL_DOWN': pygame.Rect(self.ancho_ventana - 90, 20, 30, 30),
            'VOL_UP': pygame.Rect(self.ancho_ventana - 40, 20, 30, 30)
        }
        
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
        if len(self.mensajes_log) > 500: # Aumentado para historial largo
            self.mensajes_log.pop(0)

    def dibujar_fondo_cuadricula(self):
        # Dibujar un patrón de ajedrez sutil
        color1 = (40, 42, 45)
        color2 = (45, 47, 50)
        for fila in range(self.entorno.filas):
            for col in range(self.entorno.columnas):
                color = color1 if (fila + col) % 2 == 0 else color2
                rect = pygame.Rect(col * self.ancho_celda, self.alto_hud + (fila * self.ancho_celda), self.ancho_celda, self.ancho_celda)
                pygame.draw.rect(self.pantalla, color, rect)

    def dibujar_entorno(self):
        self.dibujar_fondo_cuadricula()
        
        # Actualizar timer global de animación para el entorno
        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - self.tiempo_ultimo_frame_entorno > 200: # Velocidad de animacion del entorno
            self.tiempo_ultimo_frame_entorno = tiempo_actual
            self.frame_entorno_idx = (getattr(self, 'frame_entorno_idx', 0) + 1) % 4
            
        for fila in range(self.entorno.filas):
            for col in range(self.entorno.columnas):
                tipo = self.entorno.obtener_celda(fila, col)
                
                if tipo == VACIO:
                    continue # El fondo de cuadricula ya está dibujado
                    
                rect = pygame.Rect(col * self.ancho_celda, self.alto_hud + (fila * self.ancho_celda), self.ancho_celda, self.ancho_celda)
                
                if hasattr(self, 'sprites_animados') and tipo in self.sprites_animados:
                    frames = self.sprites_animados[tipo]
                    frame_a_dibujar = frames[getattr(self, 'frame_entorno_idx', 0) % len(frames)]
                    self.pantalla.blit(frame_a_dibujar, rect)
                elif hasattr(self, 'sprites') and tipo in self.sprites:
                    self.pantalla.blit(self.sprites[tipo], rect)
                else:
                    color = self.colores_herramientas.get(tipo, COLOR_VACIO)
                    pygame.draw.rect(self.pantalla, color, rect)
                    
                # pygame.draw.rect(self.pantalla, (50, 50, 50), rect, 1) # Borde opcional
                
    def dibujar_agente(self, x, y, agente):
        # Ajustar 'y' con el alto_hud
        y_real = y + self.alto_hud
        if self.img_agente_frames:
            # Actualizar animación
            tiempo_actual = pygame.time.get_ticks()
            if tiempo_actual - self.tiempo_ultimo_frame > self.retraso_animacion:
                self.frame_actual = (self.frame_actual + 1) % len(self.img_agente_frames)
                self.tiempo_ultimo_frame = tiempo_actual
                
            # Calcular offset para centrar el sprite que es un poco más grande
            offset = (self.img_agente_frames[0].get_width() - self.ancho_celda) // 2
            self.pantalla.blit(self.img_agente_frames[self.frame_actual], (x - offset, y_real - offset))
        else:
            rect = pygame.Rect(x, y_real, self.ancho_celda, self.ancho_celda)
            pygame.draw.circle(self.pantalla, COLOR_AGENTE, rect.center, self.ancho_celda // 2 - 4)
            
        # Dibujar rueda de energía estilo Zelda BotW sobre el agente
        import math
        porcentaje_energia = agente.energia_actual / agente.energia_maxima
        centro_rueda = (x + self.ancho_celda // 2, y_real - 10)
        radio_rueda = 12
        grosor_rueda = 4
        
        # Fondo de la rueda (negro semitransparente)
        sup_rueda = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(sup_rueda, (0, 0, 0, 150), (15, 15), radio_rueda, grosor_rueda)
        
        # Arco verde de la energía restante
        color_rueda = (50, 255, 50) if porcentaje_energia > 0.3 else (255, 50, 50)
        if porcentaje_energia > 0:
            angulo_fin = 360 * porcentaje_energia
            rect_arco = pygame.Rect(15 - radio_rueda, 15 - radio_rueda, radio_rueda * 2, radio_rueda * 2)
            pygame.draw.arc(sup_rueda, color_rueda, rect_arco, math.radians(90), math.radians(90 + angulo_fin), grosor_rueda)
            
        self.pantalla.blit(sup_rueda, (centro_rueda[0] - 15, centro_rueda[1] - 15))
        
    def dibujar_hud(self, agente):
        rect_hud = pygame.Rect(0, 0, self.ancho_ventana, self.alto_hud)
        pygame.draw.rect(self.pantalla, (10, 10, 12), rect_hud) # Fondo HUD muy oscuro, casi negro
        pygame.draw.line(self.pantalla, (197, 168, 128), (0, self.alto_hud), (self.ancho_ventana, self.alto_hud), 2) # Linea cobre/bronce delgada
        
        # Barra de Energía (Estilo God of War Auténtico)
        ancho_barra_max = 250
        ancho_barra_actual = int((agente.energia_actual / agente.energia_maxima) * ancho_barra_max)
        
        # Verde brillante GoW
        color_barra = (125, 209, 79) if agente.energia_actual > 30 else (220, 60, 40)
        
        # Rombo decorativo principal (Base de la barra)
        centro_rombo = (45, 25)
        puntos_rombo = [
            (centro_rombo[0], centro_rombo[1] - 18),
            (centro_rombo[0] + 18, centro_rombo[1]),
            (centro_rombo[0], centro_rombo[1] + 18),
            (centro_rombo[0] - 18, centro_rombo[1])
        ]
        pygame.draw.polygon(self.pantalla, (20, 20, 20), puntos_rombo)
        pygame.draw.polygon(self.pantalla, (197, 168, 128), puntos_rombo, 2) # Bronce/Oro viejo
        
        # Emblema dentro del rombo
        pygame.draw.circle(self.pantalla, (100, 90, 80), centro_rombo, 8, 1)
        txt_e = self.fuente_botones.render("E", True, (255, 255, 255))
        self.pantalla.blit(txt_e, txt_e.get_rect(center=centro_rombo))
        
        # Fondo de la barra (Más oscuro)
        rect_fondo = pygame.Rect(70, 18, ancho_barra_max, 14)
        pygame.draw.rect(self.pantalla, (25, 25, 25), rect_fondo)
        
        # Barra interior brillante
        if ancho_barra_actual > 0:
            rect_interior = pygame.Rect(70, 18, ancho_barra_actual, 14)
            pygame.draw.rect(self.pantalla, color_barra, rect_interior)
            # Brillo superior para efecto 3D
            pygame.draw.rect(self.pantalla, (200, 255, 150), (70, 18, ancho_barra_actual, 3))
            
        # Marco de la barra con ángulos
        pygame.draw.line(self.pantalla, (197, 168, 128), (70, 17), (70 + ancho_barra_max, 17), 2)
        pygame.draw.line(self.pantalla, (197, 168, 128), (70, 32), (70 + ancho_barra_max, 32), 2)
        # Remate final angular (Punta de la barra)
        puntos_remate = [
            (70 + ancho_barra_max, 17),
            (70 + ancho_barra_max + 10, 24),
            (70 + ancho_barra_max, 33)
        ]
        pygame.draw.polygon(self.pantalla, (10, 10, 12), puntos_remate) # Tapar lo que sobresale
        pygame.draw.polygon(self.pantalla, (197, 168, 128), puntos_remate, 2)
        
        # Línea de la interfaz por debajo de la barra para darle base
        pygame.draw.line(self.pantalla, (60, 55, 50), (45, 42), (70 + ancho_barra_max + 15, 42), 1)

        # Texto debajo de la barra
        txt_energia = self.fuente_botones.render(f"ENERGIA {agente.energia_actual}/{agente.energia_maxima}", True, (160, 160, 160))
        self.pantalla.blit(txt_energia, (75, 45))
        
        # ----------------------------------------------------
        # Rescatados
        # ----------------------------------------------------
        centro_r = (380, 25)
        puntos_r = [
            (centro_r[0], centro_r[1] - 15),
            (centro_r[0] + 15, centro_r[1]),
            (centro_r[0], centro_r[1] + 15),
            (centro_r[0] - 15, centro_r[1])
        ]
        pygame.draw.polygon(self.pantalla, (20, 20, 20), puntos_r)
        pygame.draw.polygon(self.pantalla, (100, 150, 220), puntos_r, 2) # Azul pálido / Plata
        
        pygame.draw.circle(self.pantalla, (80, 100, 120), centro_r, 6, 1)
        txt_r = self.fuente_botones.render("R", True, (255, 255, 255))
        self.pantalla.blit(txt_r, txt_r.get_rect(center=(centro_r[0]+1, centro_r[1])))
        
        txt_rescatados = self.fuente_media.render(f"RESCATADOS: {agente.humanos_rescatados}", True, (220, 220, 220))
        self.pantalla.blit(txt_rescatados, (405, 15))
        pygame.draw.line(self.pantalla, (60, 55, 50), (380, 42), (540, 42), 1)
        
        # Estado (Cargando humano)
        if agente.cargando_humano:
            txt_cargando = self.fuente_media.render("LLEVANDO AL HOSPITAL", True, (100, 150, 220))
            self.pantalla.blit(txt_cargando, (560, 15))
            pygame.draw.line(self.pantalla, (60, 55, 50), (560, 42), (750, 42), 1)
            
        # Botones de opciones en el HUD (Forma de rombo)
        for key in ['LOGS', 'VOL_DOWN', 'VOL_UP']:
            rect = self.botones_ui[key]
            hover = rect.collidepoint(pygame.mouse.get_pos())
            
            # Sonido
            if hover and self.btn_hover_anterior != key:
                if getattr(self, 'snd_hover', None):
                    self.snd_hover.play()
                self.btn_hover_anterior = key
            
            color_bg = (30, 28, 25) if not hover else (60, 50, 40)
            color_borde = (120, 110, 100) if not hover else (197, 168, 128)
            
            cx, cy = rect.center
            puntos_vol = [
                (cx, cy - 14),
                (cx + 14, cy),
                (cx, cy + 14),
                (cx - 14, cy)
            ]
            pygame.draw.polygon(self.pantalla, color_bg, puntos_vol)
            pygame.draw.polygon(self.pantalla, color_borde, puntos_vol, 2)
            
            texto = ""
            if key == 'VOL_DOWN': texto = "-"
            elif key == 'VOL_UP': texto = "+"
            elif key == 'LOGS': texto = "L"
            
            txt = self.fuente_hud_vol.render(texto, True, (255, 255, 255))
            self.pantalla.blit(txt, txt.get_rect(center=(cx, cy - 2)))

    def dibujar_panel_registro(self):
        rect_panel = pygame.Rect(self.ancho_mapa, self.alto_hud, self.ancho_panel, self.alto_ventana - self.alto_hud)
        pygame.draw.rect(self.pantalla, COLOR_FONDO_PANEL, rect_panel)
        pygame.draw.line(self.pantalla, (197, 168, 128), (self.ancho_mapa, self.alto_hud), (self.ancho_mapa, self.alto_ventana), 2)
        
        titulo = self.fuente_grande.render("LOG DE ACCIONES", True, (197, 168, 128))
        self.pantalla.blit(titulo, (self.ancho_mapa + 20, self.alto_hud + 20))
        
        y = self.alto_hud + 60
        for msg in self.mensajes_log[-15:]: # Mostrar menos mensajes para dar espacio a botones
            texto = self.fuente_pequena.render(msg, True, (200, 200, 200))
            self.pantalla.blit(texto, (self.ancho_mapa + 20, y))
            y += 22
            
        # Dibujar Botones UI
        colores_btn = {
            'TOGGLE_SIM': (200, 150, 50) if not getattr(self, 'simulacion_activa', False) else (50, 200, 50),
            'A_STAR': (60, 120, 200),
            'BFS': (100, 100, 180),
            'COMPARAR': (150, 100, 200),
            'TRAIN_Q': (180, 80, 80),
            'EXEC_Q': (200, 100, 100),
            'AUTO_GEN': (100, 160, 100),
            'REINICIAR': (80, 80, 80),
            'LOGS': (100, 100, 100),
            'VOL_DOWN': (60, 80, 100),
            'VOL_UP': (60, 80, 100)
        }
        textos_btn = {
            'TOGGLE_SIM': "INICIAR SIMULACION" if not getattr(self, 'simulacion_activa', False) else "PAUSAR SIMULACION",
            'A_STAR': "Utilidad (A*)",
            'BFS': "Busqueda (BFS)",
            'COMPARAR': "Comparar A* vs BFS",
            'TRAIN_Q': "Entrenar Q",
            'EXEC_Q': "Ejecutar Q",
            'AUTO_GEN': "Generar Mapa Aleatorio",
            'REINICIAR': "Reiniciar Juego",
            'LOGS': "Ver Logs",
            'VOL_DOWN': "Volumen -",
            'VOL_UP': "Volumen +"
        }
        
        for key, rect in self.botones_ui.items():
            if key in ['LOGS', 'VOL_DOWN', 'VOL_UP']:
                continue # Los dibujamos en el HUD
                
            hover = rect.collidepoint(pygame.mouse.get_pos())
            
            # Sonido de hover
            if hover and self.btn_hover_anterior != key:
                if getattr(self, 'snd_hover', None):
                    self.snd_hover.play()
                self.btn_hover_anterior = key
            elif not hover and self.btn_hover_anterior == key:
                self.btn_hover_anterior = None
                
            # Colores base estilo GOW (Marrón oscuro, grises, cobres)
            # Aplicar sutiles tintes rojo, verde y azul para diferenciar grupos
            if key in ['A_STAR', 'BFS', 'COMPARAR']:
                # Tinte Azul pálido (Hielo/Magia)
                color_fondo = (20, 25, 35) if not hover else (35, 45, 60)
                color_borde = (100, 130, 160) if not hover else (150, 190, 230)
            elif key in ['TRAIN_Q', 'EXEC_Q']:
                # Tinte Rojo oscuro (Furia/Sangre)
                color_fondo = (35, 20, 20) if not hover else (60, 30, 30)
                color_borde = (160, 80, 80) if not hover else (220, 100, 100)
            elif key in ['AUTO_GEN', 'REINICIAR']:
                # Tinte Verde oscuro (Vida/Tierra)
                color_fondo = (20, 30, 20) if not hover else (35, 50, 35)
                color_borde = (90, 140, 90) if not hover else (140, 200, 140)
            else:
                color_fondo = (30, 28, 25) if not hover else (50, 46, 40)
                color_borde = (120, 110, 100) if not hover else (197, 168, 128)
            
            if key == 'TOGGLE_SIM':
                color_fondo = (40, 35, 20) if not hover else (60, 50, 25)
                color_borde = (197, 168, 128) if not hover else (255, 230, 150)
                
            # Fondo del botón
            pygame.draw.rect(self.pantalla, color_fondo, rect)
            
            # Borde principal (Fino y afilado)
            pygame.draw.rect(self.pantalla, color_borde, rect, 1)
            
            # Detalles de esquinas (Cruces/runas para aspecto épico)
            longitud_esquina = 6
            # Superior izquierda
            pygame.draw.line(self.pantalla, color_borde, rect.topleft, (rect.left + longitud_esquina, rect.top), 2)
            pygame.draw.line(self.pantalla, color_borde, rect.topleft, (rect.left, rect.top + longitud_esquina), 2)
            # Superior derecha
            pygame.draw.line(self.pantalla, color_borde, rect.topright, (rect.right - longitud_esquina, rect.top), 2)
            pygame.draw.line(self.pantalla, color_borde, rect.topright, (rect.right, rect.top + longitud_esquina), 2)
            # Inferior izquierda
            pygame.draw.line(self.pantalla, color_borde, rect.bottomleft, (rect.left + longitud_esquina, rect.bottom), 2)
            pygame.draw.line(self.pantalla, color_borde, rect.bottomleft, (rect.left, rect.bottom - longitud_esquina), 2)
            # Inferior derecha
            pygame.draw.line(self.pantalla, color_borde, rect.bottomright, (rect.right - longitud_esquina, rect.bottom), 2)
            pygame.draw.line(self.pantalla, color_borde, rect.bottomright, (rect.right, rect.bottom - longitud_esquina), 2)
            
            # Sombra del texto (Drop shadow)
            txt_sombra = self.fuente_botones.render(textos_btn[key], True, (0, 0, 0))
            txt_rect_sombra = txt_sombra.get_rect(center=(rect.centerx + 1, rect.centery + 1))
            self.pantalla.blit(txt_sombra, txt_rect_sombra)
            
            # Texto principal
            color_txt = (200, 200, 200) if not hover else (255, 255, 255)
            if key == 'TOGGLE_SIM':
                color_txt = (240, 220, 180) if not hover else (255, 255, 255)
                
            txt = self.fuente_botones.render(textos_btn[key], True, color_txt)
            txt_rect = txt.get_rect(center=rect.center)
            self.pantalla.blit(txt, txt_rect)
            
    def dibujar_barra_herramientas(self):
        rect_barra = pygame.Rect(0, self.alto_hud + self.alto_mapa, self.ancho_mapa, self.alto_barra_herramientas)
        pygame.draw.rect(self.pantalla, (30, 30, 35), rect_barra)
        pygame.draw.line(self.pantalla, (100, 100, 100), (0, self.alto_hud + self.alto_mapa), (self.ancho_mapa, self.alto_hud + self.alto_mapa), 2)
        
        txt_herramienta = self.fuente_media.render("MODO DIOS (Pinceles):", True, (200, 200, 200))
        self.pantalla.blit(txt_herramienta, (20, self.alto_hud + self.alto_mapa + 25))
        
        # Dibujar opciones
        x = 220
        y_barra = self.alto_hud + self.alto_mapa + 15
        for tipo, color in self.colores_herramientas.items():
            rect_btn = pygame.Rect(x, y_barra, 40, 40)
            
            es_activo = (self.herramienta_actual == tipo)
            color_fondo_btn = (60, 60, 65) if es_activo else (20, 20, 25)
            
            # Dibujar fondo oscuro y borde exterior estilizado
            pygame.draw.rect(self.pantalla, color_fondo_btn, rect_btn, border_radius=5)
            
            # Dibujar icono en el boton si es posible, sino color solido (más pequeño para encajar en el borde)
            rect_icono = pygame.Rect(x+4, y_barra+4, 32, 32)
            if hasattr(self, 'sprites_animados') and tipo in self.sprites_animados:
                frame = pygame.transform.scale(self.sprites_animados[tipo][0], (32, 32))
                self.pantalla.blit(frame, rect_icono)
            elif hasattr(self, 'sprites') and tipo in self.sprites:
                frame = pygame.transform.scale(self.sprites[tipo], (32, 32))
                self.pantalla.blit(frame, rect_icono)
            else:
                pygame.draw.rect(self.pantalla, color, rect_icono, border_radius=3)
                
            color_borde = (255, 215, 0) if es_activo else (100, 100, 100) # Oro si es activo, gris si no
            pygame.draw.rect(self.pantalla, color_borde, rect_btn, 2, border_radius=5)
            
            x += 60

    def dibujar_popup(self, titulo, mensaje):
        s = pygame.Surface((self.ancho_ventana, self.alto_ventana))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        self.pantalla.blit(s, (0, 0))
        
        rect_popup = pygame.Rect(0, 0, 550, 200) # Un poco más ancho para que quepa bien el texto de Consolas
        rect_popup.center = (self.ancho_ventana//2, self.alto_ventana//2)
        pygame.draw.rect(self.pantalla, (40, 40, 45), rect_popup, border_radius=10)
        pygame.draw.rect(self.pantalla, (197, 168, 128), rect_popup, 2, border_radius=10) # Borde color GOW
        
        txt_titulo = self.fuente_grande.render(titulo, True, (255, 200, 50))
        rect_titulo = txt_titulo.get_rect(center=(rect_popup.centerx, rect_popup.top + 40))
        self.pantalla.blit(txt_titulo, rect_titulo)
        
        # Usamos Consolas (fuente_pequena o una media similar) pero mas grande
        try:
            fuente_popup_msg = pygame.font.SysFont("Consolas", 14, bold=True)
        except:
            fuente_popup_msg = self.fuente_pequena
            
        txt_msg = fuente_popup_msg.render(mensaje, True, (255, 255, 255))
        rect_msg = txt_msg.get_rect(center=(rect_popup.centerx, rect_popup.centery + 10))
        self.pantalla.blit(txt_msg, rect_msg)
        
        txt_btn = self.fuente_botones.render("Haz clic o presiona Enter para continuar", True, (150, 150, 150))
        rect_btn = txt_btn.get_rect(center=(rect_popup.centerx, rect_popup.bottom - 30))
        self.pantalla.blit(txt_btn, rect_btn)

    def dibujar_todo(self, agente, agente_x=None, agente_y=None, auto_flip=True):
        self.pantalla.fill((0, 0, 0))
        self.dibujar_entorno()
        if agente_x is not None and agente_y is not None:
            self.dibujar_agente(agente_x, agente_y, agente)
        self.dibujar_hud(agente)
        self.dibujar_barra_herramientas()
        self.dibujar_panel_registro()
        
        # Alerta de Game Over
        if agente.energia_actual <= 0:
            s = pygame.Surface((self.ancho_mapa, self.alto_mapa))
            s.set_alpha(128)
            s.fill((255,0,0))
            self.pantalla.blit(s, (0, self.alto_hud))
            
            txt_go = self.fuente_grande.render("¡AGENTE SIN ENERGIA!", True, (255, 255, 255))
            rect_go = txt_go.get_rect(center=(self.ancho_mapa//2, self.alto_hud + self.alto_mapa//2))
            self.pantalla.blit(txt_go, rect_go)
            
        if auto_flip:
            pygame.display.flip()

    def procesar_clic(self, pos):
        x, y = pos
        # Clic en barra de herramientas
        y_barra = self.alto_hud + self.alto_mapa
        if y >= y_barra and x < self.ancho_mapa and x >= 220:
            btn_idx = (x - 220) // 60
            if 0 <= btn_idx < len(self.colores_herramientas):
                tipos = list(self.colores_herramientas.keys())
                self.herramienta_actual = tipos[btn_idx]
                self.log(f"Herramienta seleccionada: {self.herramienta_actual}")
                return "HERRAMIENTA"
                
        # Clic en mapa
        elif x < self.ancho_mapa and self.alto_hud <= y < y_barra:
            col = x // self.ancho_celda
            fila = (y - self.alto_hud) // self.ancho_celda
            self.entorno.agregar_celda(fila, col, self.herramienta_actual)
            return "MAPA"
            
        # Clic en botones UI o HUD
        for key, rect in self.botones_ui.items():
            if rect.collidepoint(pos):
                if getattr(self, 'snd_clic', None):
                    self.snd_clic.play()
                return key
                    
        return None
