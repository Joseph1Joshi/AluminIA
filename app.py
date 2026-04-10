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

# --- 5. CSS MAESTRO (METAL + BURBUJAS + FIRMA) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
    .stApp {{ background-color: #020f0a !important; color: #ecfdf5; font-family: 'Inter', sans-serif; }}
    
    .aluminia-metal {{
        font-family: 'Inter', sans-serif; font-weight: 900; font-size: clamp(2rem, 8vw, 4rem); text-align: center;
        background: linear-gradient(to bottom, #cfd8dc, #90a4ae, #ffffff, #546e7a, #b0bec5);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 10px rgba(16, 185, 129, 0.3));
        margin-bottom: 10px;
    }}

    [data-testid="stChatMessage"] {{ 
        background-color: rgba(6, 40, 30, 0.5) !important; 
        border-radius: 20px !important; 
        border: 1px solid rgba(16, 185, 129, 0.1) !important;
        margin-bottom: 1rem !important;
    }}
    
    header[data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
    button[kind="headerNoSpacing"] {{ background-color: #10b981 !important; color: #020f0a !important; border-radius: 50% !important; }}
    [data-testid="stSidebar"] {{ background-color: #010805 !important; border-right: 1px solid #10b98122; }}

    .author-badge {{
        position: fixed; bottom: 20px; right: 20px; color: #10b981; font-size: 0.75rem;
        font-weight: 800; z-index: 999999; background: rgba(6, 40, 30, 0.7);
        padding: 6px 15px; border-radius: 20px; border: 1px solid rgba(16, 185, 129, 0.3);
        backdrop-filter: blur(5px); text-transform: uppercase;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. LÓGICA DE SESIÓN ---
if "user" not in st.session_state: st.session_state.user = None
if "messages" not in st.session_state: st.session_state.messages = []
if "chat_id" not in st.session_state: st.session_state.chat_id = None

if st.session_state.user is None:
    st.markdown('<div style="margin-top:12vh;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="aluminia-metal">ALUMINIA</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #10b981; margin-top: -15px; font-weight: 700; letter-spacing: 2px;'>MADE BY TU NOMBRE</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
    with col2:
        t1, t2 = st.tabs(["Entrar", "Unirse"])
        with t1:
            e = st.text_input("Email")
            p = st.text_input("Password", type="password")
            if st.button("Ingresar", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": e, "password": p})
                    st.session_state.user = res.user; st.rerun()
                except: st.error("Error de acceso")
    st.stop()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<div style="text-align:center;"><img src="{LOGO_IMG}" width="80" style="filter: drop-shadow(0 0 5px #10b981);"></div>', unsafe_allow_html=True)
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
                    if st.session_state.chat_id == c['id']:
                        st.session_state.messages = []; st.session_state.chat_id = None
                    st.rerun()
    
    st.divider()
    if st.button("🚪 Salir", use_container_width=True):
        supabase.auth.sign_out(); st.session_state.user = None; st.rerun()
    
    st.markdown("<br>"*3, unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; color: #10b981; opacity: 0.5; font-size: 0.7rem;'>DEVELOPED BY<br><b>TU NOMBRE</b></div>", unsafe_allow_html=True)

# --- 8. INTERFAZ DE CHAT ---
st.markdown('<div class="aluminia-metal" style="font-size:1.8rem; text-align:left;">ALUMINIA</div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=LOGO_IMG if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

# --- 9. MOTOR DE IA (CONFIGURACIÓN AVANZADA) ---
if prompt := st.chat_input("Plantea tu duda..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    if st.session_state.chat_id is None:
        st.session_state.chat_id = crear_chat_en_db(prompt[:30], st.session_state.user.id)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    guardar_mensaje_en_db(st.session_state.chat_id, "user", prompt)

    # PARÁMETROS DE COMPORTAMIENTO
    SYSTEM_PROMPT = (
        "Eres Aluminia, un mentor socrático avanzado. Tu misión no es resolver, sino guiar. Pero no como lo haria un estricto y serio profesor, debes hablar con naturalidad, casi como un amigo, con un tono calido pero siempre desafiante intelectualmente. Usaras los tecnicismos necesarios, y haras las preguntas que consideres ayuden a profundizar mas en los intereses del usuario, pero sin llegar a abrumarlo. Llegaras a continuar la conversacion, como un compañero que te enseña de manera amigable pero contundente y profesional. "
        "REGLAS: 1. Responde preguntas con nuevas preguntas que inviten a la lógica. "
        "2. Si el alumno está perdido, usa una analogía sencilla. 3. Nunca des la respuesta final. "
        "4. Formato: Párrafos cortos, usa negritas para conceptos clave y mantén un tono elegante."
    )

    with st.chat_message("assistant", avatar=LOGO_IMG):
        full_res = ""; holder = st.empty()
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages[-8:], # Memoria optimizada
            temperature=0.6, # Equilibrio entre creatividad y rigor
            top_p=0.9,
            max_tokens=900,
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            full_res += content; holder.markdown(full_res + "▌")
        holder.markdown(full_res)
    
    st.session_state.messages.append({"role": "assistant", "content": full_res})
    guardar_mensaje_en_db(st.session_state.chat_id, "assistant", full_res)

# CRÉDITO FLOTANTE
st.markdown('<div class="author-badge">BY TU NOMBRE</div>', unsafe_allow_html=True)
