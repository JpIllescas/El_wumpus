import pygame
import sys
from entorno import Entorno, HUMANO, ESTACION
from interfaz import Interfaz
from agente import Agente
from ia_motores import Busqueda, TomaDeDecision, MotorInferencia, QLearning

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
    interfaz.log("[B] Búsqueda BFS (No Informada)")
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
    
    while ejecutando:
        tiempo_actual = pygame.time.get_ticks()
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
                
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1: # Clic izquierdo
                    interfaz.procesar_clic(evento.pos)
                    
            elif evento.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:
                    interfaz.procesar_clic(evento.pos)
                    
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    interfaz.log(f"Energía: {agente.energia_actual}%. Pensando...")
                    mejor_ruta, mejor_objetivo = TomaDeDecision.decidir_mejor_accion(agente, entorno, interfaz)
                    if mejor_ruta:
                        agente.establecer_ruta(mejor_ruta)
                            
                elif evento.key == pygame.K_b:
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
                        
                elif evento.key == pygame.K_t:
                    humanos = entorno.obtener_posiciones_tipo(HUMANO)
                    if humanos:
                        objetivo = humanos[0]
                        inicio = (agente.fila, agente.columna)
                        interfaz.log(f"Entrenando Q-Learning (500 ep.)...")
                        tiempo_entrenamiento = motor_q.entrenar(inicio, objetivo, 500)
                        interfaz.log(f"Entrenamiento completado en {tiempo_entrenamiento}s")
                    else:
                        interfaz.log("Error: No hay humanos para entrenar.")

                elif evento.key == pygame.K_q:
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

        # Lógica de movimiento fluido
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
                interfaz.log(f"Lógica: Riesgo de fuego al frente (Nivel {riesgo})")
                
            paso_exitoso = agente.avanzar_ruta(entorno)
            if not paso_exitoso:
                 interfaz.log("¡Agente sin energía! Debe ser rescatado.")
                 agente.ruta_actual = [] # Cancelar ruta
                 
        # Mover enemigos
        if tiempo_actual - tiempo_ultimo_enemigo > retraso_enemigos:
            entorno.actualizar_enemigos()
            tiempo_ultimo_enemigo = tiempo_actual
                    
        interfaz.dibujar_todo(agente_visual_x, agente_visual_y)
        
        # Dibujar energía y estado en pantalla encima del panel de log
        texto_energia = interfaz.fuente.render(f"Energía: {agente.energia_actual}%", True, (0, 255, 255))
        interfaz.pantalla.blit(texto_energia, (interfaz.ancho_mapa + 10, 10))
        
        texto_carga = "Sí" if agente.cargando_humano else "No"
        color_carga = (50, 255, 50) if agente.cargando_humano else (200, 200, 200)
        texto_estado = interfaz.fuente.render(f"Cargando Humano: {texto_carga}", True, color_carga)
        interfaz.pantalla.blit(texto_estado, (interfaz.ancho_mapa + 10, 30))
        
        pygame.display.flip()
        
        reloj.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()