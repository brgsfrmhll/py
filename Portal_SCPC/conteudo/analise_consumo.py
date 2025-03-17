import pandas as pd
import oracledb
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib import colormaps
from sqlalchemy import create_engine
import matplotlib.dates as mdates

# Inicializa o cliente Oracle Instant Client
oracledb.init_oracle_client(lib_dir=r"C:\instantclient_23_7")

# Credenciais de acesso ao banco de dados
USERNAME = 'TASY'
PASSWORD = 'aloisk'
HOST = '129.151.37.16'
PORT = 1521
SERVICE = 'dbprod.santacasapc'

def conectar_ao_banco():
    """Estabelece uma conexão com o banco de dados Oracle usando SQLAlchemy e retorna a conexão."""
    try:
        connection_string = f'oracle+oracledb://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/?service_name={SERVICE}'
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        st.error(f"Erro ao conectar ao Oracle: {e}")
        return None

def obter_dados_material(engine):
    """Obtém os dados dos materiais disponíveis para seleção."""
    query_materials = """
    SELECT cd_material,
           ds_material
    FROM material a
    WHERE a.ie_situacao = 'A'
    """
    df_materials = pd.read_sql(query_materials, engine)
    return df_materials

def obter_dados_local_estoque(engine):
    """Obtém os dados dos locais de estoque disponíveis para seleção."""
    query_locais = """
    SELECT cd_local_estoque,
           ds_local_estoque
    FROM LOCAL_ESTOQUE
    WHERE ie_situacao = 'A'
      AND ie_centro_inventario = 'S'
    """
    df_locais = pd.read_sql(query_locais, engine)
    return df_locais

def obter_dados_consumo(engine, cd_material, cd_local=None):
    """Obtém os dados de consumo do banco de dados para o material e local selecionados.
       Se cd_local for None, retorna o consumo total sem filtrar por local."""
    query_consumo = f"""
    SELECT SUM(qt_estoque) AS qt_consumo,
           TRUNC(dt_movimento_estoque) AS dt_consumo
    FROM EIS_CONSUMO_MATMED_V
    WHERE cd_material = {cd_material}
      AND dt_mesano_referencia = TRUNC(SYSDATE, 'MM')
      AND TRUNC(dt_movimento_estoque, 'MM') = TRUNC(SYSDATE, 'MM')
      AND TRUNC(dt_movimento_estoque) > SYSDATE - 7
    """
    if cd_local is not None:
        query_consumo += f" AND cd_local_estoque = {cd_local}"
    query_consumo += """ GROUP BY TRUNC(dt_movimento_estoque)"""
    df_consumo = pd.read_sql(query_consumo, engine)
    return df_consumo

def obter_dados_estoque_atual(engine, cd_material, cd_local):
    """Obtém a quantidade atual de estoque do material no local selecionado."""
    query_estoque_atual = f"""
    SELECT SUM(qt_estoque)
    FROM saldo_estoque
    WHERE cd_material = {cd_material}
      AND dt_mesano_referencia = TRUNC(SYSDATE, 'MM')
    """
    if cd_local is not None:
        query_estoque_atual += f" AND cd_local_estoque = {cd_local}"
    estoque_atual = pd.read_sql(query_estoque_atual, engine)
    if not estoque_atual.empty:
        return estoque_atual.iloc[0, 0] if estoque_atual.iloc[0, 0] is not None else 0
    return 0

def plotar_consumo(df, estoque_atual):
    """Plota um gráfico de barras para o consumo de itens ao longo do tempo com cores em gradiente."""
    plt.figure(figsize=(8, 4))  # Tamanho reduzido
    
    if df.empty:
        st.warning("Não houveram consumo nos últimos 7 dias.")
        plt.bar(['Último Saldo'], [estoque_atual], color='lightgrey')
        plt.title('Consumo de Item nos Últimos 7 Dias (Sem Movimento)', fontsize=14)
        plt.ylabel('Quantidade em Estoque', fontsize=12)
        plt.text(0, estoque_atual, int(estoque_atual), ha='center', va='bottom')
    else:
        max_consumo = df['qt_consumo'].max() if not df.empty else 1
        normalized_consumo = 1 - (df['qt_consumo'] / max_consumo)
        colormap = colormaps['RdYlGn']
        colors = colormap(normalized_consumo)
        bar_container = plt.bar(df['dt_consumo'], df['qt_consumo'], color=colors)
        plt.title('Consumo de Item nos Últimos 7 Dias', fontsize=14)
        plt.xlabel('Data', fontsize=12)
        plt.ylabel('Quantidade Consumida', fontsize=12)
        plt.xticks(rotation=45, fontsize=10)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        for bar in bar_container:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval, int(yval), ha='center', va='bottom', fontsize=10)
    
    plt.grid(axis='y')
    plt.tight_layout()
    st.pyplot(plt, use_container_width=True)

def show():
    """Função principal da aplicação Streamlit."""
    st.title("Análise de Consumo de Materiais")
    engine = conectar_ao_banco()
    if engine:
        df_materials = obter_dados_material(engine)
        df_locais = obter_dados_local_estoque(engine)
        if not df_materials.empty and not df_locais.empty:
            material_options = df_materials.set_index('cd_material')
            selected_material = st.selectbox("Escolha um material:", material_options['ds_material'], index=0)
            local_options = df_locais.set_index('cd_local_estoque')
            locais_com_todos = pd.DataFrame({'cd_local_estoque': [0], 'ds_local_estoque': ['Todos Locais de Estoque']})
            locais_com_todos = pd.concat([locais_com_todos, local_options.reset_index()], ignore_index=True)
            selected_local = st.selectbox("Escolha um local de estoque:", locais_com_todos['ds_local_estoque'], index=0)
            cd_material = material_options.loc[material_options['ds_material'] == selected_material].index[0]
            cd_local = None if selected_local == 'Todos Locais de Estoque' else local_options.loc[local_options['ds_local_estoque'] == selected_local].index[0]
            df_consumo = obter_dados_consumo(engine, cd_material, cd_local)
            estoque_atual = obter_dados_estoque_atual(engine, cd_material, cd_local)
            plotar_consumo(df_consumo, estoque_atual)
            st.metric("Quantidade em Estoque Atual:", f"{estoque_atual}")
        elif df_materials.empty:
            st.warning("Nenhum material disponível.")
        elif df_locais.empty:
            st.warning("Nenhum local de estoque disponível.")

if __name__ == "__main__":
    show()
