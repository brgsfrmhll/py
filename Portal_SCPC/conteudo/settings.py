import streamlit as st

def show():
    st.title("Configurações")
    
    # Exemplo de configurações
    st.subheader("Preferências do Usuário")
    tema = st.selectbox("Tema", ["Claro", "Escuro"])
    notificacoes = st.checkbox("Ativar notificações")
    
    # Configurações específicas de ocupação
    st.subheader("Configurações de Ocupação")
    limite_ocupacao = st.slider("Limite de alerta de ocupação (%)", 0, 100, 80)
    enviar_relatorio = st.checkbox("Enviar relatório diário de ocupação")
    
    if st.button("Salvar Configurações"):
        # Aqui você implementaria a lógica para salvar as configurações
        st.success("Configurações salvas com sucesso!")
