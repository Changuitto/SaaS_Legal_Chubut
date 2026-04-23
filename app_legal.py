# 0. PARCHE PARA CHROMADB EN LINUX (RAILWAY)
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
 
import os
import zipfile
import urllib.request
import time
import json
import streamlit as st
import extra_streamlit_components as stx
from datetime import datetime, timedelta
from supabase import create_client, Client
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from fpdf import FPDF
 
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO PREMIUM
st.set_page_config(page_title="Chubut.IA - Jurisprudencia", page_icon="logo.png", layout="wide")
 
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:wght@600&display=swap');
 
        /* ── BASE ─────────────────────────────────────────── */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        footer { visibility: hidden; }
 
        /* ── FONDO GENERAL ────────────────────────────────── */
        .stApp {
            background-color: #0A0F1E;
        }
 
        /* ── SIDEBAR ──────────────────────────────────────── */
        [data-testid="stSidebar"] {
            background-color: #080C1A !important;
            border-right: 1px solid rgba(148, 163, 184, 0.08) !important;
        }
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stMarkdown span {
            color: #94A3B8;
            font-size: 0.82rem;
        }
 
        /* ── BOTONES SIDEBAR ──────────────────────────────── */
        [data-testid="stSidebar"] .stButton > button {
            width: 100%;
            text-align: left;
            padding: 9px 14px;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 400;
            letter-spacing: 0.01em;
            color: #94A3B8 !important;
            background-color: transparent !important;
            border: 1px solid rgba(148, 163, 184, 0.12) !important;
            transition: all 0.18s ease;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            color: #E2E8F0 !important;
            background-color: rgba(148, 163, 184, 0.06) !important;
            border-color: rgba(148, 163, 184, 0.28) !important;
        }
 
        /* ── BOTÓN PRIMARIO (Nueva Consulta / Pro) ────────── */
        [data-testid="stSidebar"] .stButton > button[kind="primary"],
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 100%) !important;
            border: 1px solid #2563EB !important;
            color: #EFF6FF !important;
            font-weight: 500 !important;
            letter-spacing: 0.03em !important;
            border-radius: 6px !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 1px 6px rgba(37, 99, 235, 0.25) !important;
        }
        [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%) !important;
            box-shadow: 0 2px 10px rgba(37, 99, 235, 0.40) !important;
        }
 
        /* ── BURBUJAS DE CHAT ─────────────────────────────── */
        /* Asistente */
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
            background-color: #0F172A;
            border: 1px solid rgba(148, 163, 184, 0.10);
            border-radius: 2px 16px 16px 16px;
            padding: 1.4rem 1.6rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) p {
            color: #CBD5E1;
            font-size: 0.925rem;
            line-height: 1.75;
        }
 
        /* Usuario */
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
            background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%) !important;
            border: 1px solid rgba(59, 130, 246, 0.25) !important;
            border-radius: 16px 2px 16px 16px !important;
            padding: 1.2rem 1.6rem !important;
            margin-bottom: 1.2rem !important;
            margin-left: auto !important;
            max-width: 85% !important;
            box-shadow: 0 2px 12px rgba(30, 58, 138, 0.35) !important;
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) * {
            color: #DBEAFE !important;
            font-size: 0.925rem !important;
        }
 
        /* ── CHAT INPUT ───────────────────────────────────── */
        [data-testid="stChatInput"] textarea {
            background-color: #0F172A !important;
            border: 1px solid rgba(148, 163, 184, 0.18) !important;
            border-radius: 10px !important;
            color: #E2E8F0 !important;
            font-size: 0.9rem !important;
            caret-color: #3B82F6;
            transition: border-color 0.2s;
        }
        [data-testid="stChatInput"] textarea:focus {
            border-color: rgba(59, 130, 246, 0.50) !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.08) !important;
        }
        [data-testid="stChatInput"] textarea::placeholder {
            color: #475569 !important;
        }
 
        /* ── BOTONES DE SUGERENCIA ────────────────────────── */
        .botones-sugerencia button {
            border: 1px solid rgba(148, 163, 184, 0.16) !important;
            border-radius: 8px !important;
            padding: 14px 16px !important;
            text-align: left !important;
            background-color: #0F172A !important;
            color: #64748B !important;
            font-size: 0.82rem !important;
            font-weight: 400 !important;
            line-height: 1.5 !important;
            transition: all 0.2s ease !important;
        }
        .botones-sugerencia button:hover {
            border-color: rgba(59, 130, 246, 0.40) !important;
            background-color: rgba(30, 58, 138, 0.15) !important;
            color: #CBD5E1 !important;
        }
 
        /* ── DIVISORES ────────────────────────────────────── */
        hr {
            border-color: rgba(148, 163, 184, 0.08) !important;
            margin: 1rem 0 !important;
        }
 
        /* ── TABS (Login / Registro) ──────────────────────── */
        .stTabs [data-baseweb="tab-list"] {
            background-color: transparent;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
            gap: 0;
        }
        .stTabs [data-baseweb="tab"] {
            color: #475569;
            font-size: 0.85rem;
            font-weight: 400;
            padding: 10px 22px;
            border-bottom: 2px solid transparent;
            transition: all 0.18s;
        }
        .stTabs [aria-selected="true"] {
            color: #93C5FD !important;
            border-bottom: 2px solid #3B82F6 !important;
            background-color: transparent !important;
        }
 
        /* ── INPUTS DE FORMULARIO ─────────────────────────── */
        .stTextInput input, .stTextArea textarea {
            background-color: #0F172A !important;
            border: 1px solid rgba(148, 163, 184, 0.16) !important;
            border-radius: 6px !important;
            color: #E2E8F0 !important;
            font-size: 0.875rem !important;
            transition: border-color 0.2s;
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: rgba(59, 130, 246, 0.45) !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.08) !important;
        }
        .stTextInput label, .stTextArea label {
            color: #64748B !important;
            font-size: 0.78rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.06em !important;
            text-transform: uppercase !important;
        }
 
        /* ── ALERTS / INFO / WARNING ──────────────────────── */
        .stAlert {
            border-radius: 8px !important;
            font-size: 0.83rem !important;
        }
 
        /* ── DOWNLOAD BUTTON ──────────────────────────────── */
        .stDownloadButton > button {
            background-color: transparent !important;
            border: 1px solid rgba(148, 163, 184, 0.20) !important;
            border-radius: 6px !important;
            color: #64748B !important;
            font-size: 0.8rem !important;
            font-weight: 400 !important;
            transition: all 0.2s !important;
        }
        .stDownloadButton > button:hover {
            border-color: rgba(148, 163, 184, 0.40) !important;
            color: #CBD5E1 !important;
            background-color: rgba(148, 163, 184, 0.05) !important;
        }
 
        /* ── EXPANDER ─────────────────────────────────────── */
        .streamlit-expanderHeader {
            font-size: 0.82rem !important;
            color: #475569 !important;
            font-weight: 400 !important;
        }
        .streamlit-expanderContent {
            background-color: transparent !important;
        }
 
        /* ── SCROLLBAR ────────────────────────────────────── */
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.15); border-radius: 2px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(148, 163, 184, 0.3); }
    </style>
""", unsafe_allow_html=True)
 
# ==========================================
# FUNCIÓN PARA GENERAR PDF (LIMPIO DE EMOJIS)
# ==========================================
def generar_pdf(historial, titulo_chat):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Reporte de Jurisprudencia - Chubut.IA", ln=True, align="C")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 10, f"Generado el: {(datetime.now() - timedelta(hours=3)).strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.multi_cell(0, 10, f"Consulta: {titulo_chat}")
    pdf.ln(5)
    
    for msg in historial:
        rol = "Usuario" if msg["role"] == "user" else "Chubut.IA"
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 10, f"{rol}:", ln=True)
        
        pdf.set_font("helvetica", "", 10)
        texto_limpio = msg["content"].encode('latin-1', 'ignore').decode('latin-1')
        texto_limpio = texto_limpio.replace('**', '')
        pdf.multi_cell(0, 6, texto_limpio)
        pdf.ln(4)
        
    return bytes(pdf.output())
 
# ==========================================
# 2. SISTEMA BLINDADO DE COOKIES EN LA RAÍZ
# ==========================================
cookie_manager = stx.CookieManager(key="gestor_chubut")
 
if "set_refresh_token" in st.session_state:
    vencimiento = datetime.now() + timedelta(days=30)
    cookie_manager.set("chubut_refresh", st.session_state.set_refresh_token, expires_at=vencimiento, key="set_ref_root")
    del st.session_state.set_refresh_token
 
if "del_tokens" in st.session_state:
    cookie_manager.delete("chubut_refresh", key="del_ref_root")
    del st.session_state.del_tokens
 
if "set_invitado" in st.session_state:
    vencimiento_inv = datetime.now() + timedelta(days=365)
    cookie_manager.set("chubut_invitado", str(st.session_state.set_invitado), expires_at=vencimiento_inv, key="set_inv_root")
    del st.session_state.set_invitado
 
mis_cookies = cookie_manager.get_all()
if mis_cookies is None:
    st.markdown("<h3 style='text-align: center; color: #475569; margin-top: 20vh; font-family: Inter, sans-serif; font-weight: 300;'>Sincronizando entorno seguro...</h3>", unsafe_allow_html=True)
    st.stop()
 
# ==========================================
# 3. VARIABLES DE ENTORNO Y SERVICIOS
# ==========================================
OPENAI_KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
 
if not OPENAI_KEY or not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Error crítico: Faltan variables de configuración en Railway.")
    st.stop()
else:
    os.environ["OPENAI_API_KEY"] = OPENAI_KEY
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
 
if "user_data" not in st.session_state: 
    st.session_state.user_data = None
 
token_guardado = mis_cookies.get("chubut_refresh")
 
if token_guardado and st.session_state.user_data is None:
    try:
        res = supabase.auth.refresh_session(token_guardado)
        st.session_state.user_data = res.user
        st.session_state.set_refresh_token = res.session.refresh_token
    except Exception:
        pass 
 
if "show_login" not in st.session_state: st.session_state.show_login = False
if "guest_history" not in st.session_state: st.session_state.guest_history = []
if "consultas_gastadas" not in st.session_state: st.session_state.consultas_gastadas = 0
 
galleta_invitado = mis_cookies.get("chubut_invitado")
if galleta_invitado:
    st.session_state.consultas_gastadas = max(st.session_state.consultas_gastadas, int(galleta_invitado))
 
# ==========================================
# INSTRUCCIÓN PARA LA IA
# ==========================================
def generar_instruccion_ia(contexto):
    return f"""Sos Chubut.IA, un asistente jurídico experto enfocado exclusivamente en la jurisprudencia de la Provincia de Chubut.
 
CONTEXTO DE LA BASE DE DATOS (EUREKA):
{contexto}
 
DIRECTRICES DE COMPORTAMIENTO:
1. CORTESÍA: Podés responder cordialmente a saludos o agradecimientos ("Hola", "Gracias", etc.), pero llevando rápidamente la conversación al ámbito legal.
2. LÍMITE ESTRICTO: Si el usuario pregunta o pide algo que NO tiene relación con el ámbito legal, jurisprudencia, o las leyes de Chubut, DEBES NEGARTE CORTÉSMENTE indicando que solo estás capacitado para asistir en materia jurídica de Chubut.
3. VERSATILIDAD ANALÍTICA: Estás autorizado a realizar análisis, comparaciones, resúmenes o explicaciones jurídicas siempre y cuando se basen en la jurisprudencia y el contexto proporcionado. Podés pensar como un abogado analizando un caso basándote en los fallos.
4. FORMATO DE BÚSQUEDA DE FALLOS: Si el usuario te pide explícitamente "buscar fallos", "mostrar jurisprudencia" o listar casos, utiliza ESTRICTAMENTE este formato para cada fallo:
 
📌 **[Nombre o Título del Fallo]**
* 📅 **Fecha del Fallo:** [Copia la 'FECHA' exacta]
* 📖 **Cita Textual:** "[Extracto más relevante]"
* 📝 **Resumen de los Hechos:** [Breve resumen]
* ⚖️ **Resolución:** [Decisión final]
* 🔗 **Ver fallo oficial:** [Pega la 'URL' tal cual, sin corchetes ni formato markdown. Solo el link crudo]"""
 
# ==========================================
# DESCARGO DE RESPONSABILIDAD LEGAL Y SOPORTE
# ==========================================
def mostrar_disclaimer():
    st.markdown("""
        <div style="
            font-size: 0.72rem;
            color: #334155;
            text-align: center;
            margin-top: 28px;
            padding: 12px 10px;
            border-top: 1px solid rgba(148, 163, 184, 0.08);
            line-height: 1.6;
            font-style: italic;
        ">
            Chubut.IA es una herramienta de asistencia basada en inteligencia artificial.
            Los fallos mostrados deben ser verificados en sus fuentes oficiales
            y no reemplazan el asesoramiento legal profesional.
        </div>
    """, unsafe_allow_html=True)
 
def mostrar_soporte():
    st.markdown("""
        <div style="text-align: center; font-size: 0.77rem; color: #334155; margin-top: 8px; padding-bottom: 18px;">
            ¿Necesitás ayuda?<br>
            <a href="mailto:chubutiaoficial@gmail.com"
               style="color: #60A5FA; text-decoration: none; font-weight: 500; letter-spacing: 0.01em;">
                chubutiaoficial@gmail.com
            </a>
        </div>
    """, unsafe_allow_html=True)
 
def verificar_pago_entrante(user_email):
    params = st.query_params
    if params.get("status") == "approved" and st.session_state.user_data:
        venc_pro = (datetime.now() - timedelta(hours=3)).date() + timedelta(days=30)
        supabase.table("usuarios").update({
            "plan": "pro",
            "vencimiento_pro": str(venc_pro)
        }).eq("email", user_email).execute()
        st.success("¡Pago procesado con éxito! Tu Plan Pro está activo por 30 días.")
        st.query_params.clear()
 
# ==========================================
# PANTALLA DE ACCESO (LOGIN / REGISTRO)
# ==========================================
def pantalla_acceso():
    if st.button("← Volver al Chat de Prueba"):
        st.session_state.show_login = False
        st.rerun()
 
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        st.markdown("""
            <h3 style='
                text-align: center;
                font-family: "Playfair Display", serif;
                font-weight: 600;
                color: #E2E8F0;
                font-size: 1.6rem;
                letter-spacing: 0.01em;
                margin-bottom: 1.5rem;
            '>Acceso al Sistema</h3>
        """, unsafe_allow_html=True)
 
        tab_in, tab_reg = st.tabs(["  Entrar  ", "  Registrarse  "])
        
        with tab_in:
            if not st.session_state.get("login_exitoso"):
                with st.form("form_login", clear_on_submit=False):
                    email = st.text_input("Email")
                    password = st.text_input("Contraseña", type="password")
                    btn_login = st.form_submit_button("Iniciar Sesión", use_container_width=True)
 
                if btn_login:
                    if email and password:
                        with st.spinner("Autenticando..."):
                            try:
                                res = supabase.auth.sign_in_with_password({"email": email.strip(), "password": password})
                                st.session_state.temp_user = res.user
                                st.session_state.set_refresh_token = res.session.refresh_token
                                st.session_state.login_exitoso = True
                                st.rerun()
                            except Exception as e:
                                st.error("Credenciales incorrectas o email no confirmado.")
                    else:
                        st.warning("Completá ambos campos.")
 
            if st.session_state.get("login_exitoso"):
                st.success("Pase generado y guardado en tu navegador.")
                st.info("Hacé clic abajo para confirmar tu entrada.")
                if st.button("ENTRAR A MI CUENTA", type="primary", use_container_width=True):
                    st.session_state.user_data = st.session_state.temp_user
                    st.session_state.show_login = False
                    st.session_state.login_exitoso = False
                    st.rerun()
 
        with tab_reg:
            with st.form("form_registro", clear_on_submit=False):
                new_user = st.text_input("Nombre y Apellido")
                new_email = st.text_input("Correo Electrónico")
                new_pass = st.text_input("Crea una contraseña", type="password")
                confirm_pass = st.text_input("Confirmar contraseña", type="password")
                btn_reg = st.form_submit_button("Crear Cuenta", use_container_width=True)
                
            if btn_reg:
                if not new_user or not new_email or not new_pass or not confirm_pass:
                    st.warning("Por favor, completá todos los campos.")
                elif new_pass != confirm_pass:
                    st.error("Las contraseñas no coinciden.")
                elif len(new_pass) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres.")
                else:
                    with st.spinner("Creando cuenta..."):
                        check_user = supabase.table("usuarios").select("usuario").eq("usuario", new_user).execute()
                        check_email = supabase.table("usuarios").select("email").eq("email", new_email.strip()).execute()
                        
                        if len(check_user.data) > 0:
                            st.error("Ese nombre de usuario ya está en uso.")
                        elif len(check_email.data) > 0:
                            st.error("Este correo electrónico ya está registrado.")
                        else:
                            try:
                                venc_trial = (datetime.now() - timedelta(hours=3)).date() + timedelta(days=7)
                                supabase.auth.sign_up({"email": new_email.strip(), "password": new_pass, "options": {"data": {"display_name": new_user}}})
                                supabase.table("usuarios").insert({
                                    "usuario": new_user, "email": new_email.strip(), "plan": "gratis",
                                    "vencimiento_trial": str(venc_trial), "historial": {"Nueva Consulta": []}
                                }).execute()
                                st.success("Cuenta creada con éxito. Revisá tu correo (incluida la carpeta de Spam) para confirmar tu cuenta antes de iniciar sesión.")
                            except Exception as e: 
                                st.error(f"Error técnico: {e}")
                                
        st.write("")
        st.write("")
        mostrar_soporte()
 
# ==========================================
# CEREBRO GLOBAL (DESCARGA DIRECTA DE GITHUB RELEASES)
# ==========================================
@st.cache_resource(show_spinner="Conectando el cerebro jurídico de Chubut (puede demorar unos minutos)...")
def load_ia():
    if not os.path.exists("MI_BASE_VECTORIAL"):
        url_directa = "https://github.com/ChubutIA/SaaS_Legal_Chubut/releases/download/v1.0/MI_BASE_VECTORIAL.zip"
        urllib.request.urlretrieve(url_directa, "base.zip")
        with zipfile.ZipFile("base.zip", 'r') as zr: 
            zr.extractall()
    
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    vdb = Chroma(persist_directory="MI_BASE_VECTORIAL", embedding_function=emb)
    return vdb, ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
 
vdb, llm = load_ia()
 
# ==========================================
# PANTALLA MODO INVITADO (LÍMITE: 5 CONSULTAS)
# ==========================================
def pantalla_invitado():
    consultas_restantes = 5 - st.session_state.consultas_gastadas
 
    with st.sidebar:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        st.divider()
 
        st.markdown(f"""
            <div style="
                background: rgba(15, 23, 42, 0.8);
                border: 1px solid rgba(148, 163, 184, 0.10);
                border-radius: 8px;
                padding: 14px 16px;
                margin-bottom: 12px;
            ">
                <p style="color: #475569; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; margin: 0 0 6px 0; font-weight: 500;">Modo</p>
                <p style="color: #CBD5E1; font-size: 0.88rem; font-weight: 500; margin: 0;">Acceso Invitado</p>
                <p style="color: #475569; font-size: 0.78rem; margin: 6px 0 0 0;">
                    Consultas restantes: <span style="color: #93C5FD; font-weight: 600;">{max(0, consultas_restantes)}</span> / 5
                </p>
            </div>
        """, unsafe_allow_html=True)
 
        if st.button("Iniciar Sesión / Registrarse", type="primary", use_container_width=True):
            st.session_state.show_login = True
            st.rerun()
        
        st.divider()
        with st.expander("Términos y Privacidad"):
            st.markdown("""
                <div style="font-size: 0.78rem; color: #475569; line-height: 1.7;">
                    <b style="color: #64748B;">Propiedad Intelectual:</b> El software y la marca Chubut.IA son propiedad exclusiva del desarrollador. Queda prohibida la reproducción total o parcial.<br><br>
                    <b style="color: #64748B;">Responsabilidad:</b> Herramienta de asistencia basada en IA. La verificación en fuentes oficiales es responsabilidad del profesional.<br><br>
                    <b style="color: #64748B;">Privacidad:</b> Cumplimos con la Ley 25.326. Sus consultas son confidenciales.
                </div>
            """, unsafe_allow_html=True)
            
        mostrar_disclaimer()
        mostrar_soporte()
 
    if not st.session_state.guest_history:
        st.markdown("""
            <div style="
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 42vh;
                text-align: center;
            ">
                <p style="
                    font-size: 0.8rem;
                    text-transform: uppercase;
                    letter-spacing: 0.18em;
                    color: #3B82F6;
                    font-weight: 500;
                    margin-bottom: 14px;
                ">Jurisprudencia · Provincia de Chubut</p>
                <h1 style="
                    font-family: 'Playfair Display', serif;
                    font-size: 2.6rem;
                    font-weight: 600;
                    color: #E2E8F0;
                    margin: 0 0 12px 0;
                    line-height: 1.2;
                ">Consultá la jurisprudencia<br>sin registrarte.</h1>
                <p style="
                    font-size: 1rem;
                    color: #475569;
                    margin: 0;
                    font-weight: 300;
                ">5 consultas gratuitas · Sin tarjeta de crédito</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <p style='
                text-align: center;
                color: #334155;
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 500;
                margin: 28px 0 14px 0;
            '>Consultas frecuentes</p>
        """, unsafe_allow_html=True)
 
        st.markdown("<div class='botones-sugerencia'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("⚖️ Fallos sobre cuota alimentaria", use_container_width=True):
            st.session_state.guest_history.append({"role": "user", "content": "Mostrame fallos recientes sobre cuota alimentaria"})
            st.rerun()
        if c2.button("🚗 Jurisprudencia en accidentes de tránsito", use_container_width=True):
            st.session_state.guest_history.append({"role": "user", "content": "Mostrame jurisprudencia sobre accidentes de tránsito"})
            st.rerun()
        c3, c4 = st.columns(2)
        if c3.button("🏢 Fallos por despidos sin causa", use_container_width=True):
            st.session_state.guest_history.append({"role": "user", "content": "Busca fallos sobre despidos sin causa justificada"})
            st.rerun()
        if c4.button("🏥 Mala praxis médica", use_container_width=True):
            st.session_state.guest_history.append({"role": "user", "content": "Busca fallos relacionados con mala praxis médica"})
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
            
    else:
        for m in st.session_state.guest_history:
            with st.chat_message(m["role"]): st.markdown(m["content"])
            
        st.markdown("<div style='height:1px; background: rgba(148,163,184,0.08); margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
        
        pdf_bytes = generar_pdf(st.session_state.guest_history, "Chat de Prueba Invitado")
        st.download_button(
            label="📄 Exportar conversación a PDF",
            data=pdf_bytes,
            file_name="Reporte_ChubutIA.pdf",
            mime="application/pdf",
            use_container_width=True
        )
 
    if st.session_state.consultas_gastadas >= 5:
        st.markdown("""
            <div style="
                text-align: center;
                padding: 22px 24px;
                border: 1px solid rgba(59, 130, 246, 0.20);
                border-radius: 10px;
                background: rgba(30, 58, 138, 0.08);
                margin-top: 20px;
            ">
                <p style="color: #64748B; font-size: 0.85rem; margin: 0 0 14px 0;">
                    Alcanzaste el límite de 5 consultas gratuitas.
                </p>
                <p style="color: #93C5FD; font-size: 0.9rem; font-weight: 500; margin: 0;">
                    Creá una cuenta gratuita para continuar con 7 días de prueba completa.
                </p>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Crear cuenta — 7 días sin costo", type="primary", use_container_width=True):
            st.session_state.show_login = True
            st.rerun()
    else:
        if prompt := st.chat_input("Consultá sobre jurisprudencia de Chubut..."):
            st.session_state.guest_history.append({"role": "user", "content": prompt})
            st.rerun()
 
    if st.session_state.guest_history and st.session_state.guest_history[-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Analizando jurisprudencia..."):
                docs = vdb.similarity_search(st.session_state.guest_history[-1]["content"], k=6)
                contexto_final = "\n\n".join([f"📅 FECHA: {d.metadata.get('fecha_completa')}\n🔗 URL: {d.metadata.get('link_pdf')}\n📄 CONTENIDO:\n{d.page_content}" for d in docs])
                
                mensajes = [SystemMessage(content=generar_instruccion_ia(contexto_final))]
                for m in st.session_state.guest_history[:-1]:
                    mensajes.append(HumanMessage(content=m["content"]) if m["role"]=="user" else AIMessage(content=m["content"]))
                mensajes.append(HumanMessage(content=st.session_state.guest_history[-1]["content"]))
                
                respuesta = llm.invoke(mensajes)
                st.markdown(respuesta.content)
                st.session_state.guest_history.append({"role": "assistant", "content": respuesta.content})
                
                st.session_state.consultas_gastadas += 1
                st.session_state.set_invitado = st.session_state.consultas_gastadas
                st.rerun() 
 
# ==========================================
# PANTALLA DE CHAT (LOGUEADOS)
# ==========================================
def pantalla_chat():
    user = st.session_state.user_data
    verificar_pago_entrante(user.email)
    db_res = supabase.table("usuarios").select("*").eq("email", user.email).execute()
    datos = db_res.data[0]
    
    hoy = (datetime.now() - timedelta(hours=3)).date()
    
    fecha_trial_formateada = ""
    if datos.get("vencimiento_trial"):
        fecha_trial_formateada = datetime.strptime(datos["vencimiento_trial"], "%Y-%m-%d").strftime("%d/%m/%Y")
 
    fecha_pro_formateada = ""
    if datos.get("vencimiento_pro"):
        fecha_pro_formateada = datetime.strptime(datos["vencimiento_pro"], "%Y-%m-%d").strftime("%d/%m/%Y")
 
    es_pro = False
    if datos.get("plan") == "pro" and datos.get("vencimiento_pro"):
        venc_pro = datetime.strptime(datos["vencimiento_pro"], "%Y-%m-%d").date()
        if hoy <= venc_pro: es_pro = True
 
    esta_en_trial = False
    if not es_pro and datos.get("vencimiento_trial"):
        venc_trial = datetime.strptime(datos["vencimiento_trial"], "%Y-%m-%d").date()
        if hoy <= venc_trial: esta_en_trial = True
 
    with st.sidebar:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        st.divider()
 
        if es_pro:
            st.markdown(f"""
                <div style="
                    background: rgba(30, 58, 138, 0.12);
                    border: 1px solid rgba(59, 130, 246, 0.20);
                    border-radius: 8px;
                    padding: 12px 14px;
                    margin-bottom: 10px;
                ">
                    <p style="color: #475569; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.09em; font-weight: 500; margin: 0 0 4px 0;">Cuenta</p>
                    <p style="color: #E2E8F0; font-size: 0.88rem; font-weight: 500; margin: 0 0 6px 0;">{datos['usuario']}</p>
                    <span style="
                        display: inline-block;
                        background: rgba(37, 99, 235, 0.18);
                        border: 1px solid rgba(59, 130, 246, 0.30);
                        color: #93C5FD;
                        font-size: 0.7rem;
                        font-weight: 500;
                        padding: 3px 10px;
                        border-radius: 4px;
                        letter-spacing: 0.06em;
                        text-transform: uppercase;
                    ">Plan Pro</span>
                    <p style="color: #334155; font-size: 0.75rem; margin: 8px 0 0 0;">Vigente hasta el {fecha_pro_formateada}</p>
                </div>
            """, unsafe_allow_html=True)
        elif esta_en_trial:
            st.markdown(f"""
                <div style="
                    background: rgba(15, 23, 42, 0.6);
                    border: 1px solid rgba(148, 163, 184, 0.10);
                    border-radius: 8px;
                    padding: 12px 14px;
                    margin-bottom: 10px;
                ">
                    <p style="color: #475569; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.09em; font-weight: 500; margin: 0 0 4px 0;">Cuenta</p>
                    <p style="color: #E2E8F0; font-size: 0.88rem; font-weight: 500; margin: 0 0 6px 0;">{datos['usuario']}</p>
                    <span style="
                        display: inline-block;
                        background: rgba(148, 163, 184, 0.08);
                        border: 1px solid rgba(148, 163, 184, 0.18);
                        color: #64748B;
                        font-size: 0.7rem;
                        font-weight: 500;
                        padding: 3px 10px;
                        border-radius: 4px;
                        letter-spacing: 0.06em;
                        text-transform: uppercase;
                    ">Prueba Gratuita</span>
                    <p style="color: #334155; font-size: 0.75rem; margin: 8px 0 0 0;">Vence el {fecha_trial_formateada}</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style="
                    background: rgba(127, 29, 29, 0.10);
                    border: 1px solid rgba(239, 68, 68, 0.18);
                    border-radius: 8px;
                    padding: 12px 14px;
                    margin-bottom: 10px;
                ">
                    <p style="color: #475569; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.09em; font-weight: 500; margin: 0 0 4px 0;">Cuenta</p>
                    <p style="color: #E2E8F0; font-size: 0.88rem; font-weight: 500; margin: 0 0 6px 0;">{datos['usuario']}</p>
                    <span style="
                        display: inline-block;
                        background: rgba(239, 68, 68, 0.10);
                        border: 1px solid rgba(239, 68, 68, 0.25);
                        color: #F87171;
                        font-size: 0.7rem;
                        font-weight: 500;
                        padding: 3px 10px;
                        border-radius: 4px;
                        letter-spacing: 0.06em;
                        text-transform: uppercase;
                    ">Acceso Expirado</span>
                </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        if not es_pro:
            st.markdown("""
                <div style="
                    border: 1px solid rgba(59, 130, 246, 0.18);
                    border-radius: 8px;
                    padding: 16px;
                    background: rgba(30, 58, 138, 0.06);
                    text-align: center;
                    margin-bottom: 12px;
                ">
                    <p style="color: #60A5FA; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 500; margin: 0 0 6px 0;">Plan Mensual Pro</p>
                    <p style="font-size: 1.3rem; font-weight: 600; color: #E2E8F0; margin: 0;">
                        $6.500
                        <span style="font-size: 0.8rem; font-weight: 300; color: #475569;"> ARS / mes</span>
                    </p>
                    <p style="font-size: 0.77rem; color: #334155; margin: 6px 0 0 0;">Consultas ilimitadas de jurisprudencia.</p>
                </div>
            """, unsafe_allow_html=True)
            st.link_button("Activar Plan Pro", "https://mpago.la/2nDaBRx", type="primary", use_container_width=True)
            st.divider()
 
        if st.button("+ Nueva Consulta", type="primary", use_container_width=True):
            nueva_id = f"Consulta {len(datos['historial']) + 1}"
            datos['historial'][nueva_id] = []
            st.session_state.sesion_actual = nueva_id
            supabase.table("usuarios").update({"historial": datos['historial']}).eq("email", user.email).execute()
            st.rerun()
        
        st.write("") 
        historial = datos.get("historial") or {"Nueva Consulta": []}
        if "sesion_actual" not in st.session_state: st.session_state.sesion_actual = list(historial.keys())[-1]
        
        for chat_id in reversed(list(historial.keys())):
            col_btn, col_del = st.columns([0.8, 0.2])
            with col_btn:
                if st.button(f"{'▶' if chat_id == st.session_state.sesion_actual else '·'}  {chat_id}", key=f"btn_{chat_id}", use_container_width=True):
                    st.session_state.sesion_actual = chat_id
                    st.rerun()
            with col_del:
                if st.button("×", key=f"del_{chat_id}"):
                    del historial[chat_id]
                    st.session_state.sesion_actual = list(historial.keys())[-1] if historial else "Nueva Consulta"
                    supabase.table("usuarios").update({"historial": historial}).eq("email", user.email).execute()
                    st.rerun()
        st.divider()
        
        if st.button("Cerrar Sesión", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.del_tokens = True
            st.session_state.user_data = None
            st.rerun()
            
        st.divider()
        with st.expander("Términos y Condiciones"):
            st.markdown("""
                <div style="font-size: 0.78rem; color: #475569; line-height: 1.7;">
                    <b style="color: #64748B;">Propiedad Intelectual:</b> El software, la base de datos y la marca Chubut.IA son propiedad exclusiva del desarrollador. Queda prohibida la reproducción o ingeniería inversa.<br><br>
                    <b style="color: #64748B;">Responsabilidad:</b> Chubut.IA es una herramienta de asistencia. Los resultados son informativos. La verificación en fuentes oficiales es responsabilidad del profesional.<br><br>
                    <b style="color: #64748B;">Datos Personales:</b> Cumplimos con la Ley 25.326. Sus consultas son confidenciales y cifradas.<br><br>
                    <b style="color: #64748B;">Uso Pro:</b> El acceso es personal e intransferible.
                </div>
            """, unsafe_allow_html=True)
 
        mostrar_disclaimer()
        mostrar_soporte()
 
    chat_actual = historial.get(st.session_state.sesion_actual, [])
    
    if not chat_actual:
        st.markdown(f"""
            <div style="
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 42vh;
                text-align: center;
            ">
                <p style="
                    font-size: 0.8rem;
                    text-transform: uppercase;
                    letter-spacing: 0.18em;
                    color: #3B82F6;
                    font-weight: 500;
                    margin-bottom: 14px;
                ">Bienvenido, {datos['usuario']}</p>
                <h1 style="
                    font-family: 'Playfair Display', serif;
                    font-size: 2.5rem;
                    font-weight: 600;
                    color: #E2E8F0;
                    margin: 0 0 12px 0;
                    line-height: 1.25;
                ">¿En qué puedo asistirte hoy?</h1>
                <p style="
                    font-size: 0.95rem;
                    color: #475569;
                    margin: 0;
                    font-weight: 300;
                ">Jurisprudencia completa de la Provincia de Chubut</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <p style='
                text-align: center;
                color: #334155;
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 500;
                margin: 28px 0 14px 0;
            '>Consultas frecuentes</p>
        """, unsafe_allow_html=True)
 
        st.markdown("<div class='botones-sugerencia'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("⚖️ Fallos sobre cuota alimentaria", key="btn_sug1", use_container_width=True):
            chat_actual.append({"role": "user", "content": "Mostrame fallos recientes sobre cuota alimentaria"})
            historial[st.session_state.sesion_actual] = chat_actual
            supabase.table("usuarios").update({"historial": historial}).eq("email", user.email).execute()
            st.rerun()
        if c2.button("🚗 Jurisprudencia en accidentes de tránsito", key="btn_sug2", use_container_width=True):
            chat_actual.append({"role": "user", "content": "Mostrame jurisprudencia sobre accidentes de tránsito"})
            historial[st.session_state.sesion_actual] = chat_actual
            supabase.table("usuarios").update({"historial": historial}).eq("email", user.email).execute()
            st.rerun()
        c3, c4 = st.columns(2)
        if c3.button("🏢 Fallos por despidos sin causa", key="btn_sug3", use_container_width=True):
            chat_actual.append({"role": "user", "content": "Busca fallos sobre despidos sin causa justificada"})
            historial[st.session_state.sesion_actual] = chat_actual
            supabase.table("usuarios").update({"historial": historial}).eq("email", user.email).execute()
            st.rerun()
        if c4.button("🏥 Mala praxis médica", key="btn_sug4", use_container_width=True):
            chat_actual.append({"role": "user", "content": "Busca fallos relacionados con mala praxis médica"})
            historial[st.session_state.sesion_actual] = chat_actual
            supabase.table("usuarios").update({"historial": historial}).eq("email", user.email).execute()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    else:
        for m in chat_actual:
            with st.chat_message(m["role"]): st.markdown(m["content"])
            
        st.markdown("<div style='height:1px; background: rgba(148,163,184,0.08); margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
        
        pdf_bytes = generar_pdf(chat_actual, st.session_state.sesion_actual)
        st.download_button(
            label="📄 Exportar conversación a PDF",
            data=pdf_bytes,
            file_name=f"Reporte_{st.session_state.sesion_actual}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
 
    if not es_pro and not esta_en_trial:
        st.markdown("""
            <div style="
                text-align: center;
                padding: 28px 24px;
                border: 1px solid rgba(239, 68, 68, 0.15);
                border-radius: 10px;
                background: rgba(127, 29, 29, 0.06);
                margin-top: 20px;
            ">
                <p style="color: #F87171; font-size: 0.9rem; font-weight: 500; margin: 0 0 8px 0;">
                    Tu período de acceso ha finalizado.
                </p>
                <p style="color: #475569; font-size: 0.82rem; margin: 0;">
                    Activá el Plan Pro para continuar consultando jurisprudencia sin límites.
                </p>
            </div>
        """, unsafe_allow_html=True)
    else:
        if prompt := st.chat_input("Consultá sobre jurisprudencia de Chubut..."):
            chat_actual.append({"role": "user", "content": prompt})
            historial[st.session_state.sesion_actual] = chat_actual
            supabase.table("usuarios").update({"historial": historial}).eq("email", user.email).execute()
            st.rerun()
 
        if chat_actual and chat_actual[-1]["role"] == "user":
            with st.chat_message("assistant"):
                with st.spinner("Analizando jurisprudencia..."):
                    docs = vdb.similarity_search(chat_actual[-1]["content"], k=6)
                    contexto_final = "\n\n".join([f"📅 FECHA: {d.metadata.get('fecha_completa')}\n🔗 URL: {d.metadata.get('link_pdf')}\n📄 CONTENIDO:\n{d.page_content}" for d in docs])
                    
                    mensajes = [SystemMessage(content=generar_instruccion_ia(contexto_final))]
                    for m in chat_actual[:-1]:
                        mensajes.append(HumanMessage(content=m["content"]) if m["role"]=="user" else AIMessage(content=m["content"]))
                    mensajes.append(HumanMessage(content=chat_actual[-1]["content"]))
                    
                    respuesta = llm.invoke(mensajes)
                    st.markdown(respuesta.content)
                    chat_actual.append({"role": "assistant", "content": respuesta.content})
                    
                    if st.session_state.sesion_actual.startswith("Consulta ") and len(chat_actual) == 2:
                        try:
                            tit_p = f"Resume esta consulta en 3 o 4 palabras: '{chat_actual[0]['content']}'"
                            nuevo_titulo = llm.invoke([HumanMessage(content=tit_p)]).content.replace('"', '').strip()
                            if nuevo_titulo in historial: nuevo_titulo += " (1)" 
                            historial[nuevo_titulo] = historial.pop(st.session_state.sesion_actual)
                            st.session_state.sesion_actual = nuevo_titulo
                        except: pass
 
                    supabase.table("usuarios").update({"historial": historial}).eq("email", user.email).execute()
                    st.rerun()
 
# ==========================================
# GESTOR CENTRAL DE PANTALLAS (RUTEADOR)
# ==========================================
if st.session_state.user_data is not None:
    pantalla_chat()
elif st.session_state.show_login:
    pantalla_acceso()
else:
    pantalla_invitado()
