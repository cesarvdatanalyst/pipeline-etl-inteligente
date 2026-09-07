# Pipeline ETL Inteligente: Automatización de Reportes para Pymes y Creadores de Contenido

Este proyecto implementa un pipeline de datos automatizado de extremo a extremo (**ETL: Extracción, Transformación y Carga**) desarrollado en **Python** y desplegado en la nube (**PythonAnywhere**). El sistema está diseñado para resolver un problema crítico del mercado: la pérdida de tiempo operativo en la limpieza y estructuración manual de reportes en formatos Excel y CSV.

## 🚀 Características Principales

* **Motor de Detección Inteligente:** El script inspecciona dinámicamente los metadatos y nombres de las columnas del archivo de entrada para identificar de forma automática el modelo de negocio (E-commerce/Ventas o Creadores de Contenido/Redes Sociales) y aplica reglas de negocio específicas para cada caso.
* **Limpieza de Datos (Data Cleaning) Universal:** Remueve registros duplicados, elimina filas completamente vacías y corrige anomalías comunes como espacios invisibles en campos de texto de forma automatizada mediante **Pandas**.
* **Ingeniería de Características (KPIs de Negocio):** 
  * **Módulo de Redes Sociales:** Calcula automáticamente la tasa de interacción (*Engagement Rate %*) y utiliza procesamiento de texto básico para clasificar el contenido por temáticas (Vlogs, Educativo, Reseñas).
  * **Módulo Financiero:** Realiza auditorías de valores nulos críticos y calcula márgenes y totales comerciales.
* **Arquitectura de Producción Segura:** Implementa aislamiento de rutas absolutas, manejo de variables de entorno (`.env`) para protección de datos y control de acceso centralizado mediante validación de listas de suscripción de correos electrónicos.
* **Gestión de Historial Automatizada:** Cuenta con una lógica de descarte y archivo que mueve los reportes crudos a un repositorio histórico con estampas de tiempo (`Timestamp`), manteniendo limpia la bandeja de entrada para procesos diarios.

## 🛠️ Tecnologías y Librerías Utilizadas

* **Lenguaje:** Python 3.x
* **Manipulación de Datos:** Pandas (DataFrames, Series, Data Cleaning)
* **Gestión del Entorno y Archivos:** OS, Shutil, Datetime, Dotenv
* **Infraestructura e Implementación:** PythonAnywhere (Cloud Environment & Scheduled Tasks)

## 📁 Estructura del Proyecto

* `Script unificado.py` - Código fuente principal con el pipeline inteligente y motor de control.
* `entrada_sucios/` - Carpeta donde se reciben los reportes crudos del cliente.
* `salida_limpios/` - Directorio donde el script deposita el producto final enriquecido en Excel.
* `historial_sucios/` - Respaldo histórico automatizado con estampas de tiempo.
* `.gitignore` - Configuración de seguridad para evitar la filtración de datos sensibles de clientes en entornos públicos.
