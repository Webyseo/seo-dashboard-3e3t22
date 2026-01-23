# ARCHIVO DE CONFIGURACIÓN Y ESTÁNDARES: REINGENIERÍA DASHBOARD SEO

## 1. OBJETIVO DEL SISTEMA

Transformar el dashboard actual de un visualizador de datos a una herramienta de **toma de decisiones estratégicas**. El enfoque principal debe ser la **rentabilidad (ROI)** y la claridad para un cliente no técnico.

## 2. REESTRUCTURACIÓN DE UX/UI (MODULO: DEEP DIVE)

### A. Nueva Tabla Maestra de Evolución

Sustituir el selector individual de palabras clave por una tabla dinámica con las siguientes columnas obligatorias:

* **Keyword:** Nombre de la palabra clave.
* **Intent:** Etiqueta visual (Pill) indicando si es Comercial, Mixta o Informativa.
* **Posición Actual:** Valor numérico entero.
* **Delta (30d):** Indicador de cambio (ej. +2 ⬆️ / -1 ⬇️) con código de color semántico (Verde/Rojo).
* **Tendencia (Sparkline):** Gráfico lineal minimalista integrado en la celda que muestre el histórico de los últimos 3 meses.
* **Valor Equivalente (€):** Ahorro estimado basado en CPC.
* **Acción Recomendada:** Texto dinámico basado en posición (ej. "Reforzar", "Optimizar CTR", "Crear Contenido").

### B. Interacción Drill-Down

* **Evento Click:** Al seleccionar una fila de la tabla, Antigravity debe actualizar el gráfico de detalle (`Evolución de Posición`) y las métricas específicas de esa keyword en tiempo real.
* **Prioridad Visual:** La tabla debe ocupar el 70% del ancho superior para facilitar el escaneo rápido de todo el proyecto.

## 3. LÓGICA DE NEGOCIO Y ALGORITMOS (STRICT)

* **Enfoque en Retención:** Priorizar en la parte superior de la tabla las keywords en "Striking Distance" (posiciones 4-10).
* **Cálculo de Oportunidad:** Implementar un algoritmo de **Uplift Valor** que calcule el tráfico ganado si la keyword sube al Top 3.
* **Detección de Riesgos:** Marcar automáticamente keywords con caída de SoV (Share of Voice) superior al 5% en el último mes.

## 4. ESTÁNDARES DE DISEÑO (UI)

* **Densidad de Información:** Usar tablas compactas para evitar scroll innecesario.
* **Tooltips Proactivos:** Añadir explicaciones emergentes en métricas complejas como SoV y Media Value para asegurar que el cliente entienda el ahorro financiero.
* **Modo:** Mantener el Dark Mode actual, utilizando contrastes de accesibilidad WCAG AA.

## 5. RECOMENDACIONES DE CONTENIDO (IA ACTIONABLE)

Antigravity debe clasificar las sugerencias bajo la jerarquía de:

1. **Quick Wins:** Ajustes de contenido en URLs existentes que ya traccionan.
2. **Nuevas Oportunidades:** Creación de contenido para keywords con dificultad baja (ej. Máster en periodismo).
3. **Acciones de Protección:** Reforzar autoridad en keywords de alto valor comercial donde la competencia está ganando terreno.