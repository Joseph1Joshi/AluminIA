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

# --- 2. DECORACIÓN Y ESTILO (CSS) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 15px !important;
        padding: 20px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #e0e0e0 !important;
    }

    /* Mejora la legibilidad de LaTeX */
    .katex-display {
        overflow-x: auto;
        overflow-y: hidden;
        padding: 10px 0;
    }

    html, body, [class*="st-"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }

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

    #MainMenu, footer, header {visibility: hidden;}
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

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("Configuración")
    st.session_state.personalidad_key = st.selectbox(
        "Estilo del mentor:", 
        options=list(PERSONALIDADES.keys()),
        index=list(PERSONALIDADES.keys()).index(st.session_state.personalidad_key)
    )
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
        
        # INSTRUCCIÓN CRÍTICA DE FORMATO
        prompt_sistema = f"""
        Eres Aluminia, mentora socrática.
        IDENTIDAD: {PERSONALIDADES[st.session_state.personalidad_key]}
        
        REGLAS DE FORMATO MATEMÁTICO:
        - Para fórmulas importantes o largas, USA BLOQUES CENTRADOS con doble signo de dólar, por ejemplo:
          $$f(x) = \\int_{{a}}^{{b}} g(x) dx$$
        - Para variables simples dentro de una oración, usa un solo signo: $x = 5$.
        - NUNCA des la respuesta, solo guía con preguntas.
        
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
