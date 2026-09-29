import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Cargar variables de entorno para desarrollo local
load_dotenv()

def pipeline_etl(ruta_archivo):
    """
    Fase 1 y 2: Extracción y Transformación Inteligente.
    Detecta el modelo de negocio, limpia anomalías y calcula KPIs específicos.
    """
    print(f"⏳ Iniciando procesamiento del archivo: {ruta_archivo}")
    
    try:
        # Extracción de datos crudos
        df = pd.read_excel(ruta_archivo)
    except Exception as e:
        raise ValueError(f"Error al leer el archivo Excel: {e}")
    
    # Motor de Detección Inteligente mediante inspección de columnas
    columnas = set(df.columns)
    
    # --- MODELO 1: REDES SOCIALES ---
    if {'Interacciones', 'Alcance', 'Seguidores'}.issubset(columnas):
        print("📊 Modelo detectado: Redes Sociales / Creadores de Contenido")
        
        # Data Cleaning: Tratamiento de nulos en métricas críticas
        df['Interacciones'] = df['Interacciones'].fillna(0)
        df['Alcance'] = df['Alcance'].fillna(0)
        
        # Transformación: Cálculo automatizado de KPI
        # Evitamos división por cero usando un condicional o reemplazo
        df['Engagement Rate %'] = df.apply(
            lambda row: (row['Interacciones'] / row['Alcance'] * 100) if row['Alcance'] > 0 else 0, 
            axis=1
        )
        df['Tipo_Modelo'] = 'Redes Sociales'

    # --- MODELO 2: FINANZAS / PYMES ---
    elif {'Ingresos', 'Gastos'}.issubset(columnas):
        print("💰 Modelo detectado: Finanzas / Pymes")
        
        # Data Cleaning: Tratamiento de nulos numéricos
        df['Ingresos'] = df['Ingresos'].fillna(0)
        df['Gastos'] = df['Gastos'].fillna(0)
        
        # Transformación: Cálculo de KPIs Financieros
        df['Margen de Ganancia %'] = df.apply(
            lambda row: ((row['Ingresos'] - row['Gastos']) / row['Ingresos'] * 100) if row['Ingresos'] > 0 else 0, 
            axis=1
        )
        df['Tipo_Modelo'] = 'Finanzas Pyme'
        
    else:
        print("❓ Modelo de negocio no identificado de forma automática.")
        df['Tipo_Modelo'] = 'Genérico / No Clasificado'

    # --- LIMPIEZA GENERAL Y AUDITORÍA ---
    # Eliminar duplicados exactos para asegurar la calidad de datos
    df = df.drop_duplicates(keep='first')
    
    # Agregar marca de tiempo para auditoría de datos (Data Compliance)
    df['Fecha_Procesamiento'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("🧹 Transformación y limpieza general finalizada.")
    return df


def load_data_to_supabase(df, table_name):
    """
    Fase 3: Carga Persistente SQL.
    Sube el DataFrame limpio a la nube para mitigar reinicios de servidores como Render.
    """
    print("🚀 Conectando con la base de datos de Supabase...")
    
    # Capturar la URI segura desde el servidor
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        raise ValueError("❌ Error: La variable de entorno 'DATABASE_URL' no está configurada.")
        
    try:
        # Corrección de protocolo por compatibilidad con SQLAlchemy >= 1.4
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        # Crear motor de conexión relacional
        engine = create_engine(db_url)
        
        # Carga masiva con Pandas. 
        # 'append' añade registros históricos sin borrar lo que ya existía
        df.to_sql(table_name, con=engine, if_exists='append', index=False)
        print(f"✅ ¡Éxito absoluto! {len(df)} filas respaldadas permanentemente en la tabla '{table_name}'.")
        
    except Exception as e:
        print(f"❌ Fallo crítico en la carga SQL: {e}")


# --- Orquestador Principal del Pipeline ---
if __name__ == "__main__":
    # Nombre del archivo Excel de entrada en tu servidor
    ARCHIVO_ENTRADA = "datos_crudos_pyme.xlsx" 
    
    # Nombre de la tabla donde se guardará todo de forma persistente
    TABLA_DESTINO = "historico_pipeline_etl"
    
    try:
        # Ejecutar Extracción y Transformación
        df_resultado = pipeline_etl(ARCHIVO_ENTRADA)
        
        # Ejecutar Carga Persistente en Postgres
        load_data_to_supabase(df_resultado, TABLA_DESTINO)
        
    except Exception as error:
        print(f"⚠ El pipeline se detuvo debido a un error en el flujo: {error}")
        
