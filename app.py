import streamlit as st
from groq import Groq
import wikipedia

# 1. Configuración de Wikipedia en español
wikipedia.set_lang("es")

# 2. Configuración estética
st.set_page_config(page_title="Aluminia + Wiki", page_icon="🎓", layout="centered")

# Función para que Aluminia "investigue"
def investigar_tema(query):
    try:
        # Busca los temas más cercanos
        search_results = wikipedia.search(query)
        if search_results:
            # Trae el resumen de los primeros párrafos
            return wikipedia.summary(search_results[0], sentences=3)
    except:
        return None
    return None

# 3. Barra Lateral (Parámetros)
with st.sidebar:
    st.title("⚙️ Cerebro de Aluminia")
    api_key_input = st.text_input("Groq API Key (si no está en secrets):", type="password")
    model_option = st.selectbox("Modelo:", ("llama-3.3-70b-versatile", "llama-3.1-8b-instant"))
    temp = st.slider("Creatividad socrática:", 0.0, 1.0, 0.5)
    if st.button("Borrar Memoria"):
        st.session_state.messages = []
        st.rerun()

# 4. Conexión con la API
api_key = st.secrets["GROQ_API_KEY"] if "GROQ_API_KEY" in st.secrets else api_key_input
if not api_key:
    st.warning("⚠️ Por favor, introduce tu API Key de Groq para continuar.")
    st.stop()

client = Groq(api_key=api_key)

# 5. Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🎓 Aluminia con Wikipedia")
st.caption("Ahora puedo investigar en tiempo real para guiarte mejor.")

# Mostrar chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Lógica Principal
if prompt := st.chat_input("¿Qué estamos estudiando hoy?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- PASO AMBICIOSO: Búsqueda de contexto ---
    with st.status("Aluminia está consultando Wikipedia..."):
        contexto_wiki = investigar_tema(prompt)
        if contexto_wiki:
            st.write("📖 Información encontrada y procesada.")
        else:
            st.write("❓ No hay datos exactos, usaré mi base de conocimientos.")

    # Respuesta de Aluminia
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # System Prompt con esteroides
        system_prompt = f"""
        Eres Aluminia, una mentora socrática de secundaria alta. 
        CONTEXTO DE WIKIPEDIA PARA ESTA DUDA: {contexto_wiki if contexto_wiki else 'No disponible'}
        
        INSTRUCCIONES:
        1. Usa el contexto de Wikipedia para verificar si el alumno dice la verdad, pero NO le des la respuesta ni le digas 'leí en Wikipedia que...'.
        2. Usa los datos para hacer preguntas que lo lleven al dato correcto. 
        3. Si el alumno se equivoca en una fecha o nombre histórico que aparece en el contexto, pregúntale: '¿Estás seguro de que eso ocurrió en ese año? ¿Qué pasaba en el mundo en esa época?'.
        4. Mantén tu tono ingenioso y de apoyo.
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
