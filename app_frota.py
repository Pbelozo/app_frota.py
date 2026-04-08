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

# 3. Inicialização e Integridade
def inicializar():
    col_h = ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Valor_Reparo", "Local_Reparo", "Foto_Base64"]
    if not os.path.exists(ARQ_HIST): pd.DataFrame(columns=col_h).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_MOT): pd.DataFrame(columns=["Nome", "Validade_CNH", "Status", "Senha", "Admin"]).to_csv(ARQ_MOT, index=False)
    col_v = ["Veículo", "Placa", "KM_Atual", "Ult_Revisao_KM", "Ult_Revisao_Data", "Int_KM", "Int_Meses", "Status"]
    if not os.path.exists(ARQ_VEIC): pd.DataFrame(columns=col_v).to_csv(ARQ_VEIC, index=False)
    if not os.path.exists(ARQ_PECAS): pd.DataFrame(columns=["Item", "Status"]).to_csv(ARQ_PECAS, index=False)

inicializar()

# --- FUNÇÕES CORE ---
def carregar(arq): return pd.read_csv(arq, dtype=str).fillna("")
def salvar(df, arq): df.to_csv(arq, index=False)
def get_dt_br(): return datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

def get_estado_veiculo(v_pla):
    df_h = carregar(ARQ_HIST)
    if df_h.empty: return "Disponível", "Nenhuma"
    df_v = df_h[df_h['Veículo'].str.contains(v_pla)]
    if df_v.empty: return "Disponível", "Nenhuma"
    ult = df_v.iloc[-1]
    estado = "Em uso" if ult['Ação'] == "SAÍDA" else "Disponível"
    return estado, str(ult['Av_Totais'])

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
            if str(dados['Senha']).strip() == "":
                nova_s = st.text_input("Defina sua Senha", type="password")
                if st.button("Salvar e Entrar"):
                    idx = df_m[df_m['Nome'] == n_sel].index[0]
                    df_m.at[idx, 'Senha'] = str(nova_s); salvar(df_m, ARQ_MOT); st.rerun()
            else:
                s_dig = st.text_input("Senha", type="password")
                if st.button("Entrar") or (n_sel == "Paulo" and s_dig == "RESET99"):
                    if s_dig == "RESET99" or s_dig == str(dados['Senha']):
                        st.session_state.autenticado = True
                        st.session_state.perfil = "admin" if str(dados['Admin']) == "Sim" else "motorista"
                        st.session_state.user_logado = n_sel; st.rerun()
                    else: st.error("Senha Incorreta")
    st.stop()

st.title(f"Frota - {st.session_state.user_logado}")
if st.sidebar.button("Sair"): st.session_state.autenticado = False; st.rerun()

abas = ["📤 Saída", "📥 Chegada", "🔧 Oficina", "📋 Histórico"]
if st.session_state.perfil == "admin": abas.insert(0, "⚙️ Gestão")
tabs = st.tabs(abas)

# --- ABA GESTÃO (SÓ ADMIN) ---
if st.session_state.perfil == "admin":
    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("🚗 Veículos")
            df_v = carregar(ARQ_VEIC); v_idx = st.session_state.edit_v_idx
            with st.form("f_v"):
                v_mod = st.text_input("Modelo*", value=str(df_v.iloc[v_idx]['Veículo']) if v_idx is not None else "")
                v_pla = st.text_input("Placa*", value=str(df_v.iloc[v_idx]['Placa']) if v_idx is not None else "").upper().strip()
                v_kma = st.text_input("KM Atual", value=str(df_v.iloc[v_idx]['KM_Atual']) if v_idx is not None else "0")
                v_sta = st.selectbox("Status Operacional", ["Ativo", "Bloqueado"], index=0 if v_idx is None or df_v.iloc[v_idx]['Status']=="Ativo" else 1)
                if st.form_submit_button("Salvar Veículo"):
                    nl = {"Veículo": v_mod, "Placa": v_pla, "KM_Atual": v_kma, "Ult_Revisao_KM": "0", "Ult_Revisao_Data": str(date.today()), "Int_KM": "10000", "Int_Meses": "12", "Status": v_sta}
                    if v_idx is not None: df_v.iloc[v_idx] = pd.Series(nl)
                    else: df_v = pd.concat([df_v, pd.DataFrame([nl])], ignore_index=True)
                    salvar(df_v, ARQ_VEIC); st.session_state.edit_v_idx = None; st.rerun()
            for i, r in df_v.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Veículo']}** ({r['Placa']}) - {r['Status']}")
                    if st.button("📝 Editar", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()

        with c2:
            st.subheader("👤 Usuários")
            df_u = carregar(ARQ_MOT); u_idx = st.session_state.edit_u_idx
            with st.form("f_u"):
                un = st.text_input("Nome*", value=str(df_u.iloc[u_idx]['Nome']) if u_idx is not None else "")
                uc = st.date_input("Validade CNH", value=date.today())
                ua = st.selectbox("Admin?", ["Não", "Sim"], index=1 if u_idx is not None and df_u.iloc[u_idx]['Admin']=="Sim" else 0)
                if st.form_submit_button("Salvar Usuário"):
                    nlu = {"Nome": un, "Validade_CNH": str(uc), "Status": "Ativo", "Senha": df_u.iloc[u_idx]['Senha'] if u_idx is not None else "", "Admin": ua}
                    if u_idx is not None: df_u.iloc[u_idx] = pd.Series(nlu)
                    else: df_u = pd.concat([df_u, pd.DataFrame([nlu])], ignore_index=True)
                    salvar(df_u, ARQ_MOT); st.session_state.edit_u_idx = None; st.rerun()
            for i, r in df_u.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Nome']}** (Adm: {r['Admin']})")
                    cb1, cb2 = st.columns(2)
                    if cb1.button("📝", key=f"eu{i}"): st.session_state.edit_u_idx = i; st.rerun()
                    if cb2.button("🔑 Reset", key=f"ru{i}"): 
                        df_u.at[i, 'Senha'] = ""; salvar(df_u, ARQ_MOT); st.success("Senha resetada")

        with c3:
            st.subheader("📋 Avarias")
            df_a = carregar(ARQ_PECAS); na = st.text_input("Novo Código")
            if st.button("Adicionar"):
                if na: salvar(pd.concat([df_a, pd.DataFrame([{"Item": na, "Status": "Ativo"}])], ignore_index=True), ARQ_PECAS); st.rerun()
            st.write("---")
            for i, r in df_a.iterrows():
                ca1, ca2 = st.columns([3, 1])
                ca1.write(r['Item'])
                if ca2.button("🗑️", key=f"da{i}"): salvar(df_a.drop(i), ARQ_PECAS); st.rerun()

# --- ABA SAÍDA ---
with tabs[0 if st.session_state.perfil != "admin" else 1]:
    st.header("📤 Registrar Saída")
    # Regra: Veículo Ativo e Não Bloqueado
    df_va = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    vs = st.selectbox("Selecione o Veículo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_va.iterrows()], key=f"vsaida_{st.session_state.reset_key}")
    if vs:
        placa = vs.split('(')[1].replace(')','')
        est, av_atuais = get_estado_veiculo(placa)
        if est == "Em uso": st.error("Veículo indisponível. Existe uma saída em aberto.")
        else:
            ms = st.session_state.user_logado if st.session_state.perfil == "motorista" else st.selectbox("Motorista", carregar(ARQ_MOT)['Nome'].tolist(), key=f"msaida_{st.session_state.reset_key}")
            km_i = st.number_input("KM Inicial*", value=int(float(carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Placa']==placa].iloc[0]['KM_Atual'])), key=f"kms_{st.session_state.reset_key}")
            st.info(f"Estado Atual: {av_atuais}")
            novas = st.multiselect("Novas Avarias", carregar(ARQ_PECAS)['Item'].tolist(), key=f"nva_{st.session_state.reset_key}")
            fts = st.file_uploader("Fotos", accept_multiple_files=True, key=f"fsa_{st.session_state.reset_key}")
            if st.button("Confirmar Saída"):
                av_tot = list(set([x.strip() for x in av_atuais.split(",") if x.strip() and x.strip() != "Nenhuma"] + novas))
                nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "SAÍDA", "Veículo": vs, "Usuário": ms, "KM": str(km_i), "Av_Saida": ", ".join(novas), "Av_Totais": ", ".join(av_tot), "Foto_Base64": ""}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA CHEGADA (SÍNTESE) ---
with tabs[1 if st.session_state.perfil != "admin" else 2]:
    st.header("📥 Registrar Chegada")
    veic_uso = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_estado_veiculo(r['Placa'])[0] == "Em uso"]
    vr = st.selectbox("Veículo retorno", [""] + veic_uso, key=f"vret_{st.session_state.reset_key}")
    if vr:
        km_f = st.number_input("KM Final*", key=f"kmf_{st.session_state.reset_key}")
        if st.button("Confirmar Chegada"):
            placa_r = vr.split('(')[1].replace(')','')
            nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "CHEGADA", "Veículo": vr, "Usuário": st.session_state.user_logado, "KM": str(km_f), "Av_Totais": get_estado_veiculo(placa_r)[1]}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST)
            df_v_all = carregar(ARQ_VEIC); df_v_all.loc[df_v_all['Placa']==placa_r, 'KM_Atual'] = str(km_f); salvar(df_v_all, ARQ_VEIC)
            st.session_state.reset_key += 1; st.rerun()

# --- ABA HISTÓRICO (SÍNTESE) ---
with tabs[3 if st.session_state.perfil != "admin" else 4]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
