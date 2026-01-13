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

    # Normalization
    # Keyword, Volume, Difficulty
    if 'Palabra clave' in df.columns:
        df['keyword'] = df['Palabra clave']
    else:
        return None, "Columna 'Palabra clave' no encontrada."

    if 'Volumen' in df.columns:
        df['volume'] = df['Volumen'].apply(normalize_int)
    
    if 'Dificultad de la palabra clave' in df.columns:
        df['difficulty'] = df['Dificultad de la palabra clave'].apply(normalize_int)
    
    if 'Intención' in df.columns:
        df['intent'] = df['Intención']

    # Process per-domain data
    # We will create a simplified structure or just keep the DF clean
    # For the dashboard, we need a main domain. We'll pick the first one found or let user choose.
    # For now, we clean the columns in place 
    
    for domain, mapping in domain_map.items():
        if 'visibility' in mapping:
            df[mapping['visibility']] = df[mapping['visibility']].apply(normalize_percent)
            # Handle N/D in position (which might be text "No está...")
            # If position is numeric 1-100.
        
        if 'position' in mapping:
            # function to handle ranking
            def parse_pos(x):
                if pd.isna(x): return 101 # Not ranked
                x_str = str(x).lower()
                if 'no está' in x_str or 'n/d' in x_str or '-' == x_str.strip(): return 101
                try:
                    return int(float(str(x).replace(',', '.')))
                except:
                    return 101
            df[mapping['position']] = df[mapping['position']].apply(parse_pos)

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
    Returns keywords where position is 4-10
    """
    if main_domain not in domain_map: return pd.DataFrame()
    pos_col = domain_map[main_domain]['position']
    
    # Filter 4 <= pos <= 10
    mask = (df[pos_col] >= 4) & (df[pos_col] <= 10)
    opportunities = df[mask].copy()
    
    # Add relevant columns for display
    display_cols = ['keyword', 'volume', 'difficulty', 'intent', pos_col]
    # Add visibility if exists
    if 'visibility' in domain_map[main_domain]:
        display_cols.append(domain_map[main_domain]['visibility'])
        
    return opportunities[display_cols].sort_values('volume', ascending=False)
