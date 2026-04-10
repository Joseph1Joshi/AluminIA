import streamlit as st
from groq import Groq
import wikipedia
import base64

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Aluminia Tutor", 
    page_icon="🎓", 
    layout="wide" # Cambiamos a wide para controlar los márgenes nosotros
)

# --- 2. CARGA DE LOGO PERSONALIZADO ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    # Intenta cargar tu diseño guardado como 'logo.png'
    logo_base64 = get_base64("logo.png")
    LOGO_IMG = f"data:image/png;base64,{logo_base64}"
except:
    # Logo de respaldo si el archivo no existe
    LOGO_IMG = "https://cdn-icons-png.flaticon.com/512/3413/3413535.png"

# --- 3. CSS MAESTRO (PROPORCIONES Y ESTÉTICA) ---
st.markdown(f"""
    <style>
    /* Importar fuente moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* Fondo animado sutil */
    .stApp {{
        background: linear-gradient(135deg, #f8f9fc 0%, #e2e8f0 100%);
        font-family: 'Inter', sans-serif !important;
    }}

    /* Limitar el ancho en PC para que no se vea "estirado" */
    .block-container {{
        max-width: 800px;
        padding-top: 2rem;
        padding-bottom: 10rem;
    }}

    /* Optimización para MÓVILES */
    @media (max-width: 640px) {{
        .block-container {{
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1rem;
        }}
        .aluminia-title {{ font-size: 2.2rem !important; }}
    }}

    /* Título de alta gama */
    .aluminia-title {{
        font-weight: 800;
        color: #1e3a8a;
        text-align: center;
        font-size: 3.5rem;
        letter-spacing: -2px;
        margin-bottom: 0px;
    }}

    .aluminia-sub {{
        text-align: center;
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }}

    /* Burbujas de Chat estilo Glassmorphism */
    [data-testid="stChatMessage"] {{
        background: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 24px !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05) !important;
        margin-bottom: 1.2rem !important;
        transition: transform 0.2s ease;
    }}

    /* Avatar circular y estilizado */
    [data-testid="stChatMessage"] img {{
        border-radius: 12px !important;
        border: 2px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}

    /* Personalización del Input (Barra de escritura) */
    .stChatInputContainer {{
        border-radius: 20px !important;
        border: 1px solid rgba(0,0,0,0.1) !important;
        background: white !important;
        box-shadow: 0 -10px 25px rgba(0,0,0,0.03) !important;
    }}

    /* Ocultar elementos de Streamlit para una experiencia limpia */
    footer {{visibility: hidden;}}
    header {{background: rgba(0,0,0,0) !important;}}
    [data-testid="stHeader"] {{background: none !important;}}
    
    /* Mejorar el renderizado de LaTeX */
    .katex {{ font-size: 1.1em !important; color: #1e293b; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR REFINADA ---
with st.sidebar:
    st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <img src="{LOGO_IMG}" width="120" style="border-radius: 20%;">
            <h2 style="color: #1e3a8a; margin-top: 10px;">Aluminia Tutor</h2>
            <p style="font-size: 0.8rem; color: #64748b;">v2.0 Beta • Llama 3.3</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    personalidad = st.selectbox(
        "Estilo de Aprendizaje",
        ["Aluminia Original 💡", "Cercana y Casual 👋", "Enfoque Práctico 🛠️", "Mente Analítica 🔍", "Entrenadora ⚡"]
    )
    
    if st.button("🗑️ Nueva Sesión", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 5. CUERPO DE LA APP ---
st.markdown('<div class="aluminia-title">Aluminia</div>', unsafe_allow_html=True)
st.markdown('<div class="aluminia-sub">Tu mentora socrática impulsada por IA</div>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes con el avatar personalizado
for msg in st.session_state.messages:
    avatar = LOGO_IMG if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- 6. LÓGICA DE INTELIGENCIA ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Error: API Key no encontrada.")
    st.stop()

client = Groq(api_key=api_key)

if prompt := st.chat_input("¿Qué vamos a descubrir hoy?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=LOGO_IMG):
        placeholder = st.empty()
        full_response = ""
        
        # El System Prompt ahora incluye instrucciones de formato premium
        sys_prompt = f"Eres Aluminia. Personalidad: {personalidad}. NUNCA des respuestas, usa el método socrático. Usa LaTeX $$ para fórmulas matemáticas centradas. Mantén párrafos cortos y usa negritas para enfatizar conceptos clave."

        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages,
            stream=True
        )

        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            full_response += content
            placeholder.markdown(full_response + "▌")
        
        placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
