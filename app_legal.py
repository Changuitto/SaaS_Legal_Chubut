import os
import streamlit as st
from supabase import create_client, Client
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 1. CONFIGURACIÓN Y CONEXIÓN
st.set_page_config(page_title="Chubut.IA - Legal", page_icon="logo.png", layout="wide")

try:
    # Conexión a OpenAI
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    # Conexión a Supabase
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("🚨 Error en las llaves de configuración. Revisá tus Secrets.")
    st.stop()

# 2. DISEÑO DE BURBUJAS
st.markdown("""
    <style>
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
            background-color: #1E293B !important; border-radius: 20px 20px 20px 2px !important;
            padding: 1.5rem !important; margin-bottom: 1rem !important;
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
            background-color: #1E3A8A !important; border-radius: 20px 20px 2px 20px !important;
            padding: 1.2rem !important; margin-bottom: 1rem !important; margin-left: auto;
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) * { color: white !important; }
    </style>
""", unsafe_allow_html=True)

# 3. ESTADO DE LA SESIÓN
if "user_data" not in st.session_state:
    st.session_state.user_data = None
if "sesiones_chat" not in st.session_state:
    st.session_state.sesiones_chat = {"Nueva Consulta": []}
if "sesion_actual" not in st.session_state:
    st.session_state.sesion_actual = "Nueva Consulta"

# ==========================================
# LÓGICA DE USUARIOS (LOGIN / REGISTRO)
# ==========================================
if st.session_state.user_data is None:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        
        tab_login, tab_registro = st.tabs(["Iniciar Sesión", "Crear Cuenta"])
        
        with tab_login:
            u_login = st.text_input("Usuario", key="u_log")
            p_login = st.text_input("Contraseña", type="password", key="p_log")
            if st.button("Ingresar", type="primary", use_container_width=True):
                res = supabase.table("usuarios").select("*").eq("usuario", u_login).eq("password", p_login).execute()
                if len(res.data) > 0:
                    st.session_state.user_data = res.data[0]
                    st.success(f"Bienvenido {u_login}")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
        
        with tab_registro:
            u_reg = st.text_input("Elegí un Usuario", key="u_reg")
            p_reg = st.text_input("Elegí una Contraseña", type="password", key="p_reg")
            if st.button("Registrarme y empezar prueba", use_container_width=True):
                # Verificamos si ya existe
                existe = supabase.table("usuarios").select("*").eq("usuario", u_reg).execute()
                if len(existe.data) > 0:
                    st.warning("Ese nombre de usuario ya está ocupado.")
                else:
                    nuevo = {"usuario": u_reg, "password": p_reg, "consultas": 3}
                    supabase.table("usuarios").insert(nuevo).execute()
                    st.success("¡Cuenta creada! Ya podés iniciar sesión.")

# ==========================================
# APLICACIÓN PRINCIPAL (CHAT)
# ==========================================
else:
    user = st.session_state.user_data
    # Refrescamos los datos del usuario desde la DB para tener el contador real
    db_user = supabase.table("usuarios").select("*").eq("id", user["id"]).execute().data[0]
    creditos = db_user["consultas"]

    with st.sidebar:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        st.divider()
        st.markdown(f"👤 **{user['usuario']}**")
        
        # EL CONTADOR DE PREGUNTAS
        if creditos > 0:
            st.info(f"🎁 Te quedan **{creditos}** consultas gratis")
        else:
            st.error("🚫 Sin consultas disponibles")
            st.markdown("### 💎 Pasate a Pro")
            st.write("Seguí usando Chubut.IA de forma ilimitada por solo **6,99 USD/mes**.")
            st.button("Pagar Suscripción (Stripe)", use_container_width=True)
        
        st.divider()
        if st.button("➕ Nueva Consulta", use_container_width=True):
            st.session_state.sesion_actual = f"Consulta {len(st.session_state.sesiones_chat)+1}"
            st.session_state.sesiones_chat[st.session_state.sesion_actual] = []
            st.rerun()
        
        st.radio("Historial", list(reversed(st.session_state.sesiones_chat.keys())), key="hist")
        if st.button("Cerrar Sesión"):
            st.session_state.user_data = None
            st.rerun()

    # Lógica de Chat
    st.title("⚖️ Asistente Legal Inteligente")
    historial = st.session_state.sesiones_chat[st.session_state.sesion_actual]

    for m in historial:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if pregunta := st.chat_input("Escribí tu consulta aquí..."):
        if creditos > 0:
            historial.append({"role": "user", "content": pregunta})
            
            with st.chat_message("assistant"):
                # 1. Buscamos en la base de datos (IA)
                # (Aquí iría tu lógica de conectar_boveda y similarity_search que ya tenías)
                respuesta = "Esta es una respuesta simulada. Conectá tu lógica de IA aquí." 
                st.write(respuesta)
                
                # 2. RESTAMOS UN CRÉDITO EN SUPABASE
                nueva_cantidad = creditos - 1
                supabase.table("usuarios").update({"consultas": nueva_cantidad}).eq("id", user["id"]).execute()
                
                historial.append({"role": "assistant", "content": respuesta})
                st.rerun()
        else:
            st.warning("Has agotado tus consultas gratuitas. Por favor, adquiere un plan para continuar.")
