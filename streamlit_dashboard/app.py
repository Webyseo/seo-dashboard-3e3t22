import streamlit as st
import pandas as pd
import google.generativeai as genai
import etl
import plotly.express as px

# Configuration
st.set_page_config(
    page_title="SEO Executive Dashboard",
    page_icon="🚀",
    layout="wide"
)

# Initialize AI
google_api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    google_api_key = st.secrets["GOOGLE_API_KEY"]
elif "general" in st.secrets and "GOOGLE_API_KEY" in st.secrets["general"]:
    google_api_key = st.secrets["general"]["GOOGLE_API_KEY"]

if google_api_key:
    genai.configure(api_key=google_api_key)
    # Store for further use
    st.session_state["api_key_configured"] = True
else:
    st.session_state["api_key_configured"] = False
    st.warning("⚠️ GOOGLE_API_KEY no encontrada. Comprueba tus Secrets en Streamlit Cloud.")

def serialize_dataframe(df):
    """Convert dataframe to string for AI context, limiting rows to save tokens"""
    return df.head(50).to_string()

def generate_ai_report(summary_stats, opportunities_sample):
    """
    Generates an executive report using Gemini-3-Flash-Preview.
    """
    if "GOOGLE_API_KEY" not in st.secrets:
        return "⚠️ Configura tu API Key para ver el reporte de IA."

    try:
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        prompt = f"""
        Actúa como un Consultor SEO Senior. Analiza los siguientes datos resumidos de un sitio web y genera un reporte ejecutivo en Español.
        
        ## Datos del Proyecto
        {summary_stats}
        
        ## Oportunidades Detectadas (Muestra de Quick Wins, Posición 4-10)
        {opportunities_sample}
        
        ## Instrucciones
        1. Resumen Ejecutivo: Estado actual y salud del proyecto.
        2. Análisis de Competencia: Quien domina el mercado (Share of Voice).
        3. Acciones Recomendadas: 3 balas con las acciones más críticas basadas en las oportunidades.
        
        Sé breve, directo y profesional. Usa formato Markdown.
        """
        
        with st.spinner('🤖 Generando análisis con Inteligencia Artificial...'):
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        return f"Error generando reporte: {str(e)}"

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/270/270798.png", width=50)
    st.title("SEO Dashboard")
    
    uploaded_file = st.file_uploader("Subir CSV mensual", type=['csv'])
    
    st.markdown("---")
    st.markdown("### Configuración")
    # Placeholder for domain selection if needed after upload

# Main App
if uploaded_file is not None:
    # 1. Process Data
    ret, err = etl.parse_csv_data(uploaded_file)
    
    if err:
        st.error(err)
    else:
        df = ret['df']
        domain_map = ret['domains']
        
        # Domain Selector
        domains_found = list(domain_map.keys())
        if not domains_found:
            st.error("No se detectaron dominios en el CSV (buscamos columnas como 'Visibilidad [dominio.com]').")
        else:
            selected_domain = st.sidebar.selectbox("Dominio Principal", domains_found)
            
            # --- CALCULATE METRICS ---
            
            # 1. Share of Voice
            sov_df = etl.calculate_sov(df, domain_map, selected_domain)
            main_sov = sov_df[sov_df['domain'] == selected_domain]['sov'].values[0] if not sov_df.empty else 0
            
            # 2. Striking Distance
            opportunities = etl.get_striking_distance(df, domain_map, selected_domain)
            quick_wins_count = len(opportunities)
            
            # 3. Top Keywords
            pos_col = domain_map[selected_domain].get('position')
            top_3 = len(df[df[pos_col] <= 3]) if pos_col else 0
            top_10 = len(df[(df[pos_col] <= 10)]) if pos_col else 0
            
            # --- AI REPORT GENERATION ---
            # Create a simplified state key based on filename
            file_key = f"report_{uploaded_file.name}_{selected_domain}"
            
            if file_key not in st.session_state:
                stats_str = f"""
                - Dominio Analizado: {selected_domain}
                - Share of Voice Actual: {main_sov:.2f}%
                - Keywords en Top 3: {top_3}
                - Keywords en Top 10: {top_10}
                - Oportunidades (Quick Wins): {quick_wins_count}
                - Competidores principales: {', '.join(sov_df.head(3)['domain'].tolist())}
                """
                
                opps_str = opportunities.head(10).to_string(index=False)
                
                st.session_state[file_key] = generate_ai_report(stats_str, opps_str)
            
            # --- UI TABS ---
            st.title(f"Reporte SEO: {selected_domain}")
            
            tab1, tab2, tab3 = st.tabs(["📊 Resumen Ejecutivo", "⚔️ Competencia", "🚀 Oportunidades"])
            
            with tab1:
                # AI Report Section
                st.subheader("💡 Análisis Inteligente (Gemini)")
                st.info(st.session_state[file_key], icon="🤖")
                
                st.markdown("### KPIs Principales")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Share of Voice", f"{main_sov:.1f}%")
                col2.metric("Top 3 Keywords", top_3)
                col3.metric("Top 10 Keywords", top_10)
                col4.metric("Quick Wins", quick_wins_count)
                
                # Charts
                st.markdown("### Distribución de Rankings")
                if pos_col:
                    # Create buckets
                    def get_bucket(p):
                        if p <= 3: return "Top 3"
                        if p <= 10: return "4-10"
                        if p <= 20: return "11-20"
                        if p <= 100: return "20+"
                        return "Not Ranked"
                    
                    df['bucket'] = df[pos_col].apply(get_bucket)
                    bucket_counts = df['bucket'].value_counts().reset_index()
                    bucket_counts.columns = ['Rango', 'Cantidad']
                    
                    fig = px.bar(bucket_counts, x='Rango', y='Cantidad', title="Distribución de Posiciones", color='Rango')
                    st.plotly_chart(fig, use_container_width=True)

            with tab2:
                st.subheader("Comparativa de Mercado")
                st.markdown("Rankeados por Share of Voice (Visibilidad Total)")
                st.dataframe(sov_df, use_container_width=True)
                
                # Chart
                fig_sov = px.pie(sov_df, values='sov', names='domain', title='Share of Voice Market Split')
                st.plotly_chart(fig_sov, use_container_width=True)

            with tab3:
                st.subheader(f"💎 Oportunidades de Alto Impacto ({quick_wins_count})")
                st.markdown("Keywords posicionadas entre 4 y 10. Optimizarlas suele traer el mayor retorno a corto plazo.")
                st.dataframe(opportunities, use_container_width=True)

else:
    st.info("👆 Sube un archivo CSV data comenzar. Usa el panel de la izquierda.")
    st.markdown("""
    ### Formato esperado del CSV
    El archivo debe contener columnas estándar de herramientas SEO (como Semrush/Ahrefs/Sistrix):
    - `Palabra clave`
    - `Volumen`
    - `Visibilidad [midominio.com]` (para detección automática)
    - `Posición [midominio.com]`
    """)
