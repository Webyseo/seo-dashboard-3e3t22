# Documentación de Auditoría: SEO Intelligence Dashboard (Streamlit)

Este documento sirve como referencia técnica y funcional para la auditoría, mantenimiento y escalado del **SEO Executive Dashboard**. Está diseñado para proporcionar a un modelo de IA o auditor externo el contexto necesario para entender la lógica de negocio y la arquitectura del sistema.

---

## 🏗️ 1. Arquitectura Técnica y Stack
El dashboard está diseñado para ser ligero, reactivo y persistente.
- **Frontend**: Streamlit + Custom CSS para una estética "Glassmorphism" premium.
- **Backend / ETL**: Python 3.9+, Pandas para manipulación de datasets masivos.
- **Base de Datos**: SQLite (Persistence Layer) gestionando 3 niveles: `Projects` > `Imports` > `Keyword Metrics`.
- **Análisis Predictivo**: Google Gemini Pro para resúmenes ejecutivos condicionados por datos reales.
- **Despliegue**: Compatible con Streamlit Cloud (requiere `secrets.toml` para `GOOGLE_API_KEY`).

---

## 🔍 2. El Motor ETL (`etl.py`)
La magia del sistema reside en su capacidad de procesar archivos de exportación de SEO (Semrush/Sistrix) sin pre-procesamiento manual.
- **Detección Dinámica**: El sistema escanea las cabeceras buscando patrones (`Visibilidad [...]`, `Posición [...]`). No depende de un orden de columnas fijo.
- **Curvas de CTR Organico**: Implementa una función de caída de tráfico basada en la posición actual (Top 1 = 30%, Top 2 = 15%, etc.).
- **Calculos Derivados**:
    - `Clics Estimados = Volumen * CTR(Posición)`.
    - `Media Value = Clics Estimados * CPC`.
- **Normalización**: Limpieza automática de €, $, %, decimales europeos (`,`) y americanos (`.`).

---

## 💾 3. Capa de Persistencia (`database.py`)
Maneja el ciclo de vida de los datos:
1. **Projects**: Registra el dominio principal y nombre del cliente.
2. **Imports**: Vincula cada archivo CSV a un mes (`YYYY-MM`) y almacena el texto del reporte generado por la IA.
3. **Keyword Metrics**: Almacenamiento granular de cada palabra clave. Los datos de competidores se guardan en un campo `data_json` para permitir comparativas N-dimensionales sin alterar el esquema SQL.

---

## 📊 4. Módulos Visuales y Estadísticas

### 1. Resumen Ejecutivo (Vista Mensual)
- **KPI Cards**: Muestra *Share of Voice* (SoV), *Tráfico Estimado*, *Ahorro Estimado* y *Oportunidades*. Incluye deltas comparativos automáticos (MoM) si existe un mes previo.
- **Análisis IA**: Bloque de texto generado por Gemini que interpreta los datos del mes, detecta anomalías y sugiere pasos a seguir.
- **Distribución de Rankings**: Gráfico de barras color-coded que segmenta las palabras clave en Top 3, 4-10 (zona de ataque), 11-20 y +20.

### 2. Comparativa de Competencia (Market Share)
- **Market Split**: Gráfico circular que muestra el SoV relativo entre todos los dominios detectados en el CSV.
- **Gap Analysis**: Identifica quién es el líder del mercado y a qué distancia se encuentra el proyecto principal.

### 3. Matriz de Oportunidades (Striking Distance)
- **Quick Wins**: Filtro automático de keywords en posiciones 4 a 10 con alto volumen.
- **Estrategia**: Prioriza los esfuerzos de contenido donde el impacto de subir 1-3 posiciones es máximo.

### 4. Resumen Global (Visión Histórica)
- **Tendencia MoM**: Gráficas de línea y área que muestran la cuota de mercado y el tráfico acumulado a lo largo de todos los meses subidos.
- **Tabla Maestra**: Desglose mensual de KPIs para exportación o revisión de auditoría.

---

## ⚠️ 5. Zona de Gestión y Seguridad
- **Regeneración de IA**: Permite borrar y volver a generar el reporte de IA si se detectan errores o si el prompt ha sido actualizado.
- **Borrado Selectivo**: Posibilidad de eliminar meses específicos para corregir subidas erróneas.
- **Shared URLs**: Generación de enlaces de solo lectura (`?import_id=...`) para compartir con clientes sin exponer la zona de edición o subida de datos.

---

## 🛠️ Notas para Auditoría de IA
Al auditar este código, se debe prestar especial atención a:
- La robustez de `etl.py` ante cabeceras de CSV desconocidas.
- La eficiencia de la persistencia en `database.py` al manejar batches de miles de palabras clave.
- La coherencia de las fechas en el prompt de la IA en `app.py`.
