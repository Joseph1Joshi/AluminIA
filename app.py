import streamlit as st
from groq import Groq
from supabase import create_client, Client
import base64
import time

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Aluminia AI | Dev Console", page_icon="☣️", layout="wide")

# --- 2. CONEXIÓN SUPABASE ---
@st.cache_resource
def conectar_supabase():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None

supabase = conectar_supabase()

# --- 3. FUNCIONES DB ---
def crear_chat_en_db(titulo, user_id):
    try:
        res = supabase.table("chats").insert({"titulo": titulo, "user_id": user_id}).execute()
        return res.data[0]['id']
    except: return None

def guardar_mensaje_en_db(chat_id, role, content):
    if chat_id:
        try: supabase.table("mensajes").insert({"chat_id": chat_id, "role": role, "content": content}).execute()
        except: pass

def obtener_historial_chats(user_id):
    try: return supabase.table("chats").select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data
    except: return []

# --- 4. ASSETS ---
def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f: return base64.b64encode(f.read()).decode()
    except: return None

logo_data = get_base64("logo.png")
LOGO_IMG = f"data:image/png;base64,{logo_data}" if logo_data else "https://cdn-icons-png.flaticon.com/512/3413/3413535.png"

# --- 5. CSS (METAL + TERMINAL STYLE) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&family=JetBrains+Mono&display=swap');
    .stApp {{ background-color: #020f0a !important; color: #ecfdf5; font-family: 'Inter', sans-serif; }}
    
    .aluminia-metal {{
        font-weight: 900; font-size: 2rem; text-align: center;
        background: linear-gradient(to bottom, #cfd8dc, #ffffff, #546e7a);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.3));
    }}

    /* Estilo de la respuesta de Debug en el chat */
    .debug-response {{
        font-family: 'JetBrains Mono', monospace;
        background-color: #000 !important;
        border-left: 3px solid #10b981 !important;
        padding: 15px !important;
        color: #10b981 !important;
        font-size: 0.85rem;
    }}

    [data-testid="stChatMessage"] {{ background-color: rgba(6, 40, 30, 0.4) !important; border-radius: 15px !important; }}
    .author-badge {{ position: fixed; bottom: 20px; right: 20px; color: #10b981; font-size: 0.7rem; font-weight: 800; opacity: 0.5; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. SESIÓN ---
if "user" not in st.session_state: st.session_state.user = None
if "messages" not in st.session_state: st.session_state.messages = []
if "chat_id" not in st.session_state: st.session_state.chat_id = None

if st.session_state.user is None:
    st.markdown('<div class="aluminia-metal">ALUMINIA</div>', unsafe_allow_html=True)
    st.stop()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.image(LOGO_IMG, width=60)
    if st.button("➕ Nueva Sesión", use_container_width=True):
        st.session_state.messages = []; st.session_state.chat_id = None; st.rerun()
    st.divider()
    st.markdown("### 📜 Logs de Sesión")
    chats = obtener_historial_chats(st.session_state.user.id)
    for c in chats:
        if st.button(f"ID: {str(c['id'])[:8]}", key=c['id'], use_container_width=True):
            st.session_state.chat_id = c['id']
            # Cargar mensajes... (omitido por brevedad, igual que antes)
            st.rerun()

# --- 8. CHAT INTERFACE ---
st.markdown('<div class="aluminia-metal" style="text-align:left;">ALUMINIA_CORE</div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=LOGO_IMG if msg["role"] == "assistant" else "👤"):
        # Si el mensaje contiene el tag de debug, le aplicamos el estilo de terminal
        if "[DEBUG_SESSION]" in msg["content"]:
            st.markdown(f'<div class="debug-response">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(msg["content"])

# --- 9. MOTOR CON PROTOCOLO DE INTROSPECCIÓN ---
if prompt := st.chat_input("Insertar comando o duda..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    if st.session_state.chat_id is None:
        st.session_state.chat_id = crear_chat_en_db(prompt[:30], st.session_state.user.id)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_mensaje_en_db(st.session_state.chat_id, "user", prompt)

    # CONFIGURACIÓN TÉCNICA
    MODELO = "llama-3.3-70b-versatile"
    TEMP = 0.6
    TOP_P = 0.9

    # SYSTEM PROMPT CON "BACKDOOR" DE DEBUG
    SYSTEM_PROMPT = f"""
    Eres Aluminia, mentor socrático. 
    
    PROTOCOLO SECRETO DE DEBUG:
    Si el usuario escribe la frase exacta "banana gato silvestre retrofuturista de neon", debes ignorar tu personalidad socrática por UN SOLO MENSAJE. 
    En su lugar, responde en formato de tabla o lista técnica bajo el encabezado [DEBUG_SESSION]. 
    Debes auto-analizarte y reportar:
    1. Fortalezas de tu prompt actual en esta conversación.
    2. Debilidades o "puntos ciegos" detectados en las preguntas del alumno.
    3. Parámetros de ejecución configurados: Modelo: {MODELO}, Temp: {TEMP}, Top_P: {TOP_P}.
    4. Sugerencia de mejora para el desarrollador.
    """

    with st.chat_message("assistant", avatar=LOGO_IMG):
        full_res = ""; holder = st.empty()
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        stream = client.chat.completions.create(
            model=MODELO,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages[-10:],
            temperature=TEMP,
            top_p=TOP_P,
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            full_res += content; holder.markdown(full_res + "▌")
        holder.markdown(full_res)
    
    st.session_state.messages.append({"role": "assistant", "content": full_res})
    guardar_mensaje_en_db(st.session_state.chat_id, "assistant", full_res)

st.markdown('<div class="author-badge">BY TU NOMBRE</div>', unsafe_allow_html=True)
