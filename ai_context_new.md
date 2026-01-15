# PRO Upgrade Spec — SEO Intelligence Dashboard (Streamlit)
**Objetivo:** guiar a un modelo de IA (dev) para implementar mejoras **nivel consultora top** sin perder la claridad para un usuario sin experiencia SEO.

> Este documento NO es teoría. Es una lista de cambios accionables con criterios de aceptación y guía técnica para Streamlit + Pandas + Plotly + SQLite.

---

## 0) Contexto del producto (lo que ya existe)
- App Streamlit con estética dark “premium”.
- Persistencia en SQLite con jerarquía: `Projects` > `Imports` (mes YYYY-MM) > `Keyword Metrics`.
- ETL robusto (cabeceras dinámicas + normalización de números/monedas).
- Módulos actuales:
  1) Resumen Ejecutivo (mensual): KPIs + texto IA + distribución rankings
  2) Competencia: tabla + pie SoV + HHI + Bar Chart
  3) Oportunidades: striking distance + Opportunity Score + Intent Validation
  4) Inteligencia avanzada: valor/ahorro + marca vs genérico
  5) Reporte Global: histórico MoM con IA insights + comparativa First vs Last
  6) Seguridad: Zona de Gestión protegida por contraseña ("Webyseo@")
- Shared URL read-only: `?import_id=...`

---

## 1) Principios no negociables (para que sea PRO y entendible)
1) **Consistencia de nombres**: una métrica = un nombre en toda la app.
2) **Transparencia de estimaciones**: todo lo estimado debe marcarse como “Estimado” + tooltip.
3) **Decisiones, no tablas**: cada pantalla debe terminar en “qué hago este mes”.
4) **Rendimiento**: soportar 100k+ filas/mes (sin bloqueos de memoria).
5) **Persistencia y compartición**: lo que se ve por URL compartida debe ser reproducible días después (datos persistidos, read-only).

---

## 2) Cambios PRO (Backlog priorizado)

### A) Impacto alto / esfuerzo bajo (Quick Wins)
**A1. Unificar nombres y micro-definiciones**
- Cambiar en toda la UI:
  - “Share of Voice”, “Cuota de mercado”, “Visibilidad” → **“Cuota de Visibilidad (SoV)”**
- Debajo de KPI / al lado del título: micro-frase fija
  - `SoV: % de visibilidad frente a competidores en este conjunto de keywords.`
- Repetir patrón para:
  - **Clics estimados**: “Estimación: Volumen × CTR(posición)”
  - **Valor equivalente (Ads)**: “Estimación: Clics estimados × CPC (si existe)”
  - **Quick Wins**: “Keywords en pos 4–10 con alto potencial de subir a Top3”

**Criterio de aceptación**
- Ninguna pantalla muestra nombres distintos para la misma métrica.
- Cada KPI estimado incluye tooltip “cómo se calcula”.

---

**A2. Etiqueta “Estimado” + Tooltips**
- Añadir badge junto a KPIs calculados por curva CTR / CPC:
  - `Clics estimados` → badge `Estimado`
  - `Valor equivalente (Ads)` → badge `Estimado`
- Tooltip estándar:
  - “Se calcula con una curva CTR por posición. Configurable.”

**Criterio de aceptación**
- Todos los KPIs estimados tienen badge y tooltip.

---

**A3. Moneda por proyecto (evitar $ por defecto)**
- Configurar moneda por `Project` (`EUR` por defecto).
- Formateo consistente:
  - miles con separador local
  - 2 decimales solo si tiene sentido

**Criterio de aceptación**
- En proyectos ES se muestra `€` y formato europeo.

---

**A4. Panel de “Calidad del dato” (confianza del cliente)**
Añadir arriba del Resumen Ejecutivo y/o Global una línea tipo:
- `Calidad de datos: CPC 62% | Intent 0% | URL 100% | Competidores 10 dominios`

**Cómo calcular**
- % de filas con columna no nula (CPC/Intent/URL)
- nº de competidores detectados en el mes

**Criterio de aceptación**
- Visible siempre que se seleccione un mes.

---

### B) Impacto alto / esfuerzo medio
**B1. “Plan de Acción del Mes” (3 pasos)**
Añadir un bloque al inicio del Resumen Ejecutivo:
- **Paso 1 — Impacto alto (3 items)**
  - Top 3 keywords/URLs por **Uplift Clics Top3** (ver B2)
- **Paso 2 — Riesgo (1 alerta)**
  - ejemplo: caída SoV MoM, dependencia alta de marca, caída clics estimados, etc.
- **Paso 3 — Ejecución (2 tareas checklist)**
  - tareas sugeridas (on-page / contenido / enlazado) basadas en datos disponibles

**Criterio de aceptación**
- El cliente puede leer este bloque y entender “qué hacer” sin mirar tablas.

---

**B2. Oportunidades con prioridad real (Uplift + Score)**
En la tabla de Oportunidades (pos 4–10), añadir columnas calculadas:
- `Uplift clics si Top3 = Volumen × (CTR(Top3) - CTR(pos_actual))`
- `Uplift valor = Uplift clics × CPC` (si CPC existe)
- `Opportunity Score (0–100)` (ver fórmula sugerida abajo)
- Orden por defecto: `Opportunity Score DESC`

**Score sugerido (editable)**
- Base:
  - `score = norm(uplift_clicks) * 0.55 + norm(volumen) * 0.20 + norm(CPC) * 0.15 + norm(1/KD) * 0.10`
- Si no hay CPC → redistribuir pesos a uplift/volumen
- Si no hay KD → eliminar factor y redistribuir

**Criterio de aceptación**
- La tabla ya no es “lista”; es un ranking priorizado accionable.

---

**B3. Deltas MoM en KPIs (en todas las vistas)**
- Mostrar en KPIs del mes:
  - `SoV` con Δ vs mes anterior
  - `Clics estimados` Δ
  - `Valor equivalente (Ads)` Δ
  - `Quick Wins` Δ
- En Global:
  - Toggle `Último mes` / `Acumulado`

**Criterio de aceptación**
- Si existe mes anterior, todos los KPIs muestran delta.

---

**B4. Competencia: Bar chart + Variación**
- Mantener tabla, pero añadir:
  - **Bar chart Top 10** por SoV
  - Columna `Δ SoV vs mes anterior` por competidor (si hay histórico)
- Mantener pie chart opcional (colapsable) o sustituirlo si se prefiere.

**Criterio de aceptación**
- Se identifica rápidamente el Top 3 competidores y su evolución.

---

**B5. Métrica PRO: Concentración del mercado (HHI)**
- Calcular HHI sobre shares (SoV%) del mes:
  - `HHI = sum((share_i * 100)^2)` donde share_i en proporción (0-1) o usar % directamente según implementación consistente.
- Texto interpretativo:
  - “Mercado muy concentrado: 1–2 dominios dominan.” / “Mercado competitivo: más repartido.”

**Criterio de aceptación**
- Se muestra HHI + interpretación en Competencia.

---

### C) Apuesta avanzada (para “modo consultora”)
**C1. Alertas automáticas (Insights)**
En Resumen Ejecutivo mostrar 3 insights automáticos (sin IA o con IA opcional):
- Insight 1: SoV baja pero clics suben (mix de keywords, cambios de posiciones)
- Insight 2: dependencia de marca alta (Marca > X%)
- Insight 3: aumento de Quick Wins (o caída)

**Criterio de aceptación**
- Los insights se generan sin inventar datos; si faltan columnas, se omite.

---

**C2. Exportable “PDF Ejecutivo”**
- Botón “Exportar PDF” del Resumen Ejecutivo (o generar HTML imprimible).
- Incluir: Plan de Acción + KPIs + 1 gráfico + Top oportunidades.

**Criterio de aceptación**
- Un PDF compartible internamente por el cliente.

---

## 3) Cambios por pantalla (Wireframe textual)

### 3.1 Resumen Ejecutivo (Mensual)
1) Encabezado: proyecto + mes seleccionado + fuente/fecha de carga
2) **Calidad de datos** (CPC/Intent/URL/Competidores)
3) **Plan de Acción del Mes (3 pasos)**
4) KPIs (con badge “Estimado” + Δ MoM)
5) Distribución de rankings (barras)
6) Tabla mínima “Top 10 oportunidades” (Opportunity Score)
7) (Opcional) Texto IA: 3 párrafos + 3 recomendaciones, con caché por import_id

---

### 3.2 Competencia
1) Tabla competidores con SoV + Δ MoM
2) Bar chart Top 10 SoV
3) HHI + interpretación
4) (Opcional) Pie chart colapsable

---

### 3.3 Oportunidades
1) Filtros: volumen min, KD max, intent, branded/no
2) Tabla priorizada con:
   - keyword, pos actual, volumen, KD, intent, CPC
   - uplift clics top3, uplift valor, score
3) Export CSV de oportunidades

---

### 3.4 Inteligencia Avanzada
1) “Valor equivalente (Ads)” top keywords (con disclaimer)
2) “Marca vs Genérico”:
   - % marca vs genérico
   - Δ MoM si existe
   - texto: “Dependencia de marca alta/baja”
3) (Opcional) Canibalización si existe URL:
   - keywords con múltiples URLs del mismo dominio

---

### 3.5 Reporte Global (Histórico)
1) Cards:
   - SoV último mes + Δ
   - clics estimados último mes + Δ
   - valor equivalente último mes + Δ
2) Toggle: `Último mes` / `Acumulado`
3) Gráficas:
   - SoV MoM (línea)
   - clics estimados MoM (área)
4) Tabla histórica (mes, SoV, clics, valor) + export

---

## 4) Reglas de cálculo (definiciones formales)

### 4.1 SoV (Cuota de Visibilidad)
- `SoV_dom = visibilidad_dom / sum(visibilidad_todos_dominios) * 100`
- Mostrar con 1 decimal.

### 4.2 CTR por posición (configurable)
- Implementar curva CTR por defecto (editable por config):
  - pos1 0.30, pos2 0.15, pos3 0.10, pos4 0.07, pos5 0.05, pos6 0.04, pos7 0.03, pos8 0.025, pos9 0.02, pos10 0.018, 11-20 decae, 20+ residual
- Guardar la curva en configuración (db o constante + override).

### 4.3 Clics estimados
- `clics_est = volumen * CTR(pos_actual)`

### 4.4 Valor equivalente (Ads)
- `valor_est = clics_est * CPC`
- Si no hay CPC: mostrar “No disponible (falta CPC)”.

### 4.5 Uplift Top3 (para oportunidades)
- `uplift_clicks = volumen * (CTR(3) - CTR(pos_actual))` (si pos_actual > 3)
- `uplift_value = uplift_clicks * CPC` (si CPC)

---

## 5) Persistencia y “Compartir URL” (read-only)
**Objetivo:** que al compartir una URL, el receptor vea exactamente los datos persistidos.

### 5.1 Reglas
- Admin (subir/borrar/regenerar IA) **no accesible** desde URL compartida.
- URL compartida debe ser:
  - `...?share_token=...` o `...?import_id=...&token=...`
- Token vinculado a:
  - `project_id`
  - `import_id` (opcional fijo a un mes) o “último mes” si es vista dinámica

### 5.2 Criterios de aceptación
- Abrir link en navegador incógnito muestra datos sin UI de administración.
- Reinicio del servidor NO rompe el link.
- Token puede revocarse.

---

## 6) Guía técnica (implementación Streamlit)
### 6.1 Arquitectura recomendada (sin reescribir todo)
- `etl.py`:
  - funciones puras, vectorizadas, sin loops por fila
- `database.py`:
  - insertar por lotes, índices en (`project_id`, `period`), (`import_id`)
- `app.py`:
  - capas: selector proyecto/mes → cargar dataset persistido → computar KPIs agregados → render

### 6.2 Rendimiento / memoria
- Usar `st.cache_data` por (project_id, period, import_id) en:
  - dataset normalizado
  - KPIs agregados
  - oportunidades calculadas
- Evitar guardar en memoria tablas enormes sin necesidad:
  - en DB guardar raw JSON competidores, pero también almacenar **agregados mensuales** (tabla `monthly_kpis` opcional) para Global rápido.
- Para tablas grandes:
  - paginar / limitar (top 200) + filtros
  - export bajo demanda

### 6.3 Localización
- Formateo de números/moneda por project settings:
  - `currency = EUR`
  - `locale = es-ES`
- Nunca mostrar `$` por defecto en proyectos ES.

---

## 7) Fallbacks (si faltan columnas)
- Si falta `CPC`:
  - ocultar valor equivalente y uplift_value
  - mantener clics estimados
- Si falta `Intent`:
  - ocultar segmentación por intent
  - mostrar “Intent no disponible”
- Si falta `KD`:
  - score sin KD (redistribuir pesos)
- Si falta `URL`:
  - no mostrar canibalización
- Si falta competencia (solo 1 dominio detectado):
  - SoV = 100% pero mostrar aviso:
    - “Competencia no detectada en el archivo. SoV puede no representar mercado.”

---

## 8) Definition of Done (DoD) — “PRO listo para cliente”
✅ Consistencia total de nombres de métricas  
✅ Badges + tooltips en todo lo estimado  
✅ Plan de Acción del Mes (3 pasos) implementado  
✅ Oportunidades con Uplift + Opportunity Score + orden por prioridad  
✅ Deltas MoM en KPIs y competencia (ahora en pp)  
✅ Competencia con Bar chart + HHI + Δ MoM  
✅ Calidad del dato visible y correcta (incluyendo Intent Validada)  
✅ Moneda EUR por defecto y estandarización de visibilidad (anti-escala)  
✅ Shared URL read-only funcional, persistente, sin zona admin  
✅ Protección por contraseña en la Zona de Gestión  
✅ Sistema de Enriquecimiento de Intención (Heurística + Persistencia) funcional  

---

## 9) Checklist de tests (mínimos)
1) Subir 2 meses (YYYY-MM) y validar:
   - deltas MoM correctos
   - selector mes funciona
2) Proyecto con CPC y sin CPC:
   - valor equivalente aparece/oculta bien
3) Dataset grande (100k filas):
   - carga razonable
   - tablas limitadas/paginadas
4) Shared URL en incógnito:
   - read-only real (sin botones admin)
5) Competencia con 1 dominio y con varios:
   - mensajes de fallback correctos
6) Validación numérica:
   - decimales europeos/americanos
   - símbolos €, $, %, N/D

---

## 10) Entregable esperado del modelo de IA (formato de respuesta)
1) Lista de tareas (orden de implementación)  
2) Cambios de UI por pantalla (componentes Streamlit)  
3) Cambios de datos/DB (si aplica)  
4) Fórmulas finales y pesos del Opportunity Score  
5) Plan de pruebas + riesgos + mitigaciones  
6) Fragmentos de pseudocódigo donde sea crítico (caché, cálculo uplift, HHI, share link)

---
FIN