import streamlit as st
from groq import Groq
import wikipedia

# --- 1. CONFIGURACIÓN DE ENTORNO ---
wikipedia.set_lang("es")
st.set_page_config(page_title="Aluminia", page_icon="🎓", layout="centered")

# Estética minimalista
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #ececec; }
    .stChatInput { border-radius: 20px; }
    .main { background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PERSONALIDADES SUTILES ---
PERSONALIDADES = {
    "Aluminia Original 💡": "Eres neutra, profesional y clara. Tu lenguaje es impecable y equilibrado. Te enfocas en la claridad absoluta.",
    "Cercana y Casual 👋": "Eres como una hermana mayor. Usas un lenguaje relajado (ej: 'mira', 'fíjate', 'tranqui'). Haces que el estudio se sienta ligero.",
    "Enfoque Práctico 🛠️": "Eres directa y pragmática. Hablas de 'herramientas' y 'utilidad'. Buscas que el alumno vea cómo aplicar lo que aprende.",
    "Mente Analítica 🔍": "Te enfocas en patrones y lógica pura. Hablas de 'evidencias' e 'hipótesis'. Eres precisa y detectivesca.",
    "Entrenadora (Coach) ⚡": "Tu tono es motivador. Hablas del aprendizaje como un entrenamiento mental. Usas frases como 'buen intento' o 'vamos a reforzar esto'."
}

# --- 3. FUNCIONES INTERNAS ---
def investigar_silenciosamente(query):
    """Consulta Wikipedia en segundo plano."""
    try:
        search_results = wikipedia.search(query)
        if search_results:
            return wikipedia.summary(search_results[0], sentences=3)
    except:
        return None
    return None

# --- 4. GESTIÓN DE SESIÓN Y BARRA LATERAL ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "personalidad_key" not in st.session_state:
    st.session_state.personalidad_key = "Aluminia Original 💡"

with st.sidebar:
    st.title("🎓 Aluminia")
    st.write("Configuración del Tutor")
    
    st.session_state.personalidad_key = st.selectbox(
        "Elige el estilo de tu guía:", 
        options=list(PERSONALIDADES.keys()),
        index=list(PERSONALIDADES.keys()).index(st.session_state.personalidad_key)
    )
    
    st.divider()
    st.caption("Cerebro: Llama-3.3-70b-Versatile")
    st.caption("Modo Socrático: Activo")
    
    if st.button("Nueva Sesión / Limpiar Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 5. CONEXIÓN CON GROQ ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Error: Configura la API KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# --- 6. INTERFAZ DE CHAT ---
st.title(st.session_state.personalidad_key)
st.info("No soy una IA para resolver tus tareas, soy una mentora para ayudarte a pensar.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 7. LÓGICA DE PROCESAMIENTO ---
if prompt := st.chat_input("¿En qué desafío estás trabajando?"):
    # Guardar y mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Investigación invisible
    datos_wiki = investigar_silenciosamente(prompt)

    with st.chat_message("assistant"):
