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
    st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="{LOGO_IMG}" width="110" style="border-radius:20px; filter: drop-shadow(0px 0px 15px rgba(16,185,129,0.5));"></div>', unsafe_allow_html=True)
    
    st.markdown("""<div class="sidebar-box"><p style="margin:0; font-size: 0.7rem; color: #a7f3d0;">SISTEMA ACTIVO</p><b>Llama-3.3-70b-Versatile</b></div>""", unsafe_allow_html=True)
    
    st.subheader("🛠️ Configuración")
    # Aquí definimos 'estilo' para que no de NameError
    estilo = st.selectbox("Personalidad:", ["Aluminia Original 💡", "Cercana 👋", "Práctica 🛠️", "Analítica 🔍", "Coach ⚡"])
    
    st.divider()
    
    if st.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_id = None
        st.rerun()
        
    st.divider()
    st.markdown("### 📊 Tu Progreso")
    st.progress(min(len(st.session_state.messages) * 10, 100))

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
    # Guardar mensaje de usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Respuesta del asistente
    with st.chat_message("assistant", avatar=LOGO_IMG):
        full_res = ""
        holder = st.empty()
        
        # System Prompt optimizado
        sys_prompt = f"Eres Aluminia. Estilo: {estilo}. NUNCA des respuestas. Usa el método socrático. Usa LaTeX ($$) para fórmulas. Párrafos cortos y negritas."

        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages,
            stream=True
        )

        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            full_res += content
            holder.markdown(full_res + "▌")
        
        holder.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        
        # Opcional: Aquí llamarías a guardar_mensaje_db(st.session_state.chat_id, ...)
