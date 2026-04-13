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
        .stButton>button { width: 100%; border-radius: 10px; text-align: left; padding-left: 15px; }
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
            
            # --- NUEVO: BOTÓN DE OLVIDÉ MI CONTRASEÑA ---
            if st.button("¿Olvidaste tu contraseña?", type="secondary"):
                if email:
                    try:
                        supabase.auth.reset_password_email(email)
                        st.success("Te enviamos un correo para recuperar tu contraseña (revisá Spam).")
                    except Exception as e:
                        st.error("Error al enviar el correo. Verificá que tu email sea correcto.")
                else:
                    st.warning("Por favor, escribí tu email en el cuadro de arriba antes de tocar este botón.")
            
            st.write("") # Espaciador
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
# PANTALLA DE CHAT (LÓGICA PRO INTEGRADA)
# ==========================================
def pantalla_chat():
    user = st.session_state.user_data
    nombre = user.user_metadata.get("display_name", user.email.split("@")[0])
    
    # Consultar DB para ver Plan y Créditos actuales
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

    # --- BARRA LATERAL ---
    with st.sidebar:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        st.divider()
        st.markdown(f"👤 **{nombre}**")
        
        if es_pro:
            st.warning("💎 **PLAN PRO ACTIVADO**")
            st.caption("Tenés acceso ilimitado a todo el sistema.")
        else:
            st.success(f"Consultas restantes: **{creditos}**")
            if creditos <= 0:
                st.error("🚫 Consultas agotadas")
                st.markdown("### 💎 Pasate a Pro")
                st.write("Seguí consultando de forma ilimitada.")
                link_mp = "https://mpago.la/1f481Uj" 
                st.link_button("Suscribirme ahora", link_mp, type="primary", use_container_width=True)

        st.divider()
        st.subheader("Tus Consultas")
        if st.button("➕ Nueva Consulta", type="primary", use_container_width=True):
            nueva_id = f"Consulta {len(st.session_state.sesiones_chat) + 1}"
            st.session_state.sesiones_chat[nueva_id] = []
            st.session_state.sesion_actual = nueva_id
            supabase.table("usuarios").update({"historial": st.session_state.sesiones_chat}).eq("email", user.email).execute()
            st.rerun()

        for nombre_chat in reversed(list(st.session_state.sesiones_chat.keys())):
            prefijo = "🟢" if nombre_chat == st.session_state.sesion_actual else "📄"
            if st.button(f"{prefijo} {nombre_chat}", key=f"btn_{nombre_chat}", use_container_width=True):
                st.session_state.sesion_actual = nombre_chat
                st.rerun()
        
        st.divider()
        if st.button("Cerrar Sesión", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user_data = None
            if "chat_iniciado" in st.session_state: del st.session_state["chat_iniciado"]
            st.rerun()

    # --- CUERPO DEL CHAT ---
    st.title(f"{st.session_state.sesion_actual}")
    
    @st.cache_resource
    def load_ia():
        emb = OpenAIEmbeddings(model="text-embedding-3-small")
        vdb = Chroma(persist_directory="MI_BASE_VECTORIAL", embedding_function=emb)
        return vdb, ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    vdb, llm = load_ia()
    historial_actual = st.session_state.sesiones_chat.get(st.session_state.sesion_actual, [])
    
    for m in historial_actual:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("¿Qué duda legal tenés sobre Chubut?"):
        if creditos > 0 or es_pro:
            historial_actual.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Buscando fallos..."):
                    docs = vdb.similarity_search(prompt, k=4)
                    ctx = "\n\n".join([d.page_content for d in docs])
                    
                    # =======================================================
                    # NUEVO: REGLAS ESTRÍCTAS EN EL PROMPT DEL SISTEMA
                    # =======================================================
                    instruccion_base = f"""Sos Chubut.IA, el asistente jurídico experto de la provincia del Chubut.
Contexto recuperado de la base de datos: {ctx}

REGLAS DE FORMATO PARA TUS RESPUESTAS:
1. VISUALIZACIÓN DE FALLOS: Siempre que el usuario solicite ver, buscar o consultar un fallo específico, DEBES usar OBLIGATORIAMENTE esta estructura visual exacta:

**Título del Fallo:** [Nombre de la carátula o título]
**Fecha:** [Fecha de resolución]
**Cita Textual:** "[Extracto clave o doctrina del fallo]"
**Resumen de los Hechos:** [Descripción concisa del caso]
**Resolución:** [Decisión tomada por el tribunal]
**Enlace al Documento:** https://play.google.com/store/apps/details?id=com.estsoft.alpdf&hl=es_UY

2. ANÁLISIS GENERALES Y OPINIONES: Si el usuario pide un análisis jurídico, una explicación o un debate, responde con texto natural y fluido (párrafos). Si durante ese análisis necesitas citar un fallo, puedes usar la estructura de la Regla 1 para presentarlo, y luego continuar con tu análisis.
"""
                    msgs_ia = [SystemMessage(content=instruccion_base)]
                    # =======================================================

                    for m in historial_actual:
                        role = HumanMessage(content=m["content"]) if m["role"]=="user" else AIMessage(content=m["content"])
                        msgs_ia.append(role)
                    
                    res = llm.invoke(msgs_ia)
                    st.markdown(res.content)
                    historial_actual.append({"role": "assistant", "content": res.content})
                    
                    # --- LÓGICA DE GASTO DE CRÉDITOS ---
                    nuevo_conteo = creditos if es_pro else creditos - 1
                    
                    # Renombrar chat si es el primero
                    sesion_vieja = st.session_state.sesion_actual
                    if sesion_vieja.startswith("Consulta ") and len(historial_actual) == 2:
                        try:
                            tit_p = f"Resume esto en 3 palabras: {prompt}"
                            nuevo_titulo = llm.invoke([HumanMessage(content=tit_p)]).content.replace('"', '').strip()
                            st.session_state.sesiones_chat[nuevo_titulo] = st.session_state.sesiones_chat.pop(sesion_vieja)
                            st.session_state.sesion_actual = nuevo_titulo
                        except: pass
                    else:
                        st.session_state.sesiones_chat[st.session_state.sesion_actual] = historial_actual

                    # Guardar todo en Supabase
                    supabase.table("usuarios").update({
                        "consultas": nuevo_conteo,
                        "historial": st.session_state.sesiones_chat
                    }).eq("email", user.email).execute()
                    st.rerun()
        else:
            st.error("No te quedan consultas. Suscribite al plan Pro para continuar.")

# --- ARRANQUE ---
if st.session_state.user_data is None: pantalla_acceso()
else: pantalla_chat()
