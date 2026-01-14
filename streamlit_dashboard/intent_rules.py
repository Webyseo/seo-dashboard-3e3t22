import re
import unicodedata

def normalize_keyword(s):
    """Normaliza el texto de la keyword para facilitar el matching"""
    if not s or not isinstance(s, str):
        return ""
    # Quitar acentos
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    # Lowercase y limpieza básica
    s = s.lower().strip()
    # Colapsar espacios múltiples
    s = re.sub(r'\s+', ' ', s)
    return s

def infer_intent(keyword):
    """
    Infiere la intención de búsqueda basándose en reglas heurísticas.
    Retorna un dict con: intent_suggested, confidence, reasons, local_modifier
    """
    kw = normalize_keyword(keyword)
    reasons = []
    local_modifier = None
    
    # 1. Modificador Local (Contexto, no intención)
    # Patrón común "en [ciudad]", "cerca de", etc.
    local_patterns = [r' en ([a-z]+)$', r' cerca de ([a-z]+)$', r' ([a-z]+) cerca$']
    for p in local_patterns:
        match = re.search(p, kw)
        if match:
            local_modifier = match.group(1)
            reasons.append(f"Detección local: {local_modifier}")
            break

    # 2. Navegacional (Alta)
    nav_tokens = ["login", "telefono", "contacto", "direccion", "horario", "como llegar", "maps", "acceder", "web", "oficial"]
    if any(token in kw for token in nav_tokens):
        return {
            "intent_suggested": "Navegacional",
            "confidence": "Alta",
            "reasons": ["Contiene señales de sitio/contacto"],
            "local_modifier": local_modifier
        }

    # 3. Transaccional (Alta)
    trans_tokens = ["precio", "tarifa", "presupuesto", "matricula", "inscripcion", "comprar", "contratar", "alquiler", "reserva", "cita", "oferta", "descuento", "barato", "coste"]
    if any(token in kw for token in trans_tokens):
        return {
            "intent_suggested": "Transaccional",
            "confidence": "Alta",
            "reasons": ["Contiene palabras de compra o precio"],
            "local_modifier": local_modifier
        }

    # 4. Comercial / Investigación (Media-Alta)
    com_tokens = ["curso", "master", "formacion", "escuela", "academia", "opiniones", "resenas", "review", "comparativa", "mejor", "top", "servicios", "agencia", "empresa"]
    if any(token in kw for token in com_tokens):
        # Si ya tiene señales comerciales pero no transaccionales directas
        return {
            "intent_suggested": "Comercial",
            "confidence": "Media-Alta",
            "reasons": ["Búsqueda de producto/servicio o comparativa"],
            "local_modifier": local_modifier
        }

    # 5. Informativa (Alta)
    info_tokens = ["que es", "como", "guia", "tutorial", "consejos", "ejemplos", "plantilla", "definicion", "significado", "porque"]
    if any(token in kw for token in info_tokens) or kw.startswith(("que ", "como ", "donde ", "cuando ")):
        return {
            "intent_suggested": "Informativa",
            "confidence": "Alta",
            "reasons": ["Patrón de pregunta o búsqueda de información"],
            "local_modifier": local_modifier
        }

    # 6. Fallback
    return {
        "intent_suggested": "Mixta/Por validar",
        "confidence": "Baja",
        "reasons": ["Sin señales claras detectadas"],
        "local_modifier": local_modifier
    }
