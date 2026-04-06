import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Controlo de Frota", page_icon="🚗")
st.title("🚗 Gestão de Frota - Checklist Digital")

# Lista de veículos
veiculos = ["Carro A", "Carro B", "Carro C", "Carro D", "Carro E"]
arquivo_dados = "historico_frota.csv"

# Criar o arquivo de histórico se não existir
if not os.path.exists(arquivo_dados):
    df_init = pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "Impacto", "Observações"])
    df_init.to_csv(arquivo_dados, index=False)

# --- INTERFACE DO UTILIZADOR ---
tab1, tab2, tab3 = st.tabs(["📤 Retirada", "📥 Devolução", "📋 Histórico"])

with tab1:
    st.header("Registar Saída")
    veiculo_sel = st.selectbox("Selecione o Veículo (Saída)", veiculos, key="saida_v")
    nome = st.text_input("Nome do Colaborador", key="saida_n")
    km = st.number_input("KM Atual", min_value=0, step=1, key="km_s")
    
    st.write("**Checklist de Segurança:**")
    c1 = st.checkbox("Pneus e Luzes em condições?")
    c2 = st.checkbox("Documentação no veículo?")
    
    if st.button("Confirmar Retirada"):
        if nome and c1 and c2:
            nova_linha = [datetime.now().strftime("%d/%m/%Y %H:%M"), "RETIRADA", veiculo_sel, nome, km, "N/A", "Checklist OK"]
            df = pd.read_csv(arquivo_dados)
            df.loc[len(df)] = nova_linha
            df.to_csv(arquivo_dados, index=False)
            st.success(f"Retirada de {veiculo_sel} registada!")
        else:
            st.error("Por favor, preencha o nome e confirme o checklist.")

with tab2:
    st.header("Registar Devolução")
    veiculo_dev = st.selectbox("Selecione o Veículo (Chegada)", veiculos, key="dev_v")
    km_fim = st.number_input("KM Final", min_value=0, step=1, key="km_d")
    
    st.write("**Estado do Veículo:**")
    impacto = st.select_slider("Nível de Avaria", options=["Nenhum", "Leve", "Moderado", "Grave"])
    obs = st.text_area("Descrição de Ocorrências")
    
    if st.button("Confirmar Devolução"):
        nova_linha = [datetime.now().strftime("%d/%m/%Y %H:%M"), "DEVOLUÇÃO", veiculo_dev, "N/A", km_fim, impacto, obs]
        df = pd.read_csv(arquivo_dados)
        df.loc[len(df)] = nova_linha
        df.to_csv(arquivo_dados, index=False)
        st.success("Devolução concluída!")

with tab3:
    st.header("Auditoria")
    if os.path.exists(arquivo_dados):
        df_hist = pd.read_csv(arquivo_dados)
        st.dataframe(df_hist)
