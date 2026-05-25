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
    # Reiniciar también la base de conocimiento para que el agente vuelva a ser "ciego"
    from ia_motores import BaseConocimiento
    agente.base_conocimiento = BaseConocimiento(entorno.filas, entorno.columnas)
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
    
    # Algoritmo de búsqueda activo para planificación y replanificación
    algoritmo_activo = "A_STAR"
    
    # Variables para animación de movimiento fluido
    agente_visual_x = agente.columna * interfaz.ancho_celda
    agente_visual_y = agente.fila * interfaz.ancho_celda
    velocidad = 5 # Píxeles por frame
    
    tiempo_ultimo_enemigo = 0
    retraso_enemigos = 500 # Se mueven cada 500ms
    
    ESTADO_INTRO = 0
    ESTADO_MENU = 1
    ESTADO_JUEGO = 2
    ESTADO_PAUSA = 3
    ESTADO_POPUP = 4
    
    estado_actual = ESTADO_INTRO
    opcion_menu_seleccionada = 0
    opcion_pausa_seleccionada = 0
    popup_titulo = ""
    popup_mensaje = ""
    
    # Variables de intro
    intro_alpha_1 = 0
    intro_alpha_2 = 0
    intro_fase = 0 # 0: FadeIn 1, 1: FadeOut 1, 2: FadeIn 2, 3: FadeOut 2
    intro_tiempo_inicio = pygame.time.get_ticks()
    

    try:
        img_jose_orig = pygame.image.load("assets/Jose_Pablo.png").convert_alpha()
        img_jose = pygame.transform.scale(img_jose_orig, (150, 200))
        img_jose_menu = pygame.transform.scale(img_jose_orig, (80, 110))
        
        img_sebas_orig = pygame.image.load("assets/Sebastian.png").convert_alpha()
        img_sebas = pygame.transform.scale(img_sebas_orig, (150, 200))
        img_sebas_menu = pygame.transform.scale(img_sebas_orig, (80, 110))
    except Exception as e:
        print("Error cargando fotos de creadores:", e)
        img_jose = None
        img_sebas = None
        img_jose_menu = None
        img_sebas_menu = None
        
    try:
        pygame.mixer.music.load("assets/intro.opus")
        pygame.mixer.music.set_volume(0.2)
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
                if evento.type == pygame.KEYDOWN:
                    if evento.key in [pygame.K_DOWN, pygame.K_TAB]:
                        opcion_menu_seleccionada = (opcion_menu_seleccionada + 1) % 3
                    elif evento.key == pygame.K_UP:
                        opcion_menu_seleccionada = (opcion_menu_seleccionada - 1) % 3
                    elif evento.key == pygame.K_RETURN:
                        if opcion_menu_seleccionada == 0: # NUEVA SIMULACION
                            reiniciar_juego(entorno, agente, interfaz)
                            agente_visual_x = agente.columna * interfaz.ancho_celda
                            agente_visual_y = agente.fila * interfaz.ancho_celda
                            estado_actual = ESTADO_JUEGO
                            try:
                                pygame.mixer.music.load("assets/juego.opus")
                                pygame.mixer.music.set_volume(0.2)
                                pygame.mixer.music.play(-1)
                            except Exception as e:
                                pass
                        elif opcion_menu_seleccionada == 1: # MAPA ALEATORIO Y JUGAR
                            reiniciar_juego(entorno, agente, interfaz)
                            generar_mapa_aleatorio(entorno, interfaz)
                            agente_visual_x = agente.columna * interfaz.ancho_celda
                            agente_visual_y = agente.fila * interfaz.ancho_celda
                            estado_actual = ESTADO_JUEGO
                            try:
                                pygame.mixer.music.load("assets/juego.opus")
                                pygame.mixer.music.set_volume(0.2)
                                pygame.mixer.music.play(-1)
                            except Exception as e:
                                pass
                        elif opcion_menu_seleccionada == 2: # SALIR
                            ejecutando = False
                            
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    y_opcion = 250
                    for i, opcion in enumerate(["NUEVA SIMULACION", "GENERAR MAPA ALEATORIO", "SALIR"]):
                        rect_hover = pygame.Rect(50, y_opcion - 5, 400, 40)
                        if rect_hover.collidepoint(evento.pos):
                            if i == 0:
                                reiniciar_juego(entorno, agente, interfaz)
                                agente_visual_x = agente.columna * interfaz.ancho_celda
                                agente_visual_y = agente.fila * interfaz.ancho_celda
                                estado_actual = ESTADO_JUEGO
                                try:
                                    pygame.mixer.music.load("assets/juego.opus")
                                    pygame.mixer.music.set_volume(0.2)
                                    pygame.mixer.music.play(-1) # Loop infinito
                                except Exception as e:
                                    pass
                            elif i == 1:
                                reiniciar_juego(entorno, agente, interfaz)
                                generar_mapa_aleatorio(entorno, interfaz)
                                agente_visual_x = agente.columna * interfaz.ancho_celda
                                agente_visual_y = agente.fila * interfaz.ancho_celda
                                estado_actual = ESTADO_JUEGO
                                try:
                                    pygame.mixer.music.load("assets/juego.opus")
                                    pygame.mixer.music.set_volume(0.2)
                                    pygame.mixer.music.play(-1)
                                except Exception as e:
                                    pass
                            elif i == 2:
                                ejecutando = False
                        y_opcion += 60
                            
            elif estado_actual == ESTADO_JUEGO:
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    estado_actual = ESTADO_PAUSA
                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    if evento.button == 1: # Clic izquierdo
                        accion = interfaz.procesar_clic(evento.pos)
                        
                        if accion == 'TOGGLE_SIM':
                            interfaz.simulacion_activa = not getattr(interfaz, 'simulacion_activa', False)
                            estado_sim = "INICIADA" if interfaz.simulacion_activa else "PAUSADA"
                            interfaz.log(f"Simulacion {estado_sim}")
                            
                        elif accion == 'COMPARAR':
                            humanos_test = entorno.obtener_posiciones_tipo(HUMANO)
                            if humanos_test:
                                h_test = humanos_test[0]
                                _, n_astar, t_astar = Busqueda.a_estrella(agente.base_conocimiento, (agente.fila, agente.columna), h_test)
                                _, n_bfs, t_bfs = Busqueda.bfs(agente.base_conocimiento, (agente.fila, agente.columna), h_test)
                                
                                estado_actual = ESTADO_POPUP
                                popup_titulo = "A* vs BFS"
                                popup_mensaje = f"A*: {n_astar} nodos, {t_astar}s | BFS: {n_bfs} nodos, {t_bfs}s"
                            else:
                                interfaz.log("Error: No hay humanos en el mapa para comparar.")
                        
                        elif accion == 'A_STAR':
                            algoritmo_activo = "A_STAR"
                            interfaz.log(f"Energia: {agente.energia_actual}%. Pensando (A*)...")
                            
                            mejor_ruta, mejor_objetivo = TomaDeDecision.decidir_mejor_accion(agente, entorno, interfaz, algoritmo="A_STAR")
                            if mejor_ruta:
                                agente.establecer_ruta(mejor_ruta)
                                
                        elif accion == 'BFS':
                            algoritmo_activo = "BFS"
                            interfaz.log(f"Energia: {agente.energia_actual}%. Pensando (BFS)...")
                            
                            mejor_ruta, mejor_objetivo = TomaDeDecision.decidir_mejor_accion(agente, entorno, interfaz, algoritmo="BFS")
                            if mejor_ruta:
                                agente.establecer_ruta(mejor_ruta)
                                
                        elif accion == 'TRAIN_Q':
                            # Usar TomaDeDecision para elegir el mejor objetivo lógico (humano o hospital) según el estado
                            mejor_ruta, mejor_objetivo = TomaDeDecision.decidir_mejor_accion(agente, entorno, interfaz, algoritmo=algoritmo_activo)
                            if mejor_objetivo:
                                objetivo = mejor_objetivo
                                inicio = (agente.fila, agente.columna)
                                interfaz.log(f"Entrenando Q-Learning (500 ep.)...")
                                tiempo_entrenamiento = motor_q.entrenar(inicio, objetivo, 500)
                                interfaz.log(f"Entrenamiento completado en {tiempo_entrenamiento}s")
                            else:
                                interfaz.log("Error: No hay objetivos viables para entrenar Q-Learning.")
                                
                        elif accion == 'EXEC_Q':
                            # Usar TomaDeDecision para elegir el mejor objetivo lógico (humano o hospital) según el estado
                            mejor_ruta, mejor_objetivo = TomaDeDecision.decidir_mejor_accion(agente, entorno, interfaz, algoritmo=algoritmo_activo)
                            if mejor_objetivo:
                                objetivo = mejor_objetivo
                                inicio = (agente.fila, agente.columna)
                                interfaz.log(f"Ejecutando Q-Learning...")
                                ruta = motor_q.obtener_ruta(inicio, objetivo)
                                if ruta:
                                    interfaz.log(f"Q-Learning: Ruta óptima hallada.")
                                    agente.establecer_ruta(ruta)
                                else:
                                    interfaz.log("Q-Learning: Aún no sabe cómo llegar.")
                            else:
                                interfaz.log("Error: No hay objetivos viables para ejecutar Q-Learning.")
                                
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
                        
            elif estado_actual == ESTADO_PAUSA:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        estado_actual = ESTADO_JUEGO
                    elif evento.key == pygame.K_UP:
                        opcion_pausa_seleccionada = (opcion_pausa_seleccionada - 1) % 3
                    elif evento.key in [pygame.K_DOWN, pygame.K_TAB]:
                        opcion_pausa_seleccionada = (opcion_pausa_seleccionada + 1) % 3
                    elif evento.key == pygame.K_RETURN:
                        if opcion_pausa_seleccionada == 0: # REANUDAR
                            estado_actual = ESTADO_JUEGO
                        elif opcion_pausa_seleccionada == 1: # ABANDONAR PARTIDA
                            estado_actual = ESTADO_MENU
                            opcion_menu_seleccionada = 0
                            try:
                                pygame.mixer.music.load("assets/intro.opus")
                                pygame.mixer.music.set_volume(0.2)
                                pygame.mixer.music.play(-1)
                            except: pass
                        elif opcion_pausa_seleccionada == 2: # SALIR
                            ejecutando = False
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    y_opcion = 250
                    for i, opcion in enumerate(["REANUDAR", "ABANDONAR PARTIDA", "SALIR"]):
                        rect_hover = pygame.Rect(50, y_opcion - 5, 400, 40)
                        if rect_hover.collidepoint(evento.pos):
                            if i == 0:
                                estado_actual = ESTADO_JUEGO
                            elif i == 1:
                                estado_actual = ESTADO_MENU
                                opcion_menu_seleccionada = 0
                                try:
                                    pygame.mixer.music.load("assets/intro.opus")
                                    pygame.mixer.music.set_volume(0.2)
                                    pygame.mixer.music.play(-1)
                                except: pass
                            elif i == 2:
                                ejecutando = False
                        y_opcion += 60
                        
            elif estado_actual == ESTADO_POPUP:
                if evento.type == pygame.KEYDOWN and evento.key in [pygame.K_RETURN, pygame.K_ESCAPE]:
                    estado_actual = ESTADO_JUEGO
                    if popup_titulo in ["GAME OVER", "¡VICTORIA!"]:
                        interfaz.simulacion_activa = False
                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    estado_actual = ESTADO_JUEGO
                    if popup_titulo in ["GAME OVER", "¡VICTORIA!"]:
                        interfaz.simulacion_activa = False
                    
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
                if dt > 4000:
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
                if dt > 6000:
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
            
            # Dibujar textos con secuencia
            if intro_fase in [1, 2, 3]:
                alpha_t1 = intro_alpha_1
                alpha_t1_sub = max(0, min(255, intro_alpha_1 * 2 - 255)) # Aparece desfasado
                
                dibujar_texto_fade(texto1, interfaz.ancho_ventana//2, interfaz.alto_ventana//2 - 20, alpha_t1)
                dibujar_texto_fade(texto1_sub, interfaz.ancho_ventana//2, interfaz.alto_ventana//2 + 20, alpha_t1_sub)
            elif intro_fase in [5, 6, 7]:
                alpha_t2 = intro_alpha_2
                alpha_fotos = max(0, min(255, intro_alpha_2 * 2 - 128))
                alpha_t3 = max(0, min(255, intro_alpha_2 * 2 - 255))
                
                dibujar_texto_fade(texto2, interfaz.ancho_ventana//2, interfaz.alto_ventana//2 - 150, alpha_t2)
                
                if img_jose and img_sebas:
                    img_jose.set_alpha(intro_alpha_2)
                    img_sebas.set_alpha(intro_alpha_2)
                    
                    # Dibujar fotos centradas (Jose a la izquierda, Sebas a la derecha)
                    interfaz.pantalla.blit(img_jose, (interfaz.ancho_ventana//2 - 180, interfaz.alto_ventana//2 - 100))
                    interfaz.pantalla.blit(img_sebas, (interfaz.ancho_ventana//2 + 30, interfaz.alto_ventana//2 - 100))
                
                dibujar_texto_fade(texto3, interfaz.ancho_ventana//2, interfaz.alto_ventana//2 + 130, intro_alpha_2)
                
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
                    opcion_menu_seleccionada = i
                
                if i == opcion_menu_seleccionada:
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
                
            # Dibujar fotos en la esquina inferior derecha del menu (sobre los nombres)
            if img_jose_menu and img_sebas_menu:
                interfaz.pantalla.blit(img_jose_menu, (interfaz.ancho_ventana - 190, interfaz.alto_ventana - 140))
                interfaz.pantalla.blit(img_sebas_menu, (interfaz.ancho_ventana - 100, interfaz.alto_ventana - 140))
                
            # Créditos en la esquina inferior derecha
            txt_creditos = fuente_creditos.render("Jose Pablo Illescas y Sebastian Holweger", True, (100, 100, 100))
            rect_cred = txt_creditos.get_rect(bottomright=(interfaz.ancho_ventana - 20, interfaz.alto_ventana - 20))
            interfaz.pantalla.blit(txt_creditos, rect_cred)
            
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
            if getattr(interfaz, 'simulacion_activa', False):
                if en_destino and agente.ruta_actual:
                    siguiente = agente.ruta_actual[0]
                    
                    # REPLANNING: Verificar si hay un obstáculo no previsto (Muro o Enemigo) bloqueando el camino
                    celda_siguiente = entorno.obtener_celda(siguiente[0], siguiente[1])
                    if celda_siguiente in [1, 5, 6]: # MURO, RATA o DUENDE
                        interfaz.log("¡Obstáculo detectado! Recalculando ruta...")
                        # 1. Registrar el obstáculo en la base de conocimiento para que la búsqueda lo rodee
                        agente.base_conocimiento.mapa_conocido[siguiente[0]][siguiente[1]] = celda_siguiente
                        
                        agente.ruta_actual = []
                        # Usar el algoritmo activo (A* o BFS) seleccionado por el usuario para recalcular
                        mejor_ruta, mejor_objetivo = TomaDeDecision.decidir_mejor_accion(agente, entorno, interfaz, algoritmo=algoritmo_activo)
                        if mejor_ruta:
                            agente.establecer_ruta(mejor_ruta)
                    else:
                        riesgo = MotorInferencia.inferir_riesgo(entorno, siguiente[0], siguiente[1])
                        if riesgo > 0:
                            interfaz.log(f"Logica: Riesgo de fuego al frente (Nivel {riesgo})")
                            
                        paso_exitoso = agente.avanzar_ruta(entorno)
                        if not paso_exitoso:
                             interfaz.log("¡Agente sin energía! Debe ser rescatado.")
                             agente.ruta_actual = [] # Cancelar ruta
                             estado_actual = ESTADO_POPUP
                             popup_titulo = "GAME OVER"
                             popup_mensaje = "¡El agente se ha quedado sin energia!"
                         
                # Mover enemigos
                if tiempo_actual - tiempo_ultimo_enemigo > retraso_enemigos:
                    entorno.actualizar_enemigos()
                    tiempo_ultimo_enemigo = tiempo_actual
                    
                # Chequear victoria
                humanos_restantes = len(entorno.obtener_posiciones_tipo(HUMANO))
                if humanos_restantes == 0 and not agente.cargando_humano and agente.humanos_rescatados > 0:
                    estado_actual = ESTADO_POPUP
                    popup_titulo = "¡VICTORIA!"
                    popup_mensaje = f"Has rescatado a {agente.humanos_rescatados} humanos exitosamente."
                        
            interfaz.dibujar_todo(agente, agente_visual_x, agente_visual_y)
            
        elif estado_actual == ESTADO_PAUSA:
            interfaz.pantalla.fill((10, 12, 15))
            try:
                fuente_titulo = pygame.font.Font("assets/font.otf", 70)
                fuente_menu = pygame.font.Font("assets/font.otf", 30)
            except Exception:
                fuente_titulo = pygame.font.SysFont("Segoe UI", 60, bold=True)
                fuente_menu = pygame.font.SysFont("Segoe UI", 30)
                
            txt_titulo_1 = fuente_titulo.render("PAUSA", True, (220, 220, 220))
            interfaz.pantalla.blit(txt_titulo_1, (50, 50))
            
            opciones = ["REANUDAR", "ABANDONAR PARTIDA", "SALIR"]
            y_opcion = 250
            pos_raton = pygame.mouse.get_pos()
            
            for i, opcion in enumerate(opciones):
                rect_hover = pygame.Rect(50, y_opcion - 5, 400, 40)
                if rect_hover.collidepoint(pos_raton):
                    opcion_pausa_seleccionada = i
                
                if i == opcion_pausa_seleccionada:
                    s = pygame.Surface((400, 40))
                    s.set_alpha(50)
                    s.fill((255, 255, 255))
                    interfaz.pantalla.blit(s, (50, y_opcion - 5))
                    color_texto = (255, 255, 255)
                else:
                    color_texto = (150, 150, 150)
                    
                txt_opcion = fuente_menu.render(opcion, True, color_texto)
                interfaz.pantalla.blit(txt_opcion, (60, y_opcion))
                y_opcion += 60
                
            pygame.display.flip()
            
        elif estado_actual == ESTADO_POPUP:
            interfaz.dibujar_todo(agente, agente_visual_x, agente_visual_y, auto_flip=False)
            interfaz.dibujar_popup(popup_titulo, popup_mensaje)
            pygame.display.flip()
        
        reloj.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
