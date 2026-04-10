import streamlit as st
from groq import Groq
import wikipedia

# --- 1. CONFIGURACIÓN DE ENTORNO ---
wikipedia.set_lang("es")
st.set_page_config(
    page_title="Aluminia | Tu Mentora Socrática", 
    page_icon="🎓", 
    layout="centered"
)

# --- 2. DECORACIÓN Y ESTILO ESTÁNDAR (CSS) ---
st.markdown("""
    <style>
    /* Fondo con degradado sutil */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Contenedor de mensajes con fuentes estándar y más espacio interno */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 15px !important;
        padding: 20px !important; /* Más espacio para evitar desbordamiento */
        margin-bottom: 15px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #e0e0e0 !important;
    }

    /* Forzar fuentes normales del sistema para máxima compatibilidad */
    html, body, [class*="st-"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }

    /* Título principal sin fuentes externas */
    .main-title {
        color: #1e3a8a;
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }

    .sub-title {
        text-align: center;
        color: #4b5563;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    /* Ajuste del input de chat */
    .stChatInputContainer {
        border-radius: 10px !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. DICCIONARIO DE PERSONALIDADES ---
PERSONALIDADES = {
    "Aluminia Original 💡": "Eres neutra, profesional y clara. Tu lenguaje es impecable.",
    "Cercana y Casual 👋": "Eres como una hermana mayor. Usas un lenguaje relajado y cercano.",
    "Enfoque Práctico 🛠️": "Eres directa y pragmática. Te enfocas en la utilidad de los conceptos.",
    "Mente Analítica 🔍": "Te enfocas en patrones y lógica pura. Eres precisa y detectivesca.",
    "Entrenadora (Coach) ⚡": "Tu tono es motivador y dinámico. Ves el estudio como un entrenamiento."
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
    st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=100)
    st.title("Configuración")
    
    st.session_state.personalidad_key = st.selectbox(
        "Estilo del mentor:", 
        options=list(PERSONALIDADES.keys()),
        index=list(PERSONALIDADES.keys()).index(st.session_state.personalidad_key)
    )
    
    st.divider()
    st.success("Cerebro: Llama-3.3-70B")
    
    if st.button("🗑️ Reiniciar Tutoría"):
        st.session_state.messages = []
        st.rerun()

# --- 7. INTERFAZ PRINCIPAL ---
st.markdown('<div class="main-title">Aluminia</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">Conversando en modo: <b>{st.session_state.personalidad_key}</b></div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 8. LÓGICA DE PROCESAMIENTO ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Falta la API KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)

if prompt := st.chat_input("¿Qué duda quieres explorar?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    datos_wiki = investigar_silenciosamente(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        prompt_sistema = f"""
        Eres Aluminia, mentora socrática de secundaria alta.
        IDENTIDAD: {PERSONALIDADES[st.session_state.personalidad_key]}
        MÉTODO: NUNCA des respuestas. Guía con preguntas inteligentes.
        WIKI-CONTEXT: {datos_wiki if datos_wiki else 'Sin datos adicionales.'}
        REGLAS: Usa LaTeX. Sé breve y fomenta la reflexión.
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
