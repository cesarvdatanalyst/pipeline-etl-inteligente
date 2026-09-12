import io
import os
import sys
from datetime import datetime
import telebot
from flask import Flask, request
import pandas as pd

# ========================================== #
# ⚙️ CONFIGURACIÓN INICIAL (BOT)             #
# ========================================== #
# 🔐 PRÁCTICA PROFESIONAL: El token se lee de forma segura desde el servidor
TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not TOKEN:
    print("ERROR: No se encontró la variable TELEGRAM_TOKEN", file=sys.stderr)

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# ========================================== #
# 🛡️ CONTROL DE ACCESO: USERNAMES VIP        #
# ========================================== #
# 🔐 Cargamos la lista de clientes autorizados de forma privada
CLIENTES_VIP_RAW = os.environ.get("CLIENTES_VIP", "")
CLIENTES_VIP = [u.strip().lower() for u in CLIENTES_VIP_RAW.split(",") if u.strip()]

def comprobar_suscripcion(username):
    if not username:
        return False
    # Si la lista está vacía en el servidor, permitimos acceso para pruebas iniciales
    if not CLIENTES_VIP:
        return True
    return str(username).strip().lower() in CLIENTES_VIP

# ========================================== #
# 🧼 MOTOR DE LIMPIEZA INTELIGENTE (RAM)     #
# ========================================== #
def limpiar_y_organizar_inteligente(file_bytes, file_name):
    try:
        if file_name.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))

        # === LIMPIEZA UNIVERSAL ===
        df.dropna(how='all', inplace=True)
        df.drop_duplicates(inplace=True)
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()

        df.columns = df.columns.str.lower()
        columnas_actuales = list(df.columns)

        # === MOTOR DE DETECCIÓN INTELIGENTE ===
        # REGLA 1: Creador de Contenido (Métricas de Redes)
        if any(col in columnas_actuales for col in ['views', 'likes', 'reproducciones']):
            columnas_interaccion = ['likes', 'comments', 'shares', 'saves']
            columnas_vistas = ['views', 'impressions']
            for col in columnas_interaccion + columnas_vistas:
                if col in df.columns:
                    df[col] = df[col].fillna(0).astype(int)
            if 'views' in df.columns:
                interacciones_totales = sum(df[col] for col in columnas_interaccion if col in df.columns)
                df['engagement_rate_%'] = (interacciones_totales / df['views']) * 100
                df['engagement_rate_%'] = df['engagement_rate_%'].fillna(0).round(2)
            if 'title' in df.columns:
                def clasificar_video(titulo):
                    t = str(titulo).lower()
                    if any(x in t for x in ['vlog', 'dia', 'rutina']): return 'Vlog Personal'
                    if any(x in t for x in ['tutorial', 'como', 'tips', 'aprende']): return 'Educativo'
                    if any(x in t for x in ['review', 'reseña', 'probando']): return 'Reseña de Producto'
                    return 'Entretenimiento / Otros'
                df['categoria_contenido'] = df['title'].apply(clasificar_video)

        # REGLA 2: Ventas y PYMEs
        elif any(col in columnas_actuales for col in ['precio', 'total', 'cantidad', 'sku', 'monto']):
            columnas_numericas = df.select_dtypes(include=['number']).columns
            df[columnas_numericas] = df[columnas_numericas].fillna(0)
            if 'precio' in df.columns and 'cantidad' in df.columns and 'total' not in df.columns:
                df['total_calculado'] = df['precio'] * df['cantidad']
        else:
            columnas_numericas = df.select_dtypes(include=['number']).columns
            df[columnas_numericas] = df[columnas_numericas].fillna(0)

        # Guardado óptimo en memoria binaria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return output
    except Exception:
        return None

# ========================================== #
# 🤖 CONTROLADOR DE EVENTOS DE TELEGRAM      #
# ========================================== #
@bot.message_handler(commands=['start', 'help'])
def enviar_bienvenida(message):
    bot.reply_to(message, "¡Hola! Bienvenido al Limpiador Inteligente de Datos. 🚀\n\n"
                          "Envíame un archivo **Excel (.xlsx)** o **CSV** desorganizado "
                          "y me encargaré de limpiarlo y estructurarlo automáticamente.")

@bot.message_handler(content_types=['document'])
def gestionar_documento(message):
    username = message.from_user.username
    if not comprobar_suscripcion(username):
        bot.reply_to(message, "⛔ **Acceso Denegado:** Tu usuario no cuenta con una suscripción activa.\n"
                              "Para contratar el servicio, contacta al administrador.")
        return

    file_name = message.document.file_name
    if not (file_name.endswith('.xlsx') or file_name.endswith('.csv')):
        bot.reply_to(message, "⚠️ Por favor, envía únicamente archivos en formato Excel (.xlsx) o .CSV")
        return

    bot.reply_to(message, "📊 Archivo recibido. Analizando estructura y procesando datos...")
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        archivo_limpio = limpiar_y_organizar_inteligente(downloaded_file, file_name)
        
        if archivo_limpio:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_salida = f"reporte_procesado_{timestamp}.xlsx"
            bot.send_document(message.chat.id, archivo_limpio, visible_file_name=nombre_salida)
            bot.send_message(message.chat.id, "✨ ¡Procesamiento finalizado con éxito! Aquí tienes tu reporte limpio.")
        else:
            bot.reply_to(message, "❌ Hubo un error procesando la estructura interna de tu archivo.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ocurrió un fallo en el servidor: {e}")

# ========================================== #
# 🌐 CONFIGURACIÓN WEBHOOK & PRODUCCIÓN       #
# ========================================== #
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.get_data():
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    return '', 200

# Añadimos una ruta raíz de control (Health Check)
# Esto evitará que Render marque tu servicio como "fallido" al arrancar
@app.route('/')
def index():
    return "Bot en línea y funcionando correctamente 🚀", 200

if __name__ == '__main__':
    # Render asigna automáticamente un puerto dinámico mediante la variable de entorno 'PORT'
    puerto = int(os.environ.get("PORT", 5000))
    # Usamos 0.0.0.0 para que sea accesible externamente desde la red de Render
    app.run(host='0.0.0.0', port=puerto)
