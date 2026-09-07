import os
import sys
import shutil
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

# 1. Configurar rutas absolutas
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

DIR_ENTRADA = os.getenv("DIR_ENTRADA", os.path.join(SCRIPT_DIR, "entrada_sucios"))
DIR_HISTORIAL = os.getenv("DIR_HISTORIAL", os.path.join(SCRIPT_DIR, "historial_sucios"))
DIR_SALIDA_CLIENTE = os.getenv("DIR_SALIDA_CLIENTE", os.path.join(SCRIPT_DIR, "salida_limpios"))

# ==========================================
# 🛡️ CONTROL DE ACCESO: CLIENTES CON PAGO ACTIVO
# ==========================================
# Aquí añadirás los correos de los clientes que ya te pagaron la suscripción
CLIENTES_VIP = [
    "cliente1@gmail.com",
    "creador_famoso@hotmail.com",
    "tu_correo_de_prueba@gmail.com"  # Agrega tu correo aquí para hacer pruebas
]

def comprobar_suscripcion(correo_usuario):
    """Verifica si el usuario tiene permiso para usar la herramienta."""
    correo_limpio = str(correo_usuario).strip().lower()
    if correo_limpio in CLIENTES_VIP:
        print(f"✅ [ACCESO CONCEDIDO]: Suscripción activa para {correo_limpio}")
        return True
    else:
        print(f"❌ [ACCESO DENEGADO]: El correo {correo_limpio} no tiene una suscripción activa.")
        return False

def inicializar_entorno():
    """Crea las carpetas necesarias si no existen."""
    for carpeta in [DIR_ENTRADA, DIR_HISTORIAL, DIR_SALIDA_CLIENTE]:
        os.makedirs(carpeta, exist_ok=True)

def limpiar_y_organizar_inteligente(ruta_archivo_sucio, ruta_archivo_limpio, correo_cliente):
    """
    Lee un archivo desorganizado, valida la suscripción del cliente,
    detecta el modelo de negocio automáticamente y procesa los datos.
    """
    # VALIDACIÓN DE SEGURIDAD ANTES DE PROCESAR
    if not comprobar_suscripcion(correo_cliente):
        print("⛔ Proceso abortado por falta de pago o credenciales inválidas.")
        return False

    print(f"📊 Analizando estructura y metadatos del archivo...")
    try:
        if ruta_archivo_sucio.endswith('.csv'):
            df = pd.read_csv(ruta_archivo_sucio)
        else:
            df = pd.read_excel(ruta_archivo_sucio)

        # === LIMPIEZA UNIVERSAL ===
        df.dropna(how='all', inplace=True)
        df.drop_duplicates(inplace=True)
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()

        # === MOTOR DE DETECCIÓN INTELIGENTE DE NEGOCIO ===
        columnas_actuales = [str(col).lower() for col in df.columns]

        # REGLA 1: Creador de Contenido
        if 'views' in columnas_actuales or 'likes' in columnas_actuales or 'reproducciones' in columnas_actuales:
            print("🎥 [DETECTADO]: Modelo Creador de Contenido / Redes Sociales.")
            df.columns = df.columns.str.lower()
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
                    elif any(x in t for x in ['tutorial', 'como', 'tips', 'aprende']): return 'Educativo'
                    elif any(x in t for x in ['review', 'reseña', 'probando']): return 'Reseña de Producto'
                    return 'Entretenimiento / Otros'
                df['categoria_contenido'] = df['title'].apply(clasificar_video)

        # REGLA 2: Ventas
        elif any(col in columnas_actuales for col in ['precio', 'total', 'cantidad', 'sku', 'monto']):
            print("🛍️ [DETECTADO]: Modelo Tienda / Ventas Comerciales.")
            columnas_numericas = df.select_dtypes(include=['number']).columns
            df[columnas_numericas] = df[columnas_numericas].fillna(0)
            df.columns = df.columns.str.lower()
            if 'precio' in df.columns and 'cantidad' in df.columns and 'total' not in df.columns:
                df['total_calculado'] = df['precio'] * df['cantidad']

        else:
            print("⚠️ [AVISO]: Estructura no identificada. Limpieza estándar aplicada.")
            columnas_numericas = df.select_dtypes(include=['number']).columns
            df[columnas_numericas] = df[columnas_numericas].fillna(0)

        # Guardar el entregable final
        df.to_excel(ruta_archivo_limpio, index=False)
        print(f"✨ ¡Procesamiento finalizado con éxito!")
        return True

    except Exception as e:
        print(f"❌ Error crítico en el pipeline de datos: {e}")
        return False

def ejecutar_proceso_diario(correo_del_usuario_actual):
    inicializar_entorno()

    nombre_archivo_objetivo = "reporte_mensual_sucio.xlsx"
    ruta_sucio = os.path.join(DIR_ENTRADA, nombre_archivo_objetivo)

    if not os.path.exists(ruta_sucio):
        print(f"⚠️ Esperando archivo '{nombre_archivo_objetivo}' en la carpeta de entrada...")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_limpio = f"reporte_final_procesado_{timestamp}.xlsx"
    nombre_historial = f"historial_sucio_{timestamp}.xlsx"

    ruta_limpio = os.path.join(DIR_SALIDA_CLIENTE, nombre_limpio)
    ruta_historial = os.path.join(DIR_HISTORIAL, nombre_historial)

    # Pasamos el correo del usuario para validar antes de limpiar
    exito = limpiar_y_organizar_inteligente(ruta_sucio, ruta_limpio, correo_del_usuario_actual)

    if exito:
        try:
            shutil.move(ruta_sucio, ruta_historial)
            print(f"✅ Pipeline ejecutado correctamente.")
        except Exception as e:
            print(f"⚠️ Archivo procesado pero no se movió al historial: {e}")

if __name__ == "__main__":
    print(f"=== 🚀 Iniciando Pipeline ETL Seguro: {datetime.now()} ===")

    # SIMULACIÓN: Aquí simulamos el correo que ingresa el usuario.
    # Para probar el bloqueo, cambia este correo por uno que NO esté en la lista CLIENTES_VIP.
    correo_simulado = "tu_correo_de_prueba@gmail.com"

    ejecutar_proceso_diario(correo_simulado)
    print("=== 🏁 Tarea Finalizada ===")
