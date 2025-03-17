import streamlit as st
from authentication import login
from conteudo import ocupacao, home, analise_consumo
from PIL import Image
import os

# Caminho absoluto para o logo
LOGO_PATH = r"C:\Users\SANTA CASA\Documents\Projetos Python\P1\Portal_SCPC\logo.png"

def main():
    st.set_page_config(page_title="Portal SCPC", layout="wide")
    
    # Tenta carregar o logo
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH)
        st.sidebar.image(logo, use_container_width=True)
    else:
        st.sidebar.title("Portal SCPC")
        st.sidebar.warning(f"Logo não encontrado em: {LOGO_PATH}")
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'

    if not st.session_state.logged_in:
        login()
    else:
        show_content()

def show_content():
    # Botão "Voltar para Home" na sidebar
    if st.sidebar.button("Voltar para Home", use_container_width=True):
        st.session_state.current_page = 'home'
        st.rerun()
    
    # Botão de Logout
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
    
    # Exibição do conteúdo com base na página atual
    if st.session_state.current_page == 'home':
        show_home()
    elif st.session_state.current_page == 'ocupacao':
        ocupacao.show()
    elif st.session_state.current_page == 'analise_consumo':
        analise_consumo.show()

def show_home():
    st.title("Bem-vindo ao Portal SCPC")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Ocupação de Leitos", use_container_width=True, key="btn_ocupacao"):
            st.session_state.current_page = 'ocupacao'
            st.rerun()
    
    with col2:
        if st.button("Análise de Consumo de Materiais", use_container_width=True, key="btn_analise_consumo"):
            st.session_state.current_page = 'analise_consumo'
            st.rerun()

if __name__ == "__main__":
    main()
