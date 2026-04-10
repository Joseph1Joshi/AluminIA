import streamlit as st
from groq import Groq
import wikipedia

# --- 1. CONFIGURACIÓN DE ENTORNO Y WIKIPEDIA ---
wikipedia.set_lang("es")
st.set_page_config(
    page_title="Aluminia | Tu Mentora Socrática", 
    page_icon="🎓", 
    layout="centered"
)

# --- 2. DECORACIÓN Y ESTILO (CSS) ---
st.markdown("""
    <style>
    /* Fondo con degradado sutil */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Contenedor de mensajes */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 20px !important;
        padding: 15px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
    }

    /* Título con estilo moderno */
    .main-title {
        font-family: 'Inter', sans-serif;
        color: #1e3a8a;
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }

    /* Subtítulos y textos informativos */
    .sub-title {
        text-align: center;
        color: #4b5563;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Input del chat */
    .stChatInputContainer {
        border-radius: 25px !important;
        background-color: white !important;
    }

    /* Esconder elementos innecesarios */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. DICCIONARIO DE PERSONALIDADES ---
PERSONALIDADES = {
    "Aluminia Original 💡": "Eres neutra, profesional y clara. Tu lenguaje es impecable. Te enfocas en la claridad absoluta.",
    "Cercana y Casual 👋": "Eres como una hermana mayor. Usas lenguaje relajado ('mira', 'tranqui'). Haces que el estudio sea ligero.",
    "Enfoque Práctico 🛠️": "Eres directa y pragmática. Hablas de 'herramientas' y 'utilidad'. Buscas la aplicación real.",
    "Mente Analítica 🔍": "Te enfocas en patrones y lógica. Hablas de 'evidencias' e 'hipótesis'. Eres precisa y detectivesca.",
    "Entrenadora (Coach) ⚡": "Tu tono es motivador. Hablas del aprendizaje como un entrenamiento. Dices 'buen intento' y 'vamos a reforzar'."
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

# --- 6. BARRA LATERAL DECORADA ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=100)
    st.title("Centro de Control")
    
    st.session_state.personalidad_key = st.selectbox(
        "¿Quién te guiará hoy?", 
        options=list(PERSONALIDADES.keys()),
        index=list(PERSONALIDADES.keys()).index(st.session_state.personalidad_key)
    )
    
    st.divider()
    st.markdown("**Estado del Sistema:**")
    st.success("Cerebro: Llama-3.3-70B")
    st.success("Wiki-Search: Conectado")
    
    if st.button("🗑️ Reiniciar Sesión"):
        st.session_state.messages = []
        st.rerun()

# --- 7. INTERFAZ PRINCIPAL ---
st.markdown('<h1 class="main-title">Aluminia</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">Estás conversando con tu guía en modo: <b>{st.session_state.personalidad_key}</b></p>', unsafe_allow_html=True)

# Mostrar historial de chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 8. LÓGICA DE PROCESAMIENTO ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("⚠️ Configura la GROQ_API_KEY en los Secrets de Streamlit.")
    st.stop()

client = Groq(api_key=api_key)

if prompt := st.chat_input("Escribe tu duda aquí..."):
    # Guardar y mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Investigación invisible
    with st.spinner(""): # Spinner invisible para no romper la estética
        datos_wiki = investigar_silenciosamente(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        prompt_sistema = f"""
        Tu nombre es Aluminia. Eres una mentora socrática de secundaria alta.
        IDENTIDAD LINGÜÍSTICA: {PERSONALIDADES[st.session_state.personalidad_key]}
        MÉTODO SOCRÁTICO: NUNCA des la respuesta. Haz preguntas que obliguen a razonar.
        CONTEXTO WIKI: {datos_wiki if datos_wiki else 'No hay datos externos.'}
        REGLAS: Usa LaTeX para matemáticas. Mantén los párrafos cortos.
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
        
        # Guardado final de la respuesta
        st.session_state.messages.append({"role": "assistant", "content": full_response})
