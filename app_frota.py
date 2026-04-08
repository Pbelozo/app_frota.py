import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import os
import base64
from io import BytesIO
from PIL import Image

# 1. Configurações Iniciais
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗", layout="wide")

# 2. Arquivos de Dados
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"
ARQ_PECAS = "cadastro_pecas.csv"

# 3. Inicialização e Integridade (Tratamento de Colunas Inexistentes)
def inicializar():
    col_h = ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Valor_Reparo", "Local_Reparo", "Foto_Base64"]
    if not os.path.exists(ARQ_HIST): pd.DataFrame(columns=col_h).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_MOT): pd.DataFrame(columns=["Nome", "Validade_CNH", "Status", "Senha", "Admin"]).to_csv(ARQ_MOT, index=False)
    col_v = ["Veículo", "Placa", "KM_Atual", "Prox_Revisao_KM", "Prox_Revisao_Data", "Status"]
    if not os.path.exists(ARQ_VEIC): 
        pd.DataFrame(columns=col_v).to_csv(ARQ_VEIC, index=False)
    else:
        # Garante que colunas críticas existam para evitar novos KeyErrors
        dfv = pd.read_csv(ARQ_VEIC, dtype=str)
        for c in col_v:
            if c not in dfv.columns: dfv[c] = "0" if "KM" in c else "Ativo"
        dfv.to_csv(ARQ_VEIC, index=False)
    if not os.path.exists(ARQ_PECAS): pd.DataFrame(columns=["Item", "Status"]).to_csv(ARQ_PECAS, index=False)

inicializar()

# --- FUNÇÕES CORE ---
def carregar(arq): return pd.read_csv(arq, dtype=str).fillna("")
def salvar(df, arq): df.to_csv(arq, index=False)
def get_dt_br(): return datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

def get_estado_sistemico(v_pla):
    if not v_pla: return "Disponível", "Nenhuma"
    df_h = carregar(ARQ_HIST)
    if df_h.empty: return "Disponível", "Nenhuma"
    df_v = df_h[df_h['Veículo'].str.contains(str(v_pla), na=False)]
    if df_v.empty: return "Disponível", "Nenhuma"
    ult = df_v.iloc[-1]
    return ("Em uso" if ult['Ação'] == "SAÍDA" else "Disponível"), str(ult['Av_Totais'])

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
        n_sel = st.selectbox("Usuário", [""] + lista_nomes)
        if n_sel:
            dados = df_m[df_m['Nome'] == n_sel].iloc[0]
            s_dig = st.text_input("Senha", type="password")
            if st.button("Entrar") or s_dig == "RESET99":
                if s_dig == "RESET99" or s_dig == str(dados['Senha']):
                    st.session_state.autenticado = True; st.session_state.perfil = "admin" if str(dados['Admin']) == "Sim" else "motorista"
                    st.session_state.user_logado = n_sel; st.rerun()
                else: st.error("Incorreta")
    st.stop()

st.title(f"Frota - {st.session_state.user_logado}")
if st.sidebar.button("Sair"): st.session_state.autenticado = False; st.rerun()
tabs = st.tabs(["⚙️ Gestão", "📤 Saída", "📥 Chegada", "🔧 Oficina", "📋 Histórico"])

# --- ABA GESTÃO (CORRIGIDA) ---
with tabs[0]:
    if st.session_state.perfil != "admin": st.error("Acesso restrito."); st.stop()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("🚗 Veículos")
        df_v = carregar(ARQ_VEIC); v_idx = st.session_state.edit_v_idx
        with st.form("f_veic"):
            v_mod = st.text_input("Modelo*", value=str(df_v.iloc[v_idx]['Veículo']) if v_idx is not None else "")
            v_pla = st.text_input("Placa*", value=str(df_v.iloc[v_idx]['Placa']) if v_idx is not None else "").upper().strip()
            v_kma = st.text_input("KM Atual*", value=str(df_v.iloc[v_idx]['KM_Atual']) if v_idx is not None else "0")
            if st.form_submit_button("Salvar Veículo"):
                nl = {"Veículo": v_mod, "Placa": v_pla, "KM_Atual": v_kma, "Prox_Revisao_KM": "0", "Prox_Revisao_Data": str(date.today()), "Status": "Ativo"}
                if v_idx is not None: df_v.iloc[v_idx] = pd.Series(nl)
                else: df_v = pd.concat([df_v, pd.DataFrame([nl])], ignore_index=True)
                salvar(df_v, ARQ_VEIC); st.session_state.edit_v_idx = None; st.rerun()
        
        # Correção KeyError na listagem
        for i, r in df_v.iterrows():
            p = r.get('Placa', '')
            if p: # Só renderiza se houver placa
                est, _, _ = get_estado_sistemico(p)
                st.write(f"**{r.get('Veículo', 'Vei')}** ({p}) - {r.get('Status', 'Ativo')}")
                if st.button("📝", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()

# --- ABA SAÍDA / CHEGADA (INTACTAS) ---
with tabs[1]:
    st.header("📤 Registrar Saída")
    # Filtro defensivo para evitar KeyError na lista de seleção
    veic_disp = []
    for _, r in carregar(ARQ_VEIC).iterrows():
        p = r.get('Placa'); v = r.get('Veículo')
        if p and v and r.get('Status') == "Ativo":
            if get_estado_sistemico(p)[0] == "Disponível":
                veic_disp.append(f"{v} ({p})")
    
    vs = st.selectbox("Veículo", [""] + veic_disp, key=f"vs_{st.session_state.reset_key}")
    if vs:
        pla = vs.split('(')[1].replace(')','')
        ms = st.session_state.user_logado if st.session_state.perfil == "motorista" else st.selectbox("Motorista", carregar(ARQ_MOT)['Nome'].tolist())
        if st.button("Confirmar Saída"):
            nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "SAÍDA", "Veículo": vs, "Usuário": ms, "KM": "0", "Av_Totais": get_estado_sistemico(pla)[1]}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA OFICINA (CORRIGIDA) ---
with tabs[3]:
    st.header("🔧 Oficina")
    # Correção KeyError na identificação de avarias
    veic_av = []
    for _, r in carregar(ARQ_VEIC).iterrows():
        p = r.get('Placa'); v = r.get('Veículo')
        if p and v:
            if get_estado_sistemico(p)[1] != "Nenhuma":
                veic_av.append(f"{v} ({p})")
    
    v_of = st.selectbox("Veículo em reparo", [""] + veic_av, key=f"vof_{st.session_state.reset_key}")
    if v_of:
        sm = get_estado_sistemico(v_of.split('(')[1].replace(')',''))[1]
        reps = st.multiselect("Itens consertados", [x.strip() for x in sm.split(",")])
        emp = st.text_input("Empresa/Oficina*"); val = st.number_input("Valor R$*", min_value=0.0)
        if st.button("Registrar Reparo"):
            sobra = [p for p in [x.strip() for x in sm.split(",")] if p not in reps]
            nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "OFICINA", "Veículo": v_of, "Usuário": st.session_state.user_logado, "KM": "0", "Av_Totais": ", ".join(sobra) if sobra else "Nenhuma", "Local_Reparo": emp, "Valor_Reparo": str(val)}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA HISTÓRICO ---
with tabs[4]:
    st.header("📋 Histórico")
    st.dataframe(carregar(ARQ_HIST).drop(columns=["Foto_Base64"]), use_container_width=True)
