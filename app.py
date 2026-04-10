import streamlit as st
from groq import Groq
import wikipedia

# --- 1. CONFIGURACIÓN Y ESTÉTICA ---
wikipedia.set_lang("es")
st.set_page_config(page_title="Aluminia", page_icon="🎓", layout="centered")

# Estilo para burbujas de chat más limpias
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .main { background-color: #f9f9f9; }
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

# --- 3. FUNCIONES DE APOYO ---
def investigar_silenciosamente(query):
    """Busca en Wikipedia sin interrumpir el flujo visual."""
    try:
        search_results = wikipedia.search(query)
        if search_results:
            return wikipedia.summary(search_results[0], sentences=3)
    except:
        return None
    return None

# --- 4. PERSISTENCIA Y BARRA LATERAL ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Inicializar o mantener la personalidad elegida
if "personalidad_key" not in st.session_state:
    st.session_state.personalidad_key = "Aluminia Original 💡"

with st.sidebar:
    st.title("🛡️ Panel de Aluminia")
    
    # Selector de personalidad con persistencia en la sesión
    st.session_state.personalidad_key = st.selectbox(
        "Personalidad de Aluminia:", 
        options=list(PERSONALIDADES.keys()),
        index=list(PERSONALIDADES.keys()).index(st.session_state.personalidad_key)
    )
    
    st.divider()
    
    # Parámetros técnicos manuales
    st.subheader("Configuración Técnica")
    model_choice = st.selectbox("Modelo (Cerebro):", ("llama-3.3-70b-versatile", "llama-3.1-8b-instant"))
    temp_val = st.slider("Creatividad (Temperatura):", 0.0, 1.0, 0.5)
    
    if st.button("Limpiar conversación"):
        st.session_state.messages = []
        st.rerun()

# --- 5. LÓGICA DE CONEXIÓN (GROQ) ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Error: Configura la API KEY en los Secrets de Streamlit.")
    st.stop()

client = Groq(api_key=api_key)

# --- 6. INTERFAZ DE USUARIO ---
st.title(f"🎓 {st.session_state.personalidad_key}")
st.caption("Mentora socrática de secundaria alta apoyada por Wikipedia.")

# Mostrar historial de chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 7. PROCESAMIENTO DE MENSAJES ---
if prompt := st.chat_input("¿Qué concepto quieres explorar hoy?"):
    # 1. Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Investigación invisible
    datos_wiki = investigar_silenciosamente(prompt)

    # 3. Generación de respuesta socrática
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # El System Prompt que une todo
        prompt_sistema = f"""
        Tu nombre es Aluminia. Eres una mentora socrática para estudiantes de 16-18 años.
        
        IDENTIDAD ACTUAL: {PERSONALIDADES[st.session_state.personalidad_key]}
        
        MÉTODO SOCRÁTICO:
        - NUNCA des la respuesta. Si el alumno te presiona, mantente firme con ingenio.
        - Tu objetivo es que el alumno descubra la lógica por sí mismo.
        - Usa el contexto de Wikipedia de forma discreta para guiar, no para dictar.
        
        CONTEXTO DE INVESTIGACIÓN:
        {datos_wiki if datos_wiki else 'No hay datos externos adicionales.'}
        
        REGLAS:
        - Usa LaTeX para matemáticas: $x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$.
        - Si el alumno dice algo falso, usa una pregunta para que él mismo note la contradicción.
        """

        # Construcción de la conversación para la API
        mensajes_api = [{"role": "system", "content": prompt_sistema}] + [
            {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
        ]
        
        # Llamada a Groq con streaming
        completion = client.chat.completions.create(
            model=model_choice,
            messages=mensajes_api,
            temperature=temp_val,
            stream=True
        )
        
        for chunk in completion:
            content = chunk.choices[0].delta.content or ""
            full_response += content
            response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
    
    # Guardar respuesta en el historial
    st.session_state.messages.append({"role": "assistant", "content": full_response})
