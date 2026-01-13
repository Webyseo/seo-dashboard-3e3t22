# Contexto Técnico: SEO Executive Dashboard

Este documento describe la arquitectura, el modelo de datos y la lógica de negocio de la aplicación "SEO Executive Dashboard". Su propósito es servir de contexto para futuras iteraciones de desarrollo o análisis por parte de una IA.

## 1. Stack Tecnológico
-   **Framework**: Next.js 14+ (App Router).
-   **Lenguaje**: TypeScript.
-   **Base de Datos**: SQLite (local).
-   **ORM**: Prisma (v5.22.0).
-   **Estilos**: Tailwind CSS + Shadcn/UI.
-   **Gráficos**: Recharts.
-   **Exportación**: @react-pdf/renderer.

## 2. Modelo de Datos (Prisma Schema)

La base de datos relacional (SQLite) está diseñada para almacenar múltiples "proyectos" (clientes), cada uno con múltiples "importaciones" mensuales.

### Entidades Principales
1.  **Project**: Contenedor principal (ej. "Cliente A").
2.  **Import**: Representa un snapshot mensual de datos (ej. "Octubre 2023"). Contiene la fecha y nombre del archivo fuente.
3.  **Keyword**: Diccionario único de palabras clave por proyecto. Se normaliza para no duplicar textos entre meses, aunque las métricas sí varían.
4.  **KeywordMetric**: Datos crudos del CSV vinculados a una Keyword y un Import específico.
    -   *Campos*: volume (búsquedas), difficulty (KD), cpc, ctr, trend.
5.  **DomainRanking**: Posicionamiento de un dominio específico para una keyword en un mes dado.
    -   *Campos*: domain (ej. "miweb.com"), position (1-100), visibility (float), url (landing page).
    -   *Lógica*: Permite almacenar tanto al dominio principal como a N competidores detectados dinámicamente.

## 3. Lógica de Negocio y ETL

### Ingesta de Datos (CSV Parser)
El sistema ingiere archivos CSV exportados de herramientas SEO estándar.
-   **Normalización**:
    -   Convierte "N/D", "-" a `null`.
    -   Parsea porcentajes ("33.3%") y monedas ("$2.50") a tipos numéricos.
    -   **Dynamic Domain Detection**: Lee los encabezados del CSV (ej. "Visibilidad [dominio.com]") para identificar automáticamente qué competidores están presentes en el reporte, sin necesidad de configuración manual.

### Métricas Calculadas
-   **Share of Voice (SoV)**:
    -   Fórmula: `(Visibilidad del Dominio Principal / Suma Visibilidad de Todos los Dominios) * 100`.
    -   Contexto: Se calcula por "Import", sumando la visibilidad de todas las keywords.
-   **Striking Distance**:
    -   Definición: Keywords posicionadas entre 4 y 10.
    -   Uso: Oportunidades de alto impacto ("Quick Wins").
-   **Top 3 / 10 / 20**: Conteos simples de keywords en esos rangos de posición.

## 4. Estructura del Dashboard (Componentes UI)

La interfaz se divide en 7 pestañas lógicas que consumen los datos procesados:

1.  **Executive Summary (Resumen Ejecutivo)**:
    -   *Objetivo*: Vista de alto nivel para el cliente.
    -   *Elementos*: KPIs Cards (SoV, Visibilidad Total), Gráfico de Tendencia SoV, Insights automáticos (generados por reglas como "Caída > 5%").
2.  **Competition (Competencia)**:
    -   *Objetivo*: Comparativa directa de mercado.
    -   *Elementos*: Tabla Benchmark (comparando SoV, Top 10 words, Posición media entre todos los dominios detectados).
3.  **Rankings**:
    -   *Objetivo*: Salud del posicionamiento.
    -   *Elementos*: Gráfico de barras con distribución de buckets (Top 3, 4-10, 11-20, >20).
4.  **Groups (Grupos)**:
    -   *Objetivo*: Rendimiento semántico.
    -   *Elementos*: Tabla agregada por la columna "Grupo Palabra Clave" del CSV. Muestra qué tópicos traen más visibilidad.
5.  **URLs**:
    -   *Objetivo*: Rendimiento de landings.
    -   *Elementos*: Tabla de URLs con más keywords posicionadas. Detecta canibalización.
6.  **Opportunities**:
    -   *Objetivo*: Plan de acción.
    -   *Lógica*: Filtra keywords en "Striking Distance" (4-10) con alto volumen y menor dificultad, etiquetándolas como "Quick Wins".
7.  **Data Quality**:
    -   *Objetivo*: Auditoría.
    -   *Elementos*: Historial de importaciones y stats de cobertura de datos.

## 5. Notas de Implementación
-   **Server Actions**: Todas las mutaciones (crear proyecto, subir CSV) ocurren en el servidor (`lib/actions.ts`).
-   **Data Service**: La lectura de datos para el frontend está centralizada en `lib/data-service.ts` para mantener consistencia en los cálculos.
-   **Next.js 15 Compatibility**: Se manejan los `params` y `searchParams` como Promesas (`await params`) en las páginas.
