import subprocess
import webbrowser
import time
import sys
import os

# Ruta a tu carpeta de proyecto
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def main():
    print("🚀 INICIANDO APEX-RADAR...")
    
    # 1. Levantamos el servidor FastAPI usando el intérprete de Python actual
    # Nos aseguramos de estar en la carpeta raíz
    servidor = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8000"],
        cwd=PROJECT_ROOT
    )
    
    # 2. Esperamos a que el servidor esté listo
    time.sleep(3)
    
    # 3. Abrimos la interfaz directamente (usando la ruta absoluta del archivo)
    frontend_path = os.path.join(PROJECT_ROOT, "frontend", "index.html")
    webbrowser.open(f"file://{frontend_path}")
    
    print("✅ SISTEMA LISTO. No cierres esta ventana.")
    
    # 4. Mantenemos el lanzador vivo
    try:
        servidor.wait()
    except KeyboardInterrupt:
        servidor.terminate()

if __name__ == "__main__":
    main()