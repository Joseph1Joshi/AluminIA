import streamlit as st
from groq import Groq
from supabase import create_client, Client
import base64

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Aluminia Tutor", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded" # Ahora inicia abierta en PC
)

# Meta tags para móviles
st.markdown("""
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="theme-color" content="#020f0a">
    </head>
""", unsafe_allow_html=True)

# --- 2. CONEXIÓN A SUPABASE ---
@st.cache_resource
def conectar_supabase():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None

supabase = conectar_supabase()

# --- 3. FUNCIONES DE BASE DE DATOS ---
def crear_chat_en_db(titulo, user_id):
    try:
        res = supabase.table("chats").insert({"titulo": titulo, "user_id": user_id}).execute()
        return res.data[0]['id']
    except: return None

def guardar_mensaje_en_db(chat_id, role, content):
    if chat_id and content:
        try:
            supabase.table("mensajes").insert({"chat_id": chat_id, "role": role, "content": content}).execute()
        except: pass

def obtener_historial_chats(user_id):
    try:
        res = supabase.table("chats").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data
    except: return []

def obtener_mensajes_del_chat(chat_id):
    try:
        res = supabase.table("mensajes").select("*").eq("chat_id", chat_id).order("created_at").execute()
        return res.data
    except: return []

# --- 4. CARGA DE LOGO ---
def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f: return base64.b64encode(f.read()).decode()
    except: return None

logo_data = get_base64("logo.png")
LOGO_IMG = f"data:image/png;base64,{logo_data}" if logo_data else "https://cdn-icons-png.flaticon.com/512/3413/3413535.png"

# --- 5. CSS MAESTRO (CORREGIDO PARA VISIBILIDAD) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp {{ 
        background-color: #020f0a; 
        font-family: 'Inter', sans-serif; 
        color: #ecfdf5; 
    }}

    /* EL PARCHE DEL BOTÓN DE MENÚ (SIDEBAR) */
    /* Hacemos que el header sea transparente pero NO invisible */
    header[data-testid="stHeader"] {{
        background-color: rgba(0,0,0,0) !important;
        color: #10b981 !important;
    }}

    /* Estilo del botón que abre la barra lateral */
    button[kind="headerNoSpacing"] {{
        background-color: #10b981 !important;
        color: #020f0a !important;
        border-radius: 50% !important;
        margin-left: 10px !important;
        margin-top: 5px !important;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
    }}
    
    /* Título Adaptativo */
    .aluminia-title {{
        font-weight: 800; text-align: center; font-size: clamp(2rem, 7vw, 3.5rem); 
        background: linear-gradient(90deg, #10b981, #a7f3d0, #10b981);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }}

    /* Inputs y Botones */
    .stButton button {{
        border-radius: 12px !important;
        background-color: #06281e !important;
        border: 1px solid #10b98144 !important;
        color: #a7f3d0 !important;
    }}
    
    [data-testid="stSidebar"] {{
        background-color: #010805 !important;
        border-right: 1px solid #10b98122;
    }}

    .stChatInputContainer {{ 
        background: #06281e !important; 
        border: 1px solid #10b98144 !important; 
        border-radius: 15px !important;
    }}

    /* Bloqueo de zoom en móvil */
    * {{ touch-action: manipulation; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. LÓGICA DE LOGIN ---
if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.markdown('<div class="aluminia-title" style="margin-top:10vh;">ALUMINIA</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
    with col2:
        t1, t2 = st.tabs(["Ingresar", "Registrarse"])
        with t1:
            e = st.text_input("Email", key="l_e")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("Entrar", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": e, "password": p})
                    st.session_state.user = res.user
                    st.rerun()
                except: st.error("Error al entrar")
        with t2:
            re = st.text_input("Email", key="r_e")
            rp = st.text_input("Password", type="password", key="r_p")
            if st.button("Crear Cuenta", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": re, "password": rp})
                    st.success("Cuenta creada. Ya puedes loguearte.")
                except: st.error("Error al registrar")
    st.stop()

# --- 7. BARRA LATERAL ---
with st.sidebar:
    st.markdown(f'<div style="text-align:center;"><img src="{LOGO_IMG}" width="80" style="border-radius:15px; margin-bottom:10px;"></div>', unsafe_allow_html=True)
    st.caption(f"Usuario: {st.session_state.user.email}")
    
    estilo = st.selectbox("Modo Tutor:", ["Original 💡", "Cercano 👋", "Analítico 🔍"])
    
    if st.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.messages = []; st.session_state.chat_id = None; st.rerun()
    
    st.divider()
    st.markdown("### 📜 Historial")
    chats_db = obtener_historial_chats(st.session_state.user.id)
    for c in chats_db:
        if st.button(f"💬 {c['titulo'][:20]}", key=c['id'], use_container_width=True):
            st.session_state.chat_id = c['id']
            m_db = obtener_mensajes_del_chat(c['id'])
            st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in m_db]
            st.rerun()
    
    st.divider()
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        supabase.auth.sign_out(); st.session_state.user = None; st.rerun()

# --- 8. INTERFAZ PRINCIPAL ---
st.markdown('<div class="aluminia-title" style="font-size:1.8rem; text-align:left;">ALUMINIA</div>', unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
if "chat_id" not in st.session_state: st.session_state.chat_id = None

for msg in st.session_state.messages:
    av = LOGO_IMG if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=av):
        st.markdown(msg["content"])

# --- 9. LÓGICA DE IA ---
api_key = st.secrets.get("GROQ_API_KEY")
if api_key and (prompt := st.chat_input("¿Qué vamos a descubrir hoy?")):
    if st.session_state.chat_id is None:
        st.session_state.chat_id = crear_chat_en_db(prompt[:30], st.session_state.user.id)

    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_mensaje_en_db(st.session_state.chat_id, "user", prompt)
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=LOGO_IMG):
        full_res = ""; holder = st.empty()
        client = Groq(api_key=api_key)
        try:
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": f"Eres Aluminia. Estilo: {estilo}. Método socrático estricto."}] + st.session_state.messages,
                stream=True
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                full_res += content; holder.markdown(full_res + "▌")
            
            holder.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            guardar_mensaje_en_db(st.session_state.chat_id, "assistant", full_res)
        except Exception as e: st.error("Fallo de conexión con la IA.")
