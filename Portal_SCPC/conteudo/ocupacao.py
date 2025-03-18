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
    st.title("Monitoramento de Leitos")
    
    # Conectar ao banco de dados
    engine = conectar_ao_banco()
    setores = obter_setores(engine)
    quartos, contagem_status = obter_quartos(engine)

    # Sidebar
    st.sidebar.header("Filtrar por Setor ou Status")
    setor_escolhido = st.sidebar.selectbox(
        "Selecionar um Setor:",
        [None] + list(setores.keys()),
        format_func=lambda x: setores[x] if x else "Todos os Setores",
        key="setor_selector"
    )
    st.sidebar.subheader("Filtrar por Status do Leito")
    
    # Usando colunas para organizar os botões de status
    col1, col2 = st.sidebar.columns(2)
    status_filtrado = None
    for i, (status, total) in enumerate(contagem_status.items()):
        cor_botao = '#28a745' if status == 'Livre' else '#ffc107' if status == 'Paciente' else '#dc3545'
        col = col1 if i % 2 == 0 else col2
        if col.button(f"{status}: {total}", key=f"status_{status}",
                      help=f"Filtrar por {status}",
                      use_container_width=True):
            status_filtrado = status
            setor_escolhido = None # Reseta a seleção de setor quando um status é selecionado

    # Botão para limpar filtros
    if st.sidebar.button("Limpar Filtros", use_container_width=True):
        status_filtrado = None
        setor_escolhido = None
        st.rerun()

    # Resumo geral na barra lateral
    st.sidebar.subheader("Resumo Geral")
    total_leitos = sum(contagem_status.values())
    ocupados = total_leitos - contagem_status.get('Livre', 0)
    st.sidebar.markdown(f"""
    <p>Total de Leitos: {total_leitos}</p>
    <p>Leitos Ocupados: {ocupados}</p>
    """, unsafe_allow_html=True)
    st.sidebar.markdown(criar_barra_ocupacao(ocupados, total_leitos), unsafe_allow_html=True)

    # Conteúdo principal
    if setor_escolhido or status_filtrado:
        if setor_escolhido:
            st.header(f"{setores[setor_escolhido]}")
            quartos_filtrados = {setor_escolhido: quartos[setor_escolhido]}
        else:
            st.header(f"Leitos com status: {status_filtrado}")
            quartos_filtrados = quartos
        for setor, setor_data in quartos_filtrados.items():
            leitos_no_setor = [l for quarto in setor_data["quartos"].values() for l in quarto if not status_filtrado or l['status'] == status_filtrado]
            if leitos_no_setor:
                if not setor_escolhido:
                    st.subheader(f"{setor_data['nome']}")
                for quarto, leitos in setor_data["quartos"].items():
                    leitos_filtrados = [l for l in leitos if not status_filtrado or l['status'] == status_filtrado]
                    if not leitos_filtrados:
                        continue
                    ocupados = sum(1 for l in leitos_filtrados if l['status'] != 'Livre')
                    total_leitos = len(leitos_filtrados)
                    st.markdown(criar_barra_status(ocupados, total_leitos), unsafe_allow_html=True)
                    if status_filtrado:
                        # Se filtrado por status, exibe informações compactas
                        st.markdown(f"<h5 style='margin-bottom:5px;'>Quarto {quarto} - {ocupados}/{total_leitos} ocupados</h5>", unsafe_allow_html=True)
                        cols = criar_colunas_dinamicas(len(leitos_filtrados))
                        for idx, leito_info in enumerate(leitos_filtrados):
                            with cols[idx % len(cols)]:
                                exibir_informacoes_leito(leito_info, engine, modo_compacto=True)
                    else:
                        # Se filtrado por setor, mantém o botão e exibe informações detalhadas
                        if st.button(f"Quarto {quarto} - {ocupados}/{total_leitos} ocupados", key=f"quarto_{setor}_{quarto}", use_container_width=True):
                            cols = criar_colunas_dinamicas(len(leitos_filtrados))
                            for idx, leito_info in enumerate(leitos_filtrados):
                                with cols[idx % len(cols)]:
                                    exibir_informacoes_leito(leito_info, engine, modo_compacto=False)
                    st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
    else:
        st.info("Por favor, selecione um setor ou um status de leito para visualizar os quartos e leitos.")

if __name__ == "__main__":
    show()
