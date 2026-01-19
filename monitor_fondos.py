import requests
import hashlib
import time
import smtplib
from email.mime.text import MIMEText  # ← Corregido: mayúscula
from bs4 import BeautifulSoup
import os

# Tus configuraciones (mantengo las tuyas)
URL = 'https://www.fondosdecultura.cl/resultados/'
HASH_FILE = 'page_hash.txt'
CHECK_INTERVAL = 1800  # 1 hora (cambia si quieres más frecuente)
EMAIL_TO = 'nordic.fire@gmail.com'
EMAIL_FROM = 'nordic.fire@gmail.com'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_PASS = 'zchb yygz hfoy oyas'  # ⚠️ Cambia por App Password real de Gmail
KEYWORDS = ['seleccionados', 'nómina', 'audiovisual', 'artes escénicas', 'becas chile crea']  # Alerta si aparecen

def get_page_content():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        resp = requests.get(URL, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')
        # Solo texto limpio (ignora scripts, estilos, menús)
        content = soup.get_text(separator=' ', strip=True).lower()
        h = hashlib.md5(content.encode()).hexdigest()
        print(f"Chequeo OK - Longitud: {len(content)} chars")
        return content, h
    except Exception as e:
        print(f"Error fetching: {e}")
        return None, None

def load_old_hash():
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, 'r') as f:
            return f.read().strip()
    print("Primer chequeo - creando baseline")
    return None

def save_hash(h):
    with open(HASH_FILE, 'w') as f:
        f.write(h)

def has_keywords(content):
    """Alerta solo si hay keywords relevantes"""
    for kw in KEYWORDS:
        if kw in content:
            print(f"Keyword detectada: {kw}")
            return True
    return False

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    try:
        # Port 465 SSL
        server = smtplib.SMTP_SSL(SMTP_SERVER, 465)
        server.login(EMAIL_FROM, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        print("✅ Email enviado!")
    except Exception as e:
        print(f"❌ Error email: {e}")

# Loop principal
print("🚀 Monitor Fondos Cultura iniciado. Ctrl+C para parar.")
old_hash = load_old_hash()
while True:
    try:
        content, new_hash = get_page_content()
        if new_hash and new_hash != old_hash:
            print("🔄 Cambio detectado en la página!")
            if has_keywords(content):
                preview = content[:1000] + "..."  # Más preview
                send_email(
                    f"🚨 CAMBIO en Fondos Cultura 2026: {URL}",
                    f"Se detectó cambio relevante.\n\nPreview:\n{preview}\n\nEnlace: {URL}"
                )
            else:
                print("Cambio menor (sin keywords) - no email")
            save_hash(new_hash)
            old_hash = new_hash
        elif content:
            print("✅ Sin cambios.")
        time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n🛑 Monitor detenido.")
        break
    except Exception as e:
        print(f"Error loop: {e}")
        time.sleep(CHECK_INTERVAL)
