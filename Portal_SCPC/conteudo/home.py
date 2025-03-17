import streamlit as st

def show():
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
