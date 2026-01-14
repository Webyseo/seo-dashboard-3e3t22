Eres un desarrollador senior especialista en Streamlit y data apps. Estás trabajando sobre un dashboard SEO ya existente (Streamlit) que carga CSVs mensuales exportados de Rank Tracker y muestra tablas tipo “Oportunidades de Crecimiento Rápido”.

PROBLEMA
- El dashboard incluye una columna “Intención”, pero Rank Tracker NO proporciona el dato de intención de búsqueda en sus informes/CSVs, por lo que aparece como N/D o vacío.
- Necesitamos mantener el valor SEO de esa columna sin engañar: debe ser un dato “enriquecido”, no de origen Rank Tracker.

OBJETIVO
Implementar un sistema de “Search Intent Enrichment” en Streamlit que:
1) Calcule una “Intención sugerida” por reglas heurísticas (realistas) a partir del texto de la keyword.
2) Permita “Intención validada” manualmente por el usuario (persistente entre meses).
3) Combine ambas en un “Intención (final)”, donde manda la validada.
4) Muestre métricas de calidad: porcentaje de intención validada (no “intent del proveedor”).
5) No requiere llamadas a Google/SERP ni APIs externas (solo reglas + validación humana).

REQUISITOS FUNCIONALES
A) Capa de persistencia independiente del CSV (NO se pierde al cambiar de mes)
- Usar SQLite (recomendado) dentro del proyecto.
- Crear DB: data/intent.db
- Tabla: keyword_intent
  - keyword_norm TEXT PRIMARY KEY
  - keyword_original TEXT
  - intent_validated TEXT  (ENUM: Informativa, Comercial, Transaccional, Navegacional, Mixta/Por validar)
  - local_modifier TEXT (ciudad/ubicación si aplica, opcional)
  - updated_at TEXT (ISO datetime)
  - notes TEXT (opcional)

B) Inferencia por reglas (heurística realista)
- Crear función normalize_keyword(s): lower, strip, colapsar espacios, opcional quitar acentos.
- Crear función infer_intent(keyword_norm) -> dict:
  - intent_suggested: (Informativa/Comercial/Transaccional/Navegacional/Mixta/Por validar)
  - confidence: (Alta/Media/Baja) o float 0-1
  - reasons: lista corta de reglas disparadas (texto)
  - local_modifier: ciudad detectada o None

Reglas recomendadas (ES), con prioridad y “confianza”:
1) Navegacional (Alta):
   - contiene marca o señales de sitio: "login", "teléfono", "contacto", "dirección", "horario", "cómo llegar", "maps"
   - o keyword coincide con nombre de empresa/proyecto (si existe lista de marcas configurable)
2) Transaccional (Alta):
   - contiene: "precio", "tarifa", "presupuesto", "matrícula", "inscripción", "comprar", "contratar", "alquiler", "reserva", "cita", "oferta", "descuento"
3) Comercial / investigación (Media-Alta):
   - contiene: "curso", "máster", "formación", "escuela", "academia", "opiniones", "reseñas", "review", "comparativa", "mejor", "top"
   - Nota: si además contiene “precio/matrícula/inscripción”, prioriza Transaccional.
4) Informativa (Alta):
   - contiene: "qué es", "como", "cómo", "guía", "tutorial", "consejos", "ejemplos", "plantilla", "definición"
5) Si hay mezcla de señales fuertes o ninguna regla aplica:
   - intent_suggested = "Mixta/Por validar"
   - confidence = Baja
6) Modificador local (no es intención, es contexto):
   - detectar ciudades comunes o patrón “en [ciudad]”, “cerca de”, “cerca”
   - devolver local_modifier="barcelona"/"madrid"/etc si detectado

C) Integración con el dataframe principal
- Al cargar el CSV mensual:
  1) Obtener columna keyword (puede llamarse "Keyword", "Palabra Clave", etc). Implementar mapeo robusto:
     - intentar detectar automáticamente el nombre de columna equivalente.
  2) Crear keyword_norm para cada fila.
  3) Consultar SQLite para traer intent_validated por keyword_norm.
  4) Para cada fila:
     - calcular intent_suggested + confidence + reasons + local_modifier con infer_intent()
     - intent_final = intent_validated si existe, sino intent_suggested
     - origin = "Validada" si existe validada, sino "Sugerida"
- Añadir columnas al dataframe mostrado:
  - "Intención" -> usar intent_final (para mantener la UI limpia)
  - "Origen intención" -> Validada / Sugerida
  - (opcional) "Confianza" -> Alta/Media/Baja
  - (opcional) "Motivo" -> string corto unido por “; ”
  - (opcional) "Local" -> ciudad detectada

D) UI/UX en Streamlit (sin iconos)
- En la pestaña donde sale la tabla de oportunidades:
  - Mantener la columna “Intención” pero que ya sea “Intención (final)”.
  - Añadir un texto/tooltip/expander:
    “Nota: Rank Tracker no proporciona intención. Este campo se enriquece por reglas y puede validarse manualmente.”
- Métrica “Calidad de datos”:
  - Sustituir “Intent 0%” por:
    “Intent validada: X%” (X = nº filas con intent_validated / total filas * 100)
  - Opcional: “Intent sugerida: 100%” si siempre hay sugerencia (o “Cobertura sugerida”)
- Añadir módulo “Validar intención”:
  1) Filtro: mostrar solo keywords con origin="Sugerida" y score alto (por ejemplo top 50 por Opportunity Score)
  2) Editor con st.data_editor (o equivalente) para:
     - keyword (solo lectura)
     - intent_suggested (solo lectura)
     - intent_validated (dropdown editable)
     - notes (editable opcional)
  3) Botón “Guardar validación”:
     - upsert a SQLite (keyword_norm, keyword_original, intent_validated, updated_at, notes)
  4) Tras guardar:
     - recargar merge y refrescar tabla principal
- Opcional: botón “Exportar enriquecido” (descargar CSV con intent_final + origin).

E) Rendimiento y robustez
- Cachear lectura del CSV (st.cache_data) con clave por fichero/mes.
- NO cachear escrituras a SQLite.
- Manejar ausencia de permisos de escritura:
  - Si falla SQLite, fallback a intent_map.csv en /data (mismo esquema) con lectura/escritura (y avisar en UI).
- Manejar duplicados:
  - keyword_norm PRIMARY KEY resuelve duplicados.
  - En el merge, si hay keywords repetidas en el CSV, aplicar misma intención a todas.

CRITERIOS DE ACEPTACIÓN (tests manuales)
1) Cargar un CSV mensual sin intent -> la tabla muestra “Intención” rellenada (sugerida) y “Origen intención = Sugerida”.
2) Validar manualmente 3 keywords -> tras refrescar la app:
   - esas 3 aparecen como “Origen = Validada”
   - “Intención” cambia a la validada (aunque la sugerida fuera distinta)
3) Cambiar de CSV (otro mes) -> las mismas keywords mantienen su intención validada.
4) El indicador superior muestra “Intent validada: X%” coherente.
5) Sin dependencias externas ni SERP.

ENTREGABLES
- Código implementado en el proyecto Streamlit existente:
  - módulo db.py (SQLite + CRUD)
  - módulo intent_rules.py (normalize + infer_intent)
  - integración en la página/tab de “Oportunidades”
  - UI “Validar intención” con guardado persistente
- Documentación breve en README:
  - explicación de “Intención sugerida vs validada”
  - cómo añadir/editar reglas
  - ubicación del intent.db

IMPORTANTE
- No afirmar que Rank Tracker da la intención.
- En UI, usar lenguaje: “Intención (enriquecida)”, “Sugerida”, “Validada”.
- Mantener compatibilidad con el dashboard actual y su estética.
