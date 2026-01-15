# SEO Intelligence Dashboard (Streamlit PRO)

Plataforma avanzada de inteligencia SEO diseñada para transformar datos crudos de herramientas como Semrush o Sistrix en reportes ejecutivos accionables.

---

## 🌟 Funcionalidades Principales

### 📈 Análisis Ejecutivo PRO
- **Share of Voice (SoV) Hardened**: Cuota de visibilidad calculada con algoritmos de endurecimiento para evitar errores de escala.
- **Deltas MoM (pp)**: Comparativas mensuales expresadas en puntos porcentuales para máxima precisión profesional.
- **Resumen IA**: Integración con Google Gemini Pro para generar análisis estratégicos mensuales.

### 🧠 Enriquecimiento de Intención de Búsqueda
- **Heurística Automática**: Clasificación de keywords en Informativa, Transaccional, Comercial o Navegacional.
- **Validación Persistente**: Módulo de validación manual integrado que guarda tus decisiones en una base de datos global.
- **Identificadores Visuales**: Diferenciación clara entre intenciones sugeridas `(S)` y validadas `(V)`.

### 🌍 Reporte Global Histórico
- **Tendencia MoM**: Evolución de KPIs a lo largo de todos los meses de importación.
- **AI Global Insights**: Análisis estratégico de tendencias históricas (Primer mes vs Último mes).
- **KPIs Acumulados**: Tráfico total capturado y ahorro económico (€) generado por el SEO.

### 🎯 Matriz de Oportunidades
- **Opportunity Score**: Priorización basada en Uplift de Clics, Volumen, Dificultad y CPC.
- **Striking Distance**: Enfoque en keywords en posiciones 4-10 listas para saltar al Top 3.

---

## 🔒 Seguridad y Gestión
- **Zona de Gestión Protegida**: Acciones de borrado o regeneración de IA requieren la contraseña maestra (`Webyseo@`).
- **Data Quality Panel**: Monitorización del progreso de validación de intención y cobertura de datos (CPC, etc.).
- **Shared URLs**: Generación de enlaces "Solo Lectura" para compartir con clientes finales.

---

## 🛠 Instalación y Uso

### Prerrequisitos
- Python 3.9+
- Google API Key (para funcionalidades de IA)

### Configuración
1. Instala las dependencias:
   ```bash
   pip install -r streamlit_dashboard/requirements.txt
   ```
2. Inicia la aplicación:
   ```bash
   streamlit run streamlit_dashboard/app.py
   ```

### Estructura del Proyecto
- `app.py`: Interfaz principal y orquestación.
- `database.py`: Capa de persistencia SQLite.
- `etl.py`: Lógica de procesamiento y cálculo SEO.
- `intent_rules.py`: Motor de inferencia de intención de búsqueda.
- `utils_metrics.py`: Estandarización de cálculos y formateo.

---

## 🛡 Notas de Auditoría
El sistema utiliza una base de datos SQLite persistente para mantener la integridad entre sesiones. Todos los cálculos de tráfico dependen de una curva CTR configurable en el código. Los valores de moneda están localizados a formato europeo (€).
