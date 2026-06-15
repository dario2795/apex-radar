import sys
import os
import requests
import random
import time
import re
import unicodedata
from bs4 import BeautifulSoup

# Esto le dice a Python que busque archivos en la carpeta padre (backend)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import guardar_vehiculo, obtener_agencias_interesadas

# Configuración de tu API de WhatsApp
EVOLUTION_BASE_URL = "http://localhost:8080"
NOMBRE_INSTANCIA = "instancia_radar"
WHATSAPP_API_KEY = "ix9wbvy9cfzswsqmjna2"

URL_MI_WHATSAPP_API = f"{EVOLUTION_BASE_URL}/message/sendText/{NOMBRE_INSTANCIA}"

# 🛡️ BANCO DE IDENTIDADES (User-Agents reales para simular navegación rotativa)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Edge/122.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def normalizar_texto(texto: str) -> str:
    """Limpia el texto: quita acentos, caracteres especiales y lo pasa a minúsculas."""
    if not texto:
        return ""
    texto = texto.lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = texto.replace("vw", "volkswagen")
    re_sub = re.sub(r'[^a-z0-9\s]', '', texto)
    return re_sub.strip()

def verificar_match_modelo(titulo_publicacion: str, modelo_buscado: str) -> bool:
    """Verifica mediante expresiones regulares si el modelo buscado está en la publicación."""
    texto_completo = normalizar_texto(titulo_publicacion)
    modelo_limpio = normalizar_texto(modelo_buscado)
    patron = rf"\b{modelo_limpio}\b"
    return bool(re.search(patron, texto_completo))

def clasificar_region_mendoza(localidad_texto: str) -> str:
    """Traduce la localidad del aviso a una de nuestras 5 regiones comerciales"""
    texto = localidad_texto.lower()
    
    if any(x in texto for x in ["san martín", "san martin", "junín", "junin", "rivadavia", "palmira", "la colonia"]):
        return "este"
    elif any(x in texto for x in ["capital", "mendoza ciudad", "guaymallén", "guaymallen", "las heras", "lavalle", "costa de araujo"]):
        return "gm_norte"
    elif any(x in texto for x in ["godoy cruz", "luján", "lujan", "maipú", "maipu", "chacras"]):
        return "gm_sur"
    elif any(x in texto for x in ["tunuyán", "tunuyan", "tupungato", "san carlos", "la consulta"]):
        return "valle_uco"
    elif any(x in texto for x in ["san rafael", "general alvear", "alvear", "malargüe", "malargue"]):
        return "sur"
    
    return "desconocido"

def limpiar_precio(precio_texto: str) -> int:
    """Transforma un texto como '$ 8.500.000' en el número entero 8500000."""
    try:
        if not precio_texto or "consultar" in precio_texto.lower():
            return 0
        numero_limpio = re.sub(r'[^\d]', '', precio_texto)
        return int(numero_limpio) if numero_limpio else 0
    except Exception:
        return 0

def enviar_alerta_whatsapp(whatsapp_numero: str, auto: dict):
    """Envía el mensaje real a través de la API usando las llaves correctas del diccionario"""
    mensaje = (
        f"🚨 *¡ALERTA RADAR!* 🚨\n\n"
        f"🚗 *Vehículo:* {auto['marca'].upper()} {auto['modelo'].upper()}\n"
        f"📅 *Año:* {auto['anio']}\n"
        f"💰 *Precio:* {auto['precio']}\n"
        f"📍 *Zona:* {auto['localidad'].title()}\n\n"
        f"🔗 *Link:* {auto['link']}"
    )
    
    numero_limpio = str(whatsapp_numero).strip().replace("+", "")
    if not numero_limpio.startswith("54"):
        numero_limpio = "549" + numero_limpio
        
    payload = {
        "number": numero_limpio,
        "options": {
            "delay": 1200,
            "presence": "composing"
        },
        "textMessage": {
            "text": mensaje
        }
    }
    
    headers = {
        "apikey": WHATSAPP_API_KEY, 
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(URL_MI_WHATSAPP_API, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            print(f"📱 [WHATSAPP] Alerta enviada exitosamente al {numero_limpio}")
        else:
            print(f"⚠️ Error de API al enviar al {numero_limpio}. Código: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Error de conexión: No se pudo conectar con Evolution API.")
    except Exception as e:
        print(f"❌ Error crítico mandando WhatsApp: {e}")
        
def scrapear_deruedas():
    print("🔎 Iniciando rastreo inteligente en DeRuedas...")
    url = "https://www.deruedas.com.ar/usados"
    
    # 🎲 ROTACIÓN DINÁMICA DE CABECERAS
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        # Se agrega timeout para que el bot no se quede colgado si la web tarda mil años en responder
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 403:
            print("🛑 [ALERTA] Código 403: ¡DeRuedas bloqueó la petición temporalmente! Aplicando retirada...")
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', id=re.compile(r'^car_'))
        
        print(f"📊 Se detectaron {len(items)} publicaciones en la portada de usados.")
        
        for item in items:
            try:
                link_tag = item.find('a', class_='redirect-result') or item.find('a', href=True)
                link = "https://www.deruedas.com.ar" + link_tag['href'] if link_tag else None
                
                marca_tag = item.find('meta', itemprop='brand')
                modelo_tag = item.find('meta', itemprop='model')
                anio_tag = item.find('meta', itemprop='vehicleModelDate')
                
                marca = marca_tag['content'].strip() if (marca_tag and 'content' in marca_tag.attrs) else ""
                modelo = modelo_tag['content'].strip() if (modelo_tag and 'content' in modelo_tag.attrs) else ""
                
                if anio_tag and 'content' in anio_tag.attrs and anio_tag['content'].isdigit():
                    anio = int(anio_tag['content'])
                else:
                    anio = 0
                
                precio_tag = item.find('span', class_='precio')
                precio_raw = precio_tag.text.strip() if precio_tag else "0"
                
                ubicacion_tag = item.find('span', class_='ubicacion')
                localidad = ubicacion_tag.text.strip() if ubicacion_tag else "Mendoza"
                
                titulo_generado = f"{marca} {modelo} {anio}"
                
                if not link or not marca or not modelo:
                    continue
                
                auto_info = {
                    "origen": "DeRuedas",
                    "titulo": titulo_generado,
                    "link": link,
                    "precio": precio_raw,
                    "marca": marca,
                    "modelo": modelo,
                    "anio": anio,
                    "localidad": localidad
                }
                
                region_aviso = clasificar_region_mendoza(auto_info["localidad"])
                es_nuevo = guardar_vehiculo(auto_info)
                
                if es_nuevo:
                    print(f"🔥 ¡Auto nuevo en radar! {marca} {modelo} en {localidad}")
                    agencias_a_notificar = obtener_agencias_interesadas(region_aviso, marca, modelo)
                    precio_auto_numerico = limpiar_precio(auto_info["precio"])
                    
                    numeros_notificados = set()
                    for agencia in agencias_a_notificar:
                        p_min = agencia.get("precio_minimo") or 0
                        p_max = agencia.get("precio_maximo") or 999999999
                        anio_min = agencia.get("anio_minimo") or 0
                        
                        if verificar_match_modelo(auto_info["titulo"], auto_info["modelo"]):
                            if (p_min <= precio_auto_numerico <= p_max) and (anio >= anio_min):
                                if agencia["whatsapp"] not in numeros_notificados:
                                    print(f"📩 Notificando a: {agencia['nombre']} (Rango: ${p_min:,} - ${p_max:,})")
                                    enviar_alerta_whatsapp(agencia["whatsapp"], auto_info)
                                    numeros_notificados.add(agencia["whatsapp"])
                                    
            except Exception as e:
                print(f"⚠️ Error procesando una tarjeta de auto: {e}")
                continue

        # ⏳ RETRASO INTELIGENTE HUMANO (Evita gatillar la simulación al mismo milisegundo)
        time.sleep(random.uniform(1.5, 4.2))

        # === 🎲 SIMULACIÓN DE PRUEBA BLINDADA ===
        id_unico_test = random.randint(100000, 999999)
        anio_aleatorio = random.choice([2013, 2014, 2016, 2018, 2019, 2020])
        
        print("\n🎲 [SIMULACIÓN] Insertando auto de prueba para forzar Match...")
        auto_test = {
            "origen": "DeRuedas_Test",
            "titulo": f"Volkswagen Gol 1.6 Trend Inmune {anio_aleatorio}",
            "link": f"https://www.deruedas.com.ar/producto.asp?id={id_unico_test}_test_whatsapp",
            "precio": "$ 8.500.000",
            "marca": "Volkswagen",
            "modelo": "Gol",
            "anio": anio_aleatorio,
            "localidad": "San Martín"
        }
        
        region_test = clasificar_region_mendoza(auto_test["localidad"])
        es_nuevo_test = guardar_vehiculo(auto_test)
        
        if es_nuevo_test:
            print(f"🔥 ¡Auto simulado en radar! {auto_test['marca']} {auto_test['modelo']}")
            agencias_a_notificar = obtener_agencias_interesadas(region_test, auto_test["marca"], auto_test["modelo"])
            precio_test_numerico = limpiar_precio(auto_test["precio"])
            
            numeros_notificados_test = set()
            for agencia in agencias_a_notificar:
                p_min = agencia.get("precio_minimo") or 0
                p_max = agencia.get("precio_maximo") or 999999999
                anio_min = agencia.get("anio_minimo") or 0
                
                if verificar_match_modelo(auto_test["titulo"], auto_test["modelo"]):
                    if (p_min <= precio_test_numerico <= p_max) and (auto_test["anio"] >= anio_min):
                        if agencia["whatsapp"] not in numeros_notificados_test:
                            print(f"📩 Notificando a: {agencia['nombre']} (Rango: ${p_min:,} - ${p_max:,})")
                            enviar_alerta_whatsapp(agencia["whatsapp"], auto_test)
                            numeros_notificados_test.add(agencia["whatsapp"])
        else:
            print("ℹ️ El auto de prueba coincidió con uno viejo (URL duplicada) o rebotó.")
            
    except Exception as e:
        print(f"❌ Error crítico en el scraper: {e}")

if __name__ == "__main__":
    scrapear_deruedas()