import streamlit as st
from sqlalchemy import text
import locale
from datetime import datetime

try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, 'C')

def obter_setores(engine):
    query = """
    SELECT DISTINCT cd_setor_atendimento, ds_setor_atendimento
    FROM UNIDADE_ATENDIMENTO_V
    WHERE ie_situacao = 'A'
      AND cd_classif_setor = 3
      AND cd_setor_atendimento IN (SELECT cd_setor_atendimento FROM SETOR_ATENDIMENTO WHERE ie_situacao = 'A')
    ORDER BY ds_setor_atendimento
    """
    with engine.connect() as connection:
        result = connection.execute(text(query))
        return {r[0]: r[1] for r in result}

def obter_quartos(engine):
    query = """
    SELECT cd_setor_atendimento, ds_setor_atendimento,
           SUBSTR(cd_unidade, 0, 3) AS quarto,
           SUBSTR(cd_unidade, 5, 1) AS leito,
           Obter_Descricao_Dominio(82, ie_status_unidade) AS status,
           nr_atendimento
    FROM UNIDADE_ATENDIMENTO_V
    WHERE ie_situacao = 'A'
    AND cd_classif_setor = 3
    AND cd_setor_atendimento IN (SELECT cd_setor_atendimento FROM SETOR_ATENDIMENTO WHERE ie_situacao = 'A')
    ORDER BY ds_setor_atendimento, quarto, leito
    """
    quartos = {}
    contagem_status = {}
    with engine.connect() as connection:
        result = connection.execute(text(query))
        for setor, ds_setor, quarto, leito, status, nr_atendimento in result:
            if setor not in quartos:
                quartos[setor] = {"nome": ds_setor, "quartos": {}}
            quartos[setor]["quartos"].setdefault(quarto, []).append({
                "leito": leito,
                "status": status,
                "nr_atendimento": nr_atendimento
            })
            contagem_status.setdefault(status, 0)
            contagem_status[status] += 1
    return quartos, contagem_status

def show():
    st.title("🏥 Monitoramento de Leitos")
    
    engine = st.session_state.db_engine
    if not engine:
        st.error("Erro de conexão com o banco de dados")
        return
    
    setores = obter_setores(engine)
    quartos, contagem_status = obter_quartos(engine)
    
    st.sidebar.header("📊 Filtros")
    setor_escolhido = st.sidebar.selectbox(
        "📍 Selecione um Setor:",
        [None] + list(setores.keys()),
        format_func=lambda x: setores[x] if x else "Todos os Setores",
        key="setor_selector"
    )

    # Resto da lógica de exibição...
    # (O código continua como no seu arquivo original)

if __name__ == "__main__":
    show()
