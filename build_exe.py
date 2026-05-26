import os
import sys
import subprocess

def build():
    print("==========================================================")
    print("🤖 INICIANDO EMPAQUETADO DEL SIMULADOR CON PYINSTALLER 🤖")
    print("==========================================================")
    
    # 1. Asegurar que PyInstaller esté instalado
    try:
        import PyInstaller
        print("✔ PyInstaller ya está instalado.")
    except ImportError:
        print("ℹ PyInstaller no está instalado. Instalándolo vía pip...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✔ PyInstaller instalado con éxito.")
        except Exception as e:
            print(f"❌ Error al instalar PyInstaller: {e}")
            sys.exit(1)
            
    # 2. Configurar el flag de assets según el sistema operativo
    # macOS/Linux usan ":" como delimitador en PyInstaller --add-data, Windows usa ";"
    sep = ";" if os.name == "nt" else ":"
    add_data_flag = f"assets{sep}assets"
    
    # 3. Definir el nombre del ejecutable
    nombre_app = "RescueAgentOllama"
    
    # 4. Construir el comando de PyInstaller
    # --onefile: Empaqueta todo en un único archivo ejecutable autocontenido
    # --windowed: Oculta la ventana de terminal negra en segundo plano al abrir la GUI
    # --add-data: Incluye la carpeta completa de recursos (sprites, fuentes, música)
    # --name: Nombre personalizado de la aplicación
    command = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--add-data={add_data_flag}",
        f"--name={nombre_app}",
        "main.py"
    ]
    
    print(f"\n🚀 Ejecutando comando de compilación:\n{' '.join(command)}\n")
    
    try:
        subprocess.check_call(command)
        print("\n==========================================================")
        print("🎉 ¡EMPAQUETADO COMPLETADO CON ÉXITO! 🎉")
        print("==========================================================")
        print(f"📁 El archivo ejecutable se encuentra en la carpeta: 'dist/'")
        if os.name == "nt":
            print(f"▶ Ejecutable generado: dist/{nombre_app}.exe")
        else:
            print(f"▶ Ejecutable generado: dist/{nombre_app} (o dist/{nombre_app}.app en macOS)")
        print("==========================================================")
    except Exception as e:
        print(f"\n❌ Error durante el empaquetado con PyInstaller: {e}")
        print("Sugerencia: Asegúrate de tener permisos de escritura en la carpeta del proyecto.")

if __name__ == "__main__":
    build()
