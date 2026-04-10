import streamlit as st
from groq import Groq
import wikipedia

# 1. Configuración de Wikipedia y Estética
wikipedia.set_lang("es")
st.set_page_config(page_title="Aluminia", page_icon="🎓", layout="centered")

# Función silenciosa de investigación
def investigar_silenciosamente(query):
    try:
        search_results = wikipedia.search(query)
        if search_results:
            return wikipedia.summary(search_results[0], sentences=3)
    except:
        return None
    return None

# 2. Barra Lateral de Control
with st.sidebar:
    st.title("⚙️ Ajustes de Aluminia")
    model_option = st.selectbox("Modelo:", ("llama-3.3-70b-versatile", "llama-3.1-8b-instant"))
    temp = st.slider("Creatividad:", 0.0, 1.0, 0.5)
    if st.button("Reiniciar Tutoría"):
        st.session_state.messages = []
        st.rerun()

# 3. Gestión de API Key
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("Falta la API KEY en los Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# 4. Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🎓 Aluminia")
st.markdown("---")

# Mostrar chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Lógica de Interacción
if prompt := st.chat_input("¿Qué tienes en mente?"):
    # Guardamos mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Búsqueda invisible en Wikipedia
    contexto_wiki = investigar_silenciosamente(prompt)

    # Respuesta de Aluminia
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # System Prompt Refinado
        system_prompt = f"""
        Eres Aluminia, una mentora socrática experta para adolescentes de secundaria alta.
        Tu misión: Guiar al alumno para que llegue a la solución por sí mismo. NUNCA des la respuesta.
        
        DATOS DE RESPALDO (Usa esto para guiar, no para copiar): 
        {contexto_wiki if contexto_wiki else 'No se encontró información externa adicional.'}
        
        REGLAS DE ORO:
        - No menciones Wikipedia a menos que sea estrictamente necesario para validar un hecho o corregir un error grave del alumno.
        - Si el alumno falla en un concepto técnico, usa el dato de respaldo para plantear una pregunta que lo corrija.
        - Usa LaTeX para cualquier fórmula o término científico: $E = mc^2$.
        - Mantén el tono de 'ayudante inteligente', no de 'bot servicial'.
        """

        messages_to_send = [{"role": "system", "content": system_prompt}] + st.session_state.messages
        
        completion = client.chat.completions.create(
            model=model_option,
            messages=messages_to_send,
            temperature=temp,
            stream=True
        )
        
        for chunk in completion:
            content = chunk.choices[0].delta.content or ""
            full_response += content
            response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
