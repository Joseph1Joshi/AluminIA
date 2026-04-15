import streamlit as st
from groq import Groq
from supabase import create_client, Client
import base64
from pypdf import PdfReader

def cargar_prompt(archivo):
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Eres un asistente útil." # Fallback por si el archivo se borra


def procesar_archivo(archivo_subido):
    texto_total = ""
    try:
        if archivo_subido.name.endswith('.pdf'):
            pdf_reader = PdfReader(archivo_subido)
            for page in pdf_reader.pages:
                texto_total += page.extract_text() + "\n"
        elif archivo_subido.name.endswith('.txt'):
            texto_total = archivo_subido.read().decode("utf-8")
        return texto_total
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return ""
        
# --- 1. CONFIGURACIÓN ---

# Si tu logo es un archivo .png o .ico, puedes pasarlo directamente aquí
st.set_page_config(
    page_title="Aluminia", 
    page_icon="logo.png", # <--- Aquí pones tu archivo
    layout="wide", 
    initial_sidebar_state="expanded"
)
# --- 2. CONEXIÓN SUPABASE ---
@st.cache_resource
def conectar_supabase():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None

supabase = conectar_supabase()

# --- 3. FUNCIONES DB ---
def crear_chat_en_db(titulo, user_id):
    try:
        res = supabase.table("chats").insert({"titulo": titulo, "user_id": user_id}).execute()
        return res.data[0]['id']
    except: return None

def guardar_mensaje_en_db(chat_id, role, content):
    if chat_id:
        try: supabase.table("mensajes").insert({"chat_id": chat_id, "role": role, "content": content}).execute()
        except: pass

def obtener_historial_chats(user_id):
    try: return supabase.table("chats").select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data
    except: return []

def obtener_mensajes_del_chat(chat_id):
    try: return supabase.table("mensajes").select("*").eq("chat_id", chat_id).order("created_at").execute().data
    except: return []

def borrar_chat_db(chat_id):
    try:
        supabase.table("mensajes").delete().eq("chat_id", chat_id).execute()
        supabase.table("chats").delete().eq("id", chat_id).execute()
        return True
    except: return False


# --- 4. ASSETS (NUEVO: INTEGRACIÓN DE TU LOGO) ---
def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f: return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        # Si no encuentra el archivo, no se rompe la app, usa un fallback
        return None 

# REEMPLAZA "logo.png" CON EL NOMBRE REAL DE TU ARCHIVO (ej: "mi_logo_final.png")
# El archivo debe estar en la misma carpeta que app.py
nombre_archivo_logo = "logo.png" 

logo_data = get_base64(nombre_archivo_logo)

# Si hay datos, crea la URI Base64; si no, usa el icono de fallback
if logo_data:
    # Si tu logo es JPG, cambia 'png' por 'jpeg'
    LOGO_IMG = f"data:image/png;base64,{logo_data}" 
else:
    LOGO_IMG = "https://cdn-icons-png.flaticon.com/512/3413/3413535.png" # Fallback
# --- 5. INICIALIZACIÓN DE ESTADOS (BASE DE DATOS EN MEMORIA) ---
if "user" not in st.session_state: st.session_state.user = None
if "messages" not in st.session_state: st.session_state.messages = []
if "chat_id" not in st.session_state: st.session_state.chat_id = None

# --- 5. CSS MAESTRO (VERSION VIBRANTE & GLOW - PARCHADA) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&family=JetBrains+Mono&display=swap');
    
    /* 1. FONDO CON PROFUNDIDAD RADIAL */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMainViewContainer"] {{
        background: radial-gradient(circle at top center, #06281e 0%, #020f0a 100%) !important;
        color: #ecfdf5;
        font-family: 'Inter', sans-serif;
        overscroll-behavior: none !important;
    }}

    /* 2. HEADER TOTALMENTE INVISIBLE */
    header[data-testid="stHeader"] {{
        background-color: rgba(0,0,0,0) !important;
    }}

    /* 3. TÍTULO METALIZADO CON PULSO DE NEÓN */
    @keyframes pulse-glow {{
        0% {{ filter: drop-shadow(0 0 10px rgba(16, 185, 129, 0.4)); }}
        50% {{ filter: drop-shadow(0 0 25px rgba(16, 185, 129, 0.7)); }}
        100% {{ filter: drop-shadow(0 0 10px rgba(16, 185, 129, 0.4)); }}
    }}

    .aluminia-metal {{
        font-family: 'Inter', sans-serif; 
        font-weight: 900; 
        font-size: clamp(2.5rem, 10vw, 4.5rem); 
        text-align: center;
        background: linear-gradient(to bottom, #cfd8dc, #90a4ae, #ffffff, #546e7a, #b0bec5);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
        animation: pulse-glow 3s infinite ease-in-out;
        margin-bottom: 15px;
        letter-spacing: -2px;
    }}

    /* 4. BURBUJAS DE CHAT CON EFECTO CRISTAL (GLASSMORPHISM) */
    [data-testid="stChatMessage"] {{ 
        background-color: rgba(6, 40, 30, 0.4) !important; 
        backdrop-filter: blur(10px);
        border-radius: 20px !important; 
        border: 1px solid rgba(16, 185, 129, 0.2) !important; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 15px !important;
        transition: transform 0.2s ease;
    }}
    
    [data-testid="stChatMessage"]:hover {{
        transform: translateY(-2px);
        border: 1px solid rgba(16, 185, 129, 0.5) !important;
    }}

    /* 5. RESPLANDOR ESPECIAL PARA EL ASISTENTE (ALUMINIA) */
    [data-testid="stChatMessage"][data-testid="stChatMessageAssistant"] {{
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.15);
        border-right: 2px solid rgba(16, 185, 129, 0.4) !important;
    }}

    /* 6. SIDEBAR ESTILO CYBER */
    [data-testid="stSidebar"] {{ 
        background-color: #010805 !important; 
        border-right: 1px solid #10b98144; 
        box-shadow: 5px 0 25px rgba(0,0,0,0.5);
    }}

    /* 7. BOTONES NEÓN */
    .stButton>button {{
        background-color: rgba(16, 185, 129, 0.1) !important;
        color: #10b981 !important;
        border: 1px solid #10b981 !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 1px;
    }}

    .stButton>button:hover {{
        background-color: #10b981 !important;
        color: #020f0a !important;
        box-shadow: 0 0 20px #10b981;
        transform: scale(1.02);
    }}

    /* Ajuste de márgenes para Móviles */
    @media (max-width: 768px) {{
        .block-container {{
            padding-top: 1.5rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }}
        .aluminia-metal {{ font-size: 2.2rem !important; }}
    }}

    .author-badge {{ 
        position: fixed; 
        bottom: 20px; 
        right: 20px; 
        color: #10b981; 
        font-size: 0.65rem; 
        text-transform: uppercase;
        letter-spacing: 2px;
        background: rgba(6, 40, 30, 0.8); 
        padding: 8px 15px; 
        border-radius: 5px; 
        border-left: 2px solid #10b981;
        z-index: 99; 
    }}

    /* --- BOTÓN FLOTANTE DE "+" (PARCHADO CON LLAVES DOBLES) --- */
    .stPopover > button {{
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        padding: 0px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: 1px solid #10b981 !important;
        background: rgba(16, 185, 129, 0.1) !important;
        color: #10b981 !important;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);
        transition: all 0.3s ease;
    }}

    .stPopover > button:hover {{
        background: #10b981 !important;
        color: #020f0a !important;
        box-shadow: 0 0 20px #10b981;
        transform: rotate(90deg);
    }}
    </style>
    """, unsafe_allow_html=True)
# --- 7. SISTEMA DE LOGIN Y REGISTRO ---
if st.session_state.user is None:
    st.markdown('<div style="margin-top:10vh;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="aluminia-metal">ALUMINIA</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #10b981; margin-top: -15px; font-weight: 700;'>De Joseph Torifio</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
    with col2:
        t1, t2 = st.tabs(["Ingresar", "Unirse"])
        with t1:
            e = st.text_input("Email", key="l_email")
            p = st.text_input("Password", type="password", key="l_pass")
            if st.button("Entrar", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": e, "password": p})
                    st.session_state.user = res.user
                    st.rerun()
                except: st.error("Intenta Nuevamente")
        with t2:
            re = st.text_input("Nuevo Email", key="r_email")
            rp = st.text_input("Nueva Password", type="password", key="r_pass")
            if st.button("Crear Cuenta", use_container_width=True):
                try:
                    auth_res = supabase.auth.sign_up({"email": re, "password": rp})
                    if auth_res:
                        st.success("¡Cuenta creada! Ya puedes ingresar.")
                        st.balloons()
                except: st.error("Error al registrar")
    st.stop()

# --- 8. SIDEBAR (REDiseño VIBRANTE) ---
with st.sidebar:
    # Logo con resplandor intenso
    st.markdown(f"""
        <div style="text-align:center; padding: 20px 0;">
            <img src="{LOGO_IMG}" width="100" style="filter: drop-shadow(0 0 20px rgba(16, 185, 129, 0.5));">
            <p style="color: #10b981; font-family: 'JetBrains Mono'; font-size: 0.6rem; margin-top: 10px; opacity: 0.6;">SYSTEM VERSION 2.1.0</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("➕ NUEVA SESIÓN", use_container_width=True):
        st.session_state.messages = []; st.session_state.chat_id = None; st.rerun()
    # --- 8. SIDEBAR (CON CARGA DE DOCUMENTOS) ---
with st.sidebar:
    # ... (Tu logo y botones anteriores) ...

    st.markdown("<h3>📂 Memoria Externa</h3>", unsafe_allow_html=True)
    archivo = st.file_uploader("Sube apuntes (PDF/TXT)", type=["pdf", "txt"], label_visibility="collapsed")
    
    if archivo:
        with st.spinner("Analizando documento..."):
            contenido = procesar_archivo(archivo)
            if contenido:
                st.session_state.contexto_documento = contenido
                st.success(f"✅ {archivo.name} cargado")
    else:
        st.session_state.contexto_documento = "" # Limpiar si no hay archivo
    st.markdown("<br><h3>Historial de Enlaces</h3>", unsafe_allow_html=True)
    
    # Contenedor de chats
    chats = obtener_historial_chats(st.session_state.user.id)
    for c in chats:
        cols = st.columns([0.85, 0.15])
        with cols[0]:
            # El botón de chat ahora tiene el efecto de desplazamiento (hover) definido en CSS
            if st.button(f"⚡ {c['titulo'][:18]}...", key=f"c_{c['id']}", use_container_width=True):
                st.session_state.chat_id = c['id']
                m_db = obtener_mensajes_del_chat(c['id'])
                st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in m_db]
                st.rerun()
        with cols[1]:
            # Botón de borrar minimalista
            if st.button("×", key=f"d_{c['id']}", help="Eliminar registro"):
                if borrar_chat_db(c['id']):
                    if st.session_state.chat_id == c['id']:
                        st.session_state.messages = []; st.session_state.chat_id = None
                    st.rerun()
    
    # Pie de la Sidebar
    st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True) # Espaciador
    st.divider()
    if st.button("🔌 DESCONECTAR SISTEMA", use_container_width=True):
        supabase.auth.sign_out(); st.session_state.user = None; st.rerun()

# --- 9. INTERFAZ DE CHAT ---
st.markdown('<div class="aluminia-metal" style="font-size:1.8rem; text-align:left;">ALUMINIA</div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=LOGO_IMG if msg["role"] == "assistant" else "👤"):
        if "[DEBUG_SESSION]" in msg["content"]:
            st.markdown(f'<div class="debug-response">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(msg["content"])
# --- 10. MOTOR DE IA (VERSIÓN CON BLOQUEO DE DOBLE SENTIDO) ---

# 1. Interfaz de Carga (Simplificada para evitar triggers falsos)
with st.container():
    col_btn, _ = st.columns([0.2, 0.8])
    with col_btn:
        with st.popover("＋ Subir"):
            archivo_adjunto = st.file_uploader(
                "Documento", 
                type=["pdf", "txt"], 
                key="chat_uploader_definitivo"
            )
            
            # Solo procesamos si el archivo existe y NO ha sido marcado como "leído"
            if archivo_adjunto:
                file_key = f"leido_{archivo_adjunto.name}"
                if not st.session_state.get(file_key, False):
                    with st.spinner("Sincronizando..."):
                        texto = procesar_archivo(archivo_adjunto)
                        if texto:
                            # 1. Guardamos el contenido
                            st.session_state.contexto_documento = texto
                            # 2. Marcamos este archivo específico como ya procesado
                            st.session_state[file_key] = True 
                            # 3. Añadimos mensaje de sistema al historial
                            msg_sistema = {
                                "role": "assistant", 
                                "content": f"📝 He memorizado **{archivo_adjunto.name}**. ¿Qué quieres analizar?"
                            }
                            st.session_state.messages.append(msg_sistema)
                            # 4. Forzamos el guardado y reinicio único
                            st.rerun()

# 2. Input de Chat (Anclado al fondo)
prompt = st.chat_input("Plantea tu duda...")

# 3. Lógica de IA (Solo se ejecuta si el usuario escribe algo)
if prompt:
    # Evitar que el prompt se procese dos veces si el usuario hace doble clic
    if "last_prompt" in st.session_state and st.session_state.last_prompt == prompt:
        st.stop()
    
    st.session_state.last_prompt = prompt

    if st.session_state.chat_id is None:
        st.session_state.chat_id = crear_chat_en_db(prompt[:30], st.session_state.user.id)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_mensaje_en_db(st.session_state.chat_id, "user", prompt)

    # Preparación de Contexto RAG
    MODELO = "llama-3.3-70b-versatile"
    raw_instructions = cargar_prompt("instrucciones.txt")
    contexto = ""
    if st.session_state.get("contexto_documento"):
        contexto = f"\n\n[CONTEXTO]:\n{st.session_state.contexto_documento[:15000]}\n---"
    
    SYSTEM_PROMPT = raw_instructions.replace("{MODELO}", MODELO).replace("{TEMP}", "0.6") + contexto

    # Respuesta Visual (Streaming)
    with st.chat_message("assistant", avatar=LOGO_IMG):
        full_res = ""
        holder = st.empty()
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            stream = client.chat.completions.create(
                model=MODELO,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages[-10:],
                temperature=0.6,
                stream=True
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                full_res += content
                holder.markdown(full_res + "▌")
            holder.markdown(full_res)
        except Exception as e:
            st.error(f"Error de conexión: {e}")
            full_res = "Hubo un hipo en la red."

    # Guardado y Rerun final
    st.session_state.messages.append({"role": "assistant", "content": full_res})
    guardar_mensaje_en_db(st.session_state.chat_id, "assistant", full_res)
    st.rerun()
