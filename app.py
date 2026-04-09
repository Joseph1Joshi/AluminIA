import streamlit as st
from groq import Groq

# Configuración de la página
st.set_page_config(page_title="Tutor Socrático", page_icon="🎓")
st.title("Aluminia")
st.markdown("---")

# Configurar el cliente de Groq (usando Secrets de Streamlit para seguridad)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Inicializar el historial de chat si no existe
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Eres un Tutor Socrático para secundaria alta. NUNCA das la respuesta directa. Guías con preguntas de reflexión."}
    ]

# Mostrar los mensajes del chat
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Entrada del usuario
if prompt := st.chat_input("¿En qué tarea estás trabajando?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Respuesta de la IA
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Llamada a Groq
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages,
            temperature=0.5,
            stream=True # Para que la respuesta aparezca poco a poco (efecto "typing")
        )
        
        for chunk in completion:
            full_response += (chunk.choices[0].delta.content or "")
            response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
