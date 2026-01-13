# Documentación para Auditoría de IA: SEO Executive Dashboard (Streamlit Version)

Este documento detalla las capacidades, lógica y arquitectura del **SEO Executive Dashboard** para que un modelo de IA pueda auditar su funcionamiento y proponer mejoras estratégicas.

---

## 1. Propósito del Dashboard
El objetivo principal es transformar exportaciones CSV brutas de herramientas SEO (Semrush, Sistrix, Ahrefs) en un **reporte ejecutivo accionable**. Está diseñado para Directores de Marketing o Dueños de Negocio que necesitan entender el mercado sin perderse en tablas de miles de filas.

---

## 2. Arquitectura y Stack
-   **Core**: Python 3.9+
-   **Frontend/App**: Streamlit (Framework interactivo para datos).
-   **Procesamiento**: Pandas (Lógica de dataframes y vectorización).
-   **Visualización**: Plotly Express (Gráficos interactivos).
-   **IA Co-Pilot**: Google Gemini API (Modelo `gemini-1.5-flash` o `gemini-2.0-flash`).
-   **Despliegue**: Optimizado para Streamlit Cloud / GitHub.

---

## 3. Motor de Datos (ETL)
La inteligencia del dashboard reside en `etl.py`, que realiza las siguientes funciones:

### A. Detección Dinámica de Dominios
El sistema no requiere configurar competidores. Escanea las cabeceras del CSV buscando patrones:
-   `Visibilidad [dominio.com]`
-   `Visibilidad dominio.com`
-   `Posición en Google dominio.com`
Esto permite cargar cualquier CSV y que la herramienta identifique al instante quiénes son los jugadores del mercado.

### B. Normalización Robusta
Maneja las inconsistencias de los formatos internacionales:
-   Limpieza de caracteres especiales en monedas y porcentajes.
-   Conversión de "N/D" o guiones a valores numéricos manejables (0 o None).
-   Mapping de columnas: Identifica sinónimos como "Volumen" vs "# de búsquedas" o "KD" vs "Dificultad".

---

## 4. Funcionalidades Principales

### 📊 Pestaña: Resumen Ejecutivo
-   **Reporte IA Generativo**: Utiliza Gemini para leer los KPIs y la muestra de oportunidades y redactar un resumen de 3 párrafos con: Contexto actual, Análisis de competencia y 3 recomendaciones críticas.
-   **KPI Cards**:
    -   **Share of Voice (SoV)**: % de visibilidad del dominio seleccionado frente al total del mercado detectado.
    -   **Top 3 / Top 10**: Conteo de keywords en posiciones privilegiadas.
    -   **Quick Wins**: Número de keywords con potencial inmediato.
-   **Gráfico de Rankings**: Histograma de distribución (Buckets: 1-3, 4-10, 11-20, 20+).

### ⚔️ Pestaña: Competencia
-   **Market Split (Pie Chart)**: Visualización de la cuota de mercado basada en la visibilidad acumulada.
-   **Benchmark Table**: Tabla que compara a todos los dominios detectados en el CSV por su visibilidad total.

### 🚀 Pestaña: Oportunidades (Striking Distance)
-   **Lógica de Filtrado**: Identifica keywords donde el dominio principal está en **Posición 4 a 10**.
-   **Propósito**: Son términos que ya están en primera página pero no en el Top 3. Optimizarlos requiere menos esfuerzo que subir desde la página 2 y ofrece el mayor retorno de inversión (ROI) a corto plazo.

---

## 5. Lógica de Métricas (Fórmulas)
-   **Total Market Visibility**: `sum(Visiblidad de todos los dominios detectados)`.
-   **Share of Voice (SoV)**: `(Visibilidad Dominio / Total Market Visibility) * 100`.
-   **Visibilidad**: Valor indexado proporcionado por el CSV (normalmente basado en volumen * CTR estimado).

---

## 6. Puntos para Auditoría y Mejora
Un modelo de IA que audite este dashboard debería considerar:
1.  **Predicción de Tráfico**: Actualmente se usa la visibilidad del CSV. Se podría implementar una curva de CTR propia basada en la posición.
2.  **Análisis de Intención**: Usar la columna `intent` para agrupar oportunidades (Informativa vs Transaccional).
3.  **Media Value**: Calcular cuánto costaría esa visibilidad en Google Ads (usando la columna CPC).
4.  **Canibalización**: Detectar si una misma keyword tiene múltiples URLs posicionadas.
5.  **Histórico**: El dashboard actual es mono-mes. Implementar carga de múltiples meses para ver tendencias (MoM).

---

## 7. Configuración de Seguridad
-   **Secrets**: La API Key de Google se maneja vía `st.secrets` para evitar fugas en el código.
-   **Caché**: Se utiliza `st.session_state` para evitar llamadas redundantes a la API de IA durante la navegación por los tabs.
