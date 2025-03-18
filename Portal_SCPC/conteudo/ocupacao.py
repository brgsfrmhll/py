import streamlit as st
from datetime import datetime
import locale
from sqlalchemy import text

# Configuração da localidade para português
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, 'C')

def obter_setores(engine):
    """Obtém os setores de atendimento ativos."""
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
    """Obtém informações sobre quartos e leitos."""
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

def obter_dados_paciente(engine, nr_atendimento):
    """Obtém dados detalhados do paciente."""
    if not nr_atendimento:
        return None
        
    query = """
    SELECT b.nr_atendimento, b.nm_paciente, b.ds_idade, b.ds_sexo,
           b.nm_medico || ' - CRM ' || b.nr_crm AS medico,
           b.nr_dia_internado || ' dia(s)' AS dias_internado,
           obter_diagnosticos_atendimento(b.nr_atendimento) AS diagnostico,
           b.ds_convenio AS convenio,
           obter_desc_tipo_acomodacao(a.cd_tipo_acomodacao) AS categoria
    FROM ATEND_CATEGORIA_CONVENIO a, ATENDIMENTO_PACIENTE_V b
    WHERE a.nr_atendimento = b.nr_atendimento
      AND a.nr_atendimento = :nr_atendimento
    """
    
    with engine.connect() as connection:
        result = connection.execute(text(query), {"nr_atendimento": nr_atendimento}).fetchone()
        return result if result else None

def show():
    """Interface principal do monitoramento de leitos."""
    st.title("🏥 Monitoramento de Leitos")

    # Verifica se há conexão com o banco de dados na sessão
    if not hasattr(st.session_state, 'db_engine'):
        st.error("Erro: Conexão com o banco de dados não encontrada.")
        return

    engine = st.session_state.db_engine
    setores = obter_setores(engine)
    quartos, contagem_status = obter_quartos(engine)

    # Sidebar com filtros
    st.sidebar.header("📊 Filtros")
    setor_escolhido = st.sidebar.selectbox(
        "📍 Selecione um Setor:",
        [None] + list(setores.keys()),
        format_func=lambda x: setores[x] if x else "Todos os Setores",
        key="setor_selector"
    )

    # Filtros por status
    st.sidebar.subheader("🎨 Filtrar por Status do Leito")
    status_filtrado = None
    
    for status, total in contagem_status.items():
        if st.sidebar.button(f"{status}: {total}", key=f"status_{status}"):
            status_filtrado = status
            setor_escolhido = None

    if st.sidebar.button("🧹 Limpar Filtros", key="limpar_filtros"):
        status_filtrado = None
        setor_escolhido = None
        st.rerun()

    # Exibição dos dados
    if setor_escolhido or status_filtrado:
        if setor_escolhido:
            st.header(f"📍 {setores[setor_escolhido]}")
            quartos_filtrados = {setor_escolhido: quartos[setor_escolhido]}
        else:
            st.header(f"Status: {status_filtrado}")
            quartos_filtrados = quartos

        for setor, setor_data in quartos_filtrados.items():
            leitos_no_setor = [
                l for quarto in setor_data["quartos"].values() 
                for l in quarto 
                if not status_filtrado or l['status'] == status_filtrado
            ]

            if leitos_no_setor:
                if not setor_escolhido:
                    st.subheader(f"📌 {setor_data['nome']}")

                for quarto, leitos in setor_data["quartos"].items():
                    leitos_filtrados = [l for l in leitos if not status_filtrado or l['status'] == status_filtrado]
                    
                    if not leitos_filtrados:
                        continue

                    ocupados = sum(1 for l in leitos_filtrados if l['status'] != 'Livre')
                    total_leitos = len(leitos_filtrados)
                    
                    st.markdown(f"**Quarto {quarto} - {ocupados}/{total_leitos} ocupados**")
                    
                    cols = st.columns(min(4, len(leitos_filtrados)))
                    for idx, leito_info in enumerate(leitos_filtrados):
                        with cols[idx % len(cols)]:
                            st.markdown(f"Leito {leito_info['leito']} - **{leito_info['status']}**")
                            
                            if leito_info['nr_atendimento']:
                                dados_paciente = obter_dados_paciente(engine, leito_info['nr_atendimento'])
                                if dados_paciente:
                                    with st.expander("👤 Dados do Paciente"):
                                        st.write(f"Nome: {dados_paciente[1]}")
                                        st.write(f"Idade: {dados_paciente[2]}")
                                        st.write(f"Médico: {dados_paciente[4]}")
                                        st.write(f"Dias Internado: {dados_paciente[5]}")
                                        st.write(f"Diagnóstico: {dados_paciente[6]}")
                                        st.write(f"Convênio: {dados_paciente[7]}")
                                        st.write(f"Categoria: {dados_paciente[8]}")
    else:
        st.info("Selecione um setor ou um status de leito para visualizar.")

if __name__ == "__main__":
    show()
