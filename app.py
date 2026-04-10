import streamlit as st
from groq import Groq
from supabase import create_client, Client
import base64

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Aluminia | Acceso Seguro", page_icon="🔐", layout="wide")
st.markdown('<meta name="theme-color" content="#020f0a">', unsafe_allow_html=True)
# --- 2. CONEXIÓN A SUPABASE ---
@st.cache_resource
def conectar_supabase():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        st.error("Error de conexión. Revisa tus Secrets.")
        return None

supabase = conectar_supabase()

# --- 3. FUNCIONES DE BASE DE DATOS (CON USER_ID) ---
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

# --- 5. CSS MAESTRO (NEÓN ESMERALDA) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp {{ background: #020f0a; font-family: 'Inter', sans-serif; color: #ecfdf5; }}
    .aluminia-title {{
        font-weight: 800; text-align: center; font-size: 3.8rem; letter-spacing: -3px;
        background: linear-gradient(90deg, #10b981, #a7f3d0, #10b981);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
    }}
    [data-testid="stSidebar"] {{ background-color: #010805 !important; border-right: 1px solid #10b98133; }}
    .stChatInputContainer {{ background: #06281e !important; border: 1px solid #10b98144 !important; border-radius: 15px !important; }}
    [data-testid="stChatMessage"] {{ background: rgba(6, 40, 30, 0.6) !important; border: 1px solid #10b98122 !important; border-radius: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. LÓGICA DE AUTENTICACIÓN ---
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.markdown('<div class="aluminia-title" style="margin-top:10vh;">ALUMINIA</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#a7f3d0; opacity:0.7;">Tu viaje hacia el conocimiento comienza aquí.</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        tab_login, tab_reg = st.tabs(["Ingresar", "Nueva Cuenta"])
        with tab_login:
            email = st.text_input("Email", key="l_email")
            pw = st.text_input("Password", type="password", key="l_pw")
            if st.button("Iniciar Sesión", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                    st.session_state.user = res.user
                    st.rerun()
                except: st.error("Error: Revisa tus credenciales.")
        with tab_reg:
            n_email = st.text_input("Email", key="r_email")
            n_pw = st.text_input("Password", type="password", key="r_pw")
            if st.button("Registrarse", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": n_email, "password": n_pw})
                    st.success("Cuenta creada. Ya puedes ingresar.")
                except: st.error("Error al registrar.")
    st.stop()

# --- 7. BARRA LATERAL (USUARIO LOGUEADO) ---
with st.sidebar:
    st.markdown(f'<div style="text-align:center;"><img src="{LOGO_IMG}" width="90" style="border-radius:15px; border: 1px solid #10b981;"></div>', unsafe_allow_html=True)
    st.caption(f"Conectado como: {st.session_state.user.email}")
    
    estilo = st.selectbox("Personalidad:", ["Aluminia Original 💡", "Cercana 👋", "Analítica 🔍", "Coach ⚡"])
    
    if st.button("➕ Nuevo Chat", use_container_width=True):
        st.session_state.messages = []; st.session_state.chat_id = None; st.rerun()
    
    st.divider()
    st.markdown("### 📜 Historial")
    chats = obtener_historial_chats(st.session_state.user.id)
    for c in chats:
        if st.button(f"💬 {c['titulo'][:20]}", key=c['id'], use_container_width=True):
            st.session_state.chat_id = c['id']
            mensajes_db = obtener_mensajes_del_chat(c['id'])
            st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in mensajes_db]
            st.rerun()
    
    st.divider()
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.user = None; st.rerun()

# --- 8. INTERFAZ DE CHAT ---
st.markdown('<div class="aluminia-title" style="font-size:2.5rem; text-align:left;">ALUMINIA</div>', unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
if "chat_id" not in st.session_state: st.session_state.chat_id = None

for msg in st.session_state.messages:
    avatar = LOGO_IMG if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- 9. LÓGICA DE IA (GROQ) ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key: st.stop()
client = Groq(api_key=api_key)

if prompt := st.chat_input("¿Qué duda exploramos hoy?"):
    if st.session_state.chat_id is None:
        st.session_state.chat_id = crear_chat_en_db(prompt[:30], st.session_state.user.id)

    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_mensaje_en_db(st.session_state.chat_id, "user", prompt)
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=LOGO_IMG):
        full_res = ""; holder = st.empty()
        sys_prompt = f"Eres Aluminia. Estilo: {estilo}. Usa el método socrático. Párrafos breves y negritas."

        try:
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages,
                stream=True
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                full_res += content; holder.markdown(full_res + "▌")
            
            holder.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            guardar_mensaje_en_db(st.session_state.chat_id, "assistant", full_res)
        except Exception as e: st.error(f"Error: {e}")
