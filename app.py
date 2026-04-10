import streamlit as st
from groq import Groq
import wikipedia
import base64

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Aluminia Tutor", 
    page_icon="🎓", 
    layout="wide"
)

# --- 2. CARGA DE LOGO PERSONALIZADO ---
def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

# Intentamos cargar tu logo
logo_data = get_base64("logo.png")
LOGO_IMG = f"data:image/png;base64,{logo_data}" if logo_data else "https://cdn-icons-png.flaticon.com/512/3413/3413535.png"

# --- 3. CSS MAESTRO (CON FONDO ANIMADO Y RESPONSIVE) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* Animación del fondo degradado */
    @keyframes gradientBG {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}

    .stApp {{
        background: linear-gradient(-45deg, #f8fafc, #e2e8f0, #f1f5f9, #cbd5e1);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        font-family: 'Inter', sans-serif !important;
    }}

    /* Contenedor principal optimizado para PC y Móvil */
    .block-container {{
        max-width: 850px;
        padding-top: 2rem;
        padding-bottom: 6rem;
    }}

    @media (max-width: 640px) {{
        .block-container {{
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }}
        .aluminia-title {{ font-size: 2.5rem !important; }}
    }}

    /* Estética de Títulos */
    .aluminia-title {{
        font-weight: 800;
        color: #1e3a8a;
        text-align: center;
        font-size: 3.5rem;
        letter-spacing: -2px;
        margin-bottom: 5px;
    }}

    .aluminia-sub {{
        text-align: center;
        color: #475569;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }}

    /* Burbujas Glassmorphism */
    [data-testid="stChatMessage"] {{
        background: rgba(255, 255, 255, 0.65) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03) !important;
        margin-bottom: 1rem !important;
    }}

    /* Estilo del Input de Chat */
    .stChatInputContainer {{
        border-radius: 15px !important;
        background: white !important;
        border: 1px solid rgba(0,0,0,0.05) !important;
    }}

    /* Ocultar elementos innecesarios */
    footer {{visibility: hidden;}}
    header {{background: transparent !important;}}
    [data-testid="stHeader"] {{background: none !important;}}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<div style="text-align:center"><img src="{LOGO_IMG}" width="100" style="border-radius:15px"></div>', unsafe_allow_html=True)
    st.title("Configuración")
    estilo = st.selectbox("Personalidad:", ["Aluminia Original 💡", "Cercana 👋", "Práctica 🛠️", "Analítica 🔍", "Coach ⚡"])
    if st.button("🗑️ Reiniciar Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 5. INTERFAZ ---
st.markdown('<div class="aluminia-title">Aluminia</div>', unsafe_allow_html=True)
st.markdown('<div class="aluminia-sub">Tu guía hacia el conocimiento propio.</div>', unsafe_allow_html=True)

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
        
        sys_prompt = f"Eres Aluminia. Estilo: {estilo}. Usa el método socrático (no des respuestas). Usa LaTeX ($$) para fórmulas matemáticas. Párrafos breves y claros."

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
