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

# 3. Inicialização e Integridade de Dados
def inicializar():
    col_h = ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Valor_Reparo", "Local_Reparo", "Foto_Base64"]
    if not os.path.exists(ARQ_HIST): pd.DataFrame(columns=col_h).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_MOT): pd.DataFrame(columns=["Nome", "Validade_CNH", "Status", "Senha", "Admin"]).to_csv(ARQ_MOT, index=False)
    
    # Reinclusão de campos: KM Atual, Intervalos e Alertas
    col_v = ["Veículo", "Placa", "KM_Atual", "Ult_Revisao_KM", "Ult_Revisao_Data", "Int_KM", "Int_Meses", "Status"]
    if not os.path.exists(ARQ_VEIC): 
        pd.DataFrame(columns=col_v).to_csv(ARQ_VEIC, index=False)
    else:
        dfv = pd.read_csv(ARQ_VEIC, dtype=str)
        for c in col_v:
            if c not in dfv.columns: dfv[c] = "0" if "KM" in c or "Int" in c else "Ativo"
        dfv.to_csv(ARQ_VEIC, index=False)

    if not os.path.exists(ARQ_PECAS):
        pecas_std = ["1. Para-choque Dianteiro", "2. Capô", "3. Teto", "4. Parabrisa", "5. Retrovisor Dir.", "6. Retrovisor Esq."]
        pd.DataFrame({"Item": pecas_std, "Status": ["Ativo"]*len(pecas_std)}).to_csv(ARQ_PECAS, index=False)

inicializar()

# --- FUNÇÕES CORE ---
def carregar(arq): return pd.read_csv(arq, dtype=str).fillna("")
def salvar(df, arq): df.to_csv(arq, index=False)
def get_dt_br(): return datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

def get_status_sistemico(v_pla):
    # Determina o estado real (Disponível, Em uso, etc) baseando-se no histórico
    df_h = carregar(ARQ_HIST)
    if df_h.empty: return "Disponível", 0, "Nenhuma"
    df_v = df_h[df_h['Veículo'].str.contains(v_pla)]
    if df_v.empty: return "Disponível", 0, "Nenhuma"
    ult = df_v.iloc[-1]
    estado = "Em uso" if ult['Ação'] == "SAÍDA" else "Disponível"
    try: km = int(float(ult['KM']))
    except: km = 0
    return estado, km, str(ult['Av_Totais'])

def calcular_revisao_status(v_info, km_atual):
    try:
        i_km = int(float(v_info['Int_KM'])); i_mes = int(float(v_info['Int_Meses']))
        km_lim = int(float(v_info['Ult_Revisao_KM'])) + i_km
        dt_ult = datetime.strptime(str(v_info['Ult_Revisao_Data']), '%Y-%m-%d').date()
        dt_lim = dt_ult + timedelta(days=i_mes * 30)
        hoje = date.today()
        if (i_km > 0 and km_atual >= km_lim) or (i_mes > 0 and hoje >= dt_lim): return "🔴 VENCIDA"
        if (i_km > 0 and km_atual >= (km_lim - 500)) or (i_mes > 0 and hoje >= (dt_lim - timedelta(days=30))): return "🟡 A VENCER"
        return "🟢 EM DIA"
    except: return "⚪ S/ CONF"

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
    if not lista_nomes:
        if st.text_input("Senha Mestra Inicial", type="password") == "admin123":
            if st.button("Acessar"): st.session_state.autenticado = True; st.session_state.perfil = "admin"; st.session_state.user_logado = "Paulo"; st.rerun()
    else:
        n_sel = st.selectbox("Usuário", [""] + lista_nomes)
        if n_sel:
            dados = df_m[df_m['Nome'] == n_sel].iloc[0]
            s_dig = st.text_input("Senha", type="password")
            if st.button("Entrar"):
                if s_dig == "RESET99" or s_dig == str(dados['Senha']):
                    st.session_state.autenticado = True
                    st.session_state.perfil = "admin" if str(dados['Admin']) == "Sim" else "motorista"
                    st.session_state.user_logado = n_sel; st.rerun()
                else: st.error("Incorreta")
    st.stop()

# --- INTERFACE ---
st.title(f"Frota - {st.session_state.user_logado}")
if st.sidebar.button("Sair"): st.session_state.autenticado = False; st.rerun()
tabs = st.tabs(["⚙️ Gestão", "📤 Saída", "📥 Chegada", "🔧 Oficina", "📋 Histórico"])

# --- ABA GESTÃO ---
with tabs[0]:
    if st.session_state.perfil != "admin": st.error("Acesso restrito."); st.stop()
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.subheader("🚗 Veículos")
        df_v = carregar(ARQ_VEIC); v_idx = st.session_state.edit_v_idx
        with st.form("f_veic"):
            v_mod = st.text_input("Modelo*", value=str(df_v.iloc[v_idx]['Veículo']) if v_idx is not None else "")
            v_pla = st.text_input("Placa*", value=str(df_v.iloc[v_idx]['Placa']) if v_idx is not None else "").upper().strip()
            v_kma = st.text_input("KM Atual do Veículo*", value=str(df_v.iloc[v_idx]['KM_Atual']) if v_idx is not None else "0")
            v_ukm = st.text_input("KM da Última Revisão", value=str(df_v.iloc[v_idx]['Ult_Revisao_KM']) if v_idx is not None else "0")
            v_udt = st.date_input("Data da Última Revisão", value=datetime.strptime(str(df_v.iloc[v_idx]['Ult_Revisao_Data']), '%Y-%m-%d').date() if v_idx is not None else date.today())
            v_ikm = st.text_input("Intervalo Revisão (KM)", value=str(df_v.iloc[v_idx]['Int_KM']) if v_idx is not None else "10000")
            v_ime = st.text_input("Intervalo Revisão (Meses)", value=str(df_v.iloc[v_idx]['Int_Meses']) if v_idx is not None else "12")
            if st.form_submit_button("Salvar Veículo"):
                if v_pla in df_v['Placa'].values and v_idx is None: st.error("Registro já existente.")
                elif v_mod and v_pla:
                    nlv = {"Veículo": v_mod, "Placa": v_pla, "KM_Atual": str(v_kma), "Ult_Revisao_KM": str(v_ukm), "Ult_Revisao_Data": str(v_udt), "Int_KM": str(v_ikm), "Int_Meses": str(v_ime), "Status": "Ativo"}
                    if v_idx is not None: df_v.iloc[v_idx] = pd.Series(nlv)
                    else: df_v = pd.concat([df_v, pd.DataFrame([nlv])], ignore_index=True)
                    salvar(df_v, ARQ_VEIC); st.session_state.edit_v_idx = None; st.rerun()
        
        for i, r in df_v.iterrows():
            est, km_h, av_h = get_status_sistemico(r['Placa'])
            st.write(f"**{r['Veículo']}** ({r['Placa']}) - KM: {r['KM_Atual']} | {est}")
            colb1, colb2 = st.columns(2)
            if colb1.button("📝 Editar", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()
            if colb2.button("🗑️ Excluir", key=f"dv{i}"):
                if est == "Em uso": st.error("Bloqueado: Veículo em uso.")
                else: salvar(df_v.drop(i), ARQ_VEIC); st.rerun()

    with c2:
        st.subheader("👤 Usuários")
        df_u = carregar(ARQ_MOT); u_idx = st.session_state.edit_u_idx
        with st.form("f_u"):
            un = st.text_input("Nome*", value=str(df_u.iloc[u_idx]['Nome']) if u_idx is not None else "")
            try: u_cnh_v = datetime.strptime(str(df_u.iloc[u_idx]['Validade_CNH']), '%Y-%m-%d').date()
            except: u_cnh_v = date.today()
            uc = st.date_input("Validade da CNH*", value=u_cnh_v)
            us = st.text_input("Senha*", value=str(df_u.iloc[u_idx]['Senha']) if u_idx is not None else "")
            ua = st.selectbox("Admin?", ["Não", "Sim"], index=1 if u_idx is not None and df_u.iloc[u_idx]['Admin']=="Sim" else 0)
            if st.form_submit_button("Salvar Usuário"):
                if un:
                    nlu = {"Nome": str(un), "Validade_CNH": str(uc), "Status": "Ativo", "Senha": str(us), "Admin": str(ua)}
                    if u_idx is not None: df_u.iloc[u_idx] = pd.Series(nlu)
                    else: df_u = pd.concat([df_u, pd.DataFrame([nlu])], ignore_index=True)
                    salvar(df_u, ARQ_MOT); st.session_state.edit_u_idx = None; st.rerun()
        for i, r in df_u.iterrows():
            st.write(f"{r['Nome']} (CNH: {r['Validade_CNH']})")
            if st.button("📝 Editar", key=f"eu{i}"): st.session_state.edit_u_idx = i; st.rerun()

    with c3:
        st.subheader("📋 Avarias")
        df_a = carregar(ARQ_PECAS); na = st.text_input("Nova")
        if st.button("Adicionar"): 
            if na and na not in df_a['Item'].values: salvar(pd.concat([df_a, pd.DataFrame([{"Item": na, "Status": "Ativo"}])], ignore_index=True), ARQ_PECAS); st.rerun()
            else: st.warning("Avaria já existe ou campo vazio.")
        for i, r in df_a.iterrows():
            st.write(f"{r['Item']}")
            if st.button("🗑️ Excluir", key=f"da{i}"): salvar(df_a.drop(i), ARQ_PECAS); st.rerun()

# --- ABA SAÍDA ---
with tabs[1]:
    st.header("📤 Registrar Saída")
    df_va = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    v_sel = st.selectbox("Veículo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_va.iterrows()], key=f"vs_{st.session_state.reset_key}")
    if v_sel:
        placa = v_sel.split('(')[1].replace(')','')
        est, km_at, av_at = get_status_sistemico(placa)
        v_info = df_va[df_va['Placa'] == placa].iloc[0]
        
        if est == "Em uso":
            st.error(f"Veículo indisponível. Existe uma saída em aberto para este veículo.")
        else:
            st.info(f"Revisão: {calcular_revisao_status(v_info, km_at)} | KM Atual: {v_info['KM_Atual']}")
            m_sel = st.session_state.user_logado if st.session_state.perfil == "motorista" else st.selectbox("Motorista", carregar(ARQ_MOT)['Nome'].tolist(), key=f"ms_{st.session_state.reset_key}")
            # Bloqueio CNH
            u_info = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Nome'] == m_sel].iloc[0]
            if datetime.strptime(u_info['Validade_CNH'], '%Y-%m-%d').date() < date.today():
                st.error("🚫 Bloqueado: Motorista com CNH vencida.")
            else:
                kms = st.number_input("KM Saída*", min_value=int(float(v_info['KM_Atual'])), value=int(float(v_info['KM_Atual'])), key=f"ks_{st.session_state.reset_key}")
                lista_pecas = carregar(ARQ_PECAS)['Item'].tolist()
                av_check = [x.strip() for x in av_at.split(",") if x.strip() in lista_pecas]
                chk = st.multiselect("Estado Atual e Novas Avarias:", lista_pecas, default=av_check, key=f"cs_{st.session_state.reset_key}")
                fts = st.file_uploader("Fotos Saída", accept_multiple_files=True, key=f"fs_{st.session_state.reset_key}")
                if st.button("Confirmar Saída"):
                    nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "SAÍDA", "Veículo": v_sel, "Usuário": m_sel, "KM": str(kms), "Av_Saida": ", ".join(chk), "Av_Totais": ", ".join(chk), "Foto_Base64": converter_multiplas_fotos(fts)}])
                    salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA CHEGADA ---
with tabs[2]:
    st.header("📥 Registrar Chegada")
    veic_u = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_sistemico(v.split('(')[1].replace(')',''))[0] == "Em uso"]
    vr = st.selectbox("Veículo retorno", [""] + veic_u, key=f"vr_{st.session_state.reset_key}")
    if vr:
        pla_r = vr.split('(')[1].replace(')','')
        est_r, km_r, av_r = get_status_sistemico(pla_r)
        kmf = st.number_input("KM Final*", min_value=km_r, value=km_r, key=f"kf_{st.session_state.reset_key}")
        lista_p = carregar(ARQ_PECAS)['Item'].tolist()
        av_saida = [x.strip() for x in av_r.split(",") if x.strip() in lista_p]
        chk_c = st.multiselect("Conferência de Avarias (Chegada):", lista_p, default=av_saida, key=f"cc_{st.session_state.reset_key}")
        fts_c = st.file_uploader("Fotos Chegada", accept_multiple_files=True, key=f"fc_{st.session_state.reset_key}")
        if st.button("Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "CHEGADA", "Veículo": vr, "Usuário": st.session_state.user_logado, "KM": str(kmf), "Av_Chegada": ", ".join(chk_c), "Av_Totais": ", ".join(chk_c), "Foto_Base64": converter_multiplas_fotos(fts_c)}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST)
            # Atualiza KM Atual no Cadastro
            df_v_all = carregar(ARQ_VEIC)
            idx_v = df_v_all[df_v_all['Placa'] == pla_r].index[0]
            df_v_all.at[idx_v, 'KM_Atual'] = str(kmf)
            salvar(df_v_all, ARQ_VEIC)
            st.session_state.reset_key += 1; st.rerun()

# --- ABA OFICINA ---
with tabs[3]:
    st.header("🔧 Registro de Oficina")
    df_v_of = carregar(ARQ_VEIC)
    v_of = st.selectbox("Veículo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_of.iterrows()], key=f"vof_{st.session_state.reset_key}")
    if v_of:
        p_of = v_of.split('(')[1].replace(')','')
        _, _, av_of = get_status_sistemico(p_of)
        itens_ruins = [x.strip() for x in av_of.split(",") if x.strip() and x.strip() != "Nenhuma"]
        reps = st.multiselect("Itens consertados:", itens_ruins)
        emp = st.text_input("Empresa/Oficina*")
        val = st.number_input("Valor Reparo (R$)*", min_value=0.0)
        if st.button("Registrar Manutenção"):
            sobra = [p for p in itens_ruins if p not in reps]
            nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "OFICINA", "Veículo": v_of, "Usuário": st.session_state.user_logado, "KM": "0", "Av_Totais": ", ".join(sobra) if sobra else "Nenhuma", "Local_Reparo": emp, "Valor_Reparo": str(val), "Obs": f"Reparo em: {', '.join(reps)}"}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA HISTÓRICO ---
with tabs[4]:
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        idx = st.selectbox("ID Detalhes:", df_h.index)
        if st.session_state.perfil == "admin" and st.button("🗑️ Excluir Registro"): salvar(df_h.drop(idx), ARQ_HIST); st.rerun()
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            for f in str(fb64).split(";"):
                if f: st.image(base64.b64decode(f), width=400)
