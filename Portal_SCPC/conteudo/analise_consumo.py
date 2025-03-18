import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib import colormaps
from sqlalchemy import text
import matplotlib.dates as mdates
import locale
from authentication import login

# Configuração da localidade para português
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, 'C')

def obter_dados_material(engine):
    """Obtém os materiais disponíveis."""
    query = text("""
        SELECT cd_material, ds_material
        FROM material
        WHERE ie_situacao = 'A'
    """)
    with engine.connect() as conn:
        df = pd.DataFrame(conn.execute(query).fetchall(), columns=['cd_material', 'ds_material'])
    return df

def obter_dados_local_estoque(engine):
    """Obtém os locais de estoque disponíveis."""
    query = text("""
        SELECT cd_local_estoque, ds_local_estoque
        FROM LOCAL_ESTOQUE
        WHERE ie_situacao = 'A'
        AND ie_centro_inventario = 'S'
    """)
    with engine.connect() as conn:
        df = pd.DataFrame(conn.execute(query).fetchall(), columns=['cd_local_estoque', 'ds_local_estoque'])
    return df

def obter_dados_consumo(engine, cd_material, cd_local=None):
    """Obtém os dados de consumo."""
    query = f"""
        SELECT SUM(qt_estoque) AS qt_consumo, TRUNC(dt_movimento_estoque) AS dt_consumo
        FROM EIS_CONSUMO_MATMED_V
        WHERE cd_material = :cd_material
        AND dt_mesano_referencia = TRUNC(SYSDATE, 'MM')
        AND TRUNC(dt_movimento_estoque, 'MM') = TRUNC(SYSDATE, 'MM')
        AND TRUNC(dt_movimento_estoque) > SYSDATE - 7
    """
    if cd_local:
        query += " AND cd_local_estoque = :cd_local"
    query += " GROUP BY TRUNC(dt_movimento_estoque)"
    with engine.connect() as conn:
        df = pd.DataFrame(conn.execute(text(query), {'cd_material': cd_material, 'cd_local': cd_local}).fetchall(),
                          columns=['qt_consumo', 'dt_consumo'])
    return df

def obter_dados_estoque_atual(engine, cd_material, cd_local=None):
    """Obtém a quantidade atual de estoque do material."""
    query = f"""
        SELECT SUM(qt_estoque)
        FROM saldo_estoque
        WHERE cd_material = :cd_material
        AND dt_mesano_referencia = TRUNC(SYSDATE, 'MM')
    """
    if cd_local:
        query += " AND cd_local_estoque = :cd_local"
    with engine.connect() as conn:
        result = conn.execute(text(query), {'cd_material': cd_material, 'cd_local': cd_local}).fetchone()
    return result[0] if result and result[0] is not None else 0

def plotar_consumo(df, estoque_atual):
    """Plota um gráfico de consumo."""
    plt.figure(figsize=(8, 4))
    if df.empty:
        st.warning("Nenhum consumo nos últimos 7 dias.")
        plt.bar(['Último Saldo'], [estoque_atual], color='lightgrey')
        plt.title('Consumo de Item nos Últimos 7 Dias (Sem Movimento)', fontsize=14)
        plt.ylabel('Quantidade em Estoque', fontsize=12)
        plt.text(0, estoque_atual, int(estoque_atual), ha='center', va='bottom')
    else:
        max_consumo = df['qt_consumo'].max()
        normalized = 1 - (df['qt_consumo'] / max_consumo)
        colormap = colormaps['RdYlGn']
        colors = colormap(normalized)
        plt.bar(df['dt_consumo'], df['qt_consumo'], color=colors)
        plt.title('Consumo de Item nos Últimos 7 Dias', fontsize=14)
        plt.xlabel('Data', fontsize=12)
        plt.ylabel('Quantidade Consumida', fontsize=12)
        plt.xticks(rotation=45, fontsize=10)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
    plt.grid(axis='y')
    plt.tight_layout()
    st.pyplot(plt)

def show():
    """Interface principal da aplicação Streamlit."""
    st.title("📊 Análise de Consumo de Materiais")
    
    # Verifica se o usuário está autenticado
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        login()
        return
    
    # Verifica se há conexão com o banco de dados na sessão
    if not hasattr(st.session_state, 'db_engine'):
        st.error("Erro: Conexão com o banco de dados não encontrada.")
        return
    
    engine = st.session_state.db_engine
    df_materials = obter_dados_material(engine)
    df_locais = obter_dados_local_estoque(engine)
    
    if df_materials.empty:
        st.warning("Nenhum material disponível.")
        return
    
    if df_locais.empty:
        st.warning("Nenhum local de estoque disponível.")
        return
    
    material_options = df_materials.set_index('cd_material')
    selected_material = st.selectbox("📦 Escolha um material:", material_options['ds_material'])
    
    local_options = df_locais.set_index('cd_local_estoque')
    locais_com_todos = pd.concat([
        pd.DataFrame({'cd_local_estoque': [None], 'ds_local_estoque': ['Todos Locais']}),
        local_options.reset_index()
    ])
    selected_local = st.selectbox("📍 Escolha um local:", locais_com_todos['ds_local_estoque'])
    
    cd_material = material_options.loc[material_options['ds_material'] == selected_material].index[0]
    cd_local = None if selected_local == 'Todos Locais' else local_options.loc[local_options['ds_local_estoque'] == selected_local].index[0]
    
    df_consumo = obter_dados_consumo(engine, cd_material, cd_local)
    estoque_atual = obter_dados_estoque_atual(engine, cd_material, cd_local)
    
    plotar_consumo(df_consumo, estoque_atual)
    st.metric("📌 Estoque Atual", f"{estoque_atual} unidades")

if __name__ == "__main__":
    show()
