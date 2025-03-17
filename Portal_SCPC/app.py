import streamlit as st
from authentication import login
from conteudo import ocupacao, home, analise_consumo
from PIL import Image
import os

# 🔹 Corrigir caminho da logo para ser compatível em LINUX e WINDOWS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Obtém o diretório atual do script
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")  # Mantém compatível no Linux

def main():
    st.set_page_config(page_title="Portal SCPC", layout="wide")

    # 🔹 Tenta carregar a logo dentro do diretório correto
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH)
        st.sidebar.image(logo, use_container_width=True)
    else:
        st.sidebar.title("Portal SCPC")
        st.sidebar.warning(f"⚠️ Logo não encontrada: {LOGO_PATH}")

    # 🔹 Inicializa variáveis de sessão
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'

    # 🔹 Verifica se o usuário está logado
    if not st.session_state.logged_in:
        login()
    else:
        show_content()

def show_content():
    """Gerencia a navegação entre páginas"""
    
    # 🔹 Botão "Home"
    if st.sidebar.button("🏠 Voltar para Home", use_container_width=True):
        st.session_state.current_page = 'home'
        st.rerun()

    # 🔹 Botão "Logout"
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    # 🔹 Navegação entre páginas
    if st.session_state.current_page == 'home':
        show_home()
    elif st.session_state.current_page == 'ocupacao':
        ocupacao.show()
    elif st.session_state.current_page == 'analise_consumo':
        analise_consumo.show()

def show_home():
    """Exibição da tela inicial"""
    
    st.title("🏥 Bem-vindo ao Portal SCPC")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Ocupação de Leitos", use_container_width=True, key="btn_ocupacao"):
            st.session_state.current_page = 'ocupacao'
            st.rerun()

    with col2:
        if st.button("📈 Análise de Consumo de Materiais", use_container_width=True, key="btn_analise_consumo"):
            st.session_state.current_page = 'analise_consumo'
            st.rerun()

if __name__ == "__main__":
    main()
