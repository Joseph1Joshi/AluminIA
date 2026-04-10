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

# --- 2. DECORACIÓN Y ESTILO CORREGIDO (CSS) ---
st.markdown("""
    <style>
    /* Fondo general */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Burbujas de chat: permitimos que el contenido (imágenes) fluya */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 15px !important;
        padding: 1.5rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #e0e0e0 !important;
        max-width: 100%;
    }

    /* Asegurar que las imágenes en el chat se vean bien */
    .stChatMessage img {
        max-width: 100%;
        border-radius: 10px;
        margin: 10px 0;
    }

    /* Fuentes del sistema */
    html, body, [class*="st-"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }

    /* Títulos */
    .main-title {
        color: #1e3a8a;
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        margin-top: -2rem;
    }

    .sub-title {
        text-align: center;
        color: #4b5563;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    /* CORRECCIÓN: Ocultar solo elementos estéticos, NO funcionales */
    footer {visibility: hidden;}
    header {background-color: transparent !important;}
    [data-testid="stHeader"] {background: none !important;}

    /* Mejorar bloques de código y fórmulas */
    code { color: #d63384; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. PERSONALIDADES ---
PERSONALIDADES = {
    "Aluminia Original 💡": "Eres neutra y profesional. Tu lenguaje es impecable.",
    "Cercana y Casual 👋": "Eres como una hermana mayor. Usas un lenguaje relajado.",
    "Enfoque Práctico 🛠️": "Eres directa y pragmática. Te enfocas en la utilidad.",
    "Mente Analítica 🔍": "Te enfocas en patrones y lógica pura.",
    "Entrenadora (Coach) ⚡": "Tu tono es motivador. Ves el estudio como un reto."
}

# --- 4. FUNCIONES ---
def investigar_silenciosamente(query):
    try:
        search_results = wikipedia.search(query)
        if search_results:
            return wikipedia.summary(search_results[0], sentences=3)
    except:
        return None
    return None

if "messages" not in st.session_state:
    st.session_state.messages = []
if "personalidad_key" not in st.session_state:
    st.session_state.personalidad_key = "Aluminia Original 💡"

# --- 5. SIDEBAR (CORREGIDA) ---
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    st.session_state.personalidad_key = st.selectbox(
        "Estilo del mentor:", 
        options=list(PERSONALIDADES.keys()),
        index=list(PERSONALIDADES.keys()).index(st.session_state.personalidad_key)
    )
    st.divider()
    if st.button("🗑️ Reiniciar Sesión"):
        st.session_state.messages = []
        st.rerun()

# --- 6. INTERFAZ ---
st.markdown('<div class="main-title">Aluminia</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">Modo: <b>{st.session_state.personalidad_key}</b></div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 7. LÓGICA ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Falta la API KEY.")
    st.stop()

client = Groq(api_key=api_key)

if prompt := st.chat_input("¿Qué exploramos hoy?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    datos_wiki = investigar_silenciosamente(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        prompt_sistema = f"""
        Eres Aluminia, mentora socrática.
        IDENTIDAD: {PERSONALIDADES[st.session_state.personalidad_key]}
        REGLAS DE FORMATO:
        - USA BLOQUES $$ para fórmulas largas.
        - USA $ para variables en línea.
        - Si necesitas explicar algo visual, describe la imagen o usa diagramas sencillos.
        - NUNCA des la respuesta directa.
        CONTEXTO: {datos_wiki if datos_wiki else 'Sin datos extra.'}
        """

        mensajes_api = [{"role": "system", "content": prompt_sistema}] + [
            {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
        ]
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=mensajes_api,
            temperature=0.5, 
            stream=True
        )
        
        for chunk in completion:
            content = chunk.choices[0].delta.content or ""
            full_response += content
            response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
