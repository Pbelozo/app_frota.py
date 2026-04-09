import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import os
import base64
from io import BytesIO
from PIL import Image

# 1. Configurações Iniciais de Segurança
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗", layout="wide")

# 2. Definição dos Arquivos (Onde seus dados ficam salvos)
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"
ARQ_PECAS = "cadastro_pecas.csv"

# 3. Função de Integridade (Garante que os dados NUNCA sumam no reinício)
def inicializar_banco_dados():
    # Cria os arquivos apenas se eles NÃO existirem. Se existirem, não toca neles.
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Valor_Reparo", "Local_Reparo", "Foto_Base64"]).to_csv(ARQ_HIST, index=False)
    
    if not os.path.exists(ARQ_MOT):
        # Usuário padrão "Paulo" criado apenas na primeira vez para você não ficar trancado fora
        df_init_mot = pd.DataFrame([{"Nome": "Paulo", "Validade_CNH": "2030-12-31", "Status": "Ativo", "Senha": "123", "Admin": "Sim"}])
        df_init_mot.to_csv(ARQ_MOT, index=False)
    
    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=["Veículo", "Placa", "KM_Atual", "Prox_Revisao_KM", "Prox_Revisao_Data", "Status"]).to_csv(ARQ_VEIC, index=False)
    
    if not os.path.exists(ARQ_PECAS):
        pecas = ["1. Capô", "2. Parabrisa", "3. Párachoque dianteiro", "4. Teto"]
        pd.DataFrame({"Item": pecas, "Status": ["Ativo"] * len(pecas)}).to_csv(ARQ_PECAS, index=False)

inicializar_banco_dados()

# --- FUNÇÕES DE APOIO ---
def carregar(arq):
    try:
        # Forçamos o Pandas a ler tudo como String (Texto) para evitar o erro de TypeError das imagens
        return pd.read_csv(arq, dtype=str).fillna("")
    except:
        return pd.DataFrame()

def salvar(df, arq):
    df.to_csv(arq, index=False)

def get_estado_sistemico(v_pla):
    df_h = carregar(ARQ_HIST)
    if df_h.empty: return "Disponível", "0", "Nenhuma"
    df_v = df_h[df_h['Veículo'].str.contains(str(v_pla), na=False)]
    if df_v.empty: return "Disponível", "0", "Nenhuma"
    ult = df_v.iloc[-1]
    est = "Em uso" if ult['Ação'] == "SAÍDA" else "Disponível"
    return est, str(ult['KM']), str(ult['Av_Totais'])

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🚗 Gestão de Frota - Login")
    df_m = carregar(ARQ_MOT)
    
    if not df_m.empty:
        # Filtramos apenas usuários Ativos para o login
        lista_usuarios = sorted(df_m[df_m['Status'] == "Ativo"]['Nome'].unique().tolist())
        
        col_login, _ = st.columns([2, 3])
        with col_login:
            user_sel = st.selectbox("Selecione seu Usuário", [""] + lista_usuarios)
            if user_sel:
                dados_u = df_m[df_m['Nome'] == user_sel].iloc[0]
                senha_input = st.text_input("Senha", type="password")
                
                if st.button("Entrar"):
                    # Chave RESET99 mantida como segurança para você
                    if senha_input == "RESET99" or senha_input == str(dados_u['Senha']):
                        st.session_state.autenticado = True
                        st.session_state.perfil = "admin" if str(dados_u['Admin']) == "Sim" else "motorista"
                        st.session_state.user_logado = user_sel
                        st.rerun()
                    else:
                        st.error("Senha Incorreta")
    else:
        st.error("Erro crítico: Banco de dados de usuários não encontrado.")
    st.stop()

# --- INTERFACE PRINCIPAL (APÓS LOGIN) ---
st.title(f"Frota - Olá, {st.session_state.user_logado}")
if st.sidebar.button("Logoff / Sair"):
    st.session_state.autenticado = False
    st.rerun()

# Definimos as abas baseadas no perfil
if st.session_state.perfil == "admin":
    tabs = st.tabs(["⚙️ Gestão", "📤 Saída", "📥 Chegada", "🔧 Oficina", "📋 Histórico"])
    tab_gestao, tab_saida, tab_chegada, tab_oficina, tab_historico = tabs
else:
    tabs = st.tabs(["📤 Saída", "📥 Chegada", "🔧 Oficina", "📋 Histórico"])
    tab_saida, tab_chegada, tab_oficina, tab_historico = tabs

# --- CONTEÚDO DA ABA GESTÃO (SÓ ADMIN) ---
if st.session_state.perfil == "admin":
    with tab_gestao:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🚗 Cadastro de Veículos")
            df_v = carregar(ARQ_VEIC)
            with st.form("novo_veiculo"):
                v_mod = st.text_input("Modelo")
                v_pla = st.text_input("Placa").upper().strip()
                if st.form_submit_button("Salvar Veículo"):
                    if v_pla and v_mod:
                        if v_pla in df_v['Placa'].values:
                            st.error("Veículo já cadastrado.")
                        else:
                            nova_v = {"Veículo": v_mod, "Placa": v_pla, "KM_Atual": "0", "Prox_Revisao_KM": "0", "Prox_Revisao_Data": str(date.today()), "Status": "Ativo"}
                            df_v = pd.concat([df_v, pd.DataFrame([nova_v])], ignore_index=True)
                            salvar(df_v, ARQ_VEIC)
                            st.success("Salvo!")
                            st.rerun()
            st.dataframe(df_v)

        with c2:
            st.subheader("👤 Cadastro de Usuários")
            df_u = carregar(ARQ_MOT)
            with st.form("novo_user"):
                u_nome = st.text_input("Nome")
                u_adm = st.selectbox("Admin?", ["Não", "Sim"])
                if st.form_submit_button("Salvar Usuário"):
                    if u_nome:
                        nova_u = {"Nome": u_nome, "Validade_CNH": str(date.today()), "Status": "Ativo", "Senha": "123", "Admin": u_adm}
                        df_u = pd.concat([df_u, pd.DataFrame([nova_u])], ignore_index=True)
                        salvar(df_u, ARQ_MOT)
                        st.success("Salvo! Senha padrão: 123")
                        st.rerun()
            st.dataframe(df_u[["Nome", "Status", "Admin"]])

# --- ABA SAÍDA ---
with tab_saida:
    st.header("📤 Registrar Saída")
    df_v_ativos = carregar(ARQ_VEIC)
    df_v_ativos = df_v_ativos[df_v_ativos['Status'] == "Ativo"]
    
    veic_lista = []
    for _, r in df_v_ativos.iterrows():
        status, _, _ = get_estado_sistemico(r['Placa'])
        if status == "Disponível":
            veic_lista.append(f"{r['Veículo']} ({r['Placa']})")
    
    veic_sel = st.selectbox("Veículo Disponível", [""] + veic_lista)
    if veic_sel:
        st.success("Veículo liberado para saída.")
        if st.button("Confirmar Saída"):
            # Lógica de registro simplificada para teste de estabilidade
            st.info("Registro processado.")

# --- ABA HISTÓRICO ---
with tab_historico:
    st.header("📋 Histórico de Movimentações")
    st.dataframe(carregar(ARQ_HIST))
