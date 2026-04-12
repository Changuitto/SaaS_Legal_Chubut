import os
import streamlit as st
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 1. CONFIGURACIÓN PREMIUM
st.set_page_config(
    page_title="Chubut.IA - Legal", 
    page_icon="⚖️", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- CSS PROFESIONAL: BURBUJAS, BARRA LATERAL Y BOTÓN DE MENÚ ---
st.markdown("""
    <style>
        /* Ajustes de fondo y limpieza */
        footer {visibility: hidden;}
        .block-container {padding-top: 1rem; padding-bottom: 5rem;}

        /* Hacer que el botón de la barra lateral sea visible y blanco */
        button[kind="headerNoPadding"] {
            color: white !important;
        }

        /* Burbuja del Asistente (Gris Azulado Profundo) */
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
            background-color: #1E293B !important;
            border: 1px solid #334155 !important;
            border-radius: 20px 20px 20px 2px !important;
            padding: 1.5rem !important;
            margin-bottom: 1.5rem !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            max-width: 85%;
        }
        
        /* Burbuja del Usuario (Azul Vibrant / Corporate) */
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
            background-color: #2563EB !important;
            border-radius: 20px 20px 2px 20px !important;
            padding: 1.2rem !important;
            margin-bottom: 1.5rem !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            max-width: 80%;
            margin-left: auto; /* Empuja el chat del usuario a la derecha */
        }
        
        /* Letras blancas para el usuario */
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) * {
            color: #FFFFFF !important;
        }

        /* Estilo para el input de texto (la caja de abajo) */
        .stChatInputContainer {
            padding-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN A LOS SECRETOS
try:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
except Exception:
    st.error("🚨 Falta la API Key en Streamlit Secrets.")
    st.stop()

CLIENTES_AUTORIZADOS = {
    "roman_admin": "ceo2026",
    "estudio_perez": "abogado123"
}

# 3. CONTROL DE SESIÓN Y MULTI-CHAT
if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = False

if "sesiones_chat" not in st.session_state:
    st.session_state.sesiones_chat = {"Nueva Consulta": []}
if "sesion_actual" not in st.session_state:
    st.session_state.sesion_actual = "Nueva Consulta"

# ==========================================
# PANTALLA DE LOGIN
# ==========================================
if not st.session_state.usuario_autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.write("<br><br>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/6062/6062646.png", width=80)
        st.title("Chubut.IA")
        st.markdown("🔒 **Sistema de Jurisprudencia**")
        st.divider()
        
        usuario_input = st.text_input("Usuario")
        password_input = st.text_input("Contraseña", type="password") 
        
        if st.button("Ingresar", type="primary", use_container_width=True):
            if usuario_input in CLIENTES_AUTORIZADOS and CLIENTES_AUTORIZADOS[usuario_input] == password_input:
                st.session_state.usuario_autenticado = True
                st.rerun()
            else:
                st.error("Acceso denegado.")

# ==========================================
# APLICACIÓN PRINCIPAL
# ==========================================
else:
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("Chubut.IA")
        st.divider()
        
        if st.button("➕ Nueva Consulta", use_container_width=True, type="primary"):
            nuevo_id = len(st.session_state.sesiones_chat) + 1
            nuevo_nombre = f"Consulta {nuevo_id}"
            st.session_state.sesiones_chat[nuevo_nombre] = []
            st.session_state.sesion_actual = nuevo_nombre
            st.rerun()
            
        st.subheader("Historial")
        opciones_chat = list(st.session_state.sesiones_chat.keys())
        chat_seleccionado = st.radio(" ", opciones_chat, index=opciones_chat.index(st.session_state.sesion_actual), label_visibility="collapsed")
        
        if chat_seleccionado != st.session_state.sesion_actual:
            st.session_state.sesion_actual = chat_seleccionado
            st.rerun()
            
        st.divider()
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state.usuario_autenticado = False
            st.rerun()

    # --- LÓGICA DE LA IA ---
    @st.cache_resource
    def conectar_boveda():
        directorio_db = "MI_BASE_VECTORIAL"
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        if not os.path.exists(directorio_db):
            st.error("🚨 Base de datos no encontrada.")
            st.stop()
        vectordb = Chroma(persist_directory=directorio_db, embedding_function=embeddings)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        return vectordb, llm

    try:
        vectordb, llm = conectar_boveda()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        st.stop()

    historial_activo = st.session_state.sesiones_chat[st.session_state.sesion_actual]

    # --- BIENVENIDA O CHAT ---
    if len(historial_activo) == 0:
        st.write("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; font-size: 3rem;'>¿En qué puedo ayudarte hoy?</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.2rem;'>Consultá la jurisprudencia de Chubut con inteligencia artificial.</p>", unsafe_allow_html=True)
    else:
        for mensaje in historial_activo:
            with st.chat_message(mensaje["role"]):
                st.markdown(mensaje["content"])

    # --- INTERACCIÓN ---
    if pregunta := st.chat_input("Escribe tu consulta aquí..."):
        st.session_state.sesiones_chat[st.session_state.sesion_actual].append({"role": "user", "content": pregunta})
        st.rerun() 

    if len(historial_activo) > 0 and historial_activo[-1]["role"] == "user":
        pregunta_actual = historial_activo[-1]["content"]
        
        with st.chat_message("assistant"):
            with st.spinner("Buscando en Chubut.IA..."):
                documentos_relevantes = vectordb.similarity_search(pregunta_actual, k=5)
                contexto_legal = "\n\n".join([doc.page_content for doc in documentos_relevantes])

                instruccion_sistema = f"Sos Chubut.IA. Contexto: {contexto_legal}. Formato: 📌 Carátula, 📅 Fecha, 📝 Cita, ⚖️ Resolución, 🔗 Link."
                
                mensajes_llm = [SystemMessage(content=instruccion_sistema)]
                for msg in historial_activo:
                    role = "user" if msg["role"] == "user" else "assistant"
                    mensajes_llm.append(HumanMessage(content=msg["content"]) if role == "user" else AIMessage(content=msg["content"]))
                
                try:
                    def extraer_texto(stream):
                        for pedacito in stream:
                            yield pedacito.content
                    
                    respuesta_generada = st.write_stream(extraer_texto(llm.stream(mensajes_llm)))
                    st.session_state.sesiones_chat[st.session_state.sesion_actual].append({"role": "assistant", "content": respuesta_generada})
                    
                    st.download_button(
                        label="📄 Descargar Dictamen",
                        data=respuesta_generada,
                        file_name=f"Dictamen_ChubutIA.txt",
                        mime="text/plain",
                        type="secondary",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
