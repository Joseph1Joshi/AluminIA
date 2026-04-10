import streamlit as st
from groq import Groq
import wikipedia

# --- 1. CONFIGURACIÓN ---
wikipedia.set_lang("es")
st.set_page_config(page_title="Aluminia", page_icon="🎓", layout="centered")

# --- 2. CSS PROTEGIDO (No rompe iconos) ---
st.markdown("""
    <style>
    /* Fondo */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    /* Títulos con clases personalizadas para no heredar estilos de sistema */
    .aluminia-title {
        font-family: sans-serif;
        color: #1e3a8a;
        text-align: center;
        font-size: 40px;
        font-weight: bold;
        padding-top: 20px;
    }

    .aluminia-sub {
        font-family: sans-serif;
        text-align: center;
        color: #4b5563;
        font-size: 16px;
        margin-bottom: 30px;
    }

    /* Burbujas de chat: usamos selectores que no tocan los iconos del avatar */
    [data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 15px !important;
        border: 1px solid #e0e0e0 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }

    /* Ajuste para que el texto de las burbujas sea legible pero NO rompa los iconos */
    [data-testid="stChatMessage"] .st-expanderHeader, 
    [data-testid="stChatMessage"] p, 
    [data-testid="stChatMessage"] li {
        font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        line-height: 1.6;
    }

    /* Escondemos basura de la UI pero dejamos el header funcional para el menú */
    footer {visibility: hidden;}
    header {background: rgba(0,0,0,0) !important;}
    
    /* Evitar que los iconos se conviertan en texto plano */
    span[data-testid="stIconMaterial"] {
        font-family: "Material Symbols Outlined" !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGICA Y PERSONALIDADES ---
PERSONALIDADES = {
    "Aluminia Original 💡": "Eres neutra y profesional.",
    "Cercana y Casual 👋": "Eres relajada, como una hermana mayor.",
    "Enfoque Práctico 🛠️": "Eres directa y pragmática.",
    "Mente Analítica 🔍": "Te enfocas en patrones y lógica.",
    "Entrenadora (Coach) ⚡": "Eres motivadora y enérgica."
}

if "messages" not in st.session_state:
    st.session_state.messages = []
if "personalidad_key" not in st.session_state:
    st.session_state.personalidad_key = "Aluminia Original 💡"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("Configuración")
    st.session_state.personalidad_key = st.selectbox(
        "Estilo del mentor:", 
        options=list(PERSONALIDADES.keys())
    )
    if st.button("Limpiar conversación"):
        st.session_state.messages = []
        st.rerun()

# --- 5. INTERFAZ ---
st.markdown('<div class="aluminia-title">Aluminia</div>', unsafe_allow_html=True)
st.markdown(f'<div class="aluminia-sub">Modo: <b>{st.session_state.personalidad_key}</b></div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. API GROQ ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Configura la API KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)

if prompt := st.chat_input("¿En qué te puedo ayudar?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Wikipedia invisible
    try:
        search_results = wikipedia.search(prompt)
        datos_wiki = wikipedia.summary(search_results[0], sentences=2) if search_results else ""
    except:
        datos_wiki = ""

    with st.chat_message("assistant"):
        full_response = ""
        placeholder = st.empty()
        
        prompt_sistema = f"""
        Eres Aluminia, mentora socrática. 
        Personalidad: {PERSONALIDADES[st.session_state.personalidad_key]}
        Método: No des respuestas, haz preguntas. Usa LaTeX ($$) para fórmulas.
        Contexto extra: {datos_wiki}
        """

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": prompt_sistema}] + 
                     [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            temperature=0.6,
            stream=True
        )
        
        for chunk in completion:
            content = chunk.choices[0].delta.content or ""
            full_response += content
            placeholder.markdown(full_response + "▌")
        
        placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
