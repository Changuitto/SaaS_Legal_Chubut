import os
import streamlit as st
from supabase import create_client, Client
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Chubut.IA - Legal", page_icon="logo.png", layout="wide")

# --- CSS PROFESIONAL MEJORADO ---
st.markdown("""
    <style>
        footer {visibility: hidden;}
        
        /* Estilos para los botones de la barra lateral (AHORA TRANSPARENTES Y ELEGANTES) */
        [data-testid="stSidebar"] .stButton>button { 
            width: 100%; 
            border-radius: 8px; 
            text-align: left; 
            padding-left: 10px; 
            background-color: transparent; /* Quita el recuadro blanco */
            border: 1px solid rgba(128, 128, 128, 0.3); /* Borde sutil */
            color: inherit;
            transition: all 0.2s ease-in-out;
        }
        /* Efecto al pasar el mouse */
        [data-testid="stSidebar"] .stButton>button:hover {
            border-color: rgba(128, 128, 128, 0.8);
            background-color: rgba(128, 128, 128, 0.1);
        }
        
        /* Estilos para los mensajes de chat */
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
            border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 20px 20px 20px 2px;
            padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
            background-color: #1E3A8A !important; border-radius: 20px 20px 2px 20px;
            padding: 1.2rem; margin-bottom: 1rem; margin-left: auto;
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) * { color: white !important; }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN A SERVICIOS
try:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception:
    st.error("🚨 Error de configuración en Secrets.")
    st.stop()

# 3. ESTADO DE SESIÓN BÁSICO
if "user_data" not in st.session_state: st.session_state.user_data = None
if "recovery_mode" not in st.session_state: st.session_state.recovery_mode = False

# ==========================================
# LÓGICA DE RECUPERACIÓN
# ==========================================
def pantalla_recuperacion():
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("<h3 style='text-align: center;'>Restablecer Contraseña</h3>", unsafe_allow_html=True)
        st.info("Ingresá tu nueva contraseña para volver a acceder a tu cuenta.")
        
        new_pass = st.text_input("Nueva Contraseña", type="password")
        confirm_pass = st.text_input("Confirmar Nueva Contraseña", type="password")
        
        if st.button("Confirmar Cambio de Contraseña", type="primary", use_container_width=True):
            if new_pass == confirm_pass and len(new_pass) >= 6:
                try:
                    supabase.auth.update_user({"password": new_pass})
                    st.success("¡Contraseña actualizada con éxito!")
                    st.session_state.recovery_mode = False
                    st.session_state.user_data = None
                    st.info("Ya podés iniciar sesión con tu nueva clave.")
                    if st.button("Ir al Inicio"):
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al actualizar: {e}")
            else:
                st.error("Las contraseñas deben coincidir y tener al menos 6 caracteres.")
        
        if st.button("Cancelar"):
            st.session_state.recovery_mode = False
            st.rerun()

# ==========================================
# PANTALLA DE ACCESO
# ==========================================
def pantalla_acceso():
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        st.markdown("<h3 style='text-align: center;'>Acceso al Sistema</h3>", unsafe_allow_html=True)
        tab_in, tab_reg = st.tabs(["🔑 Entrar", "📝 Registrarse"])
        
        with tab_in:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Contraseña", type="password", key="login_pass")
            
            if st.button("¿Olvidaste tu contraseña?", type="secondary"):
                if email:
                    try:
                        supabase.auth.reset_password_email(email)
                        st.success("Te enviamos un correo para recuperar tu contraseña (revisá Spam).")
                    except Exception as e:
                        st.error("Error al enviar el correo.")
                else:
                    st.warning("Escribí tu email arriba para que podamos enviarte el link de recuperación.")
            
            st.write("") 
            if st.button("Iniciar Sesión", type="primary", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user_data = res.user
                    st.rerun()
                except Exception as e:
                    st.error("Credenciales incorrectas o email no confirmado.")

        with tab_reg:
            new_user = st.text_input("Nombre / Estudio", placeholder="Ej: Roman_Juridico")
            new_email = st.text_input("Tu Gmail")
            new_pass = st.text_input("Contraseña", type="password")
            confirm_pass = st.text_input("Confirmar Contraseña", type="password")
            if st.button("Crear Cuenta", use_container_width=True):
                if new_pass != confirm_pass: st.error("Las contraseñas no coinciden.")
                else:
                    try:
                        supabase.auth.sign_up({"email": new_email, "password": new_pass, "options": {"data": {"display_name": new_user}}})
                        st.success("¡Cuenta creada! Revisa tu email (Spam incluido).")
                    except Exception as e: st.error(f"Error: {e}")

# ==========================================
# PANTALLA DE CHAT
# ==========================================
def pantalla_chat():
    user = st.session_state.user_data
    nombre = user.user_metadata.get("display_name", user.email.split("@")[0])
    
    db_res = supabase.table("usuarios").select("*").eq("email", user.email).execute()
    
    if len(db_res.data) == 0:
        historial_db = {"Nueva Consulta": []}
        supabase.table("usuarios").insert({
            "usuario": nombre, "email": user.email, "consultas": 3, "plan": "gratis", "historial": historial_db
        }).execute()
        creditos = 3
        es_pro = False
    else:
        creditos = db_res.data[0]["consultas"]
        es_pro = db_res.data[0].get("plan") == "pro"
        historial_db = db_res.data[0].get("historial") or {"Nueva Consulta": []}

    if "chat_iniciado" not in st.session_state:
        st.session_state.sesiones_chat = historial_db
        st.session_state.sesion_actual = list(historial_db.keys())[-1]
        st.session_state.chat_iniciado = True

    with st.sidebar:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        st.divider()
        st.markdown(f"👤 **{nombre}**")
        
        if es_pro:
            st.warning("💎 **PLAN PRO ACTIVADO**")
        else:
            st.success(f"Consultas restantes: **{creditos}**")
            if creditos <= 0:
                st.error("🚫 Consultas agotadas")
                link_mp = "https://mpago.la/1f481Uj" 
                st.link_button("Suscribirme ahora", link_mp, type="primary", use_container_width=True)

        st.divider()
        if st.button("➕ Nueva Consulta", type="primary", use_
