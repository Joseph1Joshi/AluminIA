import streamlit as st
from groq import Groq
import wikipedia

# --- 1. CONFIGURACIÓN DE ENTORNO ---
wikipedia.set_lang("es")
st.set_page_config(
    page_title="Aluminia Dark", 
    page_icon="🎓", 
    layout="centered"
)

# --- 2. DECORACIÓN MODO OSCURO (CSS) ---
st.markdown("""
    <style>
    /* Fondo oscuro profundo */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    /* Contenedor de mensajes estilo Dark */
    .stChatMessage {
        background-color: #1a1c24 !important;
        border-radius: 15px !important;
        padding: 15px !important;
        margin-bottom: 15px !important;
        border: 1px solid #30363d !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    }

    /* Títulos en Neón Azul sutil */
    .main-title {
        color: #58a6ff;
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }

    .sub-title {
        text-align: center;
        color: #8b949e;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Input del chat adaptado */
    .stChatInputContainer {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 15px !important;
    }

    /* Estilo de la barra lateral */
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }

    /* Botones y otros elementos */
    .stButton>button {
        background-color: #21262d !important;
        color: #c9d1d9 !important;
        border: 1px solid #30363d !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. PERSONALIDADES ---
PERSONALIDADES = {
    "Aluminia Original 💡": "Eres neutra, profesional y clara.",
    "Cercana y Casual 👋": "Eres como una hermana mayor, hablas relajado.",
    "Enfoque Práctico 🛠️": "Eres directa, hablas de herramientas y utilidad.",
    "Mente Analítica 🔍": "Te enfocas en patrones, lógica y evidencias.",
    "Entrenadora (Coach) ⚡": "Eres motivadora y ves el estudio como un reto físico."
}

# --- 4. FUNCIONES INTERNAS ---
def investigar_silenciosamente(query):
    try:
        search_results = wikipedia.search(query)
        if search_results:
            return wikipedia.summary(search_results[0], sentences=3)
    except:
        return None
    return None

# --- 5. GESTIÓN DE SESIÓN ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "personalidad_key" not in st.session_state:
    st.session_state.personalidad_key = "Aluminia Original 💡"

# --- 6. BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=80)
    st.title("Aluminia Settings")
    
    st.session_state.personalidad_key = st.selectbox(
        "Tono de voz:", 
        options=list(PERSONALIDADES.keys()),
        index=list(PERSONALIDADES.keys()).index(st.session_state.personalidad_key)
    )
    
    st.divider()
    st.info("Modelo: Llama-3.3-70B\n\nModo: Dark Education")
    
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 7. INTERFAZ PRINCIPAL ---
st.markdown('<h1 class="main-title">Aluminia</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">Guía socrática en modo: {st.session_state.personalidad_key}</p>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 8. LÓGICA DE PROCESAMIENTO ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("GROQ_API_KEY no configurada.")
    st.stop()

client = Groq(api_key=api_key)

if prompt := st.chat_input("¿Qué reto resolveremos hoy?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    datos_wiki = investigar_silenciosamente(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        prompt_sistema = f"""
        Eres Aluminia, mentora socrática de 16-18 años.
        IDENTIDAD: {PERSONALIDADES[st.session_state.personalidad_key]}
        MÉTODO: Prohibido dar respuestas. Haz preguntas críticas.
        CONOCIMIENTO EXTRA: {datos_wiki if datos_wiki else 'No disponible.'}
        REGLAS: Usa LaTeX. Sé breve y desafiante.
        """

        mensajes_api = [{"role": "system", "content": prompt_sistema}] + [
            {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
        ]
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=mensajes_api,
            temperature=0.6, 
            stream=True
        )
        
        for chunk in completion:
            content = chunk.choices[0].delta.content or ""
            full_response += content
            response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
