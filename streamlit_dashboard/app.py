import streamlit as st
import pandas as pd
import google.generativeai as genai
import etl
import database
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

# Initialize AI
google_api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    google_api_key = str(st.secrets["GOOGLE_API_KEY"])
elif "general" in st.secrets and "GOOGLE_API_KEY" in st.secrets["general"]:
    google_api_key = str(st.secrets["general"]["GOOGLE_API_KEY"])

if google_api_key:
    # Clean key from literal quotes or spaces
    google_api_key = google_api_key.strip().strip('"').strip("'")
    genai.configure(api_key=google_api_key)
    st.session_state["api_key_configured"] = True
else:
    st.session_state["api_key_configured"] = False

# Helper for AI Report
def get_ai_analysis(import_id, summary_stats, opportunities_sample):
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
        Actúa como un Consultor SEO Senior. Analiza los siguientes datos resumidos de un sitio web y genera un reporte ejecutivo en Español.
        
        ## Datos del Proyecto
        {summary_stats}
        
        ## Muestra de Oportunidades (Posición 4-10)
        {opportunities_sample}
        
        ## Instrucciones
        1. Resumen Ejecutivo: Estado actual y salud del proyecto.
        2. Análisis de Competencia: Quien domina el mercado (Share of Voice).
        3. Acciones Recomendadas: 3 balas con las acciones más críticas basadas en las oportunidades.
        
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
            selected_import_row = st.selectbox("Mes de Análisis", imports_df.to_dict('records'), format_func=lambda x: f"{x['month']} ({x['filename']})")
            current_import_id = selected_import_row['id']
            stored_report = selected_import_row['report_text']
        else:
            st.info("No hay datos cargados para este proyecto.")
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
        with st.expander("📚 Glosario Ejecutivo"):
            st.markdown("""
            - **Share of Voice (SoV)**: Tu cuota de visibilidad en el mercado frente a competidores.
            - **Clics Estimados**: Tráfico probable basado en volumen y posición (CTR).
            - **Media Value**: Cuánto te ahorrarías en Google Ads por este tráfico orgánico.
            - **Striking Distance**: Keywords en pos. 4-10. Fáciles de subir al Top 3.
            - **Quick Wins**: Oportunidades de alto volumen y baja dificultad.
            """)

# --- MAIN DASHBOARD ---
if 'current_import_id' in locals() and current_import_id:
    df, domain_map = database.load_import_data(current_import_id)
    
    if df.empty:
        st.error("No se pudieron cargar los datos del mes seleccionado.")
    else:
        # Filter for selected project domain
        # In this persistent version, we use the domain stored in the project
        selected_domain = main_domain if mode == "admin" else list(domain_map.keys())[0]
        
        # Metrics Calculation
        sov_df = etl.calculate_sov(df, domain_map, selected_domain)
        main_sov = sov_df[sov_df['domain'] == selected_domain]['sov'].values[0] if not sov_df.empty else 0
        opportunities = etl.get_striking_distance(df, domain_map, selected_domain)
        
        pos_col = domain_map.get(selected_domain, {}).get('position')
        top_3 = len(df[df[pos_col] <= 3]) if pos_col else 0
        top_10 = len(df[df[pos_col] <= 10]) if pos_col else 0
        
        # Advanced Metrics Totals
        total_clics = df[f'clics_{selected_domain}'].sum() if f'clics_{selected_domain}' in df.columns else 0
        total_media_value = df[f'media_value_{selected_domain}'].sum() if f'media_value_{selected_domain}' in df.columns else 0

        # AI Report Logic
        report_display = stored_report
        if not report_display:
            stats_str = f"Dom: {selected_domain}, SoV: {main_sov:.2f}%, Top 10: {top_10}, Clics Est: {total_clics:.0f}, Media Value: ${total_media_value:.0f}"
            opps_str = opportunities.head(10).to_string(index=False)
            report_display = get_ai_analysis(current_import_id, stats_str, opps_str)

        # --- MoM TREND CALCULATION ---
        prev_month_id = None
        current_idx = imports_df[imports_df['id'] == current_import_id].index[0]
        if current_idx + 1 < len(imports_df):
            prev_month_id = imports_df.iloc[current_idx + 1]['id']
        
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
        
        t1, t2, t3, t4 = st.tabs(["📊 Resumen Ejecutivo", "⚔️ Competencia", "🚀 Oportunidades", "🧠 Inteligencia Avanzada"])
        
        with t1:
            st.subheader("💡 Análisis Estratégico")
            st.info(report_display, icon="🤖")
            
            st.markdown("### KPIs del Mes")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Share of Voice", f"{main_sov:.1f}%", delta=f"{delta_sov:+.1f}%" if delta_sov is not None else None)
            c2.metric("Clics Estimados", f"{total_clics:,.0f}", delta=f"{delta_clics:+,.0f}" if delta_clics is not None else None)
            c3.metric("Media Value", f"${total_media_value:,.0f}")
            c4.metric("Quick Wins", len(opportunities))
            
            # Ranking Chart
            st.markdown("---")
            if pos_col:
                def get_bucket(p):
                    if p <= 3: return "Top 3"
                    if p <= 10: return "4-10"
                    if p <= 20: return "11-20"
                    return "20+"
                df['bucket'] = df[pos_col].apply(get_bucket)
                fig = px.bar(df['bucket'].value_counts().reset_index(), x='index', y='bucket', labels={'index':'Rango', 'bucket':'Keywords'}, title="Distribución de Rankings")
                st.plotly_chart(fig, use_container_width=True)

        with t2:
            st.subheader("Benchmark de Mercado")
            st.dataframe(sov_df, use_container_width=True)
            fig_pie = px.pie(sov_df, values='sov', names='domain', title="Market Share (Visibilidad)")
            st.plotly_chart(fig_pie, use_container_width=True)

        with t3:
            st.subheader("💎 Striking Distance (Pos. 4-10)")
            st.markdown("Keywords con alto potencial de conversión si suben al Top 3.")
            st.dataframe(opportunities[['keyword', 'volume', 'difficulty', 'intent', pos_col]], use_container_width=True)

        with t4:
            st.subheader("🎯 Análisis de Valor y Canibalización")
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("#### Keywords de Mayor Valor ($)")
                mv_df = df.sort_values(f'media_value_{selected_domain}', ascending=False).head(10)
                st.dataframe(mv_df[['keyword', 'volume', 'cpc', f'media_value_{selected_domain}']], use_container_width=True)
            
            with col_b:
                st.markdown("#### Segmentación Branded vs Original")
                brand_stats = df.groupby('is_branded').agg({f'clics_{selected_domain}': 'sum', 'keyword': 'count'}).reset_index()
                fig_brand = px.bar(brand_stats, x='is_branded', y=f'clics_{selected_domain}', title="Tráfico Marca vs Genérico")
                st.plotly_chart(fig_brand, use_container_width=True)

else:
    st.info("👋 Bienvenido. Selecciona un proyecto y un mes en la barra lateral para comenzar.")
    if st.session_state.get("api_key_configured"):
        st.success("✅ IA Configurada y lista.")
    else:
        st.warning("⚠️ IA Deshabilitada (Falta API Key).")

