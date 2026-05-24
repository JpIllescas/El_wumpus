import pygame
import sys
import math
from entorno import Entorno, HUMANO, ESTACION
from interfaz import Interfaz
from agente import Agente
from ia_motores import Busqueda, TomaDeDecision, MotorInferencia, QLearning

import random

def reiniciar_juego(entorno, agente, interfaz):
    entorno.limpiar_mapa()
    agente.fila = 0
    agente.columna = 0
    agente.energia_actual = agente.energia_maxima
    agente.humanos_rescatados = 0
    agente.cargando_humano = False
    agente.ruta_actual = []
    interfaz.log("Juego reiniciado.")
    
def generar_mapa_aleatorio(entorno, interfaz):
    entorno.limpiar_mapa()
    # Generar muros aleatorios
    for _ in range(30):
        f, c = random.randint(0, entorno.filas-1), random.randint(0, entorno.columnas-1)
        if (f, c) != (0, 0): entorno.agregar_celda(f, c, 1) # MURO
    
    # Generar fuego
    for _ in range(10):
        f, c = random.randint(0, entorno.filas-1), random.randint(0, entorno.columnas-1)
        if (f, c) != (0, 0) and entorno.obtener_celda(f, c) == 0: entorno.agregar_celda(f, c, 2) # FUEGO
        
    # Generar humanos
    for _ in range(5):
        f, c = random.randint(0, entorno.filas-1), random.randint(0, entorno.columnas-1)
        if (f, c) != (0, 0) and entorno.obtener_celda(f, c) == 0: entorno.agregar_celda(f, c, 3) # HUMANO
        
    # Generar base/estacion
    for _ in range(1):
        f, c = random.randint(0, entorno.filas-1), random.randint(0, entorno.columnas-1)
        if (f, c) != (0, 0) and entorno.obtener_celda(f, c) == 0: entorno.agregar_celda(f, c, 4) # ESTACION
        
    # Generar enemigos
    for _ in range(2):
        f, c = random.randint(0, entorno.filas-1), random.randint(0, entorno.columnas-1)
        if (f, c) != (0, 0) and entorno.obtener_celda(f, c) == 0: entorno.agregar_celda(f, c, 5) # RATA
    for _ in range(1):
        f, c = random.randint(0, entorno.filas-1), random.randint(0, entorno.columnas-1)
        if (f, c) != (0, 0) and entorno.obtener_celda(f, c) == 0: entorno.agregar_celda(f, c, 6) # DUENDE
        
    interfaz.log("Mapa aleatorio generado.")

def main():
    # Configuración inicial
    FILAS = 15
    COLUMNAS = 20
    
    entorno = Entorno(FILAS, COLUMNAS)
    interfaz = Interfaz(entorno)
    agente = Agente(0, 0) # Agente inicia en (0,0)
    
    # Conectar el agente con el panel de log de la interfaz
    agente.log_callback = interfaz.log
    
    interfaz.log("Sistema iniciado.")
    interfaz.log("Modo Dios activado. Pinta el mapa.")
    interfaz.log("[ESPACIO] Toma de Decisiones Autónoma")
    interfaz.log("[B] Busqueda BFS (No Informada)")
    interfaz.log("[T] Entrenar Q-Learning")
    interfaz.log("[Q] Ejecutar ruta Q-Learning")
    
    reloj = pygame.time.Clock()
    ejecutando = True
    
    # Instancia de Q-Learning
    motor_q = QLearning(entorno)
    
    # Variables para animación de movimiento fluido
    agente_visual_x = agente.columna * interfaz.ancho_celda
    agente_visual_y = agente.fila * interfaz.ancho_celda
    velocidad = 5 # Píxeles por frame
    
    tiempo_ultimo_enemigo = 0
    retraso_enemigos = 500 # Se mueven cada 500ms
    
    ESTADO_INTRO = 0
    ESTADO_MENU = 1
    ESTADO_JUEGO = 2
    
    estado_actual = ESTADO_INTRO
    
    # Variables de intro
    intro_alpha_1 = 0
    intro_alpha_2 = 0
    intro_fase = 0 # 0: FadeIn 1, 1: FadeOut 1, 2: FadeIn 2, 3: FadeOut 2
    intro_tiempo_inicio = pygame.time.get_ticks()
    
    try:
        pygame.mixer.music.load("assets/intro.opus")
        pygame.mixer.music.play(-1) # Loop infinito
    except Exception as e:
        print("No se pudo cargar musica de intro:", e)
        
    while ejecutando:
        tiempo_actual = pygame.time.get_ticks()
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
                
            if estado_actual == ESTADO_INTRO:
                if evento.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    estado_actual = ESTADO_MENU
            
            elif estado_actual == ESTADO_MENU:
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    y_opcion = 250
                    for i, opcion in enumerate(["NUEVA SIMULACION", "GENERAR MAPA ALEATORIO", "SALIR"]):
                        rect_hover = pygame.Rect(50, y_opcion - 5, 400, 40)
                        if rect_hover.collidepoint(evento.pos):
                            if i == 0:
                                estado_actual = ESTADO_JUEGO
                                try:
                                    pygame.mixer.music.load("assets/juego.opus")
                                    pygame.mixer.music.play(-1) # Loop infinito
                                except Exception as e:
                                    print("No se pudo cargar musica de juego:", e)
                            elif i == 1:
                                generar_mapa_aleatorio(entorno, interfaz)
                            elif i == 2:
                                ejecutando = False
                        y_opcion += 60
                            
            elif estado_actual == ESTADO_JUEGO:
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if evento.button == 1: # Clic izquierdo
                        accion = interfaz.procesar_clic(evento.pos)
                        
                        if accion == 'A_STAR':
                            interfaz.log(f"Energia: {agente.energia_actual}%. Pensando...")
                            mejor_ruta, mejor_objetivo = TomaDeDecision.decidir_mejor_accion(agente, entorno, interfaz)
                            if mejor_ruta:
                                agente.establecer_ruta(mejor_ruta)
                                
                        elif accion == 'BFS':
                            humanos = entorno.obtener_posiciones_tipo(HUMANO)
                            if humanos:
                                objetivo = humanos[0]
                                inicio = (agente.fila, agente.columna)
                                interfaz.log(f"Buscando con BFS hacia Humano...")
                                ruta, nodos, tiempo = Busqueda.bfs(entorno, inicio, objetivo)
                                if ruta:
                                    interfaz.log(f"BFS: Ruta hallada en {tiempo}s")
                                    interfaz.log(f"BFS: Nodos explorados: {nodos}")
                                    agente.establecer_ruta(ruta)
                                else:
                                    interfaz.log("BFS: No hay ruta posible.")
                            else:
                                interfaz.log("Error: No hay humanos en el mapa.")
                                
                        elif accion == 'TRAIN_Q':
                            humanos = entorno.obtener_posiciones_tipo(HUMANO)
                            if humanos:
                                objetivo = humanos[0]
                                inicio = (agente.fila, agente.columna)
                                interfaz.log(f"Entrenando Q-Learning (500 ep.)...")
                                tiempo_entrenamiento = motor_q.entrenar(inicio, objetivo, 500)
                                interfaz.log(f"Entrenamiento completado en {tiempo_entrenamiento}s")
                            else:
                                interfaz.log("Error: No hay humanos para entrenar.")
                                
                        elif accion == 'EXEC_Q':
                            humanos = entorno.obtener_posiciones_tipo(HUMANO)
                            if humanos:
                                objetivo = humanos[0]
                                inicio = (agente.fila, agente.columna)
                                interfaz.log(f"Ejecutando Q-Learning...")
                                ruta = motor_q.obtener_ruta(inicio, objetivo)
                                if ruta:
                                    interfaz.log(f"Q-Learning: Ruta óptima hallada.")
                                    agente.establecer_ruta(ruta)
                                else:
                                    interfaz.log("Q-Learning: Aún no sabe cómo llegar.")
                            else:
                                interfaz.log("Error: No hay humanos en el mapa.")
                                
                        elif accion == 'AUTO_GEN':
                            generar_mapa_aleatorio(entorno, interfaz)
                            
                        elif accion == 'REINICIAR':
                            reiniciar_juego(entorno, agente, interfaz)
                            agente_visual_x = agente.columna * interfaz.ancho_celda
                            agente_visual_y = agente.fila * interfaz.ancho_celda
                            
                        elif accion == 'VOL_DOWN':
                            vol = pygame.mixer.music.get_volume()
                            nuevo_vol = max(0.0, vol - 0.1)
                            pygame.mixer.music.set_volume(nuevo_vol)
                            interfaz.log(f"Volumen: {int(nuevo_vol*100)}%")
                            
                        elif accion == 'VOL_UP':
                            vol = pygame.mixer.music.get_volume()
                            nuevo_vol = min(1.0, vol + 0.1)
                            pygame.mixer.music.set_volume(nuevo_vol)
                            interfaz.log(f"Volumen: {int(nuevo_vol*100)}%")
                        
                elif evento.type == pygame.MOUSEMOTION:
                    if pygame.mouse.get_pressed()[0]:
                        interfaz.procesar_clic(evento.pos)
                    
        if estado_actual == ESTADO_INTRO:
            interfaz.pantalla.fill((0, 0, 0))
            
            try:
                fuente_intro = pygame.font.Font("assets/font.otf", 40)
                fuente_intro_peq = pygame.font.Font("assets/font.otf", 24)
            except Exception:
                fuente_intro = pygame.font.SysFont("Segoe UI", 36)
                fuente_intro_peq = pygame.font.SysFont("Segoe UI", 24)
            
            # Textos de Santa Monica Style
            texto1 = fuente_intro.render("Universidad Mariano Galvez", True, (255, 255, 255))
            texto1_sub = fuente_intro_peq.render("presenta", True, (200, 200, 200))
            
            texto2 = fuente_intro.render("Un proyecto de", True, (255, 255, 255))
            texto3 = fuente_intro_peq.render("Jose Pablo Illescas y Sebastian Holweger", True, (200, 200, 200))
            
            dt = tiempo_actual - intro_tiempo_inicio
            velocidad_fade = 4 # Más rápido para transiciones fluidas
            
            # Máquina de estados interna para la intro (más detallada)
            # Fase 0: Espera inicial (1s)
            # Fase 1: Fade-in texto 1
            # Fase 2: Hold texto 1 (2.5s)
            # Fase 3: Fade-out texto 1
            # Fase 4: Espera en negro (0.5s)
            # Fase 5: Fade-in texto 2
            # Fase 6: Hold texto 2 (2.5s)
            # Fase 7: Fade-out texto 2
            # Fase 8: Fin -> MENU
            
            if intro_fase == 0:
                if dt > 1000:
                    intro_fase = 1
                    intro_tiempo_inicio = tiempo_actual
            elif intro_fase == 1:
                intro_alpha_1 = min(255, intro_alpha_1 + velocidad_fade)
                if intro_alpha_1 >= 255:
                    intro_fase = 2
                    intro_tiempo_inicio = tiempo_actual
            elif intro_fase == 2:
                if dt > 2500:
                    intro_fase = 3
                    intro_tiempo_inicio = tiempo_actual
            elif intro_fase == 3:
                intro_alpha_1 = max(0, intro_alpha_1 - velocidad_fade)
                if intro_alpha_1 <= 0:
                    intro_fase = 4
                    intro_tiempo_inicio = tiempo_actual
            elif intro_fase == 4:
                if dt > 500:
                    intro_fase = 5
                    intro_tiempo_inicio = tiempo_actual
            elif intro_fase == 5:
                intro_alpha_2 = min(255, intro_alpha_2 + velocidad_fade)
                if intro_alpha_2 >= 255:
                    intro_fase = 6
                    intro_tiempo_inicio = tiempo_actual
            elif intro_fase == 6:
                if dt > 2500:
                    intro_fase = 7
                    intro_tiempo_inicio = tiempo_actual
            elif intro_fase == 7:
                intro_alpha_2 = max(0, intro_alpha_2 - velocidad_fade)
                if intro_alpha_2 <= 0:
                    estado_actual = ESTADO_MENU
            
            # Función helper para dibujar texto con fade
            def dibujar_texto_fade(texto, centro_x, centro_y, alpha):
                texto.set_alpha(alpha)
                rect = texto.get_rect(center=(centro_x, centro_y))
                interfaz.pantalla.blit(texto, rect)
            
            # Dibujar textos
            if intro_fase in [1, 2, 3]:
                dibujar_texto_fade(texto1, interfaz.ancho_ventana//2, interfaz.alto_ventana//2 - 20, intro_alpha_1)
                dibujar_texto_fade(texto1_sub, interfaz.ancho_ventana//2, interfaz.alto_ventana//2 + 20, intro_alpha_1)
            elif intro_fase in [5, 6, 7]:
                dibujar_texto_fade(texto2, interfaz.ancho_ventana//2, interfaz.alto_ventana//2 - 20, intro_alpha_2)
                dibujar_texto_fade(texto3, interfaz.ancho_ventana//2, interfaz.alto_ventana//2 + 30, intro_alpha_2)
                
            # Loading icon (Rotating Arc - Estilo Omega)
            angulo = (tiempo_actual // 5) % 360
            rect_carga = pygame.Rect(interfaz.ancho_ventana - 60, interfaz.alto_ventana - 60, 40, 40)
            # Dibujar arco rojo con un "hueco"
            pygame.draw.arc(interfaz.pantalla, (220, 30, 30), rect_carga, math.radians(angulo), math.radians(angulo + 300), 5)
            
            try:
                fuente_peq = pygame.font.Font("assets/font.otf", 16)
            except:
                fuente_peq = interfaz.fuente_pequena
                
            txt_skip = fuente_peq.render("Presiona cualquier tecla para saltar", True, (80, 80, 80))
            interfaz.pantalla.blit(txt_skip, (20, interfaz.alto_ventana - 30))
            
            pygame.display.flip()
            
        elif estado_actual == ESTADO_MENU:
            interfaz.pantalla.fill((10, 12, 15)) # Fondo muy oscuro
            
            try:
                fuente_titulo = pygame.font.Font("assets/font.otf", 70)
                fuente_menu = pygame.font.Font("assets/font.otf", 30)
                fuente_creditos = pygame.font.Font("assets/font.otf", 16)
            except Exception:
                fuente_titulo = pygame.font.SysFont("Segoe UI", 60, bold=True)
                fuente_menu = pygame.font.SysFont("Segoe UI", 30)
                fuente_creditos = pygame.font.SysFont("Segoe UI", 16)
                
            # Título (Alineado arriba a la izquierda, estilo GoW)
            txt_titulo_1 = fuente_titulo.render("SIMULADOR", True, (220, 220, 220))
            txt_titulo_2 = fuente_titulo.render("DE RESCATE IA", True, (100, 150, 255)) # Un toque azul claro
            interfaz.pantalla.blit(txt_titulo_1, (50, 50))
            interfaz.pantalla.blit(txt_titulo_2, (50, 110))
            
            # Opciones del menú
            opciones = ["NUEVA SIMULACION", "GENERAR MAPA ALEATORIO", "SALIR"]
            rects_opciones = []
            y_opcion = 250
            
            pos_raton = pygame.mouse.get_pos()
            
            for i, opcion in enumerate(opciones):
                # Crear un rectangulo invisible para detectar el hover
                rect_hover = pygame.Rect(50, y_opcion - 5, 400, 40)
                rects_opciones.append(rect_hover)
                
                if rect_hover.collidepoint(pos_raton):
                    # Dibujar barra de highlight sutil
                    s = pygame.Surface((400, 40))
                    s.set_alpha(50)
                    s.fill((255, 255, 255))
                    interfaz.pantalla.blit(s, (50, y_opcion - 5))
                    
                    color_texto = (255, 255, 255) # Texto brilla en blanco
                else:
                    color_texto = (150, 150, 150) # Texto gris apagado
                    
                txt_opcion = fuente_menu.render(opcion, True, color_texto)
                interfaz.pantalla.blit(txt_opcion, (60, y_opcion))
                y_opcion += 60
                
            # Créditos en la esquina inferior derecha
            txt_creditos = fuente_creditos.render("Jose Pablo Illescas y Sebastian Holweger", True, (100, 100, 100))
            rect_cred = txt_creditos.get_rect(bottomright=(interfaz.ancho_ventana - 20, interfaz.alto_ventana - 20))
            interfaz.pantalla.blit(txt_creditos, rect_cred)
            
            # Manejar clics en el menú en el loop de eventos anterior... wait,
            # we need to handle clicks in the event loop above. 
            # I will add the logic to check clicks in the event loop.
            
            pygame.display.flip()
            
        elif estado_actual == ESTADO_JUEGO:
            # Logica de movimiento fluido
            destino_x = agente.columna * interfaz.ancho_celda
            destino_y = agente.fila * interfaz.ancho_celda
            
            if agente_visual_x < destino_x: agente_visual_x = min(agente_visual_x + velocidad, destino_x)
            elif agente_visual_x > destino_x: agente_visual_x = max(agente_visual_x - velocidad, destino_x)
            
            if agente_visual_y < destino_y: agente_visual_y = min(agente_visual_y + velocidad, destino_y)
            elif agente_visual_y > destino_y: agente_visual_y = max(agente_visual_y - velocidad, destino_y)
    
            en_destino = (agente_visual_x == destino_x and agente_visual_y == destino_y)
    
            # Mover al agente si tiene una ruta y ya llegó a su casilla visual
            if en_destino and agente.ruta_actual:
                siguiente = agente.ruta_actual[0]
                riesgo = MotorInferencia.inferir_riesgo(entorno, siguiente[0], siguiente[1])
                if riesgo > 0:
                    interfaz.log(f"Logica: Riesgo de fuego al frente (Nivel {riesgo})")
                    
                paso_exitoso = agente.avanzar_ruta(entorno)
                if not paso_exitoso:
                     interfaz.log("¡Agente sin energía! Debe ser rescatado.")
                     agente.ruta_actual = [] # Cancelar ruta
                     
            # Mover enemigos
            if tiempo_actual - tiempo_ultimo_enemigo > retraso_enemigos:
                entorno.actualizar_enemigos()
                tiempo_ultimo_enemigo = tiempo_actual
                        
            interfaz.dibujar_todo(agente, agente_visual_x, agente_visual_y)
        
        reloj.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()