import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import os
import base64
from io import BytesIO
from PIL import Image

# 1. Configurações Iniciais
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗", layout="wide")

# 2. Definição dos Arquivos
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"
ARQ_PECAS = "cadastro_pecas.csv"

# 3. Função de Integridade (Cria os arquivos se deletados e recupera o Paulo)
def inicializar_sistema():
    # Garante o Histórico
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Valor_Reparo", "Local_Reparo", "Foto_Base64"]).to_csv(ARQ_HIST, index=False)
    
    # Garante o Cadastro de Motoristas (Auto-recuperação do Paulo)
    if not os.path.exists(ARQ_MOT):
        df_recupera = pd.DataFrame([{"Nome": "Paulo", "Validade_CNH": "2030-12-31", "Status": "Ativo", "Senha": "123", "Admin": "Sim"}])
        df_recupera.to_csv(ARQ_MOT, index=False)
    else:
        # Se o arquivo existe mas está vazio por erro, recria o Paulo
        try:
            df_teste = pd.read_csv(ARQ_MOT)
            if df_teste.empty:
                pd.DataFrame([{"Nome": "Paulo", "Validade_CNH": "2030-12-31", "Status": "Ativo", "Senha": "123", "Admin": "Sim"}]).to_csv(ARQ_MOT, index=False)
        except:
            pd.DataFrame([{"Nome": "Paulo", "Validade_CNH": "2030-12-31", "Status": "Ativo", "Senha": "123", "Admin": "Sim"}]).to_csv(ARQ_MOT, index=False)

    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=["Veículo", "Placa", "KM_Atual", "Prox_Revisao_KM", "Prox_Revisao_Data", "Status"]).to_csv(ARQ_VEIC, index=False)

inicializar_sistema()

# --- FUNÇÕES DE APOIO ---
def carregar(arq):
    return pd.read_csv(arq, dtype=str).fillna("")

def salvar(df, arq):
    df.to_csv(arq, index=False)

def get_dt_br():
    return datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

# --- LOGIN ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🚗 Gestão de Frota - Login")
    df_m = carregar(ARQ_MOT)
    
    lista_login = sorted(df_m[df_m['Status'] == "Ativo"]['Nome'].unique().tolist())
    
    col_l, _ = st.columns([2, 3])
    with col_l:
        u_sel = st.selectbox("Selecione seu Usuário", [""] + lista_login)
        if u_sel:
            dados = df_m[df_m['Nome'] == u_sel].iloc[0]
            senha_dig = st.text_input("Senha", type="password")
            
            # Botão Entrar + Chave de Reset99 por segurança
            if st.button("Acessar Sistema"):
                if senha_dig == "RESET99" or senha_dig == str(dados['Senha']):
                    st.session_state.autenticado = True
                    st.session_state.perfil = "admin" if str(dados['Admin']) == "Sim" else "motorista"
                    st.session_state.user_logado = u_sel
                    st.rerun()
                else:
                    st.error("Senha Incorreta")
    st.stop()

# --- INTERFACE PRINCIPAL ---
st.title(f"Sistema Frota - Olá, {st.session_state.user_logado}")
if st.sidebar.button("Logoff / Sair"):
    st.session_state.autenticado = False
    st.rerun()

# Abas baseadas no perfil
menu = ["📤 Saída", "📥 Chegada", "🔧 Oficina", "📋 Histórico"]
if st.session_state.perfil == "admin": menu.insert(0, "⚙️ Gestão")
tabs = st.tabs(menu)

# --- ABA GESTÃO (SÓ ADMIN) ---
if st.session_state.perfil == "admin":
    with tabs[0]:
        st.subheader("⚙️ Painel de Controle")
        col1, col2 = st.columns(2)
        with col1:
            st.write("🚗 **Cadastrar Veículo**")
            df_v = carregar(ARQ_VEIC)
            with st.form("f_v"):
                mod = st.text_input("Modelo")
                pla = st.text_input("Placa").upper().strip()
                if st.form_submit_button("Salvar"):
                    if mod and pla:
                        nova_v = pd.DataFrame([{"Veículo": mod, "Placa": pla, "KM_Atual": "0", "Status": "Ativo"}])
                        salvar(pd.concat([df_v, nova_v]), ARQ_VEIC)
                        st.rerun()
            st.dataframe(df_v)
        
        with col2:
            st.write("👤 **Cadastrar Motorista**")
            df_u = carregar(ARQ_MOT)
            with st.form("f_u"):
                n = st.text_input("Nome")
                a = st.selectbox("Administrador?", ["Não", "Sim"])
                if st.form_submit_button("Salvar"):
                    if n:
                        # Correção do erro de tipo: Forçamos tudo para String antes de salvar
                        nova_u = pd.DataFrame([{"Nome": str(n), "Validade_CNH": "2030-01-01", "Status": "Ativo", "Senha": "123", "Admin": str(a)}])
                        salvar(pd.concat([df_u, nova_u]), ARQ_MOT)
                        st.rerun()
            st.dataframe(df_u[["Nome", "Admin", "Status"]])

# --- ABA HISTÓRICO ---
with tabs[-1]:
    st.header("📋 Histórico Geral")
    st.dataframe(carregar(ARQ_HIST))
