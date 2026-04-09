# App de Gestão de Frota - Streamlit
# Versão simplificada e funcional baseada na especificação

import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ==========================
# CONFIG
# ==========================
DATA_PATH = "data"
os.makedirs(DATA_PATH, exist_ok=True)

ARQ_VEIC = f"{DATA_PATH}/veiculos.csv"
ARQ_USU = f"{DATA_PATH}/usuarios.csv"
ARQ_MOV = f"{DATA_PATH}/movimentacoes.csv"
ARQ_AVA = f"{DATA_PATH}/avarias.csv"

# ==========================
# FUNÇÕES BASE
# ==========================

def carregar(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df


def salvar(df, path):
    df.to_csv(path, index=False)

# ==========================
# INICIALIZAÇÃO
# ==========================

def init_data():
    if not os.path.exists(ARQ_VEIC):
        salvar(pd.DataFrame(columns=["placa","modelo","km","status","bloqueado"]), ARQ_VEIC)
    if not os.path.exists(ARQ_USU):
        salvar(pd.DataFrame(columns=["usuario","senha","admin","cnh_validade","bloqueado"]), ARQ_USU)
    if not os.path.exists(ARQ_MOV):
        salvar(pd.DataFrame(columns=["placa","usuario","data_saida","data_retorno","km_saida","km_retorno","status"]), ARQ_MOV)
    if not os.path.exists(ARQ_AVA):
        salvar(pd.DataFrame(columns=["descricao"]), ARQ_AVA)

init_data()

# ==========================
# LOGIN
# ==========================

if "user" not in st.session_state:
    st.session_state.user = None

usuarios = carregar(ARQ_USU)

if st.session_state.user is None:
    st.title("Login")
    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        u = usuarios[(usuarios["usuario"] == user) & (usuarios["senha"] == senha)]
        if not u.empty:
            st.session_state.user = user
            st.session_state.admin = bool(u.iloc[0]["admin"])
            st.success("Login realizado")
            st.rerun()
        else:
            st.error("Usuário inválido")

    st.stop()

# ==========================
# MENU
# ==========================

menu = ["Retirada", "Devolução", "Gestão"]
if st.session_state.admin:
    menu.append("Cadastros")

aba = st.sidebar.selectbox("Menu", menu)

veiculos = carregar(ARQ_VEIC)
mov = carregar(ARQ_MOV)

# ==========================
# RETIRADA
# ==========================

if aba == "Retirada":
    st.title("Retirada de Veículo")

    if not veiculos.empty:
        disp = veiculos[(veiculos["status"] == "Disponível") & (veiculos["bloqueado"] == False)]

        placa = st.selectbox("Veículo", disp["placa"] if not disp.empty else [])
        km = st.number_input("KM Saída", min_value=0)

        if st.button("Confirmar saída"):
            if placa:
                nova = pd.DataFrame([{
                    "placa": placa,
                    "usuario": st.session_state.user,
                    "data_saida": datetime.now(),
                    "data_retorno": "",
                    "km_saida": km,
                    "km_retorno": "",
                    "status": "Em uso"
                }])

                mov = pd.concat([mov, nova], ignore_index=True)
                salvar(mov, ARQ_MOV)

                veiculos.loc[veiculos["placa"] == placa, "status"] = "Em uso"
                salvar(veiculos, ARQ_VEIC)

                st.success("Saída registrada")
                st.rerun()

# ==========================
# DEVOLUÇÃO
# ==========================

if aba == "Devolução":
    st.title("Devolução de Veículo")

    em_uso = mov[mov["status"] == "Em uso"]

    placa = st.selectbox("Veículo", em_uso["placa"] if not em_uso.empty else [])
    km = st.number_input("KM Retorno", min_value=0)

    if st.button("Confirmar devolução"):
        if placa:
            idx = mov[(mov["placa"] == placa) & (mov["status"] == "Em uso")].index
            mov.loc[idx, "data_retorno"] = datetime.now()
            mov.loc[idx, "km_retorno"] = km
            mov.loc[idx, "status"] = "Finalizado"
            salvar(mov, ARQ_MOV)

            veiculos.loc[veiculos["placa"] == placa, "status"] = "Disponível"
            veiculos.loc[veiculos["placa"] == placa, "km"] = km
            salvar(veiculos, ARQ_VEIC)

            st.success("Devolução registrada")
            st.rerun()

# ==========================
# GESTÃO
# ==========================

if aba == "Gestão":
    st.title("Gestão")

    if not veiculos.empty:
        for i, v in veiculos.iterrows():
            col1, col2, col3 = st.columns([3,1,1])
            col1.write(f"{v['placa']} - {v['modelo']}")

            if col2.button("Bloquear", key=f"b{i}"):
                veiculos.loc[i, "bloqueado"] = True
                salvar(veiculos, ARQ_VEIC)
                st.rerun()

            if col3.button("Excluir", key=f"e{i}"):
                if v['placa'] not in mov['placa'].values:
                    veiculos = veiculos.drop(i)
                    salvar(veiculos, ARQ_VEIC)
                    st.rerun()
                else:
                    st.warning("Veículo com histórico")

# ==========================
# CADASTROS
# ==========================

if aba == "Cadastros" and st.session_state.admin:
    st.title("Cadastro de Veículos")

    placa = st.text_input("Placa")
    modelo = st.text_input("Modelo")

    if st.button("Cadastrar"):
        if placa not in veiculos.get("placa", []).values:
            novo = pd.DataFrame([{
                "placa": placa,
                "modelo": modelo,
                "km": 0,
                "status": "Disponível",
                "bloqueado": False
            }])
            veiculos = pd.concat([veiculos, novo], ignore_index=True)
            salvar(veiculos, ARQ_VEIC)
            st.success("Cadastrado")
            st.rerun()
        else:
            st.error("Duplicado")
