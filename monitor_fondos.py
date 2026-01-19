import os
import requests
import hashlib
import time
from bs4 import BeautifulSoup
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Configuración desde Railway Variables
URL = 'https://www.fondosdecultura.cl/resultados/'
HASH_FILE = 'page_hash.txt'
CHECK_INTERVAL = 1800  # 30 minutos
KEYWORDS = ['seleccionados', 'nómina', 'audiovisual', 'artes escénicas', 'becas chile crea']

def get_page_content():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        resp = requests.get(URL, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')
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
    for kw in KEYWORDS:
        if kw in content:
            print(f"Keyword detectada: {kw}")
            return True
    return False

def send_email(subject, body):
    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        message = Mail(
            from_email=os.getenv('EMAIL_FROM'),
            to_emails=os.getenv('EMAIL_TO'),
            subject=subject,
            plain_text_content=body  # FIJO
        )
        response = sg.send(message)
        print(f"✅ Email OK - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error SendGrid: {e}")

# Loop principal
print("🚀 Monitor Fondos Cultura iniciado en Railway. Ctrl+C para parar.")
old_hash = load_old_hash()
while True:
    try:
        content, new_hash = get_page_content()
        if new_hash and new_hash != old_hash:
            print("🔄 Cambio detectado!")
            if has_keywords(content):
                preview = content[:1000] + "..."
                send_email(
                    f"🚨 CAMBIO Fondos Cultura 2026: {URL}",
                    f"Se detectó cambio relevante.\n\nPreview:\n{preview}\n\nEnlace: {URL}"
                )
            else:
                print("Cambio menor - no email")
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
