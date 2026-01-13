import sqlite3
import pandas as pd
import json
import os

DB_PATH = "seo_dashboard_v2.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Projects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        main_domain TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Imports table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS imports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        month TEXT NOT NULL,
        filename TEXT,
        report_text TEXT, -- Stores the AI generated report
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )
    """)
    # Ensure UNIQUE constraint on project_id and month if table already exists
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_project_month ON imports(project_id, month)")
    except Exception as e:
        print(f"Warning: Could not create unique index on imports table. It might already exist or there's an issue: {e}")
    
    # Keywords & Metrics table (Denormalized for performance in this MVP)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS keyword_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        import_id INTEGER NOT NULL,
        keyword TEXT NOT NULL,
        volume INTEGER,
        difficulty INTEGER,
        intent TEXT,
        cpc REAL,
        data_json TEXT, -- Stores positions and visibility for all domains as JSON
        FOREIGN KEY (import_id) REFERENCES imports (id)
    )
    """)
    
    conn.commit()
    conn.close()

def save_project(name, main_domain):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO projects (name, main_domain) VALUES (?, ?)", (name, main_domain))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor.execute("SELECT id FROM projects WHERE name = ?", (name,))
        return cursor.fetchone()[0]
    finally:
        conn.close()

def get_projects():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM projects", conn)
    conn.close()
    return df

def save_import_data(project_id, month, filename, df, domain_map):
    """
    Saves a monthly import and all its associated keyword metrics.
    df: The processed dataframe
    domain_map: The mapping of columns to domains
    """
    if df.empty:
        print("No keywords to save. Skipping import.")
        return False

    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Create Import record (Upsert logic using INDEX)
        cursor.execute("INSERT OR REPLACE INTO imports (project_id, month, filename) VALUES (?, ?, ?)", 
                       (project_id, month, filename))
        
        # Get the actual ID (SQLite REPLACE might change it)
        cursor.execute("SELECT id FROM imports WHERE project_id = ? AND month = ?", (project_id, month))
        import_id = cursor.fetchone()[0]
        
        # 2. Clear old metrics for this import
        cursor.execute("DELETE FROM keyword_metrics WHERE import_id = ?", (import_id,))
        
        # 3. Batch insert metrics
        metrics_list = []
        for _, row in df.iterrows():
            # Extract domain-specific data into a JSON
            domain_data = {}
            for domain, cols in domain_map.items():
                domain_data[domain] = {
                    'pos': row[cols['position']] if pd.notnull(row.get(cols.get('position'))) else None,
                    'vis': row[cols['visibility']] if pd.notnull(row.get(cols.get('visibility'))) else 0,
                    'clics': row.get(f'clics_{domain}', 0),
                    'media_value': row.get(f'media_value_{domain}', 0)
                }
            
            metrics_list.append((
                import_id,
                str(row['keyword']),
                int(row['volume']) if pd.notnull(row['volume']) else 0,
                int(row['difficulty']) if pd.notnull(row['difficulty']) else 0,
                str(row.get('intent', 'N/D')),
                float(row['cpc']) if pd.notnull(row['cpc']) else 0.0,
                json.dumps(domain_data)
            ))
        
        cursor.executemany("""
            INSERT INTO keyword_metrics (import_id, keyword, volume, difficulty, intent, cpc, data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, metrics_list)
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_report_text(import_id, text):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE imports SET report_text = ? WHERE id = ?", (text, import_id))
    conn.commit()
    conn.close()

def load_import_data(import_id):
    """Loads metrics for a specific import and reconstructs the dataframe"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM keyword_metrics WHERE import_id = ?", (import_id,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return pd.DataFrame(), {}
    
    data = []
    domain_map = {} # We'll reconstruction the basic structure
    
    for r in rows:
        item = {
            'keyword': r['keyword'],
            'volume': r['volume'],
            'difficulty': r['difficulty'],
            'intent': r['intent'],
            'cpc': r['cpc']
        }
        # Reconstruct domain columns
        domain_data = json.loads(r['data_json'])
        for domain, vals in domain_data.items():
            pos_col = f"Posición [{domain}]"
            vis_col = f"Visibilidad [{domain}]"
            item[pos_col] = vals['pos']
            item[vis_col] = vals['vis']
            item[f"clics_{domain}"] = vals.get('clics', 0)
            item[f"media_value_{domain}"] = vals.get('media_value', 0)
            
            if domain not in domain_map:
                domain_map[domain] = {'position': pos_col, 'visibility': vis_col}
        
        data.append(item)
    
    df = pd.DataFrame(data)
    # Add is_branded flag
    df['is_branded'] = df.apply(lambda x: any(d.split('.')[0].lower() in x['keyword'].lower() for d in domain_map.keys()), axis=1)
    
    return df, domain_map

def get_project_imports(project_id):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM imports WHERE project_id = ? ORDER BY month DESC", conn, params=(project_id,))
    conn.close()
    return df
