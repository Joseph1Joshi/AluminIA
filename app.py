import streamlit as st
from groq import Groq
import wikipedia
import base64
from supabase import create_client, Client

# --- CONEXIÓN INVISIBLE CON SUPABASE ---
@st.cache_resource # Esto evita que se conecte mil veces y sea más rápido
def conectar_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = conectar_supabase()

# --- FUNCIONES MAESTRAS DE ALUMINIA ---

def crear_nuevo_chat_db(titulo="Nueva Exploración"):
    # Crea un chat y nos devuelve su ID único
    res = supabase.table("chats").insert({"titulo": titulo}).execute()
    return res.data[0]['id']

def guardar_mensaje_db(chat_id, role, content):
    # Guarda cada frase del usuario o de Aluminia
    supabase.table("mensajes").insert({
        "chat_id": chat_id,
        "role": role,
        "content": content
    }).execute()

def cargar_mensajes_de_chat(chat_id):
    # Trae los mensajes viejos cuando cambias de chat
    res = supabase.table("mensajes").select("*").eq("chat_id", chat_id).order("created_at").execute()
    return res.data
# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Aluminia Tutor | Green Edition", 
    page_icon="🎓", 
    layout="wide"
)

# --- 2. CARGA DE LOGO ---
def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

logo_data = get_base64("logo.png")
LOGO_IMG = f"data:image/png;base64,{logo_data}" if logo_data else "https://cdn-icons-png.flaticon.com/512/3413/3413535.png"

# --- 3. CSS MAESTRO (GREEN DARK MODE CON TÍTULO CON BRILLOS) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* Fondo animado en tonos verdes oscuros */
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
        color: #e2e8f0;
    }}

    /* Contenedor principal */
    .block-container {{
        max-width: 850px;
        padding-top: 1rem;
        padding-bottom: 6rem;
    }}

    /* --- EFECTO DE BRILLO EN EL TÍTULO --- */
    @keyframes glint {{
        0% {{ background-position: -200px; }}
        100% {{ background-position: 200px; }}
    }}

    .aluminia-title {{
        font-weight: 800;
        text-align: center;
        font-size: 3.8rem;
        letter-spacing: -3px;
        margin-bottom: 0px;
        position: relative;
        display: inline-block;
        width: 100%;
        
        /* Color base verde neón */
        color: #10b981;
        
        /* Efecto de brillo que recorre el texto */
        background: linear-gradient(90deg, #10b981 0%, #a7f3d0 50%, #10b981 100%);
        background-size: 200px 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: glint 3s infinite linear;
        
        /* Brillo neón de fondo (Glow) */
        text-shadow: 0 0 15px rgba(16, 185, 129, 0.6), 0 0 30px rgba(16, 185, 129, 0.4);
    }}

    .aluminia-sub {{
        text-align: center;
        color: #a7f3d0;
        font-size: 1.2rem;
        margin-bottom: 2.5rem;
        font-weight: 600;
        text-shadow: 0 0 5px rgba(16, 185, 129, 0.5);
    }}

    /* Burbujas Glassmorphism Verdes (Cristal Esmeralda Ahumado) */
    [data-testid="stChatMessage"] {{
        background: rgba(6, 40, 30, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        border-radius: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4) !important;
        margin-bottom: 1rem !important;
    }}

    /* Texto dentro de las burbujas */
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {{
        color: #ecfdf5 !important;
    }}

    /* Input de Chat adaptado al verde */
    .stChatInputContainer {{
        border-radius: 15px !important;
        background: #06281e !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
    }}
    
    .stChatInputContainer textarea {{
        color: white !important;
    }}

    /* Barra lateral verde */
    [data-testid="stSidebar"] {{
        background-color: #020f0a !important;
        border-right: 1px solid rgba(16, 185, 129, 0.2);
    }}
    
    /* Títulos en la sidebar en verde */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
        color: #10b981 !important;
    }}

    /* Botones de Streamlit customizados en verde */
    .stButton>button {{
        background-color: transparent;
        border: 2px solid #10b981;
        color: #10b981;
        border-radius: 10px;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        background-color: #10b981;
        color: white;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.5);
    }}

    /* Ocultar elementos innecesarios */
    footer {{visibility: hidden;}}
    header {{background: transparent !important;}}
    [data-testid="stHeader"] {{background: none !important;}}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<div style="text-align:center"><img src="{LOGO_IMG}" width="100" style="border-radius:15px; filter: drop-shadow(0px 0px 15px rgba(16,185,129,0.7));"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>Configuración</h2>", unsafe_allow_html=True)
    estilo = st.selectbox("Personalidad Socrática:", ["Aluminia Original 💡", "Cercana 👋", "Práctica 🛠️", "Analítica 🔍", "Coach ⚡"])
    if st.button("🗑️ Reiniciar Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 5. INTERFAZ ---
# Título con el efecto de brillo animado
st.markdown('<div class="aluminia-title">ALUMINIA</div>', unsafe_allow_html=True)
st.markdown('<div class="aluminia-sub">Enciende la chispa del conocimiento.</div>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    avatar = LOGO_IMG if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- 6. LÓGICA ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Por favor, añade tu GROQ_API_KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)

if prompt := st.chat_input("¿Qué duda exploramos hoy?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=LOGO_IMG):
        full_res = ""
        holder = st.empty()
        
        # El System Prompt se adapta a la temática
        sys_prompt = f"Eres Aluminia, versión neón esmeralda. Estilo: {estilo}. NUNCA des respuestas directas. Usa el método socrático para guiar. Usa LaTeX ($$) para fórmulas. Párrafos breves. Resalta términos clave en negrita."

        try:
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
        except Exception as e:
            st.error(f"Ocurrió un error con la API: {e}")
