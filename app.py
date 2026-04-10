import streamlit as st
from groq import Groq
import wikipedia
import base64

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Aluminia Tutor | Dark Edition", 
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

# --- 3. CSS MAESTRO (DARK MODE EDITION) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* Fondo animado en tonos oscuros */
    @keyframes gradientBG {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}

    .stApp {{
        background: linear-gradient(-45deg, #0f172a, #1e293b, #0f172a, #111827);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        font-family: 'Inter', sans-serif !important;
        color: #f8fafc;
    }}

    /* Contenedor principal */
    .block-container {{
        max-width: 850px;
        padding-top: 2rem;
        padding-bottom: 6rem;
    }}

    /* Títulos en modo oscuro */
    .aluminia-title {{
        font-weight: 800;
        color: #60a5fa; /* Azul brillante para resaltar */
        text-align: center;
        font-size: 3.5rem;
        letter-spacing: -2px;
        margin-bottom: 5px;
        text-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }}

    .aluminia-sub {{
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }}

    /* Burbujas Glassmorphism Oscuras (Cristal Ahumado) */
    [data-testid="stChatMessage"] {{
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        margin-bottom: 1rem !important;
    }}

    /* Texto dentro de las burbujas */
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {{
        color: #e2e8f0 !important;
    }}

    /* Input de Chat adaptado al modo oscuro */
    .stChatInputContainer {{
        border-radius: 15px !important;
        background: #1e293b !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }}
    
    .stChatInputContainer textarea {{
        color: white !important;
    }}

    /* Barra lateral oscura */
    [data-testid="stSidebar"] {{
        background-color: #0f172a !important;
        border-right: 1px solid rgba(255,255,255,0.1);
    }}

    /* Ocultar elementos innecesarios */
    footer {{visibility: hidden;}}
    header {{background: transparent !important;}}
    [data-testid="stHeader"] {{background: none !important;}}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<div style="text-align:center"><img src="{LOGO_IMG}" width="100" style="border-radius:15px; filter: drop-shadow(0px 0px 10px rgba(96,165,250,0.5));"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:white;'>Configuración</h2>", unsafe_allow_html=True)
    estilo = st.selectbox("Personalidad:", ["Aluminia Original 💡", "Cercana 👋", "Práctica 🛠️", "Analítica 🔍", "Coach ⚡"])
    if st.button("🗑️ Reiniciar Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 5. INTERFAZ ---
st.markdown('<div class="aluminia-title">Aluminia</div>', unsafe_allow_html=True)
st.markdown('<div class="aluminia-sub">Explorando el conocimiento en las sombras.</div>', unsafe_allow_html=True)

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
        
        sys_prompt = f"Eres Aluminia, versión nocturna. Estilo: {estilo}. Usa el método socrático. Usa LaTeX ($$) para fórmulas. Párrafos breves. Resalta términos clave en negrita."

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
