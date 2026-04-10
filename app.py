import streamlit as st
from groq import Groq
import wikipedia

# --- 1. CONFIGURACIÓN ---
wikipedia.set_lang("es")
st.set_page_config(page_title="Aluminia", page_icon="🎓", layout="centered")
# --- PARCHE PARA PWA ---
st.components.v1.html(
    """
    <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function() {
        navigator.serviceWorker.register('https://aluminia.streamlit.app/sw.js').then(function(registration) {
          console.log('ServiceWorker registration successful with scope: ', registration.scope);
        }, function(err) {
          console.log('ServiceWorker registration failed: ', err);
        });
      });
    }
    </script>
    """,
    height=0,
)
# --- 2. CONFIGURACIÓN DE LOGOS ---
# Puedes usar un emoji o una URL de una imagen (en formato .png o .jpg)
LOGO_USUARIO = "👤" 
LOGO_ALUMINIA = "https://cdn-icons-png.flaticon.com/512/3413/3413535.png" # Ejemplo de logo

# --- 3. CSS PROTEGIDO ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .aluminia-title { font-family: sans-serif; color: #1e3a8a; text-align: center; font-size: 40px; font-weight: bold; padding-top: 20px; }
    .aluminia-sub { font-family: sans-serif; text-align: center; color: #4b5563; font-size: 16px; margin-bottom: 30px; }
    
    [data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 15px !important;
        border: 1px solid #e0e0e0 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }

    /* Fix para asegurar que las imágenes de los avatares no se deformen */
    [data-testid="stChatMessage"] img {
        border-radius: 50%;
        object-fit: cover;
    }

    footer {visibility: hidden;}
    header {background: rgba(0,0,0,0) !important;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. LÓGICA DE PERSONALIDADES ---
PERSONALIDADES = {
    "Aluminia Original 💡": "Eres neutra y profesional.",
    "Cercana y Casual 👋": "Eres relajada, como una hermana mayor.",
    "Enfoque Práctico 🛠️": "Eres directa y pragmática.",
    "Mente Analítica 🔍": "Te enfocas en patrones y lógica.",
    "Entrenadora (Coach) ⚡": "Eres motivadora y enérgica."
}

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("Configuración")
    st.session_state.personalidad_key = st.selectbox(
        "Estilo del mentor:", options=list(PERSONALIDADES.keys())
    )
    if st.button("Limpiar conversación"):
        st.session_state.messages = []
        st.rerun()

# --- 6. INTERFAZ ---
st.markdown('<div class="aluminia-title">Aluminia</div>', unsafe_allow_html=True)
st.markdown(f'<div class="aluminia-sub">Modo: <b>{st.session_state.personalidad_key}</b></div>', unsafe_allow_html=True)

# MOSTRAR MENSAJES CON LOGOS CUSTOM
for msg in st.session_state.messages:
    # Si el rol es assistant usa el logo de Aluminia, si no el del usuario
    avatar_actual = LOGO_ALUMINIA if msg["role"] == "assistant" else LOGO_USUARIO
    with st.chat_message(msg["role"], avatar=avatar_actual):
        st.markdown(msg["content"])

# --- 7. PROCESAMIENTO ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Configura la API KEY.")
    st.stop()

client = Groq(api_key=api_key)

if prompt := st.chat_input("¿En qué te puedo ayudar?"):
    # Guardar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=LOGO_USUARIO):
        st.markdown(prompt)

    # Wiki invisible
    try:
        search_results = wikipedia.search(prompt)
        datos_wiki = wikipedia.summary(search_results[0], sentences=2) if search_results else ""
    except:
        datos_wiki = ""

    # Respuesta del asistente
    with st.chat_message("assistant", avatar=LOGO_ALUMINIA):
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
