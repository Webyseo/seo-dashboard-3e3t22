# Documentación de Auditoría: SEO Intelligence Dashboard (Streamlit)

Este documento sirve como referencia técnica y funcional para la auditoría, mantenimiento y escalado del **SEO Executive Dashboard**. Está diseñado para proporcionar a un modelo de IA o auditor externo el contexto necesario para entender la lógica de negocio y la arquitectura del sistema.

---

## 🏗️ 1. Arquitectura Técnica y Stack
El dashboard está diseñado para ser ligero, reactivo y persistente.
- **Frontend**: Streamlit + Custom CSS para una estética "Glassmorphism" premium.
- **Backend / ETL**: Python 3.9+, Pandas para manipulación de datasets masivos.
- **Base de Datos**: SQLite (Persistence Layer) gestionando 4 niveles: `Projects` > `Imports` > `Keyword Metrics` + la nueva tabla Global de `Keyword Intent`.
- **Análisis Predictivo**: Google Gemini Pro para resúmenes ejecutivos mensuales e históricos (Global Report).
- **Seguridad**: Control de acciones críticas mediante contraseña gestora ("Webyseo@").
- **Despliegue**: Compatible con Streamlit Cloud.

---

## 🔍 2. El Motor ETL (`etl.py`)
La magia del sistema reside en su capacidad de procesar archivos de exportación de SEO (Semrush/Sistrix) sin pre-procesamiento manual.
- **Detección Dinámica**: El sistema escanea las cabeceras buscando patrones (`Visibilidad [...]`, `Posición [...]`). No depende de un orden de columnas fijo.
- **Curvas de CTR Organico**: Implementa una función de caída de tráfico basada en la posición actual (Top 1 = 30%, Top 2 = 15%, etc.).
- **Calculos Derivados**:
    - `Clics Estimados = Volumen * CTR(Posición)`.
    - `Media Value = Clics Estimados * CPC`.
- **Endurecimiento de Métricas (`utils_metrics.py`)**: Centraliza el cálculo de visibilidad para evitar errores de escala, aplicando guardas anti-multiplicación y estandarizando el delta en puntos porcentuales (pp).
- **Normalización**: Limpieza automática de €, $, %, decimales europeos (`,`) y americanos (`.`).

---

## 💾 3. Capa de Persistencia (`database.py`)
Maneja el ciclo de vida de los datos:
1. **Projects**: Registra el dominio principal y nombre del cliente.
2. **Imports**: Vincula cada archivo CSV a un mes (`YYYY-MM`) y almacena el texto del reporte generado por la IA.
3. **Keyword Metrics**: Almacenamiento granular de cada palabra clave. Los datos de competidores se guardan en un campo `data_json` para permitir comparativas N-dimensionales.
4. **Keyword Intent (Persistencia Global)**: Almacena las intenciones de búsqueda validadas manualmente. Estas prevalecen sobre las sugerencias automáticas y son persistentes entre diferentes meses de importación.

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

### 4. Enriquecimiento de Intención de Búsqueda (`intent_rules.py`)
- **Heurística Automática**: Clasifica keywords en Informativa, Transaccional, Comercial o Navegacional basándose en patrones léxicos y modificadores locales.
- **Validación Manual (V)**: Módulo de edición interactiva directo en el dashboard para corregir sugerencias. Las keywords validadas se marcan con `(V)` y las automáticas con `(S)`.

### 5. Resumen Global (Visión Histórica PRO)
- **Tendencia MoM**: Gráficas de línea y área que muestran la cuota de mercado y el tráfico acumulado.
- **AI Global Insights**: Análisis estratégico de tendencias históricas comparando el primer mes contra el último mes cargado.
- **Tabla Maestra**: Desglose mensual de KPIs para exportación.

---

## ⚠️ 5. Zona de Gestión y Seguridad
- **Control de Acciones Críticas**: Las funciones de "Regenerar Análisis IA" y "Borrar Mes" están protegidas por la contraseña `Webyseo@` para evitar consumo innecesario de API o pérdida accidental de datos.
- **Shared URLs**: Generación de enlaces de solo lectura (`?import_id=...`) para compartir con clientes.
- **Branding**: Personalización visual con logo de Radiofònics y estética premium adaptada.

---

## 🛠️ Notas para Auditoría de IA
Al auditar este código, se debe prestar especial atención a:
- La robustez de `etl.py` ante cabeceras de CSV desconocidas.
- La lógica de `utils_metrics.py` para asegurar que el SoV (Visibilidad) nunca sufra errores de escala.
- La persistencia de `database.py` al manejar batches de miles de palabras clave y la integridad de la tabla de intenciones.
- El refinamiento de las reglas en `intent_rules.py` para mejorar la precisión de las sugerencias automáticas.
- La coherencia de las fechas en el prompt de la IA en `app.py`.