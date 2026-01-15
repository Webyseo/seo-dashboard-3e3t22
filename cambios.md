# SEO Intelligence Dashboard — Client Extensions vNext

> **Documento de especificación funcional y técnica**
> Extensión PRO solicitada por cliente.
> Diseñado para ejecución directa por IA / equipo dev.

---

## 0. Objetivo del documento

Este documento define **nuevas funcionalidades solicitadas por el cliente** para el SEO Intelligence Dashboard, con el objetivo de:

* Aumentar la **capacidad de análisis táctico** (keyword a keyword)
* Mejorar la **comprensión del journey del usuario**
* Traducir datos SEO en **instrucciones claras para el equipo de marketing**
* Elevar el rol de la IA a **asistente estratégico accionable**

Este documento **no sustituye** la documentación existente. La extiende.

---

## 1. Actualización del motor de IA

### 1.1 Modelo

* Sustituir el modelo actual por:
  **`gemini-3-flash-preview`**

### 1.2 Rol de la IA (no negociable)

La IA:

* ❌ No genera datos
* ❌ No extrapola fuera del dataset
* ❌ No rellena huecos con suposiciones

La IA **solo interpreta y prioriza** los datos calculados por el sistema.

### 1.3 Uso principal

* Generación de informes mensuales
* Generación de informes globales (histórico)
* Redacción de **recomendaciones accionables para marketing**

Los resultados deben cachearse por `import_id`.

---

## 2. Comparativo mes a mes por palabra clave

### 2.1 Descripción funcional

Añadir un módulo que permita analizar la evolución **individual de cada keyword**.

### 2.2 Métricas por keyword

Por cada palabra clave seleccionada:

* Posición por mes
* Δ Posición vs mes anterior
* Clics estimados por mes
* Δ Clics estimados
* Valor / Coste equivalente estimado por mes
* Δ Valor estimado

### 2.3 Visualización

* Tabla cronológica por keyword
* Indicadores visuales:

  * ⬆ mejora
  * ⬇ empeora
  * ⏸ estable

### 2.4 Criterio de aceptación

* El usuario puede entender claramente si una keyword **mejora, empeora o se estanca** sin interpretar datos técnicos.

---

## 3. Comprensión del journey del usuario

### 3.1 Objetivo

Permitir entender **cómo llega el usuario** a través del buscador.

### 3.2 Enriquecimiento por keyword

Relacionar:

* Keyword
* Intent (informativa / comercial / transaccional / navegacional)
* Tipo de contenido actual
* URL asociada (si existe)

### 3.3 Detección de gaps

Detectar y marcar:

* Keywords con intención clara **sin contenido adecuado**
* Keywords donde el tipo de contenido no coincide con la intención

### 3.4 Criterio de aceptación

* El dashboard identifica oportunidades de contenido alineadas con la intención del usuario.

---

## 4. Coste por clic y valor económico por keyword

### 4.1 Requisito

Mostrar el **coste estimado por clic por palabra clave**, aunque sea aproximado.

### 4.2 Métricas

Por keyword:

* CPC (si existe)
* Clics estimados
* Coste equivalente SEO (si fuera Ads)

Todas las métricas deben ir marcadas como:

> **ESTIMADO**

con tooltip explicativo.

### 4.3 Fallback

* Si no existe CPC → mostrar “No disponible (falta CPC)”

---

## 5. Comparativa de competencia por selección de keywords

### 5.1 Funcionalidad

Añadir un selector manual que permita elegir **N keywords** (ej. 5 / 10 / 15).

### 5.2 Vista resultante

Para las keywords seleccionadas:

* Dominio
* Posición
* Visibilidad

Comparando:

* Dominio principal
* Competidores detectados

### 5.3 Uso principal

* Campañas
* Landings estratégicas
* Servicios clave

### 5.4 Criterio de aceptación

* El usuario puede analizar competencia **solo sobre keywords estratégicas**, no sobre todo el dataset.

---

## 6. Sugerencias de keywords sin canibalización

### 6.1 Objetivo

Proponer **nuevas oportunidades de contenido** sin canibalizar URLs existentes.

### 6.2 Reglas

Una keyword es elegible si:

* No tiene URL asociada
* O existe un gap claro de intención
* No compite con otra URL del mismo dominio

### 6.3 Output

* Top 5 ideas de contenido
* Agrupadas por intención / tópico

### 6.4 Criterio de aceptación

* Las sugerencias no generan conflictos internos de posicionamiento.

---

## 7. Nuevo estándar de informes IA (marketing-first)

### 7.1 Estructura obligatoria del informe

Cada informe debe incluir **siempre**:

#### 1. Resumen ejecutivo

* Qué ha pasado
* Qué ha cambiado vs mes anterior
* Impacto real

#### 2. Diagnóstico basado en datos

* Keywords destacadas
* Quick wins
* Riesgos
* Dependencia de marca

#### 3. Recomendaciones para marketing

Formato obligatorio:

**Acciones prioritarias**

* Crear contenido nuevo para: X, Y
* Optimizar contenido existente: URL A

**Acciones a evitar**

* No crear contenido para: Z (canibalización)

#### 4. Checklist operativo

* ☐ Crear contenido
* ☐ Optimizar títulos
* ☐ Refuerzo semántico
* ☐ Enlazado interno
* ☐ No lanzar Ads si SEO ya cubre

### 7.2 Lenguaje

* No técnico
* Directivo
* Orientado a ejecución

---

## 8. Prompt base para la IA (resumen)

El prompt debe:

* Referenciar métricas reales
* Usar condicionales si faltan datos
* No inventar valores
* Priorizar acciones
* Dirigirse al **equipo de marketing**, no a SEOs técnicos

---

## 9. Definition of Done (DoD)

✅ Comparativo keyword mes a mes funcional
✅ Coste estimado por keyword visible y marcado
✅ Selección de keywords para análisis competitivo
✅ Sugerencias sin canibalización operativas
✅ Informes IA con recomendaciones accionables
✅ Uso de `gemini-3-flash-preview` confirmado
✅ Fallbacks claros cuando falten datos

---

## 10. Resultado esperado

El dashboard pasa de ser:

> “Una herramienta de reporting SEO”

A ser:

> **Un sistema operativo de decisiones SEO + marketing**

---

FIN