import streamlit as st
import pandas as pd
import google.generativeai as genai
import etl
import database
import intent_rules
import plotly.express as px
from datetime import datetime

# Initialize Database
database.init_db()

# Configuration
st.set_page_config(
    page_title="SEO Executive Dashboard",
    page_icon="🚀",
    layout="wide"
)

# ============================================
# PRO CONSTANTS - Naming & Formatting
# ============================================
KPI_LABELS = {
    'sov': 'Cuota de Visibilidad (SoV)',
    'traffic': 'Tráfico Estimado',
    'value': 'Valor Equivalente (Ads)',
    'opportunities': 'Oportunidades de Impacto'
}

KPI_TOOLTIPS = {
    'sov': '% de visibilidad frente a competidores en este conjunto de keywords',
    'traffic': 'Estimación: Volumen × CTR(posición)',
    'value': 'Estimación: Tráfico estimado × CPC',
    'opportunities': 'Keywords en pos 4-10 con alto potencial de subir a Top3'
}

# Tooltips para columnas de tablas
COLUMN_HELP = {
    # Oportunidades
    'Palabra Clave': 'Término de búsqueda que los usuarios escriben en Google',
    'Pos. Actual': 'Posición actual de tu sitio en Google para esta keyword (1-100)',
    'Búsquedas/mes': 'Número estimado de búsquedas mensuales de esta keyword',
    'Dificultad': 'Dificultad SEO normalizada (0-100). Más alto = más difícil posicionar. Valores >100 se ajustan automáticamente',
    'Intención': 'Tipo de búsqueda. (V) = Validada manualmente, (S) = Sugerida por reglas heurísticas.',
    'CPC': 'Coste Por Clic en Google Ads. Indica valor comercial de la keyword',
    'Uplift Tráfico (Top3)': 'Tráfico adicional estimado si esta keyword sube a Top 3 (posiciones 1-3)',
    'Uplift Valor (€)': 'Valor económico del tráfico adicional (Uplift × CPC). Lo que ahorrarías en publicidad',
    'Score': 'Puntuación de prioridad (0-100). Combina potencial de tráfico, volumen, valor y dificultad. Más alto = mayor prioridad',
    
    # Competencia
    'Competidor': 'Dominio competidor detectado en el análisis',
    'Puntuación de Visibilidad': 'Métrica agregada de visibilidad del dominio',
    'Cuota de Mercado (%)': '% de visibilidad total que captura este dominio frente al total del mercado',
    
    # Inteligencia Avanzada
    'Búsquedas': 'Volumen de búsquedas mensuales',
    'Ahorro/mes': 'Valor mensual estimado del tráfico orgánico (lo que costaría en Google Ads)',
    'Tipo': 'Clasificación de la keyword: Marca (incluye nombre de tu empresa) o Genérica (búsqueda general)',
    
    # Global/Histórico
    'Mes': 'Periodo de análisis (YYYY-MM)',
    'SoV (%)': 'Cuota de Visibilidad en ese mes',
    'Tráfico Est.': 'Tráfico estimado total del mes',
    'Valor Est. (€)': 'Valor equivalente en publicidad del tráfico orgánico'
}

def format_currency(value, currency='EUR'):
    """Formatea valores monetarios según configuración del proyecto"""
    if currency == 'EUR':
        # Formato europeo: 1.234,56 €
        formatted = f"{value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"{formatted} €"
    else:
        # Formato americano: $1,234.56
        return f"${value:,.2f}"

def format_number(value):
    """Formatea números grandes con separadores europeos"""
    return f"{value:,.0f}".replace(',', '.')

def render_data_quality_panel(df, domain_map):
    """Muestra panel de calidad de datos"""
    cpc_coverage = (df['cpc'] > 0).sum() / len(df) * 100 if len(df) > 0 else 0
    
    # Calculate validated intent percentage
    num_validated = (df['origin_intent'] == 'Validada').sum() if 'origin_intent' in df.columns else 0
    intent_valid_pct = (num_validated / len(df) * 100) if len(df) > 0 else 0
    
    num_competitors = len(domain_map)
    
    st.info(f"📊 **Calidad de datos**: CPC {cpc_coverage:.0f}% | Intent Validada {intent_valid_pct:.0f}% | Competidores {num_competitors} dominios")

def render_intent_validation_module(df):
    """Módulo para validar manualmente la intención de búsqueda"""
    st.markdown("### 📝 Validar Intención (Enriquecimiento)")
    st.caption("Selecciona keywords para validar su intención. Los cambios persistirán entre meses.")
    
    # Filter for suggested ones with high score to focus on what matters
    if 'Score' in df.columns:
        df_to_validate = df[df['origin_intent'] == 'Sugerida'].sort_values('Score', ascending=False).head(20)
    else:
        df_to_validate = df[df['origin_intent'] == 'Sugerida'].head(20)
        
    if df_to_validate.empty:
        st.success("✅ ¡Todas las keywords visibles tienen intención validada!")
        return

    # Prepare data for editor
    editor_df = df_to_validate[['keyword', 'intent']].copy()
    editor_df.columns = ['Palabra Clave', 'Intención Sugerida']
    editor_df['Nueva Intención'] = editor_df['Intención Sugerida']
    
    intent_options = ["Informativa", "Comercial", "Transaccional", "Navegacional", "Mixta/Por validar"]
    
    edited_df = st.data_editor(
        editor_df,
        column_config={
            "Palabra Clave": st.column_config.TextColumn(disabled=True),
            "Intención Sugerida": st.column_config.TextColumn(disabled=True),
            "Nueva Intención": st.column_config.SelectboxColumn(
                options=intent_options,
                required=True
            )
        },
        hide_index=True,
        use_container_width=True,
        key="intent_editor"
    )
    
    if st.button("Guardar Validaciones"):
        # Detect rows that changed
        changed_rows = edited_df[edited_df['Nueva Intención'] != edited_df['Intención Sugerida']]
        if not changed_rows.empty:
            for _, row in changed_rows.iterrows():
                kw_norm = intent_rules.normalize_keyword(row['Palabra Clave'])
                database.upsert_keyword_intent(kw_norm, row['Palabra Clave'], row['Nueva Intención'])
            st.success(f"✅ Se han validado {len(changed_rows)} keywords.")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("No has realizado ningún cambio en la columna 'Nueva Intención'.")

def render_help_section():
    """Renderiza sección de ayuda con glosario de términos"""
    with st.expander("❓ Glosario de Términos SEO"):
        st.markdown("""
        ### 📖 Guía Rápida de Métricas
        
        **Cuota de Visibilidad (SoV)**  
        Porcentaje de visibilidad que tu sitio tiene frente a la competencia. Si tienes 30% y tu competidor 70%, él domina el mercado.
        
        **Tráfico Estimado**  
        Número de visitantes que recibes por búsquedas orgánicas. Se calcula multiplicando el volumen de búsquedas por la tasa de clics según tu posición.
        
        **Valor Equivalente (Ads)**  
        Lo que te costaría conseguir ese mismo tráfico pagando en Google Ads. Es el "ahorro" que te genera el SEO.
        
        **Opportunity Score**  
        Puntuación que combina: ¿Cuánto tráfico puedo ganar? + ¿Qué tan valiosa es la keyword? + ¿Qué tan difícil es mejorar?
        
        **Uplift**  
        Ganancia potencial. "Uplift Tráfico" = visitantes adicionales si subes a Top 3. "Uplift Valor" = valor económico de esos visitantes.
        
        **HHI (Índice de Concentración)**  
        Mide si el mercado está dominado por 1-2 jugadores o es competitivo. Valores altos = mercado concentrado.
        
        **Intención de Búsqueda**  
        - **Informativa**: Usuario busca aprender (ej: "qué es SEO")
        - **Transaccional**: Usuario quiere comprar (ej: "comprar zapatos online")
        - **Navegacional**: Usuario busca una marca específica (ej: "Nike tienda")
        
        **Dificultad (KD)**  
        Qué tan difícil es posicionar para esa keyword (0-100). Más alto = más competencia y esfuerzo necesario.
        """)

# ============================================
# AI Configuration
# ============================================
google_api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    google_api_key = str(st.secrets["GOOGLE_API_KEY"])
elif "general" in st.secrets and "GOOGLE_API_KEY" in st.secrets["general"]:
    google_api_key = str(st.secrets["general"]["GOOGLE_API_KEY"])

if google_api_key:
    google_api_key = google_api_key.strip().strip('"').strip("'")
    genai.configure(api_key=google_api_key)
    st.session_state["api_key_configured"] = True
else:
    st.session_state["api_key_configured"] = False

# Helper for AI Report
def get_ai_analysis(import_id, summary_stats, opportunities_sample, analysis_month):
    """Generates or retrieves AI report from DB"""
    if not st.session_state.get("api_key_configured"):
        return "⚠️ Configura una API Key válida para habilitar el reporte de IA."
    
    try:
        # Try both preview and stable models as fallback
        models = ['gemini-2.0-flash-exp', 'gemini-1.5-flash']
        selected_model = None
        
        # Check available models via diagnostic
        try:
            available = [m.name for m in genai.list_models()]
            for m in models:
                if any(m in a for a in available):
                    selected_model = m
                    break
        except:
            selected_model = 'gemini-1.5-flash' # Default fallback
            
        model = genai.GenerativeModel(selected_model or 'gemini-1.5-flash')
        
        prompt = f"""
        Actúa como un Consultor SEO Senior. Analiza los siguientes datos de un sitio web para el PERIODO EXCLUSIVO de {analysis_month} y genera un reporte ejecutivo en Español.
        
        ## REGLA DE ORO DE LA FECHA
        El periodo de análisis es: {analysis_month}
        **IMPORTANTE**: NO inventes fechas. NO uses la fecha de hoy (ignore system date). 
        El reporte DEBE comenzar con: # Informe Ejecutivo SEO - {analysis_month}
        
        ## Datos del Proyecto ({analysis_month})
        {summary_stats}
        
        ## Muestra de Oportunidades
        {opportunities_sample}
        
        ## Instrucciones de Estructura
        1. Resumen Ejecutivo: Estado actual y salud del proyecto en {analysis_month}.
        2. Análisis de Competencia: Quien domina el mercado.
        3. Acciones Recomendadas: 3 balas con las acciones más críticas.
        
        Sé breve, directo y profesional. Usa formato Markdown.
        """
        
        with st.spinner('🤖 Generando análisis estratégico...'):
            response = model.generate_content(prompt)
            report_text = response.text
            # Save to DB
            database.update_report_text(import_id, report_text)
            return report_text
    except Exception as e:
        return f"Error en IA: {str(e)}"

def get_global_ai_analysis(project_id, history_stats_str):
    """Genera un análisis histórico de tendencias usando Gemini Pro"""
    if not st.session_state.get("api_key_configured"):
        return "⚠️ Configura una API Key válida para habilitar el análisis global de IA."
    
    # Simple caching in session state by project
    cache_key = f"global_report_{project_id}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    try:
        models = ['gemini-2.0-flash-exp', 'gemini-1.5-flash']
        selected_model = 'gemini-1.5-flash'
        try:
            available = [m.name for m in genai.list_models()]
            for m in models:
                if any(m in a for a in available):
                    selected_model = m
                    break
        except: pass
            
        model = genai.GenerativeModel(selected_model)
        
        prompt = f"""
        Actúa como un Consultor SEO Senior. Analiza la EVOLUCIÓN HISTÓRICA del proyecto SEO y ayuda al cliente a entender el valor generado.
        
        ## Datos Históricos (Métricas por Mes)
        {history_stats_str}
        
        ## Instrucciones:
        1. Contexto Estratégico: Resume la tendencia general (%) y si hay crecimiento sostenido.
        2. Hitos de Valor: Destaca el mes con mayor visibilidad o tráfico.
        3. Recomendación Forward-looking: 1 consejo para el próximo trimestre.
        
        Sé muy directo, enfocado a negocio. Usa Markdown elegante.
        """
        
        response = model.generate_content(prompt)
        report_text = response.text
        
        st.session_state[cache_key] = report_text
        return report_text
    except Exception as e:
        return f"❌ Error en análisis global: {str(e)}"

# --- SIDEBAR & NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/270/270798.png", width=50)
    st.title("SEO Intelligence")
    
    # Check for Shared View via URL Params
    params = st.query_params
    shared_import_id = params.get("import_id")
    
    if shared_import_id:
        st.info("🔗 Vista de Compartida (Lectura)")
        mode = "shared"
        current_import_id = int(shared_import_id)
        current_view = "monthly"
    else:
        st.markdown("### Gestión de Proyectos")
        mode = "admin"
        
        # Project Selection
        projects_df = database.get_projects()
        if projects_df.empty:
            st.warning("No hay proyectos. Crea uno nuevo:")
            new_p_name = st.text_input("Nombre del Proyecto (ej. Mi Cliente)")
            new_p_domain = st.text_input("Dominio Principal (ej. dominio.com)")
            if st.button("Crear Proyecto"):
                if new_p_name and new_p_domain:
                    database.save_project(new_p_name, new_p_domain)
                    st.rerun()
            st.stop()
        
        selected_p_row = st.selectbox("Seleccionar Proyecto", projects_df.to_dict('records'), format_func=lambda x: x['name'])
        project_id = selected_p_row['id']
        main_domain = selected_p_row['main_domain']
        
        st.markdown("---")
        
        # Import Selection
        imports_df = database.get_project_imports(project_id)
        if not imports_df.empty:
            # Convert to list for stable indexing
            import_list = imports_df.to_dict('records')
            options = ["📊 Resumen Global"] + [f"📅 {row['month']} ({row['filename']})" for row in import_list]
            selected_option = st.selectbox("Vista de Datos", options)
            
            if selected_option == "📊 Resumen Global":
                current_view = "global"
                current_import_id = None
                stored_report = None
            else:
                current_view = "monthly"
                # Use index to find the correct ID (safe even with duplicate months)
                idx = options.index(selected_option) - 1
                selected_import_row = import_list[idx]
                current_import_id = selected_import_row['id']
                stored_report = selected_import_row['report_text']
                analysis_month = selected_import_row['month']
        else:
            st.info("No hay datos cargados para este proyecto.")
            current_view = "empty"
            current_import_id = None
            stored_report = None
            
        # Upload Section
        st.markdown("### 🔝 Subir Nuevo Mes")
        with st.expander("Subir CSV"):
            new_month = st.date_input("Mes de los datos", value=datetime.now()).strftime("%Y-%m")
            uploaded_file = st.file_uploader("CSV de Semrush/Sistrix", type=['csv'])
            if uploaded_file and st.button("Procesar y Guardar"):
                ret, err = etl.parse_csv_data(uploaded_file)
                if err:
                    st.error(err)
                else:
                    success = database.save_import_data(project_id, new_month, uploaded_file.name, ret['df'], ret['domains'])
                    if success:
                        st.success("¡Datos guardados!")
                        st.rerun()
                    else:
                        st.error("Error al guardar en BD.")

        # Shared Link
        if current_import_id:
            st.markdown("---")
            # Try to get host automatically
            share_url = f"https://seo-dashboard-3e3t22.streamlit.app/?import_id={current_import_id}"
            st.text_input("🔗 Enlace para compartir (Lectura)", share_url)
            
        st.markdown("---")
        render_help_section()

# --- MAIN DASHBOARD ---
if current_view == "global":
    st.title(f"🌍 Reporte Global: {main_domain}")
    st.markdown("Comparativa histórica de todos los datos cargados para este proyecto.")
    
    all_imports = database.get_project_imports(project_id)
    
    if all_imports.empty:
        st.info("Sube más datos mensuales para desbloquear la vista histórica.")
    else:
        history_data = []
        progress_bar = st.progress(0)
        for i, (_, imp) in enumerate(all_imports.iterrows()):
            df_month, d_map = database.load_import_data(imp['id'])
            if not df_month.empty:
                sov_df = etl.calculate_sov(df_month, d_map, main_domain)
                sov = sov_df[sov_df['domain'] == main_domain]['sov'].values[0] if not sov_df.empty else 0
                history_data.append({
                    'Mes': imp['month'],
                    'SoV': sov,
                    'Tráfico': df_month[f'clics_{main_domain}'].sum() if f'clics_{main_domain}' in df_month.columns else 0,
                    'Ahorro': df_month[f'media_value_{main_domain}'].sum() if f'media_value_{main_domain}' in df_month.columns else 0
                })
            progress_bar.progress((i + 1) / len(all_imports))
        progress_bar.empty()
        
        if history_data:
            h_df = pd.DataFrame(history_data).sort_values('Mes')
            
            # --- AI GLOBAL INSIGHTS ---
            stats_summary = h_df.to_string(index=False)
            global_insights = get_global_ai_analysis(project_id, stats_summary)
            
            st.info(global_insights, icon="🤖")
            st.markdown("---")
            
            # Overall Summary Cards (Aggregated)
            st.subheader("💡 Resumen de Valor Acumulado")
            c1, c2, c3 = st.columns(3)
            
            # Comparison metrics (First vs Last)
            first_sov = h_df['SoV'].iloc[0]
            last_sov = h_df['SoV'].iloc[-1]
            delta_sov_total = last_sov - first_sov
            
            c1.metric(
                "Visibilidad Actual", 
                f"{last_sov:.1%}", 
                delta=f"{delta_sov_total:+.1%}" if len(h_df) > 1 else None,
                help="Porcentaje de visibilidad en el último mes cargado vs el primero."
            )
            
            total_clics = h_df['Tráfico'].sum()
            c2.metric(
                "Total Tráfico Capturado", 
                format_number(total_clics),
                help="Suma total de clics estimados de todos los meses analizados."
            )
            
            total_ahorro = h_df['Ahorro'].sum()
            c3.metric(
                "Total Ahorro (Media Value)", 
                format_currency(total_ahorro),
                help="Suma total del valor económico equivalente en Google Ads (€)."
            )
            
            # Trend Chart
            st.markdown("---")
            st.markdown("### 📈 Evolución Histórica")
            
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                fig_sov = px.line(
                    h_df, 
                    x='Mes', 
                    y='SoV', 
                    title="Tendencia de Visibilidad (%)", 
                    markers=True,
                    color_discrete_sequence=['#4CAF50'],
                    labels={'SoV': 'Cuota de Visibilidad'}
                )
                fig_sov.update_xaxes(type='category')
                st.plotly_chart(fig_sov, use_container_width=True)
            
            with col_chart2:
                fig_clics = px.area(
                    h_df, 
                    x='Mes', 
                    y='Tráfico', 
                    title="Evolución de Tráfico (Visitantes)", 
                    markers=True,
                    color_discrete_sequence=['#2196F3'],
                    labels={'Tráfico': 'Clics Estimados'}
                )
                fig_clics.update_xaxes(type='category')
                st.plotly_chart(fig_clics, use_container_width=True)
            
            st.subheader("📋 Detalle Histórico")
            st.dataframe(h_df.rename(columns={
                'Mes': 'Periodo',
                'SoV': '% Visibilidad',
                'Tráfico': 'Tráfico Est.',
                'Ahorro': 'Valor Media (€)'
            }), use_container_width=True, hide_index=True)
            
            # Export all history
            csv_history = h_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Histórico Completo (CSV)",
                data=csv_history,
                file_name=f"historico_seo_{main_domain}.csv",
                mime="text/csv"
            )

            # --- ZONA DE GESTIÓN GLOBAL ---
            st.markdown("---")
            with st.expander("⚙️ Zona de Gestión Global"):
                st.warning("⚠️ Acciones delicadas: usa con precaución.")
                global_mngt_pwd = st.text_input("🔑 Contraseña de Gestión (Global)", type="password", key="global_pwd_input")
                
                if global_mngt_pwd == "Webyseo@":
                    if st.button("🔄 Regenerar Análisis Global", help="Borra el análisis histórico actual y genera uno nuevo."):
                        cache_key = f"global_report_{project_id}"
                        if cache_key in st.session_state:
                            del st.session_state[cache_key]
                        st.success("Análisis histórico borrado. Refresca la página para generar uno nuevo.")
                        st.rerun()
                elif global_mngt_pwd:
                    st.error("❌ Contraseña incorrecta.")
                else:
                    st.info("💡 Introduce la contraseña para habilitar la regeneración del análisis global.")
        else:
            st.info("Sube datos para ver el reporte global.")

elif current_view == "monthly" and current_import_id:
    df, domain_map = database.load_import_data(current_import_id)
    analysis_month = selected_import_row['month'] if 'selected_import_row' in locals() else "Análisis Reciente"
    
    if df.empty:
        st.error(f"⚠️ No hay palabras clave guardadas para {analysis_month}.")
        st.info("Esto puede ocurrir si la subida anterior falló o el archivo estaba vacío. Por favor, intenta subir el CSV de nuevo para este mes en la barra lateral.")
        if st.button("Eliminar este registro vacío"):
            conn = database.get_connection()
            conn.execute("DELETE FROM imports WHERE id = ?", (current_import_id,))
            conn.commit()
            conn.close()
            st.rerun()
    else:
        # Filter for selected project domain
        selected_domain = main_domain
        
        # Metrics Calculation
        sov_df = etl.calculate_sov(df, domain_map, selected_domain)
        main_sov = sov_df[sov_df['domain'] == selected_domain]['sov'].values[0] if not sov_df.empty else 0
        opportunities = etl.get_striking_distance(df, domain_map, selected_domain)
        
        # --- PHASE 4: INTENT ENRICHMENT ---
        validated_intents = database.get_validated_intents()
        
        def enrich_row(row):
            kw_norm = intent_rules.normalize_keyword(row['keyword'])
            # Priority: 1. Validated, 2. Suggested
            if kw_norm in validated_intents:
                return validated_intents[kw_norm], "Validada"
            else:
                suggestion = intent_rules.infer_intent(row['keyword'])
                return suggestion['intent_suggested'], "Sugerida"

        intent_results = df.apply(enrich_row, axis=1)
        df['intent'] = [r[0] for r in intent_results]
        df['origin_intent'] = [r[1] for r in intent_results]
        
        # Also update opportunities DF (it's a subset/copy)
        if not opportunities.empty:
            opp_intents = opportunities.apply(enrich_row, axis=1)
            opportunities['intent'] = [r[0] for r in opp_intents]
            opportunities['origin_intent'] = [r[1] for r in opp_intents]

        pos_col = domain_map.get(selected_domain, {}).get('position')
        top_10 = len(df[df[pos_col] <= 10]) if pos_col else 0
        
        # Advanced Metrics Totals
        total_clics = df[f'clics_{selected_domain}'].sum() if f'clics_{selected_domain}' in df.columns else 0
        total_media_value = df[f'media_value_{selected_domain}'].sum() if f'media_value_{selected_domain}' in df.columns else 0

        # AI Report Logic
        report_display = stored_report
        if not report_display:
            stats_str = f"Dom: {selected_domain}, SoV: {main_sov:.2f}%, Top 10: {top_10}, Clics Est: {total_clics:.0f}, Media Value: {total_media_value:.0f}€"
            opps_str = opportunities.head(10).to_string(index=False)
            report_display = get_ai_analysis(current_import_id, stats_str, opps_str, analysis_month)

        # --- MoM TREND CALCULATION ---
        prev_month_id = None
        imports_list = database.get_project_imports(project_id)
        current_idx = imports_list[imports_list['id'] == current_import_id].index[0]
        if current_idx + 1 < len(imports_list):
            prev_month_id = imports_list.iloc[current_idx + 1]['id']
        
        delta_sov = None
        delta_clics = None
        
        if prev_month_id:
            df_prev, domain_map_prev = database.load_import_data(prev_month_id)
            if not df_prev.empty:
                # Calculate previous SoV
                sov_df_prev = etl.calculate_sov(df_prev, domain_map_prev, selected_domain)
                prev_sov = sov_df_prev[sov_df_prev['domain'] == selected_domain]['sov'].values[0] if not sov_df_prev.empty else 0
                delta_sov = main_sov - prev_sov
                
                # Calculate previous Clics
                prev_clics = df_prev[f'clics_{selected_domain}'].sum() if f'clics_{selected_domain}' in df_prev.columns else 0
                delta_clics = total_clics - prev_clics

        st.title(f"Dashboard SEO: {selected_domain}")
        st.caption(f"📅 Mes de Análisis Seleccionado: {analysis_month}")
        
        # Panel de Calidad de Datos
        render_data_quality_panel(df, domain_map)
        
        t1, t2, t3, t4 = st.tabs(["📊 Resumen Ejecutivo", "⚔️ Competencia", "🚀 Oportunidades", "🧠 Inteligencia Avanzada"])
        
        with t1:
            st.subheader("💡 Análisis Estratégico")
            st.info(report_display, icon="🤖")
            
            st.markdown("### KPIs del Mes")
            c1, c2, c3, c4 = st.columns(4)
            
            # KPI 1: SoV
            c1.metric(
                KPI_LABELS['sov'],
                f"{main_sov:.1f}%",
                delta=f"{delta_sov:+.1f}%" if delta_sov is not None else None,
                help=KPI_TOOLTIPS['sov']
            )
            
            # KPI 2: Tráfico Estimado (con badge)
            with c2:
                st.metric(
                    KPI_LABELS['traffic'],
                    format_number(total_clics),
                    delta=f"{delta_clics:+,.0f}".replace(',', '.') if delta_clics is not None else None,
                    help=KPI_TOOLTIPS['traffic']
                )
                st.markdown('<span style="background:#FFA500;padding:2px 6px;border-radius:4px;font-size:10px;color:white;">ESTIMADO</span>', unsafe_allow_html=True)
            
            # KPI 3: Valor Equivalente (con badge)
            with c3:
                st.metric(
                    KPI_LABELS['value'],
                    format_currency(total_media_value),
                    help=KPI_TOOLTIPS['value']
                )
                st.markdown('<span style="background:#FFA500;padding:2px 6px;border-radius:4px;font-size:10px;color:white;">ESTIMADO</span>', unsafe_allow_html=True)
            
            # KPI 4: Oportunidades
            c4.metric(
                KPI_LABELS['opportunities'],
                len(opportunities),
                help=KPI_TOOLTIPS['opportunities']
            )
            
            # Ranking Chart
            st.markdown("---")
            if pos_col:
                def get_bucket(p):
                    if p <= 3: return "Top 3"
                    if p <= 10: return "4-10"
                    if p <= 20: return "11-20"
                    return "20+"
                df['bucket'] = df[pos_col].apply(get_bucket)
                v_counts = df['bucket'].value_counts().reset_index()
                v_counts.columns = ['Rango', 'Keywords']
                
                # Order buckets logically
                order = ["Top 3", "4-10", "11-20", "20+"]
                v_counts['Rango'] = pd.Categorical(v_counts['Rango'], categories=order, ordered=True)
                v_counts = v_counts.sort_values('Rango')

                fig = px.bar(
                    v_counts, 
                    x='Rango', 
                    y='Keywords', 
                    title="Distribución de Rankings",
                    color='Rango',
                    color_discrete_map={
                        "Top 3": "#2E7D32", 
                        "4-10": "#4CAF50", 
                        "11-20": "#FFC107", 
                        "20+": "#F44336"
                    }
                )
                st.plotly_chart(fig, use_container_width=True)

            # --- ZONA DE GESTIÓN ---
            st.markdown("---")
            with st.expander("⚙️ Zona de Gestión de Datos"):
                st.warning("⚠️ Acciones delicadas: usa con precaución.")
                # Password protection for sensitive actions
                mngt_pwd = st.text_input("🔑 Contraseña de Gestión", type="password", help="Introduce la contraseña para habilitar acciones críticas.")
                
                col1, col2 = st.columns(2)
                
                if mngt_pwd == "Webyseo@":
                    if col1.button("🔄 Regenerar Análisis IA", help="Borra el reporte actual y genera uno nuevo con la fecha corregida."):
                        database.update_report_text(current_import_id, None)
                        st.success("Reporte borrado con éxito. Al refrescar, la IA generará un nuevo análisis con la fecha del CSV.")
                        st.rerun()
                    
                    if col2.button("🗑️ Borrar este Mes", help="Elimina permanentemente los datos de este mes para que puedas volver a subirlos."):
                        conn = database.get_connection()
                        conn.execute("DELETE FROM imports WHERE id = ?", (current_import_id,))
                        conn.commit()
                        conn.close()
                        st.warning(f"Mes {analysis_month} eliminado del sistema.")
                        st.rerun()
                elif mngt_pwd:
                    st.error("❌ Contraseña incorrecta.")
                else:
                    st.info("💡 Introduce la contraseña para habilitar los botones de gestión.")

        with t2:
            st.subheader("📊 Comparativa de Mercado")
            
            # Calculate HHI with error handling
            try:
                if not sov_df.empty and 'sov' in sov_df.columns:
                    hhi_value, hhi_interpretation, hhi_color = etl.calculate_hhi(sov_df)
                    
                    # Display HHI
                    col_hhi1, col_hhi2 = st.columns([1, 2])
                    with col_hhi1:
                        st.metric("Índice HHI", f"{hhi_value:.0f}", help="Índice Herfindahl-Hirschman: mide concentración del mercado (0-10000)")
                    with col_hhi2:
                        st.markdown(f"**{hhi_interpretation}**")
                    
                    st.markdown("---")
                else:
                    st.warning("No hay datos de competencia suficientes para calcular HHI")
            except Exception as e:
                st.error(f"Error calculando HHI: {str(e)}")
            
            # Column descriptions
            with st.expander("ℹ️ ¿Qué significan estas métricas?"):
                st.markdown(f"""
                📊 **Cuota de Mercado (%)**: {COLUMN_HELP.get('Cuota de Mercado (%)', '')}  
                📈 **Puntuación de Visibilidad**: {COLUMN_HELP.get('Puntuación de Visibilidad', '')}  
                🏢 **Competidor**: {COLUMN_HELP.get('Competidor', '')}  
                📉 **HHI**: {COLUMN_HELP.get('HHI (Índice de Concentración)', 'Mide si el mercado está dominado por 1-2 jugadores o es competitivo')}
                """)
            
            # Bar chart Top 10
            st.markdown("### Top 10 Competidores por Cuota de Visibilidad")
            top_10 = sov_df.head(10)
            fig_bar = px.bar(
                top_10,
                x='sov',
                y='domain',
                orientation='h',
                title="",
                labels={'sov': 'Cuota de Visibilidad (%)', 'domain': 'Dominio'},
                color='sov',
                color_continuous_scale='Blues'
            )
            fig_bar.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Table with data
            st.markdown("### Datos Detallados")
            sov_display = sov_df.rename(columns={
                'domain': 'Competidor',
                'visibility_score': 'Puntuación de Visibilidad',
                'sov': 'Cuota de Mercado (%)'
            })
            st.dataframe(sov_display, use_container_width=True, hide_index=True)
            
            # Pie chart (collapsible)
            with st.expander("📊 Ver Gráfico Circular"):
                fig_pie = px.pie(
                    sov_df, 
                    values='sov', 
                    names='domain', 
                    title="Reparto de Cuota de Mercado (Visibilidad)",
                    labels={'domain': 'Dominio', 'sov': 'Cuota (%)'}
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        with t3:
            st.subheader("🎯 Oportunidades de Crecimiento Rápido")
            st.markdown("Keywords priorizadas por **Opportunity Score**: combinación de potencial de tráfico, volumen y dificultad.")
            
            # Column descriptions
            with st.expander("ℹ️ ¿Qué significa cada columna?"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    **{COLUMN_HELP.get('Palabra Clave', '')}**  
                    📍 **Pos. Actual**: {COLUMN_HELP.get('Pos. Actual', '')}  
                    📊 **Búsquedas/mes**: {COLUMN_HELP.get('Búsquedas/mes', '')}  
                    ⚡ **Dificultad**: {COLUMN_HELP.get('Dificultad', '')}  
                    🎯 **Intención**: {COLUMN_HELP.get('Intención', '')}
                    """)
                with col2:
                    st.markdown(f"""
                    💰 **CPC**: {COLUMN_HELP.get('CPC', '')}  
                    📈 **Uplift Tráfico**: {COLUMN_HELP.get('Uplift Tráfico (Top3)', '')}  
                    💎 **Uplift Valor**: {COLUMN_HELP.get('Uplift Valor (€)', '')}  
                    🏆 **Score**: {COLUMN_HELP.get('Score', '')}
                    """)
            
            if not opportunities.empty:
                # Rename columns for display
                rename_map = {
                    'keyword': 'Palabra Clave',
                    'volume': 'Búsquedas/mes',
                    'difficulty': 'Dificultad',
                    'intent': 'Intención',
                    'cpc': 'CPC',
                    'uplift_trafico': 'Uplift Tráfico (Top3)',
                    'uplift_valor': 'Uplift Valor (€)',
                    'opportunity_score': 'Score'
                }
                
                # Add position column if exists
                if pos_col in opportunities.columns:
                    rename_map[pos_col] = 'Pos. Actual'
                
                opps_display = opportunities.copy()
                
                # Format currency columns
                if 'uplift_valor' in opps_display.columns:
                    opps_display['uplift_valor'] = opps_display['uplift_valor'].apply(lambda x: f"{x:,.0f} €".replace(',', '.'))
                if 'cpc' in opps_display.columns:
                    opps_display['cpc'] = opps_display['cpc'].apply(lambda x: f"{x:.2f} €" if x > 0 else "N/D")
                
                # Format number columns
                if 'uplift_trafico' in opps_display.columns:
                    opps_display['uplift_trafico'] = opps_display['uplift_trafico'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
                
                # Add (V) or (S) label to intent for clarity
                opps_display['intent'] = opps_display.apply(lambda x: f"{x['intent']} (V)" if x['origin_intent'] == 'Validada' else f"{x['intent']} (S)", axis=1)
                
                opps_display = opps_display.rename(columns=rename_map)
                
                # Ensure only display columns are shown
                final_cols = ['Palabra Clave', 'Pos. Actual', 'Búsquedas/mes', 'Dificultad', 'Intención', 'CPC', 'Uplift Tráfico (Top3)', 'Uplift Valor (€)', 'Score']
                opps_display = opps_display[[c for c in final_cols if c in opps_display.columns]]
                
                st.dataframe(opps_display, use_container_width=True, hide_index=True)
                
                # Export button
                csv_data = opportunities.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Exportar Oportunidades (CSV)",
                    data=csv_data,
                    file_name=f"oportunidades_{selected_domain}_{analysis_month}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No hay keywords en posición 4-10 para este mes.")

            # --- VALIDATION MODULE ---
            st.markdown("---")
            with st.expander("📝 Gestionar Calidad: Validar Intención"):
                render_intent_validation_module(df)

        with t4:
            st.subheader("🧠 Inteligencia de Valor y Marca")
            
            # Help section
            with st.expander("ℹ️ ¿Qué muestran estas métricas?"):
                st.markdown(f"""
                💰 **Ahorro Estimado**: {COLUMN_HELP.get('Ahorro/mes', '')}  
                🏷️ **Marca vs Genérico**: {COLUMN_HELP.get('Tipo', '')}  
                📊 **Búsquedas**: {COLUMN_HELP.get('Búsquedas', '')}
                
                **¿Por qué es importante?**  
                - Keywords de **Marca** indican reconocimiento (la gente te busca por nombre)
                - Keywords **Genéricas** traen nuevos clientes que no te conocían
                - El **Ahorro** muestra el valor real del SEO vs. pagar por publicidad
                """)
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("#### 💰 Keywords con mayor Ahorro Estimado")
                st.caption("Palabras que te están ahorrando dinero en publicidad (Google Ads).")
                mv_df = df.sort_values(f'media_value_{selected_domain}', ascending=False).head(15).copy()
                mv_display = mv_df.rename(columns={
                    'keyword': 'Palabra Clave',
                    'volume': 'Búsquedas',
                    'cpc': 'Coste Clic (Ads)',
                    f'media_value_{selected_domain}': 'Ahorro Estimado'
                })
                st.dataframe(mv_display[['Palabra Clave', 'Búsquedas', 'Coste Clic (Ads)', 'Ahorro Estimado']], use_container_width=True)
            
            with col_b:
                st.markdown("#### 🏷️ Tráfico: Marca vs. Genérico")
                st.caption("Diferencia entre personas que ya te conocen (Marca) vs. nuevos clientes (Genérico).")
                
                brand_stats = df.groupby('is_branded').agg({f'clics_{selected_domain}': 'sum', 'keyword': 'count'}).reset_index()
                brand_stats['is_branded'] = brand_stats['is_branded'].map({True: 'Búsquedas de Marca', False: 'Búsquedas Genéricas'})
                
                fig_brand = px.bar(
                    brand_stats, 
                    x='is_branded', 
                    y=f'clics_{selected_domain}', 
                    title="Distribución de Tráfico Mensual",
                    labels={'is_branded': 'Tipo de Palabra Clave', f'clics_{selected_domain}': 'Clics Estimados'},
                    color='is_branded',
                    color_discrete_sequence=['#1E88E5', '#D81B60']
                )
                st.plotly_chart(fig_brand, use_container_width=True)

else:
    st.info("👋 Bienvenido. Selecciona un proyecto y un mes en la barra lateral para comenzar.")
    if st.session_state.get("api_key_configured"):
        st.success("✅ IA Configurada y lista.")
    else:
        st.warning("⚠️ IA Deshabilitada (Falta API Key).")

