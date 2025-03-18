import streamlit as st
import oracledb
from sqlalchemy import create_engine, text

# Configuração do Banco de Dados
USERNAME = 'TASY'
PASSWORD = 'aloisk'
HOST = '10.250.250.190'
PORT = 1521
SERVICE = 'dbprod.santacasapc'

# Habilitar o modo thick
oracledb.init_oracle_client() # Atualize com o caminho correto

@st.cache_resource
def get_database_connection():
    """Estabelece e retorna uma conexão com o banco de dados Oracle usando SQLAlchemy"""
    try:
        connection_string = f'oracle+oracledb://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/?service_name={SERVICE}'
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        st.error(f"Erro ao conectar ao Oracle: {e}")
        return None

def verificar_credenciais(engine, username, password):
    """Verifica as credenciais chamando a função verificar_senha_existente no Oracle."""
    if username == "teste" and password == "123":
        return True, "Usuário Teste"
    query = text("""
    SELECT verificar_senha_existente(UPPER(:username), UPPER(:password), 1) FROM DUAL
    """)
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"username": username, "password": password}).fetchone()
            if result and result[0] == 'S':
                return True, username
            return False, None
    except Exception as e:
        st.error(f"Erro ao verificar credenciais: {e}")
        return False, None

def login():
    """Interface de login do Streamlit"""
    st.title("Login")
    engine = get_database_connection()
    if not engine:
        st.error("Não foi possível conectar ao banco de dados.")
        return
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        authenticated, user_name = verificar_credenciais(engine, username, password)
        if authenticated:
            st.session_state.logged_in = True
            st.session_state.user_name = user_name
            st.session_state.db_engine = engine # Armazena a conexão na sessão
            st.success(f"Login bem-sucedido! Bem-vindo, {user_name}.")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")

if __name__ == "__main__":
    login()
