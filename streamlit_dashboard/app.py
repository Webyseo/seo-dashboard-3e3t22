import streamlit as st
import pandas as pd
import google.generativeai as genai
import etl
import database
import intent_rules
import utils_metrics
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
# Helper for rerun compatibility
def safe_rerun():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

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
    """
    Muestra panel de calidad de datos como SEMÁFORO operativo (P0.2).
    Returns: cpc_coverage (float) for gating economic metrics elsewhere.
    """
    cpc_coverage = (df['cpc'] > 0).sum() / len(df) * 100 if len(df) > 0 else 0
    
    # Calculate validated intent percentage
    num_validated = (df['origin_intent'] == 'Validada').sum() if 'origin_intent' in df.columns else 0
    intent_valid_pct = (num_validated / len(df) * 100) if len(df) > 0 else 0
    
    num_competitors = len(domain_map)
    
    # Semáforo logic (P0.2)
    if cpc_coverage >= 70:
        color = "#2E7D32"  # Green
        icon = "🟢"
        label = "Alta"
        warning_msg = None
    elif cpc_coverage >= 40:
        color = "#FFA000"  # Amber
        icon = "🟡"
        label = "Media"
        warning_msg = "Métricas económicas con confianza media."
    else:
        color = "#C62828"  # Red
        icon = "🔴"
        label = "Baja"
        warning_msg = "⚠️ Métricas económicas orientativas (CPC incompleto). Prioriza SoV/posición."
    
    # Render semaphore
    st.markdown(
        f'<div style="padding:10px;border-radius:8px;background:linear-gradient(135deg, {color}22, {color}11);border-left:4px solid {color};">'
        f'{icon} <b>Calidad de datos</b>: CPC <b>{cpc_coverage:.0f}%</b> ({label}) | Intent Validada {intent_valid_pct:.0f}% | Competidores {num_competitors} dominios'
        f'</div>',
        unsafe_allow_html=True
    )
    
    if warning_msg:
        st.warning(warning_msg)
    
    return cpc_coverage  # Return for gating logic

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
            safe_rerun()
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
    """Generates or retrieves AI report from DB with Marketing-First focus"""
    if not st.session_state.get("api_key_configured"):
        return "⚠️ Configura una API Key válida para habilitar el reporte de IA."
    
    try:
        # Upgrade to Gemini 3 Flash (User Request)
        # We forcefully try gemini-3-flash-preview first
        selected_model = 'gemini-3-flash-preview'

        try:
            # We still list models just in case we need to fallback, but we default to 3-flash
            available_models = [m.name for m in genai.list_models()]
            available_names = [n.replace('models/', '') for n in available_models]
            
            # If 3-flash is not explicitly in list, we STILL try it (it might be preview-hidden)
            # But if we want to be safe, we could check. 
            # Per instruction: "Force utilize gemini-3-flash-preview"
            pass 
        except Exception as e:
            print(f"Error listing models: {e}")
            
        model = genai.GenerativeModel(selected_model)
        
        prompt = f"""
        Actúa como un Director de Marketing y Estratega SEO Senior. Tu audiencia es el equipo de marketing, no técnicos SEO.
        Analiza los datos del mes: {analysis_month}.
        
        DATOS CLAVE:
        {summary_stats}
        
        TOP OPORTUNIDADES (Volumen alto, Posición 4-10):
        {opportunities_sample}
        
        Genera un informe estratégico con EXACTAMENTE esta estructura (usa Markdown):

        ## 1. Resumen Ejecutivo
        * **Qué ha pasado**: Breve resumen de la situación (visibilidad, tráfico, valor).
        * **Cambios Clave**: Qué ha mejorado o empeorado respecto al mes anterior.
        * **Impacto Real**: Traduce los datos a impacto de negocio (posibles leads/ventas).

        ## 2. Diagnóstico basado en Datos
        * **Keywords Destacadas**: Menciona 2-3 keywords que están moviendo la aguja.
        * **Quick Wins Identificados**: Oportunidades claras para atacar ya.
        * **Riesgos**: Dependencia de marca excesiva, caídas en keywords clave, etc.

        ## 3. Recomendaciones para Marketing (ACCIONABLES)
        *Divide en acciones claras:*
        * **🛡️ Acciones Prioritarias**:
            * "Crear contenido nuevo para: [TEMA/KEYWORD]"
            * "Optimizar landing page de: [URL/KEYWORD]"
        * **🚫 Acciones a Evitar**:
            * "No crear contenido sobre X porque canibaliza..."
        
        ## 4. Checklist Operativo
        * [ ] Tarea 1
        * [ ] Tarea 2
        * [ ] Tarea 3
        
        **Tono**: Directivo, estratégico, orientado a la acción. NO uses jerga técnica innecesaria. NO inventes datos.
        """
        
        with st.spinner('🧠 Analizando estrategia de marketing (Gemini 3 Flash)...'):
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
        selected_model = 'gemini-3-flash-preview'
        # We skip the list check to force the preview model
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
    st.image("assets/logo_radiofonics.png", width=120)
    st.title("SEO Intelligence")
    
    # Check for Shared View via URL Params (backward compatible)
    try:
        params = st.query_params  # Streamlit >= 1.30
    except AttributeError:
        params = st.experimental_get_query_params()  # Older versions
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
                    safe_rerun()
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
                    if not ret['domains']:
                        st.warning("⚠️ No se detectaron columnas de 'Visibilidad'. Las gráficas de cuota de mercado (SoV) estarán vacías. Verifica el formato del CSV.")
                    success = database.save_import_data(project_id, new_month, uploaded_file.name, ret['df'], ret['domains'])
                    if success:
                        st.success("¡Datos guardados!")
                        safe_rerun()
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
    n_meses_global = len(all_imports)  # P0.4: Track historical depth
    
    # P0.4: Show historical depth in global view
    if not all_imports.empty:
        last_month_global = all_imports.iloc[0]['month']
        st.caption(f"📊 **Histórico**: {n_meses_global} meses | Último mes cargado: {last_month_global}")
    
    if all_imports.empty:
        st.info("Sube más datos mensuales para desbloquear la vista histórica.")
    else:
        history_data = []
        progress_bar = st.progress(0)
        for i, (_, imp) in enumerate(all_imports.iterrows()):
            df_month, d_map = database.load_import_data(imp['id'])
            if not df_month.empty:
                sov_df = etl.calculate_sov(df_month, d_map, main_domain)
                sov_rows = sov_df[sov_df['domain'] == main_domain]
                sov = sov_rows['sov'].values[0] if not sov_rows.empty else 0
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
            
            # --- VISIBILIDAD HARDENING (Phase 5) ---
            vis_stats = utils_metrics.get_visibility_stats(h_df['SoV'])
            
            # Sync the dataframe with corrected values (for the chart)
            h_df['SoV'] = vis_stats['series']

            c1.metric(
                "Visibilidad Actual", 
                vis_stats['formatted_value'], 
                delta=vis_stats['formatted_delta'],
                help="Porcentaje de visibilidad en el último mes cargado vs el primero. El delta se expresa en puntos porcentuales (pp)."
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
            
            # P0.4: Historical warning in trend charts
            if n_meses_global < 3:
                st.warning(f"⚠️ **Tendencia preliminar** (n={n_meses_global}). Se requieren ≥3 meses para análisis de tendencia robusto. Las conclusiones deben interpretarse con cautela.")
            
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
            }))
            
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
                        safe_rerun()
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
            safe_rerun()
    else:
        # Filter for selected project domain
        selected_domain = main_domain
        
        # Metrics Calculation
        sov_df = etl.calculate_sov(df, domain_map, selected_domain)
        sov_rows = sov_df[sov_df['domain'] == selected_domain]
        main_sov = sov_rows['sov'].values[0] if not sov_rows.empty else 0
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

        # --- MoM TREND CALCULATION + P0.1/P0.4 ENHANCEMENTS ---
        prev_month_id = None
        imports_list = database.get_project_imports(project_id)
        n_meses = len(imports_list)  # P0.4: Track historical depth
        current_idx = imports_list[imports_list['id'] == current_import_id].index[0]
        if current_idx + 1 < len(imports_list):
            prev_month_id = imports_list.iloc[current_idx + 1]['id']
        
        delta_sov = None
        delta_clics = None
        delta_top3 = None
        delta_top10 = None
        risks_count = 0  # P0.1: Keywords with significant drops
        
        # Calculate current Top3 and Top10
        top_3 = len(df[df[pos_col] <= 3]) if pos_col else 0
        top_10 = len(df[df[pos_col] <= 10]) if pos_col else 0
        
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
                
                # Calculate previous Top3/Top10
                prev_pos_col = domain_map_prev.get(selected_domain, {}).get('position')
                if prev_pos_col:
                    prev_top3 = len(df_prev[df_prev[prev_pos_col] <= 3])
                    prev_top10 = len(df_prev[df_prev[prev_pos_col] <= 10])
                    delta_top3 = top_3 - prev_top3
                    delta_top10 = top_10 - prev_top10
                    
                    # P0.1: Calculate Risks (keywords that dropped >=2 positions or left Top10)
                    # Merge on keyword to compare positions
                    merged = df.merge(
                        df_prev[['keyword', prev_pos_col]].rename(columns={prev_pos_col: 'prev_pos'}),
                        on='keyword',
                        how='left'
                    )
                    # Risk: dropped >=2 positions OR was in Top10 and now isn't
                    risks_mask = (
                        ((merged[pos_col] - merged['prev_pos']) >= 2) |  # Dropped 2+ positions
                        ((merged['prev_pos'] <= 10) & (merged[pos_col] > 10))  # Left Top10
                    )
                    risks_count = risks_mask.sum()

        st.title(f"Dashboard SEO: {selected_domain}")
        
        # P0.4: Show historical depth in caption
        last_month = imports_list.iloc[0]['month'] if not imports_list.empty else "N/A"
        st.caption(f"📅 Mes de Análisis: **{analysis_month}** | 📊 Histórico: **{n_meses} meses** | Último cargado: {last_month}")
        
        # P0.4: Historical warning
        if n_meses < 3:
            st.warning(f"⚠️ **Tendencia preliminar** (n={n_meses}). Se requieren ≥3 meses para análisis de tendencia robusto.")
        
        # Panel de Calidad de Datos (now returns CPC coverage for gating)
        cpc_coverage = render_data_quality_panel(df, domain_map)
        
        t1, t2, t3, t4, t5 = st.tabs(["📊 Resumen Ejecutivo", "⚔️ Competencia", "🚀 Oportunidades", "🧠 Inteligencia Avanzada", "🔎 Deep Dive"])
        
        with t1:
            st.subheader("💡 Análisis Estratégico")
            st.info(report_display, icon="🤖")
            
            # ==========================================
            # P0.1: HOME "ESTADO DEL MES" (5 KPIs)
            # ==========================================
            st.markdown("### 📈 Estado del Mes")
            c1, c2, c3, c4, c5 = st.columns(5)
            
            # Determine if deltas should be shown (n_meses >= 2)
            show_deltas = n_meses >= 2
            
            # KPI 1: SoV
            c1.metric(
                KPI_LABELS['sov'],
                f"{main_sov:.1f}%",
                delta=f"{delta_sov:+.1f} pp" if show_deltas and delta_sov is not None else None,
                help=KPI_TOOLTIPS['sov']
            )
            
            # KPI 2: Keywords Top3 / Top10
            with c2:
                st.metric(
                    "Top 3 / Top 10",
                    f"{top_3} / {top_10}",
                    delta=f"{delta_top3:+d} / {delta_top10:+d}" if show_deltas and delta_top3 is not None else None,
                    help="Número de keywords en posiciones 1-3 y 1-10"
                )
            
            # KPI 3: Tráfico Estimado (siempre marcado)
            with c3:
                st.metric(
                    KPI_LABELS['traffic'],
                    format_number(total_clics),
                    delta=f"{delta_clics:+,.0f}".replace(',', '.') if show_deltas and delta_clics is not None else None,
                    help=KPI_TOOLTIPS['traffic']
                )
                st.markdown('<span style="background:#FFA500;padding:2px 6px;border-radius:4px;font-size:10px;color:white;">ESTIMADO</span>', unsafe_allow_html=True)
            
            # KPI 4: Valor Equivalente (GATED by CPC coverage - P0.2)
            with c4:
                if cpc_coverage >= 40:  # Show if Yellow or Green
                    st.metric(
                        KPI_LABELS['value'],
                        format_currency(total_media_value),
                        help=KPI_TOOLTIPS['value']
                    )
                    if cpc_coverage >= 70:
                        st.markdown('<span style="background:#2E7D32;padding:2px 6px;border-radius:4px;font-size:10px;color:white;">ESTIMADO</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span style="background:#FFA000;padding:2px 6px;border-radius:4px;font-size:10px;color:white;">CONFIANZA MEDIA</span>', unsafe_allow_html=True)
                else:  # Red: Hide by default
                    st.metric(
                        KPI_LABELS['value'],
                        "—",
                        help="Oculto por CPC insuficiente (<40%)"
                    )
                    st.markdown('<span style="background:#C62828;padding:2px 6px;border-radius:4px;font-size:10px;color:white;">CPC INSUFICIENTE</span>', unsafe_allow_html=True)
            
            # KPI 5: Riesgos (P0.1)
            with c5:
                if show_deltas:
                    risk_color = "#C62828" if risks_count > 5 else ("#FFA000" if risks_count > 0 else "#2E7D32")
                    st.metric(
                        "⚠️ Riesgos",
                        risks_count,
                        help="Keywords con caída ≥2 posiciones o salida de Top10"
                    )
                    if risks_count > 0:
                        st.markdown(f'<span style="background:{risk_color};padding:2px 6px;border-radius:4px;font-size:10px;color:white;">{risks_count} en riesgo</span>', unsafe_allow_html=True)
                else:
                    st.metric(
                        "⚠️ Riesgos",
                        "—",
                        help="Requiere histórico previo para calcular"
                    )
                    st.caption("Histórico insuficiente")
            
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
                        safe_rerun()
                    
                    if col2.button("🗑️ Borrar este Mes", help="Elimina permanentemente los datos de este mes para que puedas volver a subirlos."):
                        conn = database.get_connection()
                        conn.execute("DELETE FROM imports WHERE id = ?", (current_import_id,))
                        conn.commit()
                        conn.close()
                        st.warning(f"Mes {analysis_month} eliminado del sistema.")
                        safe_rerun()
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
            
            # Wrapper for Competitor Analysis with Filters (Phase 6)
            st.markdown("### 🔬 Análisis Granular (Filtros)")
            selected_keywords_comp = st.multiselect(
                "Filtrar por Keywords específicas (deja vacío para ver todo el mercado):",
                options=df['keyword'].unique()
            )
            
            # Recalculate SOV if filter is active
            display_sov_df = sov_df
            if selected_keywords_comp:
                filtered_comp_df = df[df['keyword'].isin(selected_keywords_comp)]
                if not filtered_comp_df.empty:
                    display_sov_df = etl.calculate_sov(filtered_comp_df, domain_map, selected_domain)
                    st.caption(f"Análisis basado en {len(selected_keywords_comp)} keywords seleccionadas.")
                else:
                    st.warning("No hay datos para las keywords seleccionadas.")

            # Bar chart Top 10
            st.markdown("### Top 10 Competidores por Cuota de Visibilidad")
            top_10 = display_sov_df.head(10)
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
            st.dataframe(sov_display)
            
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
            st.subheader("🚀 Matriz de Oportunidades")
            
            # P0.3: Enhanced documentation with Motivo explanation
            st.markdown("""
            > **Quick Wins**: Keywords en posiciones 4-10 (Striking Distance) con alto potencial de impacto.
            > <span style="background:#FFA500;padding:2px 6px;border-radius:4px;font-size:10px;color:white;">ESTIMADO</span> Los valores son proyecciones basadas en CTR × CPC.
            """, unsafe_allow_html=True)

            if not opportunities.empty:
                # Add financial columns if CPC exists
                opp_display = opportunities.copy()
                
                # Format CPC
                if 'cpc' in opp_display.columns:
                    opp_display['CPC Est.'] = opp_display['cpc'].apply(lambda x: format_currency(x) if x > 0 else "—")
                
                # Format Uplift Value (P0.3: show "—" if null)
                if 'uplift_value' in opp_display.columns:
                    opp_display['Uplift Valor'] = opp_display['uplift_value'].apply(
                        lambda x: format_currency(x) if pd.notnull(x) and x > 0 else "Sin estimación €"
                    )
                
                # Intent badge formatting function
                def format_intent(val):
                    if pd.isna(val):
                        return "🤖 Mixta"
                    if "(V)" in str(val) or val == "Validada":
                        return f"✅ {val}"
                    return f"🤖 {val}"
                
                if 'intent' in opp_display.columns:
                    opp_display['Intención'] = opp_display['intent'].apply(format_intent)

                # Use the dynamic position column name for selection, then rename
                cols_to_select = ['keyword', pos_col, 'volume', 'difficulty', 'Intención', 'CPC Est.', 'uplift_clicks', 'Uplift Valor', 'motivo', 'opportunity_score']
                # Filter strictly for existing columns to avoid KeyError
                cols_to_select = [c for c in cols_to_select if c in opp_display.columns]

                st.dataframe(
                    opp_display[cols_to_select].rename(columns={
                        'keyword': 'Palabra Clave',
                        pos_col: 'Pos. Actual',
                        'volume': 'Búsquedas/mes',
                        'difficulty': 'Dificultad',
                        'uplift_clicks': 'Uplift Tráfico',
                        'motivo': '📊 Motivo',
                        'opportunity_score': 'Score'
                    })
                )
                
                # Export Button
                csv = opp_display.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar Oportunidades (CSV)",
                    data=csv,
                    file_name=f"oportunidades_{selected_domain}_{analysis_month}.csv",
                    mime="text/csv"
                )
                
                 # Intent Validation Module Integration
                st.markdown("---")
                render_intent_validation_module(df)
                
            else:
                st.info("No se encontraron oportunidades 'Quick Win' (Pos 4-10) en este mes.")
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
                
                media_col = f'media_value_{selected_domain}'
                if media_col in df.columns:
                    mv_df = df.sort_values(media_col, ascending=False).head(15).copy()
                    mv_display = mv_df.rename(columns={
                        'keyword': 'Palabra Clave',
                        'volume': 'Búsquedas',
                        'cpc': 'Coste Clic (Ads)',
                        media_col: 'Ahorro Estimado'
                    })
                    st.dataframe(mv_display[['Palabra Clave', 'Búsquedas', 'Coste Clic (Ads)', 'Ahorro Estimado']])
                else:
                    st.warning("No se encontraron datos de valor económico (media value) para este dominio.")
            
            with col_b:
                st.markdown("#### 🏷️ Tráfico: Marca vs. Genérico")
                st.caption("Diferencia entre personas que ya te conocen (Marca) vs. nuevos clientes (Genérico).")
                
                clicks_col = f'clics_{selected_domain}'
                if clicks_col in df.columns and 'is_branded' in df.columns:
                    brand_stats = df.groupby('is_branded').agg({clicks_col: 'sum', 'keyword': 'count'}).reset_index()
                    brand_stats['is_branded'] = brand_stats['is_branded'].map({True: 'Búsquedas de Marca', False: 'Búsquedas Genéricas'})
                    
                    fig_brand = px.bar(
                        brand_stats, 
                        x='is_branded', 
                        y=clicks_col, 
                        title="Distribución de Tráfico Mensual",
                        labels={'is_branded': 'Tipo de Palabra Clave', clicks_col: 'Clics Estimados'},
                        color='is_branded',
                        color_discrete_sequence=['#1E88E5', '#D81B60']
                    )
                    st.plotly_chart(fig_brand, use_container_width=True)
                else:
                    st.info("Desglose Marca/Genérico no disponible (faltan datos).")

        with t5:
            st.subheader("🔎 Keyword Deep Dive (Evolución por Palabra)")
            st.markdown("Analiza la historia de una keyword específica a través de todos los meses cargados.")
            
            # P0.4: Historical warning in deep dive
            if n_meses < 3:
                st.info(f"📊 Histórico limitado ({n_meses} meses). Para análisis de tendencia robusto, se recomiendan ≥3 meses.")
            
            all_keywords = sorted(df['keyword'].unique())
            selected_kw_dive = st.selectbox("Selecciona una palabra clave:", all_keywords)
            
            if selected_kw_dive:
                import json
                kw_history_df = database.get_keyword_history(project_id, selected_kw_dive)
                
                # Get current keyword data for context messages (P0.5)
                kw_current_row = df[df['keyword'] == selected_kw_dive]
                current_pos = kw_current_row[pos_col].values[0] if pos_col and not kw_current_row.empty else None
                current_traffic = kw_current_row[f'clics_{selected_domain}'].values[0] if f'clics_{selected_domain}' in kw_current_row.columns and not kw_current_row.empty else 0
                current_value = kw_current_row[f'media_value_{selected_domain}'].values[0] if f'media_value_{selected_domain}' in kw_current_row.columns and not kw_current_row.empty else 0
                
                # P0.5: Context message for 0€/0 traffic or zero value
                if current_traffic == 0 or current_value == 0:
                    st.warning(
                        "💡 **Potencial latente**. Esta keyword aún está fuera del rango de captación significativa. "
                        "Prioriza subir 1–2 posiciones para comenzar a captar tráfico."
                    )
                
                # P0.5: Striking distance badge
                if current_pos and 4 <= current_pos <= 10:
                    st.success(f"🎯 **Striking Distance** (Posición {current_pos:.0f}): Esta keyword está en zona de ataque. Un pequeño impulso puede generar gran impacto.")
                elif current_pos and current_pos <= 3:
                    st.info(f"🏆 **Top 3** (Posición {current_pos:.0f}): Esta keyword ya está capturando tráfico significativo.")
                
                if not kw_history_df.empty:
                    # Parse domain data json
                    history_parsed = []
                    for _, row in kw_history_df.iterrows():
                        d_data = json.loads(row['data_json'])
                        main_d_data = d_data.get(selected_domain, {})
                        history_parsed.append({
                            'Mes': row['month'],
                            'Posición': main_d_data.get('pos', 101),
                            'Tráfico Est.': main_d_data.get('clics', 0),
                            'Valor (€)': main_d_data.get('media_value', 0),
                            'CPC': row['cpc']
                        })
                    
                    hp_df = pd.DataFrame(history_parsed)
                    
                    # Metrics Delta
                    if len(hp_df) >= 2:
                        last = hp_df.iloc[-1]
                        prev = hp_df.iloc[-2]
                        
                        k1, k2, k3 = st.columns(3)
                        
                        # Position (Lower is better)
                        pos_delta = last['Posición'] - prev['Posición']
                        
                        k1.metric("Posición Actual", f"{last['Posición']:.0f}", delta=f"{pos_delta:.0f}", delta_color="inverse")
                        k2.metric("Tráfico Est.", f"{last['Tráfico Est.']:.0f}", delta=f"{last['Tráfico Est.'] - prev['Tráfico Est.']:.0f}")
                        k3.metric("Valor (€)", f"{last['Valor (€)']:.2f}€", delta=f"{last['Valor (€)'] - prev['Valor (€)']:.2f}€")
                    else:
                        # Only 1 month of data
                        last = hp_df.iloc[-1]
                        k1, k2, k3 = st.columns(3)
                        k1.metric("Posición Actual", f"{last['Posición']:.0f}")
                        k2.metric("Tráfico Est.", f"{last['Tráfico Est.']:.0f}")
                        k3.metric("Valor (€)", f"{last['Valor (€)']:.2f}€")
                        st.caption("Sin comparativa disponible (solo 1 mes de datos).")
                    
                    # Chart
                    fig_kw = px.line(hp_df, x='Mes', y='Posición', markers=True, title=f"Evolución de Posición: {selected_kw_dive}")
                    fig_kw['layout']['yaxis']['autorange'] = "reversed" # 1 is top
                    st.plotly_chart(fig_kw, use_container_width=True)
                    
                    st.dataframe(hp_df)
                else:
                    st.warning("No hay histórico suficiente para esta keyword.")

else:
    st.info("👋 Bienvenido. Selecciona un proyecto y un mes en la barra lateral para comenzar.")
    if st.session_state.get("api_key_configured"):
        st.success("✅ IA Configurada y lista.")
    else:
        st.warning("⚠️ IA Deshabilitada (Falta API Key).")

