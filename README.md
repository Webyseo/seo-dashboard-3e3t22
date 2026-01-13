# SEO Executive Dashboard

Aplicación web profesional para el análisis de rendimiento SEO, diseñada para agencias y consultores. Permite visualizar KPIs, comparar competidores y generar informes ejecutivos en PDF.

## 🚀 Instalación y Puesta en Marcha

### Prerrequisitos
- Node.js 18+ instalado.
- Un archivo CSV mensual con los datos de exportación.

### Pasos Iniciales
1.  Clona el repositorio o descomprime el proyecto.
2.  Instala las dependencias:
    ```bash
    npm install
    ```
3.  Inicializa la base de datos (SQLite):
    ```bash
    npx prisma db push
    ```
4.  Inicia el servidor de desarrollo:
    ```bash
    npm run dev
    ```
5.  Abre [http://localhost:3000](http://localhost:3000) en tu navegador.

## 📊 Guía de Uso

### 1. Crear Proyecto
Al iniciar, verás la pantalla "Your Projects". Crea un nuevo proyecto para tu cliente (ej. "Radiofonics"). Esto te llevará al dashboard vacío del proyecto.

### 2. Importar Datos (CSV)
En la pestaña "Data Quality" o en el inicio si no hay datos:
1.  Selecciona el **Mes** del reporte (ej. "Octubre 2023").
2.  Sube el archivo CSV.
3.  El sistema detectará automáticamente las columnas y los dominios de la competencia.

**Nota**: El sistema maneja valores "N/D", porcentajes y monedas automáticamente.

### 3. Interpretar KPIs (Executive Summary)
-   **Share of Voice (SoV)**: Tu visibilidad comparada con la visibilidad total del mercado (suma de todos los dominios rastreados).
-   **Striking Distance**: Palabras clave en posiciones 4-10 (Página 1 baja), donde una pequeña optimización puede generar gran impacto.
-   **Top 3 / 10 / 20**: Cantidad de palabras clave en estos rangos.

### 4. Pestañas de Análisis
-   **Competition**: Tabla comparativa con competidores (SoV, Visibilidad, Posición Media).
-   **Rankings**: Distribución de palabras clave por rangos de posición.
-   **Groups**: Rendimiento agrupado por "Grupo Palabra Clave".
-   **Opportunities**: Listado automático de "Quick Wins" (Pos 4-10 con alto volumen).

### 5. Exportar Informe
En la pestaña "Executive Summary", pulsa el botón **"Export PDF"**. Esto generará un archivo PDF profesional con los KPIs principales y los insights automáticos, listo para enviar por email.

## 🛠 Comandos Útiles

-   `npm run build`: Construir para producción.
-   `npx prisma studio`: Ver la base de datos visualmente.
-   `npx prisma db push`: Actualizar esquema de BD si haces cambios.
