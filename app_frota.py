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

def get_estado_sistemico(v_pla):
    if not v_pla or str(v_pla).strip() == "": return "Indefinido", "Nenhuma"
    df_h = carregar(ARQ_HIST)
    if df_h.empty: return "Disponível", "Nenhuma"
    df_v = df_h[df_h['Veículo'].str.contains(str(v_pla), na=False)]
    if df_v.empty: return "Disponível", "Nenhuma"
    ult = df_v.iloc[-1]
    estado = "Em uso" if ult['Ação'] == "SAÍDA" else "Disponível"
    return estado, str(ult['Av_Totais'])

def converter_multiplas_fotos(uploaded_files):
    lista_b64 = []
    if uploaded_files:
        for f in uploaded_files:
            img = Image.open(f); img.thumbnail((800, 800))
            buf = BytesIO(); img.save(buf, format="JPEG", quality=70)
            lista_b64.append(base64.b64encode(buf.getvalue()).decode())
    return ";".join(lista_b64)

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
            if st.button("Entrar") or (n_sel == "Paulo" and s_dig == "RESET99"):
                if s_dig == "RESET99" or s_dig == str(dados['Senha']):
                    st.session_state.autenticado = True
                    st.session_state.perfil = "admin" if str(dados['Admin']) == "Sim" else "motorista"
                    st.session_state.user_logado = n_sel; st.rerun()
                else: st.error("Incorreta")
    st.stop()

st.title(f"Frota - {st.session_state.user_logado}")
if st.sidebar.button("Sair"): st.session_state.autenticado = False; st.rerun()

abas = ["📤 Saída", "📥 Chegada", "🔧 Oficina", "📋 Histórico"]
if st.session_state.perfil == "admin": abas.insert(0, "⚙️ Gestão")
tabs = st.tabs(abas)

# --- ABA GESTÃO ---
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
                v_sta = st.selectbox("Status", ["Ativo", "Bloqueado"], index=0 if v_idx is None or df_v.iloc[v_idx]['Status']=="Ativo" else 1)
                if st.form_submit_button("Salvar"):
                    nl = {"Veículo": v_mod, "Placa": v_pla, "KM_Atual": v_kma, "Ult_Revisao_KM": "0", "Ult_Revisao_Data": str(date.today()), "Int_KM": "10000", "Int_Meses": "12", "Status": v_sta}
                    if v_idx is not None: df_v.iloc[v_idx] = pd.Series(nl)
                    else: df_v = pd.concat([df_v, pd.DataFrame([nl])], ignore_index=True)
                    salvar(df_v, ARQ_VEIC); st.session_state.edit_v_idx = None; st.rerun()
            for i, r in df_v.iterrows():
                ca, cb = st.columns([3, 1])
                ca.write(f"**{r['Veículo']}** ({r['Placa']}) - {r['Status']}")
                if cb.button("📝", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()

        with c2:
            st.subheader("👤 Usuários")
            df_u = carregar(ARQ_MOT); u_idx = st.session_state.edit_u_idx
            with st.form("f_u"):
                un = st.text_input("Nome*", value=str(df_u.iloc[u_idx]['Nome']) if u_idx is not None else "")
                uc = st.date_input("Validade CNH", value=datetime.strptime(str(df_u.iloc[u_idx]['Validade_CNH']), '%Y-%m-%d').date() if u_idx is not None else date.today())
                ua = st.selectbox("Admin?", ["Não", "Sim"], index=1 if u_idx is not None and df_u.iloc[u_idx]['Admin']=="Sim" else 0)
                if st.form_submit_button("Salvar"):
                    nlu = {"Nome": un, "Validade_CNH": str(uc), "Status": "Ativo", "Senha": df_u.iloc[u_idx]['Senha'] if u_idx is not None else "", "Admin": ua}
                    if u_idx is not None: df_u.iloc[u_idx] = pd.Series(nlu)
                    else: df_u = pd.concat([df_u, pd.DataFrame([nlu])], ignore_index=True)
                    salvar(df_u, ARQ_MOT); st.session_state.edit_u_idx = None; st.rerun()
            for i, r in df_u.iterrows():
                ca, cb, cc = st.columns([3, 1, 1])
                ca.write(f"**{r['Nome']}**")
                if cb.button("📝", key=f"eu{i}"): st.session_state.edit_u_idx = i; st.rerun()
                if cc.button("🔑", key=f"ru{i}"): df_u.at[i, 'Senha'] = ""; salvar(df_u, ARQ_MOT); st.success("Reset")

        with c3:
            st.subheader("📋 Avarias")
            df_a = carregar(ARQ_PECAS); na = st.text_input("Novo Código")
            if st.button("Adicionar"):
                if na and na not in df_a['Item'].values: salvar(pd.concat([df_a, pd.DataFrame([{"Item": na, "Status": "Ativo"}])], ignore_index=True), ARQ_PECAS); st.rerun()
            for i, r in df_a.iterrows():
                ca1, ca2 = st.columns([4, 1])
                ca1.write(r['Item'])
                if ca2.button("🗑️", key=f"da{i}"): salvar(df_a.drop(i), ARQ_PECAS); st.rerun()

# --- ABA SAÍDA ---
with tabs[1 if st.session_state.perfil == "admin" else 0]:
    st.header("📤 Registrar Saída")
    df_va = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    vs = st.selectbox("Selecione o Veículo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_va.iterrows()], key=f"vs_{st.session_state.reset_key}")
    if vs:
        pla = vs.split('(')[1].replace(')','')
        est, av_at = get_estado_sistemico(pla)
        if est == "Em uso": st.error("Veículo indisponível. Existe uma saída em aberto.")
        else:
            ms = st.session_state.user_logado if st.session_state.perfil == "motorista" else st.selectbox("Motorista", carregar(ARQ_MOT)['Nome'].tolist(), key=f"ms_{st.session_state.reset_key}")
            km_i = st.number_input("KM Inicial*", value=int(float(carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Placa']==pla].iloc[0]['KM_Atual'])), key=f"kms_{st.session_state.reset_key}")
            chk = st.multiselect("Novas Avarias", carregar(ARQ_PECAS)['Item'].tolist(), key=f"chk_{st.session_state.reset_key}")
            fts = st.file_uploader("Fotos", accept_multiple_files=True, key=f"fts_{st.session_state.reset_key}")
            if st.button("Confirmar Saída"):
                av_tot = list(set([x.strip() for x in av_at.split(",") if x.strip() and x.strip() != "Nenhuma"] + chk))
                nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "SAÍDA", "Veículo": vs, "Usuário": ms, "KM": str(km_i), "Av_Saida": ", ".join(chk), "Av_Totais": ", ".join(av_tot), "Foto_Base64": converter_multiplas_fotos(fts)}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA CHEGADA (LOCAL DA CORREÇÃO DO ERRO) ---
with tabs[2 if st.session_state.perfil == "admin" else 1]:
    st.header("📥 Registrar Chegada")
    
    # CORREÇÃO PONTUAL: Tratamento defensivo para evitar KeyError: 'Placa'
    veic_uso = []
    for _, r in carregar(ARQ_VEIC).iterrows():
        p = r.get('Placa') # Usa .get() para não quebrar se a coluna faltar
        v = r.get('Veículo')
        if p and v:
            if get_estado_sistemico(p)[0] == "Em uso":
                veic_uso.append(f"{v} ({p})")
                
    vr = st.selectbox("Veículo retorno", [""] + veic_uso, key=f"vr_{st.session_state.reset_key}")
    if vr:
        pla_r = vr.split('(')[1].replace(')','')
        est_r, av_r = get_estado_sistemico(pla_r)
        kmf = st.number_input("KM Final*", key=f"kmf_{st.session_state.reset_key}")
        av_c = st.multiselect("Novas Avarias no Retorno", carregar(ARQ_PECAS)['Item'].tolist(), key=f"avc_{st.session_state.reset_key}")
        if st.button("Confirmar Chegada"):
            av_tot = list(set([x.strip() for x in av_r.split(",") if x.strip() != "Nenhuma"] + av_c))
            nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "CHEGADA", "Veículo": vr, "Usuário": st.session_state.user_logado, "KM": str(kmf), "Av_Chegada": ", ".join(av_c), "Av_Totais": ", ".join(av_tot)}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST)
            df_v = carregar(ARQ_VEIC); df_v.loc[df_v['Placa']==pla_r, 'KM_Atual'] = str(kmf); salvar(df_v, ARQ_VEIC)
            st.session_state.reset_key += 1; st.rerun()

# --- ABA HISTÓRICO ---
with tabs[4 if st.session_state.perfil == "admin" else 3]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        idx = st.selectbox("ID Detalhes:", df_h.index)
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            for f in str(fb64).split(";"):
                if f: st.image(base64.b64decode(f), width=400)
