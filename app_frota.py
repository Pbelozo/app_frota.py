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

# 3. Inicialização e Proteção de Dados
def inicializar():
    if not os.path.exists(ARQ_MOT):
        pd.DataFrame(columns=["Nome", "Validade_CNH", "Status", "Senha", "Admin"]).to_csv(ARQ_MOT, index=False)
    
    # Se o arquivo existir, vamos garantir que ele não esteja corrompido
    try:
        df = pd.read_csv(ARQ_MOT)
        if df.empty:
            # Se estiver vazio, cria o Paulo como admin padrão
            pd.DataFrame([{"Nome": "Paulo", "Validade_CNH": "2030-01-01", "Status": "Ativo", "Senha": "admin", "Admin": "Sim"}]).to_csv(ARQ_MOT, index=False)
    except:
        pd.DataFrame([{"Nome": "Paulo", "Validade_CNH": "2030-01-01", "Status": "Ativo", "Senha": "admin", "Admin": "Sim"}]).to_csv(ARQ_MOT, index=False)

    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Int_KM", "Int_Meses", "Alert_KM", "Alert_Dias", "Status"]).to_csv(ARQ_VEIC, index=False)
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Valor_Reparo", "Local_Reparo", "Foto_Base64"]).to_csv(ARQ_HIST, index=False)

inicializar()

def carregar(arq): return pd.read_csv(arq).fillna("")
def salvar(df, arq): df.to_csv(arq, index=False)

# --- LOGIN ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🚗 Gestão de Frota - Login de Emergência")
    
    # Criamos uma lista de usuários e adicionamos o acesso de emergência
    df_m = carregar(ARQ_MOT)
    lista_login = sorted(df_m['Nome'].unique().tolist())
    lista_login.append("ADMIN_PROVISORIO")
    
    user_sel = st.selectbox("Selecione seu Usuário", [""] + lista_login)
    
    if user_sel == "ADMIN_PROVISORIO":
        senha = st.text_input("Senha de Emergência", type="password")
        if st.button("Acessar"):
            if senha == "admin123":
                st.session_state.autenticado = True
                st.session_state.perfil = "admin"
                st.session_state.user_logado = "Paulo"
                st.rerun()
            else: st.error("Senha incorreta")
    
    elif user_sel != "":
        dados = df_m[df_m['Nome'] == user_sel].iloc[0]
        senha_i = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if str(senha_i) == str(dados['Senha']):
                st.session_state.autenticado = True
                st.session_state.perfil = "admin" if str(dados['Admin']) == "Sim" else "motorista"
                st.session_state.user_logado = user_sel
                st.rerun()
    st.stop()

# --- ABA GESTÃO (PARA VOCÊ ARRUMAR SEU NOME) ---
st.title(f"Bem-vindo, {st.session_state.user_logado}")
if st.sidebar.button("Sair"): st.session_state.autenticado = False; st.rerun()

t1, t2 = st.tabs(["⚙️ Gestão de Usuários", "📋 Outras Funções"])

with t1:
    st.subheader("Corrigir Cadastro")
    df_u = carregar(ARQ_MOT)
    st.write("Usuários atuais no banco de dados:")
    st.dataframe(df_u)
    
    with st.form("fix_paulo"):
        st.write("Recadastrar Paulo como Admin")
        p_nome = st.text_input("Nome", value="Paulo")
        p_senha = st.text_input("Nova Senha", value="123")
        if st.form_submit_button("Resetar meu Usuário"):
            # Remove qualquer 'Paulo' antigo e adiciona o novo limpo
            df_u = df_u[df_u['Nome'] != "Paulo"]
            novo = {"Nome": p_nome, "Validade_CNH": "2030-01-01", "Status": "Ativo", "Senha": p_senha, "Admin": "Sim"}
            df_u = pd.concat([df_u, pd.DataFrame([novo])], ignore_index=True)
            salvar(df_u, ARQ_MOT)
            st.success("Usuário Paulo restaurado com sucesso! Agora você pode sair e logar normalmente.")

with t2:
    st.write("Use a aba anterior para restaurar seu acesso principal.")
