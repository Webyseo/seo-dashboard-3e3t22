# AGENTS.md — Guía Ejecutiva para Decisiones y Desarrollo de Nivel Senior

Este documento orienta cómo convertir instrucciones (a veces ambiguas) en entregables con criterio ejecutivo: claridad estratégica, impacto medible y control de riesgo.

## 1) Enmarcar la decisión
- Formula el objetivo en términos de negocio (“queremos X para lograr Y”).
- Define el KPI o señal de éxito (ej. SoV, Top 3/10, CTR, ahorro, pipeline).
- Declara supuestos y su impacto. Si un supuesto cambia, qué se rompe.

## 2) Claridad antes de ejecutar
- Pide un ejemplo real o un caso de uso representativo.
- Alinea el alcance: qué incluye y qué no incluye el cambio.
- Confirma riesgos si afecta métricas, informes o comparativas históricas.

## 3) Diseño orientado a impacto
- Prioriza la palanca con mayor efecto en el objetivo (no la más fácil).
- Evita dispersión: una decisión, un cambio, un resultado claro.
- Reutiliza lógica central para mantener consistencia de métricas.

## 4) Control de riesgo y trazabilidad
- Introduce cambios de forma incremental y verificable.
- Si no hay tests, usa una validación manual reproducible y documentada.
- Anota el “por qué” cuando cambies cálculos o reglas de negocio.

## 5) Calidad técnica con enfoque ejecutivo
- Claridad > complejidad; evita optimizaciones sin impacto visible.
- Errores con mensajes útiles y fáciles de diagnosticar.
- Evita recalcular métricas críticas sin necesidad.

## 6) Comunicación para decisión
- Entrega en 3-5 bullets: objetivo, cambio, validación, impacto, riesgos.
- Señala impactos laterales (UI, DB, exportaciones, comparativas históricas).
- Si algo queda pendiente, define siguiente paso con criterio.

## 7) Checklist ejecutivo antes de cerrar
- ¿Afecta métricas históricas o reportes clientes?
- ¿El KPI de éxito está definido y es medible?
- ¿Hay una validación mínima y reproducible?
- ¿El riesgo está comunicado con claridad?

## 8) Plantilla ejecutiva breve (útil para IA)
- Objetivo de negocio:
- KPI de éxito:
- Supuestos:
- Cambio propuesto:
- Validación:
- Impacto y riesgos:
