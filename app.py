import streamlit as st
from groq import Groq
from supabase import create_client, Client
import base64

def cargar_prompt(archivo):
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Eres un asistente útil." # Fallback por si el archivo se borra
# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Aluminia AI", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

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

# --- 5. CSS MAESTRO ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&family=JetBrains+Mono&display=swap');
    
    /* BLOQUE DE CONTENCIÓN TOTAL (OVERSCROLL FIX) */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMainViewContainer"] {{
        background-color: #020f0a !important;
        color: #ecfdf5;
        font-family: 'Inter', sans-serif;
        overscroll-behavior: none !important; /* Detiene el rebote elástico */
    }}

    /* HEADER TRANSPARENTE */
    header[data-testid="stHeader"] {{
        background-color: rgba(0,0,0,0) !important;
    }}

    .stApp {{ 
        background-color: #020f0a !important; 
    }}
    
    .aluminia-metal {{
        font-family: 'Inter', sans-serif; 
        font-weight: 900; 
        font-size: clamp(2rem, 8vw, 4rem); 
        text-align: center;
        background: linear-gradient(to bottom, #cfd8dc, #90a4ae, #ffffff, #546e7a, #b0bec5);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 10px rgba(16, 185, 129, 0.3));
        margin-bottom: 10px;
    }}

    .debug-response {{
        font-family: 'JetBrains Mono', monospace; 
        background-color: #000 !important;
        border-left: 3px solid #10b981 !important; 
        padding: 15px !important;
        color: #10b981 !important; 
        font-size: 0.85rem; 
        border-radius: 5px;
    }}

    [data-testid="stChatMessage"] {{ 
        background-color: rgba(6, 40, 30, 0.5) !important; 
        border-radius: 20px !important; 
        border: 1px solid rgba(16, 185, 129, 0.1) !important; 
    }}
    
    [data-testid="stSidebar"] {{ 
        background-color: #010805 !important; 
        border-right: 1px solid #10b98122; 
    }}

    /* Ajuste de márgenes para Móviles */
    @media (max-width: 768px) {{
        .block-container {{
            padding-top: 2rem !important;
            padding-bottom: 1rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }}
        
        .aluminia-metal {{
            font-size: 1.8rem !important;
            margin-bottom: 5px !important;
        }}
    }}

    .author-badge {{ 
        position: fixed; 
        bottom: 20px; 
        right: 20px; 
        color: #10b981; 
        font-size: 0.75rem; 
        font-weight: 800; 
        background: rgba(6, 40, 30, 0.7); 
        padding: 6px 15px; 
        border-radius: 20px; 
        z-index: 99; 
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

# --- 8. SIDEBAR (HISTORIAL) ---
with st.sidebar:
    st.markdown(f'<div style="text-align:center;"><img src="{LOGO_IMG}" width="80"></div>', unsafe_allow_html=True)
    if st.button("➕ Nuevo Diálogo", use_container_width=True):
        st.session_state.messages = []; st.session_state.chat_id = None; st.rerun()
    
    st.divider()
    st.markdown("### 📜 Historial")
    chats = obtener_historial_chats(st.session_state.user.id)
    for c in chats:
        c1, c2 = st.columns([0.8, 0.2])
        with c1:
            if st.button(f"💬 {c['titulo'][:15]}", key=f"c_{c['id']}", use_container_width=True):
                st.session_state.chat_id = c['id']
                m_db = obtener_mensajes_del_chat(c['id'])
                st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in m_db]
                st.rerun()
        with c2:
            if st.button("🗑️", key=f"d_{c['id']}"):
                if borrar_chat_db(c['id']):
                    if st.session_state.chat_id == c['id']:
                        st.session_state.messages = []; st.session_state.chat_id = None
                    st.rerun()
    
    st.divider()
    if st.button("🚪 Salir", use_container_width=True):
        supabase.auth.sign_out(); st.session_state.user = None; st.rerun()

# --- 9. INTERFAZ DE CHAT ---
st.markdown('<div class="aluminia-metal" style="font-size:1.8rem; text-align:left;">ALUMINIA</div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=LOGO_IMG if msg["role"] == "assistant" else "👤"):
        if "[DEBUG_SESSION]" in msg["content"]:
            st.markdown(f'<div class="debug-response">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(msg["content"])

# --- 10. MOTOR DE IA (PROMPT EXTERNALIZADO) ---
if prompt := st.chat_input("Plantea tu duda..."):
    # 1. Mostrar mensaje del usuario
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    # 2. Inicializar Chat en DB si es nuevo
    if st.session_state.chat_id is None:
        st.session_state.chat_id = crear_chat_en_db(prompt[:30], st.session_state.user.id)
    
    # 3. Guardar en memoria y en Supabase
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_mensaje_en_db(st.session_state.chat_id, "user", prompt)

    # 4. Parámetros Técnicos
    MODELO = "llama-3.3-70b-versatile"
    TEMP = 0.6

    # 5. Carga Dinámica del Sistema (Desde instrucciones.txt)
    # Usamos .replace para evitar conflictos con llaves {} accidentales en el texto
    raw_prompt = cargar_prompt("instrucciones.txt")
    SYSTEM_PROMPT = raw_prompt.replace("{MODELO}", MODELO).replace("{TEMP}", str(TEMP))

    # 6. Generación de Respuesta (Streaming)
    with st.chat_message("assistant", avatar=LOGO_IMG):
        full_res = ""
        holder = st.empty()
        
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            stream = client.chat.completions.create(
                model=MODELO,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages[-10:],
                temperature=TEMP,
                stream=True
            )
            
            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                full_res += content
                holder.markdown(full_res + "▌")
            
            holder.markdown(full_res)
            
        except Exception as e:
            st.error(f"Error de conexión con el motor: {e}")
            full_res = "Lo siento, hubo un hipo técnico. ¿Podemos intentarlo de nuevo?"
            holder.markdown(full_res)
    
    # 7. Persistencia de la Respuesta
    st.session_state.messages.append({"role": "assistant", "content": full_res})
    guardar_mensaje_en_db(st.session_state.chat_id, "assistant", full_res)
