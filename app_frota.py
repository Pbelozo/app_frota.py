import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import os
import base64
from io import BytesIO
from PIL import Image

# 1. Configuração da Página
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗", layout="wide")

# 2. Arquivos
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"
ARQ_PECAS = "cadastro_pecas.csv"

# 3. Inicialização e Correção de Tipos
def inicializar():
    if not os.path.exists(ARQ_HIST): pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Valor_Reparo", "Local_Reparo", "Foto_Base64"]).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_MOT): pd.DataFrame(columns=["Nome", "Validade_CNH", "Status", "Senha", "Admin"]).to_csv(ARQ_MOT, index=False)
    if not os.path.exists(ARQ_VEIC): pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Int_KM", "Int_Meses", "Alert_KM", "Alert_Dias", "Status"]).to_csv(ARQ_VEIC, index=False)
    if not os.path.exists(ARQ_PECAS):
        pd.DataFrame({"Item": ["Capô", "Teto", "Parabrisa"], "Status": ["Ativo"]*3}).to_csv(ARQ_PECAS, index=False)

inicializar()

def carregar(arq): return pd.read_csv(arq, dtype=str).fillna("")
def salvar(df, arq): df.to_csv(arq, index=False)
def get_dt_br(): return datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

# --- LOGIN ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0
if 'edit_v_idx' not in st.session_state: st.session_state.edit_v_idx = None
if 'edit_u_idx' not in st.session_state: st.session_state.edit_u_idx = None

if not st.session_state.autenticado:
    st.title("🚗 Gestão de Frota - Login")
    df_m = carregar(ARQ_MOT)
    lista_nomes = sorted(df_m[df_m['Status'] == "Ativo"]['Nome'].unique().tolist())
    
    col_l, _ = st.columns([2, 3])
    with col_l:
        if not lista_nomes:
            st.warning("Nenhum usuário cadastrado.")
            s_mestra = st.text_input("Senha Mestra para Configuração Inicial", type="password")
            if st.button("Acessar") and s_mestra == "admin123":
                st.session_state.autenticado = True
                st.session_state.perfil = "admin"
                st.session_state.user_logado = "Configurador"
                st.rerun()
        else:
            n_sel = st.selectbox("Selecione seu Usuário", [""] + lista_nomes)
            if n_sel:
                dados = df_m[df_m['Nome'] == n_sel].iloc[0]
                s_i = st.text_input("Senha", type="password")
                if st.button("Entrar"):
                    if str(s_i) == str(dados['Senha']):
                        st.session_state.autenticado = True
                        st.session_state.perfil = "admin" if str(dados['Admin']) == "Sim" else "motorista"
                        st.session_state.user_logado = n_sel
                        st.rerun()
                    else: st.error("Senha Incorreta")
    st.stop()

# --- INTERFACE (APÓS LOGIN) ---
st.title(f"Sistema Frota - Logado como: {st.session_state.user_logado}")
if st.sidebar.button("Sair"): st.session_state.autenticado = False; st.rerun()

tabs = st.tabs(["⚙️ Gestão & Cadastro", "📤 Saída", "📥 Chegada", "🔧 Oficina", "📋 Histórico"])

# --- ABA GESTÃO ---
with tabs[0]:
    if st.session_state.perfil != "admin": st.error("Acesso restrito ao Admin."); st.stop()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("👤 Cadastro de Usuários")
        df_u = carregar(ARQ_MOT)
        u_idx = st.session_state.edit_u_idx
        with st.form("f_u"):
            un = st.text_input("Nome Completo", value=str(df_u.iloc[u_idx]['Nome']) if u_idx is not None else "")
            uc = st.date_input("Validade CNH")
            us = st.text_input("Senha de Acesso", type="password")
            ua = st.selectbox("Administrador?", ["Não", "Sim"], index=1 if u_idx is not None and df_u.iloc[u_idx]['Admin']=="Sim" else 0)
            if st.form_submit_button("Salvar Usuário"):
                nova_linha = {"Nome": un, "Validade_CNH": str(uc), "Status": "Ativo", "Senha": str(us), "Admin": ua}
                if u_idx is not None: df_u.iloc[u_idx] = pd.Series(nova_linha)
                else: df_u = pd.concat([df_u, pd.DataFrame([nova_linha])], ignore_index=True)
                salvar(df_u, ARQ_MOT); st.session_state.edit_u_idx = None; st.rerun()
        for i, r in df_u.iterrows():
            st.write(f"ID {i}: {r['Nome']} (Adm: {r['Admin']})")
            if st.button("📝 Editar", key=f"eu{i}"): st.session_state.edit_u_idx = i; st.rerun()

    with c2:
        st.subheader("🚗 Cadastro de Veículos")
        # Formulário simplificado de veículo para você restabelecer a frota
        df_v = carregar(ARQ_VEIC)
        with st.form("f_v"):
            vm = st.text_input("Modelo"); vp = st.text_input("Placa").upper()
            if st.form_submit_button("Cadastrar Veículo"):
                nv = {"Veículo": vm, "Placa": vp, "Status": "Ativo", "Ult_Revisao_KM": "0", "Ult_Revisao_Data": str(date.today()), "Int_KM": "10000", "Int_Meses": "12", "Alert_KM": "500", "Alert_Dias": "30"}
                salvar(pd.concat([df_v, pd.DataFrame([nv])], ignore_index=True), ARQ_VEIC); st.rerun()
        st.dataframe(df_v[["Veículo", "Placa", "Status"]])

st.info("⚠️ Após cadastrar seu usuário, saia do sistema e entre novamente com seu nome e senha pessoal.")
