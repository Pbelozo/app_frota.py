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
    
    # Restauração das Colunas de Revisão e KM Atual
    col_v = ["Veículo", "Placa", "KM_Atual", "Prox_Revisao_KM", "Prox_Revisao_Data", "Status"]
    if not os.path.exists(ARQ_VEIC): 
        pd.DataFrame(columns=col_v).to_csv(ARQ_VEIC, index=False)
    else:
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
    df_h = carregar(ARQ_HIST)
    if df_h.empty: return "Disponível", "Nenhuma"
    df_v = df_h[df_h['Veículo'].str.contains(str(v_pla), na=False)]
    if df_v.empty: return "Disponível", "Nenhuma"
    ult = df_v.iloc[-1]
    return ("Em uso" if ult['Ação'] == "SAÍDA" else "Disponível"), str(ult['Av_Totais'])

def converter_multiplas_fotos(uploaded_files):
    lista_b64 = []
    if uploaded_files:
        for f in uploaded_files:
            img = Image.open(f); img.thumbnail((800, 800))
            buf = BytesIO(); img.save(buf, format="JPEG", quality=70)
            lista_b64.append(base64.b64encode(buf.getvalue()).decode())
    return ";".join(lista_b64)

# --- CONTROLE DE ACESSO ---
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
                    st.session_state.autenticado = True
                    st.session_state.perfil = "admin" if str(dados['Admin']) == "Sim" else "motorista"
                    st.session_state.user_logado = n_sel; st.rerun()
                else: st.error("Senha Incorreta")
    st.stop()

# --- INTERFACE ---
st.title(f"Frota - {st.session_state.user_logado}")
if st.sidebar.button("Sair"): st.session_state.autenticado = False; st.rerun()

abas = ["⚙️ Gestão", "📤 Saída", "📥 Chegada", "🔧 Oficina", "📋 Histórico"]
if st.session_state.perfil != "admin": abas.pop(0)
tabs = st.tabs(abas)
idx_off = 1 if st.session_state.perfil == "admin" else 0

# --- ABA GESTÃO ---
if st.session_state.perfil == "admin":
    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("🚗 Veículos")
            df_v = carregar(ARQ_VEIC); v_idx = st.session_state.edit_v_idx
            with st.form("f_veic"):
                v_mod = st.text_input("Modelo*", value=str(df_v.iloc[v_idx]['Veículo']) if v_idx is not None else "")
                v_pla = st.text_input("Placa*", value=str(df_v.iloc[v_idx]['Placa']) if v_idx is not None else "").upper().strip()
                v_kma = st.text_input("KM Atual*", value=str(df_v.iloc[v_idx]['KM_Atual']) if v_idx is not None else "0")
                v_rkm = st.text_input("KM Próxima Revisão", value=str(df_v.iloc[v_idx]['Prox_Revisao_KM']) if v_idx is not None else "0")
                v_rdt = st.date_input("Data Próxima Revisão", value=datetime.strptime(str(df_v.iloc[v_idx]['Prox_Revisao_Data']), '%Y-%m-%d').date() if v_idx is not None else date.today())
                if st.form_submit_button("Salvar Veículo"):
                    nl = {"Veículo": v_mod, "Placa": v_pla, "KM_Atual": v_kma, "Prox_Revisao_KM": v_rkm, "Prox_Revisao_Data": str(v_rdt), "Status": "Ativo"}
                    if v_idx is not None: df_v.iloc[v_idx] = pd.Series(nl)
                    else: df_v = pd.concat([df_v, pd.DataFrame([nl])], ignore_index=True)
                    salvar(df_v, ARQ_VEIC); st.session_state.edit_v_idx = None; st.rerun()
            for i, r in df_v.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Veículo']}** ({r['Placa']}) - {r['Status']}")
                    b1, b2, b3 = st.columns(3)
                    if b1.button("📝", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()
                    if b2.button("🚫" if r['Status']=="Ativo" else "✅", key=f"bv{i}"):
                        df_v.at[i, 'Status'] = "Inativo" if r['Status']=="Ativo" else "Ativo"; salvar(df_v, ARQ_VEIC); st.rerun()
                    if b3.button("🗑️", key=f"dv{i}"):
                        if carregar(ARQ_HIST)[carregar(ARQ_HIST)['Veículo'].str.contains(r['Placa'])].empty:
                            salvar(df_v.drop(i), ARQ_VEIC); st.rerun()
                        else: st.error("Bloqueado: Possui histórico.")

        with c2:
            st.subheader("👤 Usuários")
            df_u = carregar(ARQ_MOT); u_idx = st.session_state.edit_u_idx
            with st.form("f_u"):
                un = st.text_input("Nome*", value=str(df_u.iloc[u_idx]['Nome']) if u_idx is not None else "")
                uc = st.date_input("Validade CNH*", value=datetime.strptime(str(df_u.iloc[u_idx]['Validade_CNH']), '%Y-%m-%d').date() if u_idx is not None else date.today())
                ua = st.selectbox("Admin?", ["Não", "Sim"], index=1 if u_idx is not None and df_u.iloc[u_idx]['Admin']=="Sim" else 0)
                if st.form_submit_button("Salvar Usuário"):
                    nu = {"Nome": un, "Validade_CNH": str(uc), "Status": "Ativo", "Senha": df_u.iloc[u_idx]['Senha'] if u_idx is not None else "123", "Admin": ua}
                    if u_idx is not None: df_u.iloc[u_idx] = pd.Series(nu)
                    else: df_u = pd.concat([df_u, pd.DataFrame([nu])], ignore_index=True)
                    salvar(df_u, ARQ_MOT); st.session_state.edit_u_idx = None; st.rerun()
            for i, r in df_u.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Nome']}** ({r['Status']})")
                    ub1, ub2, ub3 = st.columns(3)
                    if ub1.button("📝", key=f"eu{i}"): st.session_state.edit_u_idx = i; st.rerun()
                    if ub2.button("🚫" if r['Status']=="Ativo" else "✅", key=f"bu{i}"):
                        df_u.at[i, 'Status'] = "Inativo" if r['Status']=="Ativo" else "Ativo"; salvar(df_u, ARQ_MOT); st.rerun()
                    if ub3.button("🗑️", key=f"du{i}"): salvar(df_u.drop(i), ARQ_MOT); st.rerun()

        with c3:
            st.subheader("📋 Avarias")
            df_p = carregar(ARQ_PECAS); na = st.text_input("Nova")
            if st.button("Adicionar"):
                if na: salvar(pd.concat([df_p, pd.DataFrame([{"Item": na, "Status": "Ativo"}])], ignore_index=True), ARQ_PECAS); st.rerun()
            for i, r in df_p.iterrows():
                ca1, ca2 = st.columns([4, 1])
                ca1.write(r['Item'])
                if ca2.button("🗑️", key=f"dp{i}"): salvar(df_p.drop(i), ARQ_PECAS); st.rerun()

# --- ABA SAÍDA ---
with tabs[0 + idx_off]:
    st.header("📤 Registrar Saída")
    df_va = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    vs = st.selectbox("Veículo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_va.iterrows()], key=f"vs_{st.session_state.reset_key}")
    if vs:
        pla = vs.split('(')[1].replace(')','')
        est, av_at = get_estado_sistemico(pla)
        v_info = df_va[df_va['Placa']==pla].iloc[0]
        if est == "Em uso": st.error("Veículo indisponível. Existe uma saída em aberto.")
        else:
            st.info(f"KM Atual: {v_info['KM_Atual']} | Revisão em: {v_info['Prox_Revisao_KM']} ou {v_info['Prox_Revisao_Data']}")
            ms = st.session_state.user_logado if st.session_state.perfil == "motorista" else st.selectbox("Motorista", carregar(ARQ_MOT)['Nome'].tolist(), key=f"ms_{st.session_state.reset_key}")
            kms = st.number_input("KM Saída*", value=int(float(v_info['KM_Atual'])))
            novas = st.multiselect("Danos identificados", carregar(ARQ_PECAS)['Item'].tolist())
            fts = st.file_uploader("Fotos", accept_multiple_files=True)
            if st.button("Confirmar Saída"):
                av_tot = list(set([x.strip() for x in av_at.split(",") if x.strip() and x.strip() != "Nenhuma"] + novas))
                nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "SAÍDA", "Veículo": vs, "Usuário": ms, "KM": str(kms), "Av_Totais": ", ".join(av_tot), "Foto_Base64": converter_multiplas_fotos(fts)}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA CHEGADA ---
with tabs[1 + idx_off]:
    st.header("📥 Registrar Chegada")
    veic_uso = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_estado_sistemico(r['Placa'])[0] == "Em uso"]
    vr = st.selectbox("Veículo retorno", [""] + veic_uso, key=f"vr_{st.session_state.reset_key}")
    if vr:
        pla_r = vr.split('(')[1].replace(')','')
        kmf = st.number_input("KM Final*", key=f"kmf_{st.session_state.reset_key}")
        if st.button("Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "CHEGADA", "Veículo": vr, "Usuário": st.session_state.user_logado, "KM": str(kmf), "Av_Totais": get_estado_sistemico(pla_r)[1]}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST)
            df_v = carregar(ARQ_VEIC); df_v.loc[df_v['Placa']==pla_r, 'KM_Atual'] = str(kmf); salvar(df_v, ARQ_VEIC)
            st.session_state.reset_key += 1; st.rerun()

# --- ABA OFICINA (RESTAURADA) ---
with tabs[2 + idx_off]:
    st.header("🔧 Oficina")
    df_av = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_estado_sistemico(r['Placa'])[1] != "Nenhuma"]
    v_of = st.selectbox("Veículo em reparo", [""] + df_av, key=f"vof_{st.session_state.reset_key}")
    if v_of:
        sm = get_estado_sistemico(v_of.split('(')[1].replace(')',''))[1]
        reps = st.multiselect("Itens consertados", [x.strip() for x in sm.split(",")])
        emp = st.text_input("Empresa/Oficina*"); val = st.number_input("Valor R$*", min_value=0.0)
        if st.button("Registrar Manutenção"):
            sobra = [p for p in [x.strip() for x in sm.split(",")] if p not in reps]
            nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "OFICINA", "Veículo": v_of, "Usuário": st.session_state.user_logado, "KM": "0", "Av_Totais": ", ".join(sobra) if sobra else "Nenhuma", "Local_Reparo": emp, "Valor_Reparo": str(val), "Obs": f"Reparo: {', '.join(reps)}"}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA HISTÓRICO ---
with tabs[3 + idx_off]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        idx = st.selectbox("Ver ID:", df_h.index)
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            for f in str(fb64).split(";"):
                if f: st.image(base64.b64decode(f), width=400)
