import sys
import os
import time

# Guardamos la ruta de la carpeta donde vive este archivo run_radar.py
base_dir = os.path.dirname(os.path.abspath(__file__))

# Le enseñamos a Python a mirar adentro de la carpeta actual y de backend
if base_dir not in sys.path:
    sys.path.append(base_dir)
# Si por alguna razón estás parado afuera, este le enseña a mirar la subcarpeta backend
sys.path.append(os.path.join(base_dir, 'backend'))

# Importación limpia gracias al sys.path inteligente de arriba
try:
    from scrapers.scraper import scrapear_deruedas
except ModuleNotFoundError:
    from backend.scrapers.scraper import scrapear_deruedas

# Configura cada cuántos minutos querés que corra el radar
INTERVALO_MINUTOS = 10

if __name__ == "__main__":
    print(f"🚀 [RADAR] Iniciado de fondo. Ciclo programado: cada {INTERVALO_MINUTOS} minutos...")
    
    try:
        while True:
            print("\n🔍 [RADAR] Iniciando nueva ronda de raspaje en DeRuedas...")
            
            try:
                # 🏎️ Corre el motor de búsqueda
                scrapear_deruedas()
                print("✅ [RADAR] Ciclo completado con éxito.")
                
            except Exception as error_ciclo:
                # 🛡️ Si algo adentro de 'scrapear_deruedas' explota (bloqueo, caída de internet, etc.)
                # este bloque atrapa el error, avisa en consola y evita que el script se apague.
                print(f"⚠️ [ALERTA RADAR] Ocurrió un tropiezo en este ciclo: {error_ciclo}")
                print("🔄 [RADAR] Manteniendo motor encendido. Se reintentará en la próxima vuelta.")
            
            print(f"💤 [RADAR] Esperando {INTERVALO_MINUTOS} minutos para el próximo ciclo...")
            time.sleep(INTERVALO_MINUTOS * 60)
            
    except KeyboardInterrupt:
        print("\n🛑 [RADAR] Motor apagado de forma manual por el usuario.")