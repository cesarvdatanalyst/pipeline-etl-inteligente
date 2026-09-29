import os
import pandas as pd
from datetime import datetime
from flask import Flask, jsonify
from sqlalchemy import create_engine
from dotenv import load_dotenv

# 1. Inicialización de la aplicación Flask requerida por Render
app = Flask(__name__)

# 2. Carga segura de variables de entorno (Base de Datos)
load_dotenv()

def pipeline_etl(ruta_archivo):
    """
    Fases 1 y 2 del Pipeline: Extracción y Transformación Inteligente.
    Clasifica automáticamente el modelo comercial y genera métricas limpias.
    """
    print(f"⏳ Procesando archivo de datos: {ruta_archivo}")
    try:
        df = pd.read_excel(ruta_archivo)
    except Exception as e:
        raise ValueError(f"Fallo al leer la estructura del Excel: {e}")
    
    columnas = set(df.columns)
    
    # --- MODELO INDUSTRIAL: REDES SOCIALES ---
    if {'Interacciones', 'Alcance', 'Seguidores'}.issubset(columnas):
        print("📊 Segmento Detectado: Redes Sociales y Creadores")
        df['Interacciones'] = df['Interacciones'].fillna(0)
        df['Alcance'] = df['Alcance'].fillna(0)
        df['Engagement Rate %'] = df.apply(
            lambda r: (r['Interacciones'] / r['Alcance'] * 100) if r['Alcance'] > 0 else 0, 
            axis=1
        )
        df['Tipo_Modelo'] = 'Redes Sociales'

    # --- MODELO INDUSTRIAL: FINANZAS / PYMES ---
    elif {'Ingresos', 'Gastos'}.issubset(columnas):
        print("💰 Segmento Detectado: Finanzas y Pymes Comerciales")
        df['Ingresos'] = df['Ingresos'].fillna(0)
        df['Gastos'] = df['Gastos'].fillna(0)
        df['Margen de Ganancia %'] = df.apply(
            lambda r: ((r['Ingresos'] - r['Gastos']) / r['Ingresos'] * 100) if r['Ingresos'] > 0 else 0, 
            axis=1
        )
        df['Tipo_Modelo'] = 'Finanzas Pyme'
        
    else:
        print("❓ Estructura de modelo genérica o no identificada.")
        df['Tipo_Modelo'] = 'Genérico / No Clasificado'

    # Data Quality: Eliminación de registros duplicados redundantes
    df = df.drop_duplicates(keep='first')
    
    # Auditoría Legal: Estampa de tiempo obligatoria (Data Compliance)
    df['Fecha_Procesamiento'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return df


def load_data_to_supabase(df, table_name):
    """
    Fase 3 del Pipeline: Carga Masiva y Persistente en Supabase (PostgreSQL).
    Resuelve de forma definitiva el borrado de datos por reinicio en Render.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("La variable de entorno 'DATABASE_URL' no se encuentra configurada en el servidor.")
        
    try:
        # Estandarización de protocolo compatible con SQLAlchemy >= 1.4
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        engine = create_engine(db_url)
        
        # 'if_exists=append' asegura que los nuevos reportes se sumen al histórico existente
        df.to_sql(table_name, con=engine, if_exists='append', index=False)
        print(f"🚀 Base de datos sincronizada: {len(df)} registros insertados en '{table_name}'.")
        return True
    except Exception as e:
        print(f"❌ Fallo crítico de conexión en la carga SQL: {e}")
        return False


# --- RUTAS DE LA API FLASK (Requeridas para el despliegue exitoso en Render) ---

@app.route('/')
def home():
    """Ruta base para validar que el servicio web de Render está operando en vivo."""
    return jsonify({
        "status": "online",
        "message": "Intelligent ETL Data Pipeline is running successfully.",
        "environment": "Production Cloud (Render + Supabase)"
    }), 200


@app.route('/run-pipeline')
def run_pipeline_endpoint():
    """Endpoint de control para disparar el procesamiento de datos bajo demanda."""
    archivo_prueba = "datos_crudos_pyme.xlsx"
    tabla_destino = "historico_pipeline_etl"
    
    # Crear un archivo básico simulado si no existe en el disco local de Render
    # CORREGIDO: Se agregaron los valores numéricos correspondientes para la prueba de ingresos
    if not os.path.exists(archivo_prueba):
        df_dummy = pd.DataFrame({'Ingresos':, 'Gastos': [9000, 11000]})
        df_dummy.to_excel(archivo_prueba, index=False)
        
    try:
        df_limpio = pipeline_etl(archivo_prueba)
        success = load_data_to_supabase(df_limpio, tabla_destino)
        if success:
            return jsonify({"status": "success", "rows_processed": len(df_limpio)}), 200
        else:
            return jsonify({"status": "error", "message": "Fallo en la sincronización SQL"}), 500
    except Exception as error:
        return jsonify({"status": "error", "message": str(error)}), 500


# Bloque de ejecución local estándar
if __name__ == "__main__":
    # Render asignará un puerto dinámico mediante la variable de entorno PORT
    puerto = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto)
