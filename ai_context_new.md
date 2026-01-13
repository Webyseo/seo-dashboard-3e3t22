# Prompt de Auditoría y Mejora — SEO Executive Dashboard (Streamlit)

Este documento contiene un **prompt listo para copiar y pegar** y compartir con otro modelo de IA para que audite y proponga mejoras a un **Dashboard SEO ejecutivo**: más avanzado en métricas/estadística, pero **entendible para un público sin experiencia SEO**.

---

## Cómo usar
1) Copia el bloque **PROMPT** completo.
2) Pégalo en el otro modelo de IA.
3) Si quieres, ajusta el apartado **CONTEXTO** con el nombre real del proyecto/cliente.

---

## PROMPT (copy/paste)

```text
Actúa como un Product + Data + UX Lead senior especializado en dashboards SEO para público no técnico (dueños de negocio y directores de marketing sin experiencia SEO). 

CONTEXTO (lo que YA existe)
Tenemos un “SEO Executive Dashboard” en Streamlit (Python/Pandas/Plotly) que convierte CSVs (Semrush/Sistrix/Ahrefs u otras exportaciones similares) en un reporte ejecutivo.
- ETL: detección dinámica de dominios desde cabeceras tipo “Visibilidad [dominio]”, “Visibilidad dominio”, “Posición en Google dominio”.
- Normalización: soporta formatos internacionales, “N/D”, guiones, símbolos, y mapea sinónimos (“Volumen” vs “# de búsquedas”, “KD” vs “Dificultad”, etc.).
- Tabs actuales:
  1) Resumen Ejecutivo: cards KPI (Share of Voice, Top3/Top10, Quick Wins), histograma de posiciones, y resumen generativo IA (3 párrafos + 3 recomendaciones).
  2) Competencia: market split y benchmark de visibilidad.
  3) Oportunidades (Striking Distance): keywords donde el dominio está pos 4–10.
- Métrica base: “Visibilidad” viene indexada en el CSV. SoV = visibilidad dominio / visibilidad total mercado * 100.
- Limitación actual: análisis mono-mes (sin histórico), y falta capa de “estadística avanzada entendible”.

OBJETIVO DE TU TRABAJO
1) Auditar el dashboard actual (desde el punto de vista de ejecutivo no técnico) y detectar huecos.
2) Proponer y priorizar mejoras concretas en 3 niveles:
   - “Impacto alto / esfuerzo bajo” (quick wins de producto)
   - “Impacto alto / esfuerzo medio”
   - “Apuesta avanzada” (estadísticas/insights premium)
3) Definir nuevas métricas y visualizaciones avanzadas, PERO:
   - Deben ser fáciles de explicar con una frase.
   - Cada métrica debe incluir: definición simple, fórmula, cómo interpretarla, y qué acción sugiere.
4) Entregar un plan de implementación para Streamlit/Pandas/Plotly (sin escribir la app completa), con pseudocódigo o snippets cuando ayude.

REQUISITOS CLAVE (NO NEGOCIABLES)
- Público sin experiencia SEO: evita jerga o tradúcela con analogías.
- Nada de “tablas interminables”: prioriza insights, rankings y acciones.
- Transparencia: si una métrica es estimada (CTR, tráfico, valor), indícalo explícitamente.
- Rendimiento: pensar en CSVs grandes (100k+ filas). Vectorización, caché, y evitar operaciones que disparen memoria.
- Compatibilidad: seguir usando detección dinámica de dominios + normalización robusta.
- No inventes datos: si falta una columna (p.ej. CPC o intent), propones fallback (y cómo se comporta).

PERSISTENCIA + HISTÓRICO MENSUAL (NO NEGOCIABLE)
- Cada mes voy a subir 1 archivo (CSV) con los datos completos por palabra clave.
- El sistema debe almacenar esos archivos de forma PERSISTENTE en el servidor (no solo en memoria y no se pierde al reiniciar).
- Debe soportar múltiples meses por “proyecto/dominio” y permitir comparar tendencias entre meses (MoM) usando esos archivos almacenados.
- Debe existir un registro/índice de “subidas” (fecha, mes, nombre de archivo, dominio/proyecto, nº filas, validación OK/KO, etc.).
- Debe permitir re-subir un mes (sobrescribir o versionar) con reglas claras y auditables.
- Debe definirse un “mes activo” por defecto (último subido), y un selector para cambiar de mes.

COMPARTIR POR URL (READ-ONLY)
- Cuando yo comparta una URL del dashboard, cualquier persona que reciba esa URL debe poder ver los datos y el histórico almacenado (sin tener que subir archivos).
- La vista compartida debe ser de solo lectura (no permite editar ni subir).
- La URL debe apuntar a datos persistidos asociados a un identificador de reporte/proyecto (y, si aplica, un token de acceso).
- La experiencia compartida debe cargar siempre los mismos datos persistidos asociados a esa URL, incluso días después.
- Si propones autenticación, que sea simple (por ejemplo: enlace con token o contraseña de proyecto), pero la prioridad es que la URL funcione para terceros.

REQUISITOS TÉCNICOS PARA LA PERSISTENCIA
- Proponer una estrategia realista para Streamlit en producción:
  - Opción A: Base de datos (SQLite en MVP / Postgres en producción) + tabla de “uploads” + tabla de “keywords mensuales”.
  - Opción B: Guardado de CSV en almacenamiento persistente + metadatos en DB (recomendado si los CSV son grandes).
- Incluir cómo se hace el “ingest” mensual (validación, normalización, deduplicación, versionado).
- Incluir cómo se resuelven proyectos/múltiples dominios y cómo se selecciona el “mes activo”.
- Incluir consideraciones de rendimiento (100k+ filas por mes) y caché por mes/proyecto.
- Incluir un enfoque simple de multi-tenant (separación por proyecto/cliente) si aplica.

MEJORAS QUE QUIERO SÍ O SÍ CUBRIR (mínimo)
A) Predicción de tráfico/clics (modelo CTR por posición):
   - Proponer una curva CTR configurable (por defecto genérica) para estimar clics = volumen * CTR(posición).
   - Mostrar “clics estimados actuales” y “clics potenciales” si sube a Top3.
B) Media Value (valor publicitario):
   - Con CPC (si existe), estimar valor = clics estimados * CPC.
C) Análisis por intención:
   - Si hay “intent”, agrupar oportunidades por Informativa/Transaccional/etc. y explicar qué tipo de contenido corresponde.
D) Canibalización:
   - Detectar keywords con múltiples URLs del mismo dominio (si hay URL). Señalar riesgo y acción sugerida.
E) Histórico multi-mes + almacenamiento persistente:
   - Permitir cargar cada mes un CSV (por proyecto/dominio) y guardarlo de forma persistente.
   - Poder seleccionar mes actual vs meses anteriores y ver tendencias MoM:
     SoV, clics estimados, valor estimado, Top3/Top10, quick wins, striking distance,
     ganadores/perdedores, y cambios de ranking.
   - Soportar “re-subida” de un mes (sobrescritura o versionado) con histórico de cambios.
   - Vista compartible por URL (read-only) que muestre exactamente el dataset persistido.

PROPUESTAS “ESTADÍSTICAS AVANZADAS PERO ENTENDIBLES” (quiero ideas)
Incluye al menos 8 ideas con:
- nombre de la métrica (humana),
- definición en 1 frase,
- fórmula,
- visual recomendada,
- “qué decisión ayuda a tomar”.
Ejemplos del tipo que busco (no te limites a esto):
- Concentración del mercado (HHI) para ver si 1–2 competidores dominan.
- “Opportunity Score” combinando Volumen, posición, dificultad, y valor.
- “Share of Top3” (qué % de keywords del mercado están copadas por cada dominio en Top3).
- Distribución por percentiles (p50/p75/p90) de posiciones y cómo evoluciona.
- “Gap de contenido”: oportunidades por intent + temas (si hay cluster/categoría o se infiere por n-grams).
- “Riesgo”: dependencia excesiva de pocas keywords (cola larga vs concentración).

DISEÑO / UX (muy importante)
- Proponer una estructura de navegación ideal (tabs y sub-secciones).
- Añadir filtros útiles (proyecto, dominio, mes, intent si aplica, branded vs non-branded, rango de volumen, KD, posición).
- Incluir un “Glosario ejecutivo” fijo: 10 términos máximo, explicados simple.
- Cada pantalla debe responder: 
  1) ¿Cómo vamos?
  2) ¿Contra quién competimos?
  3) ¿Dónde está el dinero/impacto?
  4) ¿Qué hago este mes?

ENTREGABLES (FORMATO DE RESPUESTA)
1) Auditoría breve del estado actual (fortalezas, riesgos, y “qué falta para ser executive-grade”).
2) Backlog priorizado (tabla: mejora / impacto / esfuerzo / dependencia).
3) Definición de métricas nuevas (con fórmulas + interpretación + acción).
4) Wireframe textual de cada tab (qué cards, qué gráfico, qué tabla mínima).
5) Plan técnico (ETL + modelo de datos + cache + estructura de funciones).
6) Lista de “fallbacks” cuando falten columnas (CPC, intent, URL, etc.).
7) Checklist de calidad (validación de datos, tests mínimos, performance).
8) Diseño de persistencia y compartir URL (esquema de tablas/storage, flujo de ingest mensual, versionado, y cómo se genera/resuelve la URL compartida read-only).

RESTRICCIONES DE ESTILO
- Escribe en español neutro, directo, sin relleno.
- Todo lo que propongas debe poder implementarse con Pandas/Plotly/Streamlit.
- Si propones IA generativa, limita llamadas (resumen ejecutivo) y usa caché para no repetir.
- Siempre que menciones una métrica, añade el “para qué sirve” en lenguaje humano.

Ahora produce tu respuesta siguiendo EXACTAMENTE el formato de entregables.