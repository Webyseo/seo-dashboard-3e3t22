import pandas as pd
import re

def normalize_currency(val):
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    val = str(val).replace('$', '').replace('€', '').replace(',', '.')
    try:
        return float(val)
    except:
        return 0.0

def normalize_percent(val):
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    val = str(val).replace('%', '').replace(',', '.')
    try:
        return float(val)
    except:
        return 0.0

def normalize_int(val):
    if pd.isna(val): return 0
    if isinstance(val, (int, float)): return int(val)
    val = str(val).replace('.', '').replace(',', '') # remove thousands separator
    try:
        return int(val)
    except:
        return 0

def parse_csv_data(file):
    """
    Parses the uploaded CSV file and returns a structured DataFrame and metadata.
    """
    try:
        df = pd.read_csv(file)
    except Exception as e:
        return None, f"Error reading CSV: {str(e)}"

    # Dynamic column detection
    cols = df.columns
    
    # Identify standard columns vs dynamic domain columns
    # Expected standard columns: 'Palabra clave', 'Volumen', 'Dificultad de la palabra clave', 'CPC', 'Intención'
    # Dynamic: 'Posición [domain]', 'Visibilidad [domain]', 'Tráfico [domain]'
    
    domain_map = {} # { 'domain.com': { 'position': 'Posición [domain.com]', 'visibility': 'Visibilidad ...' } }
    
    for col in cols:
        # Check for Visibility column (Anchor)
        # Format can be "Visibilidad [domain.com]" or "Visibilidad domain.com"
        if 'Visibilidad' in col:
            # Extract domain 
            # 1. Try brackets
            match_brackets = re.search(r'Visibilidad\s*\[(.*?)\]', col)
            if match_brackets:
                domain = match_brackets.group(1)
            else:
                # 2. Try simple suffix if it starts with Visibilidad
                if col.startswith('Visibilidad '):
                    domain = col.replace('Visibilidad ', '').strip()
                else:
                    continue # Not a visibility column we recognize
            
            if domain not in domain_map: domain_map[domain] = {}
            domain_map[domain]['visibility'] = col
            
            # Now try to find matching Position and Traffic columns for this domain
            # We look for columns that contain the domain name and "Posición" or "Tráfico"
            
            # Position candidates
            # "Posición [domain]", "Posición en Google domain", "Posición domain"
            possible_pos_cols = [
                f"Posición [{domain}]",
                f"Posición en Google {domain}", 
                f"Posición {domain}"
            ]
            for pcol in possible_pos_cols:
                if pcol in cols:
                    domain_map[domain]['position'] = pcol
                    break
            
            # Traffic candidates
            # "Tráfico [{domain}]", "Tráfico {domain}"
            possible_traf_cols = [
                f"Tráfico [{domain}]",
                f"Tráfico {domain}"
            ]
            for tcol in possible_traf_cols:
                if tcol in cols:
                    domain_map[domain]['traffic'] = tcol
                    break

    # --- Robust Column Detection for Standard Metrics ---
    
    # 1. Keyword
    kw_variants = ['Palabra clave', 'Keyword', 'Palabras clave']
    found_kw = next((c for c in kw_variants if c in df.columns), None)
    df['keyword'] = df[found_kw] if found_kw else "N/D"

    # 2. Volume
    vol_variants = ['Volumen', '# de búsquedas', 'Search Volume', 'Volumen de búsqueda']
    found_vol = next((c for c in vol_variants if c in df.columns), None)
    df['volume'] = df[found_vol].apply(normalize_int) if found_vol else 0
    
    # 3. Difficulty
    diff_variants = ['Dificultad de la palabra clave', 'Google Dificultad Palabra Clave', 'KD', 'Keyword Difficulty']
    found_diff = next((c for c in diff_variants if c in df.columns), None)
    df['difficulty'] = df[found_diff].apply(normalize_int) if found_diff else 0
    
    # 4. Intent
    intent_variants = ['Intención', 'Intent', 'Search Intent']
    found_intent = next((c for c in intent_variants if c in df.columns), None)
    df['intent'] = df[found_intent] if found_intent else "N/D"

    # 5. IPC/CPC
    cpc_variants = ['CPC', 'CPC prom.', 'Coste por clic']
    found_cpc = next((c for c in cpc_variants if c in df.columns), None)
    df['cpc'] = df[found_cpc].apply(normalize_currency) if found_cpc else 0.0

    # --- 1. Normalization Loop for Domains ---
    for domain, mapping in domain_map.items():
        if 'visibility' in mapping:
            df[mapping['visibility']] = df[mapping['visibility']].apply(normalize_percent)
        
        if 'position' in mapping:
            # function to handle ranking
            def parse_pos(x):
                if pd.isna(x): return 101 # Not ranked
                x_str = str(x).lower().strip()
                if x_str in ['no está', 'n/d', '-', '', 'none']: return 101
                try:
                    # Handle cases like "1,0" or "5.0"
                    return int(float(str(x).replace(',', '.')))
                except:
                    return 101
            df[mapping['position']] = df[mapping['position']].apply(parse_pos)

    # --- 2. Advanced Metrics: CTR & Media Value ---
    def get_ctr(pos):
        try:
            pos = int(pos)
        except:
            return 0
            
        if pos == 1: return 0.30
        if pos == 2: return 0.15
        if pos == 3: return 0.10
        if pos == 4: return 0.07
        if pos == 5: return 0.05
        if pos == 6: return 0.04
        if pos == 7: return 0.03
        if pos == 8: return 0.02
        if pos == 9: return 0.015
        if pos == 10: return 0.01
        if 10 < pos <= 20: return 0.005
        return 0

    for domain, mapping in domain_map.items():
        pos_col = mapping.get('position')
        if pos_col:
            # Now x[pos_col] is guaranteed to be numeric (int 1-100 or 101)
            df[f'clics_{domain}'] = df.apply(
                lambda x: x['volume'] * get_ctr(x[pos_col]) if pd.notnull(x[pos_col]) else 0, 
                axis=1
            )
            df[f'media_value_{domain}'] = df[f'clics_{domain}'] * df['cpc']

    # --- 3. Branding Detection ---
    df['is_branded'] = df.apply(lambda x: any(d.split('.')[0].lower() in str(x['keyword']).lower() for d in domain_map.keys()), axis=1)

    return {
        'df': df,
        'domains': domain_map,
        'original_cols': cols
    }, None

def calculate_sov(df, domain_map, main_domain):
    """
    Calculates Share of Voice for the main domain vs others.
    SoV = (Domain Visibility / Sum of All Visibilities for this keyword) * 100 
    But typically SoV in tools is aggregate.
    Simple Metric: Sum of Visibility per domain / Total Visibility Sum across all keywords?
    
    Let's use the definition from the context: 
    (Visibilidad del Dominio Principal / Suma Visibilidad de Todos los Dominios) * 100
    This seems to be per-keyword or global. Let's assume Global Average Visibility or Sum.
    
    Actually, usually it's Sum(Visibility * Search Volume) / Total Potential Traffic.
    
    Given the prompt description: "(Visibilidad del Dominio Principal / Suma Visibilidad de Todos los Dominios) * 100"
    We will calculate total visibility sum for each domain first.
    """
    
    stats = {}
    total_market_vis = 0
    
    for domain, mapping in domain_map.items():
        if 'visibility' in mapping:
            vis_col = mapping['visibility']
            total_vis = df[vis_col].sum()
            stats[domain] = total_vis
            total_market_vis += total_vis
            
    sov_data = []
    for domain, vis in stats.items():
        sov = (vis / total_market_vis * 100) if total_market_vis > 0 else 0
        sov_data.append({
            'domain': domain,
            'visibility_score': vis,
            'sov': sov
        })
        
    return pd.DataFrame(sov_data).sort_values('sov', ascending=False)


def get_striking_distance(df, domain_map, main_domain):
    """
    Returns keywords where position is 4-10 with PRO metrics:
    - Uplift Tráfico Top3
    - Uplift Valor
    - Opportunity Score (0-100)
    """
    if main_domain not in domain_map: 
        return pd.DataFrame()
    
    pos_col = domain_map[main_domain]['position']
    
    # Filter 4 <= pos <= 10
    mask = (df[pos_col] >= 4) & (df[pos_col] <= 10)
    opportunities = df[mask].copy()
    
    if opportunities.empty:
        return pd.DataFrame()
    
    # CTR Curve (same as in parse_csv_data)
    ctr_curve = {
        1: 0.30, 2: 0.15, 3: 0.10, 4: 0.07, 5: 0.05,
        6: 0.04, 7: 0.03, 8: 0.025, 9: 0.02, 10: 0.018
    }
    
    # Average CTR for Top 3
    ctr_top3 = (ctr_curve[1] + ctr_curve[2] + ctr_curve[3]) / 3
    
    # Calculate Uplift Tráfico
    opportunities['uplift_trafico'] = opportunities.apply(
        lambda x: x['volume'] * (ctr_top3 - ctr_curve.get(int(x[pos_col]), 0)) if x['volume'] > 0 else 0,
        axis=1
    )
    
    # Calculate Uplift Valor (if CPC available)
    has_cpc = 'cpc' in opportunities.columns and (opportunities['cpc'] > 0).any()
    if has_cpc:
        opportunities['uplift_valor'] = opportunities['uplift_trafico'] * opportunities['cpc']
    else:
        opportunities['uplift_valor'] = 0
    
    # Opportunity Score (0-100) with adaptive weights
    def normalize(series):
        """Min-max normalization"""
        if series.max() == series.min():
            return pd.Series([0.5] * len(series), index=series.index)
        return (series - series.min()) / (series.max() - series.min())
    
    has_kd = 'difficulty' in opportunities.columns and (opportunities['difficulty'] > 0).any()
    
    # Adaptive scoring based on available data
    if has_cpc and has_kd:
        # Full scoring
        score = (
            normalize(opportunities['uplift_trafico']) * 0.55 +
            normalize(opportunities['volume']) * 0.20 +
            normalize(opportunities['cpc']) * 0.15 +
            normalize(1 / (opportunities['difficulty'] + 1)) * 0.10
        ) * 100
    elif has_cpc:
        # Without KD
        score = (
            normalize(opportunities['uplift_trafico']) * 0.65 +
            normalize(opportunities['volume']) * 0.25 +
            normalize(opportunities['cpc']) * 0.10
        ) * 100
    elif has_kd:
        # Without CPC
        score = (
            normalize(opportunities['uplift_trafico']) * 0.70 +
            normalize(opportunities['volume']) * 0.20 +
            normalize(1 / (opportunities['difficulty'] + 1)) * 0.10
        ) * 100
    else:
        # Minimal scoring
        score = (
            normalize(opportunities['uplift_trafico']) * 0.70 +
            normalize(opportunities['volume']) * 0.30
        ) * 100
    
    opportunities['opportunity_score'] = score.round(1)
    
    # Select display columns
    base_cols = ['keyword', pos_col, 'volume']
    optional_cols = ['difficulty', 'intent', 'cpc', 'uplift_trafico', 'uplift_valor', 'opportunity_score']
    
    display_cols = base_cols + [c for c in optional_cols if c in opportunities.columns]
    
    # Sort by Opportunity Score descending
    return opportunities[display_cols].sort_values('opportunity_score', ascending=False)

def calculate_hhi(sov_df):
    """
    Calcula el Índice Herfindahl-Hirschman (HHI) para medir concentración del mercado
    Returns: (hhi_value, interpretation_text)
    """
    hhi = (sov_df['sov'] ** 2).sum()
    
    # Interpretación según umbrales estándar
    if hhi > 2500:
        interpretation = "🔴 Mercado muy concentrado: 1-2 dominios dominan"
        color = "red"
    elif hhi > 1500:
        interpretation = "🟡 Mercado moderadamente concentrado"
        color = "orange"
    else:
        interpretation = "🟢 Mercado competitivo: visibilidad repartida"
        color = "green"
    
    return hhi, interpretation, color
