import streamlit as st
from groq import Groq
from supabase import create_client, Client
import base64

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Aluminia Tutor | Green Edition", 
    page_icon="🎓", 
    layout="wide"
)

# --- 2. CONEXIÓN A SUPABASE (SECRETS) ---
@st.cache_resource
def conectar_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Error al conectar con Supabase. Revisa tus Secrets.")
        return None

supabase = conectar_supabase()
# --- FUNCIONES DE PERSISTENCIA ---

def crear_chat_en_db(titulo="Nueva Consulta"):
    """Crea un registro en la tabla 'chats' y devuelve su ID"""
    res = supabase.table("chats").insert({"titulo": titulo}).execute()
    return res.data[0]['id']

def guardar_mensaje_en_db(chat_id, role, content):
    """Guarda cada mensaje vinculado a un chat_id"""
    if chat_id:
        supabase.table("mensajes").insert({
            "chat_id": chat_id,
            "role": role,
            "content": content
        }).execute()

def obtener_historial_chats():
    """Trae la lista de todos los chats para la barra lateral"""
    res = supabase.table("chats").select("*").order("created_at", desc=True).execute()
    return res.data

def obtener_mensajes_del_chat(chat_id):
    """Trae los mensajes de un chat específico al seleccionarlo"""
    res = supabase.table("mensajes").select("*").eq("chat_id", chat_id).order("created_at").execute()
    return res.data
# --- 3. CARGA DE LOGO ---
def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

logo_data = get_base64("logo.png")
LOGO_IMG = f"data:image/png;base64,{logo_data}" if logo_data else "https://cdn-icons-png.flaticon.com/512/3413/3413535.png"

# --- 4. CSS MAESTRO (DARK GREEN + TÍTULO BRILLANTE + SIDEBAR) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* Fondo animado verde oscuro */
    @keyframes gradientBG {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}

    .stApp {{
        background: linear-gradient(-45deg, #051d14, #0a3d2e, #051d14, #020f0a);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        font-family: 'Inter', sans-serif !important;
        color: #ecfdf5;
    }}

    .block-container {{ max-width: 850px; padding-top: 1rem; }}

    /* Efecto de brillo en el título */
    @keyframes glint {{
        0% {{ background-position: -200px; }}
        100% {{ background-position: 200px; }}
    }}

    .aluminia-title {{
        font-weight: 800; text-align: center; font-size: 3.8rem;
        letter-spacing: -3px; margin-bottom: 0px; width: 100%;
        background: linear-gradient(90deg, #10b981 0%, #a7f3d0 50%, #10b981 100%);
        background-size: 200px 100%;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: glint 3s infinite linear;
        text-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
    }}

    .aluminia-sub {{ text-align: center; color: #a7f3d0; font-size: 1.1rem; margin-bottom: 2rem; opacity: 0.8; }}

    /* Burbujas de chat Glassmorphism */
    [data-testid="stChatMessage"] {{
        background: rgba(6, 40, 30, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        border-radius: 20px !important;
    }}

    /* Estilos de Sidebar */
    .sidebar-box {{
        background: rgba(16, 185, 129, 0.05); border-left: 3px solid #10b981;
        padding: 15px; border-radius: 0 15px 15px 0; margin-bottom: 20px;
    }}

    [data-testid="stSidebar"] {{ background-color: #020f0a !important; border-right: 1px solid rgba(16, 185, 129, 0.1); }}

    .stChatInputContainer {{ border-radius: 15px !important; background: #06281e !important; border: 1px solid rgba(16, 185, 129, 0.2) !important; }}
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÓGICA DE PERSISTENCIA (ESTADO INICIAL) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

# --- 6. BARRA LATERAL (DEFINICIÓN DE VARIABLES) ---
with st.sidebar:
    # ... (tus logos y configuraciones anteriores) ...

    st.markdown("### 📜 Historial de Chats")
    
    # Botón para limpiar y empezar de cero
    if st.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_id = None
        st.rerun()

    st.divider()

    # Listar chats desde Supabase
    try:
        chats_viejos = obtener_historial_chats()
        for chat in chats_viejos:
            # Botón estilizado para cada chat previo
            if st.button(f"💬 {chat['titulo'][:20]}...", key=chat['id'], use_container_width=True):
                st.session_state.chat_id = chat['id']
                # Cargar mensajes de ese chat
                mensajes_db = obtener_mensajes_del_chat(chat['id'])
                st.session_state.messages = [
                    {"role": m["role"], "content": m["content"]} for m in mensajes_db
                ]
                st.rerun()
    except:
        st.caption("Aún no hay chats guardados.")
# --- 7. INTERFAZ PRINCIPAL ---
st.markdown('<div class="aluminia-title">ALUMINIA</div>', unsafe_allow_html=True)
st.markdown('<div class="aluminia-sub">Enciende la chispa del conocimiento propio.</div>', unsafe_allow_html=True)

# Mostrar historial
for msg in st.session_state.messages:
    avatar = LOGO_IMG if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- 8. LÓGICA DE INTELIGENCIA (GROQ) ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Falta GROQ_API_KEY en Secrets.")
    st.stop()

client = Groq(api_key=api_key)

if prompt := st.chat_input("¿Qué vamos a descubrir hoy?"):
    # 1. Si es el primer mensaje, creamos el chat en la DB
    if st.session_state.chat_id is None:
        # Usamos las primeras palabras del prompt como título
        titulo_corto = prompt[:30]
        st.session_state.chat_id = crear_chat_en_db(titulo_corto)

    # 2. Guardar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_mensaje_en_db(st.session_state.chat_id, "user", prompt)
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 3. Generar y guardar respuesta de Aluminia
    with st.chat_message("assistant", avatar=LOGO_IMG):
        # ... (aquí va tu lógica de stream actual) ...
        
        # Al terminar el stream, guardamos en DB
        guardar_mensaje_en_db(st.session_state.chat_id, "assistant", full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
