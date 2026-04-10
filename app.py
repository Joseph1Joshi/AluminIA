import streamlit as st
from groq import Groq
from supabase import create_client, Client
import base64

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Aluminia AI", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

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

def obtener_mensajes_del_chat(chat_id):
    try: return supabase.table("mensajes").select("*").eq("chat_id", chat_id).order("created_at").execute().data
    except: return []

def borrar_chat_db(chat_id):
    try:
        supabase.table("mensajes").delete().eq("chat_id", chat_id).execute()
        supabase.table("chats").delete().eq("id", chat_id).execute()
        return True
    except: return False

# --- 4. ASSETS ---
def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f: return base64.b64encode(f.read()).decode()
    except: return None

logo_data = get_base64("logo.png")
LOGO_IMG = f"data:image/png;base64,{logo_data}" if logo_data else "https://cdn-icons-png.flaticon.com/512/3413/3413535.png"

# --- 5. CSS MAESTRO ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&family=JetBrains+Mono&display=swap');
    .stApp {{ background-color: #020f0a !important; color: #ecfdf5; font-family: 'Inter', sans-serif; }}
    
    .aluminia-metal {{
        font-family: 'Inter', sans-serif; font-weight: 900; font-size: clamp(2rem, 8vw, 4rem); text-align: center;
        background: linear-gradient(to bottom, #cfd8dc, #90a4ae, #ffffff, #546e7a, #b0bec5);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 10px rgba(16, 185, 129, 0.3));
        margin-bottom: 10px;
    }}

    .debug-response {{
        font-family: 'JetBrains Mono', monospace; background-color: #000 !important;
        border-left: 3px solid #10b981 !important; padding: 15px !important;
        color: #10b981 !important; font-size: 0.85rem; border-radius: 5px;
    }}

    [data-testid="stChatMessage"] {{ background-color: rgba(6, 40, 30, 0.5) !important; border-radius: 20px !important; border: 1px solid rgba(16, 185, 129, 0.1) !important; }}
    [data-testid="stSidebar"] {{ background-color: #010805 !important; border-right: 1px solid #10b98122; }}
    .author-badge {{ position: fixed; bottom: 20px; right: 20px; color: #10b981; font-size: 0.75rem; font-weight: 800; background: rgba(6, 40, 30, 0.7); padding: 6px 15px; border-radius: 20px; z-index: 99; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. SISTEMA DE LOGIN Y REGISTRO REPARADO ---
if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.markdown('<div style="margin-top:10vh;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="aluminia-metal">ALUMINIA</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #10b981; margin-top: -15px; font-weight: 700; letter-spacing: 2px;'>MADE BY TU NOMBRE</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
    with col2:
        t1, t2 = st.tabs(["Ingresar", "Unirse"])
        
        with t1:
            e = st.text_input("Email", key="l_email")
            p = st.text_input("Password", type="password", key="l_pass")
            if st.button("Entrar", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": e, "password": p})
                    st.session_state.user = res.user
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error de acceso: {ex}")
                    
        with t2:
            st.markdown("<p style='font-size: 0.9rem; opacity: 0.7;'>Crea una cuenta para guardar tus progresos socráticos.</p>", unsafe_allow_html=True)
            new_e = st.text_input("Nuevo Email", key="r_email")
            new_p = st.text_input("Nueva Password", type="password", key="r_pass")
            if st.button("Crear Cuenta", use_container_width=True):
                try:
                    # Registro en Supabase
                    auth_res = supabase.auth.sign_up({"email": new_e, "password": new_p})
                    if auth_res:
                        st.success("¡Cuenta creada con éxito! Ya puedes cambiar a la pestaña 'Ingresar'.")
                        st.balloons()
                except Exception as ex:
                    st.error(f"Error al registrar: {ex}")
    st.stop()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<div style="text-align:center;"><img src="{LOGO_IMG}" width="80"></div>', unsafe_allow_html=True)
    if st.button("➕ Nuevo Diálogo", use_container_width=True):
        st.session_state.messages = []; st.session_state.chat_id = None; st.rerun()
    
    st.divider()
    st.markdown("### 📜 Historial")
    chats = obtener_historial_chats(st.session_state.user.id)
    for c in chats:
        c1, c2 = st.columns([0.8, 0.2])
        with c1:
            if st.button(f"💬 {c['titulo'][:15]}", key=f"c_{c['id']}", use_container_width=True):
                st.session_state.chat_id = c['id']
                m_db = obtener_mensajes_del_chat(c['id'])
                st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in m_db]
                st.rerun()
        with c2:
            if st.button("🗑️", key=f"d_{c['id']}"):
                if borrar_chat_db(c['id']):
                    if st.session_state.get("chat_id") == c['id']:
                        st.session_state.messages = []; st.session_state.chat_id = None
                    st.rerun()
    
    st.divider()
    if st.button("🚪 Salir", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

# --- 8. INTERFAZ DE CHAT ---
st.markdown('<div class="aluminia-metal" style="font-size:1.8rem; text-align:left;">ALUMINIA</div>', unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
if "chat_id" not in st.session_state: st.session_state.chat_id = None

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=LOGO_IMG if msg["role"] == "assistant" else "👤"):
        if "[DEBUG_SESSION]" in msg["content"]:
            st.markdown(f'<div class="debug-response">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(msg["content"])

# --- 9. MOTOR DE IA ---
if prompt := st.chat_input("Plantea tu duda..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    if st.session_state.chat_id is None:
        st.session_state.chat_id = crear_chat_en_db(prompt[:30], st.session_state.user.id)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_mensaje_en_db(st.session_state.chat_id, "user", prompt)

    MODELO = "llama-3.3-70b-versatile"
    TEMP = 0.6

    SYSTEM_PROMPT = f"""
    Eres Aluminia, mentor socrático. Guía al alumno con preguntas.
    
    [PROTOCOL_DEBUG_RECOGNITION]
    Si el usuario escribe exactamente "banana gato salvaje retrofuturista de neon", rompe el personaje por completo.
    Responde bajo el encabezado [DEBUG_SESSION] analizando tus propios parámetros:
    - Estado del motor: {MODELO}
    - Temperatura: {TEMP}
    - Análisis de la eficiencia del método socrático en esta sesión.
    - Puntos de mejora técnica.
    """

    with st.chat_message("assistant", avatar=LOGO_IMG):
        full_res = ""; holder = st.empty()
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        stream = client.chat.completions.create(
            model=MODELO,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages[-10:],
            temperature=TEMP,
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            full_res += content; holder.markdown(full_res + "▌")
        holder.markdown(full_res)
    
    st.session_state.messages.append({"role": "assistant", "content": full_res})
    guardar_mensaje_en_db(st.session_state.chat_id, "assistant", full_res)

st.markdown('<div class="author-badge">BY TU NOMBRE</div>', unsafe_allow_html=True)
