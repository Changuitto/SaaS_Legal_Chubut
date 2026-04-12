import os
import streamlit as st
from supabase import create_client, Client
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Chubut.IA - Legal", page_icon="logo.png", layout="wide")

# --- CSS PROFESIONAL ---
st.markdown("""
    <style>
        footer {visibility: hidden;}
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

# 3. ESTADO DE SESIÓN
if "user_data" not in st.session_state: st.session_state.user_data = None
if "sesiones_chat" not in st.session_state: st.session_state.sesiones_chat = {"Nueva Consulta": []}
if "sesion_actual" not in st.session_state: st.session_state.sesion_actual = "Nueva Consulta"

# ==========================================
# FUNCIONES DE AUTENTICACIÓN
# ==========================================
def login_screen():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        st.markdown("<h3 style='text-align: center;'>Acceso al Sistema</h3>", unsafe_allow_html=True)
        
        tab_in, tab_reg = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
        
        with tab_in:
            email = st.text_input("Email", key="li_email")
            password = st.text_input("Contraseña", type="password", key="li_pass")
            if st.button("Entrar", type="primary", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user_data = res.user
                    st.rerun()
                except:
                    st.error("Credenciales incorrectas.")
            
            if st.button("¿Olvidaste tu contraseña?", variant="ghost"):
                if email:
                    supabase.auth.reset_password_for_email(email)
                    st.info(f"Se envió un enlace de recuperación a {email}")
                else:
                    st.warning("Ingresá tu email primero.")

        with tab_reg:
            new_user = st.text_input("Nombre de Usuario / Estudio")
            new_email = st.text_input("Correo Electrónico")
            new_pass = st.text_input("Contraseña", type="password")
            confirm_pass = st.text_input("Confirmar Contraseña", type="password")
            
            if st.button("Crear Cuenta Gratis", use_container_width=True):
                if new_pass != confirm_pass:
                    st.error("Las contraseñas no coinciden.")
                elif len(new_pass) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres.")
                elif not new_user or "@" not in new_email:
                    st.error("Completá todos los campos correctamente.")
                else:
                    try:
                        # Registro oficial en Supabase con metadata
                        res = supabase.auth.sign_up({
                            "email": new_email, 
                            "password": new_pass,
                            "options": {"data": {"display_name": new_user}}
                        })
                        st.success("¡Cuenta creada! Ya podés iniciar sesión.")
                    except Exception as e:
                        st.error(f"Error: {e}")

# ==========================================
# INTERFAZ DE CHAT IA
# ==========================================
def chat_screen():
    user = st.session_state.user_data
    # Obtenemos el nombre de usuario de la metadata o el email
    display_name = user.user_metadata.get("display_name", user.email.split("@")[0])
    
    # Manejo de créditos (Sincronización con tabla 'usuarios')
    db_res = supabase.table("usuarios").select("*").eq("email", user.email).execute()
    if len(db_res.data) == 0:
        # Si no existe en la tabla de créditos, lo creamos
        supabase.table("usuarios").insert({"usuario": display_name, "email": user.email, "consultas": 3, "password": "AUTH_USER"}).execute()
        creditos = 3
    else:
        creditos = db_res.data[0]["consultas"]

    with st.sidebar:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        st.divider()
        st.markdown(f"👤 **{display_name}**")
        
        if creditos > 0:
            st.success(f"🎁 Consultas gratis: **{creditos}**")
        else:
            st.error("🚫 Consultas agotadas")
            st.markdown("### 💎 Plan Pro")
            st.write("Acceso ilimitado por **6,99 USD/mes**.")
            st.button("Pagar con Mercado Pago", type="primary", use_container_width=True)
        
        st.divider()
        if st.button("➕ Nueva Consulta", use_container_width=True):
            st.session_state.sesion_actual = f"Consulta {len(st.session_state.sesiones_chat)+1}"
            st.session_state.sesiones_chat[st.session_state.sesion_actual] = []
            st.rerun()
            
        if st.button("Cerrar Sesión", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user_data = None
            st.rerun()

    # --- LÓGICA DE IA (RAG) ---
    @st.cache_resource
    def get_ai():
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectordb = Chroma(persist_directory="MI_BASE_VECTORIAL", embedding_function=embeddings)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        return vectordb, llm

    vectordb, llm = get_ai()
    
    historial = st.session_state.sesiones_chat[st.session_state.sesion_actual]
    for m in historial:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if pregunta := st.chat_input("Hacé tu consulta legal..."):
        if creditos > 0:
            historial.append({"role": "user", "content": pregunta})
            with st.chat_message("user"): st.markdown(pregunta)
            
            with st.chat_message("assistant"):
                with st.spinner("Analizando jurisprudencia..."):
                    docs = vectordb.similarity_search(pregunta, k=4)
                    contexto = "\n\n".join([d.page_content for d in docs])
                    sys_msg = f"Sos Chubut.IA. Contexto: {contexto}. Formato: 📌 Carátula, 📅 Fecha, 📝 Cita, ⚖️ Resolución."
                    
                    # Generar respuesta
                    res_ai = llm.invoke([SystemMessage(content=sys_msg), HumanMessage(content=pregunta)])
                    st.markdown(res_ai.content)
                    
                    # Guardar y descontar crédito
                    historial.append({"role": "assistant", "content": res_ai.content})
                    supabase.table("usuarios").update({"consultas": creditos - 1}).eq("email", user.email).execute()
                    st.rerun()
        else:
            st.warning("Por favor, adquirí el plan Pro para continuar consultando.")

# MAIN
if st.session_state.user_data is None:
    login_screen()
else:
    chat_screen()
