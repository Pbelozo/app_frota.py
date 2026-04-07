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

# 3. Inicialização
def inicializar():
    if not os.path.exists(ARQ_HIST): pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Valor_Reparo", "Local_Reparo", "Foto_Base64"]).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_MOT): pd.DataFrame(columns=["Nome", "Validade_CNH", "Status", "Senha", "Admin"]).to_csv(ARQ_MOT, index=False)
    if not os.path.exists(ARQ_VEIC): pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Int_KM", "Int_Meses", "Alert_KM", "Alert_Dias", "Status"]).to_csv(ARQ_VEIC, index=False)
    if not os.path.exists(ARQ_PECAS):
        p_std = ["1. Capô", "2. Parabrisa", "3. Párachoque dianteiro", "4. Teto"]
        pd.DataFrame({"Item": p_std, "Status": ["Ativo"] * len(p_std)}).to_csv(ARQ_PECAS, index=False)

inicializar()

def carregar(arq): return pd.read_csv(arq).fillna("")
def salvar(df, arq): df.to_csv(arq, index=False)
def get_dt_br(): return datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

def get_status_veiculo(v_alvo):
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        df_v = df_h[df_h['Veículo'] == v_alvo]
        if not df_v.empty:
            ult = df_v.iloc[-1]
            try: km_val = int(float(ult['KM']))
            except: km_val = 0
            return {"acao": ult['Ação'], "user": ult['Usuário'], "km": km_val, "av": str(ult['Av_Totais']) if str(ult['Av_Totais']).strip() != "" else "Nenhuma"}
    return {"acao": "CHEGADA", "user": "Ninguém", "km": 0, "av": "Nenhuma"}

def calcular_revisao(v_info, km_atual):
    try:
        km_limite = int(v_info['Ult_Revisao_KM']) + int(v_info['Int_KM'])
        dt_ult = datetime.strptime(str(v_info['Ult_Revisao_Data']), '%Y-%m-%d').date()
        dt_limite = dt_ult + timedelta(days=int(v_info['Int_Meses']) * 30)
        hoje = date.today()
        if km_atual >= km_limite: return "🔴 VENCIDA (KM)", f"Limite {km_limite} KM"
        if hoje >= dt_limite: return "🔴 VENCIDA (Prazo)", f"Venceu {dt_limite.strftime('%d/%m/%Y')}"
        return "🟢 EM DIA", "OK"
    except: return "⚪ SEM DADOS", "Acesse Gestão"

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
        n_sel = st.selectbox("Selecione seu Usuário", [""] + lista_nomes)
        if n_sel:
            dados = df_m[df_m['Nome'] == n_sel].iloc[0]
            s_i = st.text_input("Senha", type="password")
            if st.button("Entrar"):
                # Mantido o Reset de Emergência para você caso precise
                if n_sel == "Paulo" and s_i == "RESET99":
                    st.session_state.autenticado = True; st.session_state.perfil = "admin"; st.session_state.user_logado = "Paulo"; st.rerun()
                elif str(s_i) == str(dados['Senha']):
                    st.session_state.autenticado = True
                    st.session_state.perfil = "admin" if str(dados['Admin']) == "Sim" else "motorista"
                    st.session_state.user_logado = n_sel; st.rerun()
                else: st.error("Senha Incorreta")
    st.stop()

# --- INTERFACE ---
st.title(f"Frota - {st.session_state.user_logado}")
if st.sidebar.button("Sair"): st.session_state.autenticado = False; st.rerun()

abas = ["📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"]
if st.session_state.perfil == "admin": abas.insert(0, "⚙️ Gestão & Cadastro")
tabs = st.tabs(abas)
idx_tab = 0 if st.session_state.perfil == "admin" else -1

# --- ABA GESTÃO ---
if st.session_state.perfil == "admin":
    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("🚗 Veículos")
            df_v = carregar(ARQ_VEIC); v_idx = st.session_state.edit_v_idx
            with st.form("f_v"):
                v_mod = st.text_input("Modelo", value=str(df_v.iloc[v_idx]['Veículo']) if v_idx is not None else "")
                v_pla = st.text_input("Placa", value=str(df_v.iloc[v_idx]['Placa']) if v_idx is not None else "").upper().strip()
                v_km_r = st.number_input("KM Últ. Revisão", value=int(df_v.iloc[v_idx]['Ult_Revisao_KM']) if v_idx is not None else 0)
                v_dt_r = st.date_input("Data Últ. Revisão", value=datetime.strptime(str(df_v.iloc[v_idx]['Ult_Revisao_Data']), '%Y-%m-%d').date() if v_idx is not None else date.today())
                v_i_km = st.number_input("Intervalo KM", value=int(df_v.iloc[v_idx]['Int_KM']) if v_idx is not None else 10000)
                v_i_m = st.number_input("Intervalo Meses", value=int(df_v.iloc[v_idx]['Int_Meses']) if v_idx is not None else 12)
                if st.form_submit_button("Salvar Veículo"):
                    if v_idx is not None:
                        df_v.at[v_idx, 'Veículo'] = v_mod; df_v.at[v_idx, 'Placa'] = v_pla
                        df_v.at[v_idx, 'Ult_Revisao_KM'] = v_km_r; df_v.at[v_idx, 'Ult_Revisao_Data'] = str(v_dt_r)
                        df_v.at[v_idx, 'Int_KM'] = v_i_km; df_v.at[v_idx, 'Int_Meses'] = v_i_m
                    else:
                        nv = {"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": v_km_r, "Ult_Revisao_Data": str(v_dt_r), "Int_KM": v_i_km, "Int_Meses": v_i_m, "Alert_KM": 500, "Alert_Dias": 30, "Status": "Ativo"}
                        df_v = pd.concat([df_v, pd.DataFrame([nv])], ignore_index=True)
                    salvar(df_v, ARQ_VEIC); st.session_state.edit_v_idx = None; st.rerun()
            for i, r in df_v.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Veículo']}** ({r['Placa']})")
                    if st.button("📝 Editar", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()

        with c2:
            st.subheader("👤 Usuários")
            df_u = carregar(ARQ_MOT); u_idx = st.session_state.edit_u_idx
            with st.form("f_u"):
                un = st.text_input("Nome", value=str(df_u.iloc[u_idx]['Nome']) if u_idx is not None else "")
                try: dt_c = datetime.strptime(str(df_u.iloc[u_idx]['Validade_CNH']), '%Y-%m-%d').date() if u_idx is not None else date.today()
                except: dt_c = date.today()
                uc = st.date_input("CNH", value=dt_c)
                us = st.text_input("Senha", value=str(df_u.iloc[u_idx]['Senha']) if u_idx is not None else "")
                ua = st.selectbox("Admin?", ["Não", "Sim"], index=0 if u_idx is None or str(df_u.iloc[u_idx]['Admin'])=="Não" else 1)
                if st.form_submit_button("Salvar Usuário"):
                    if u_idx is not None:
                        # CORREÇÃO AQUI: Atualização campo a campo para evitar TypeError
                        df_u.at[u_idx, 'Nome'] = un
                        df_u.at[u_idx, 'Validade_CNH'] = str(uc)
                        df_u.at[u_idx, 'Senha'] = str(us)
                        df_u.at[u_idx, 'Admin'] = ua
                    else:
                        nu = {"Nome": un, "Validade_CNH": str(uc), "Status": "Ativo", "Senha": str(us), "Admin": ua}
                        df_u = pd.concat([df_u, pd.DataFrame([nu])], ignore_index=True)
                    salvar(df_u, ARQ_MOT); st.session_state.edit_u_idx = None; st.rerun()
            for i, r in df_u.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Nome']}** ({r['Admin']})")
                    if st.button("📝 Editar", key=f"eu{i}"): st.session_state.edit_u_idx = i; st.rerun()

        with c3:
            st.subheader("📋 Avarias")
            df_a = carregar(ARQ_PECAS); na = st.text_input("Nova")
            if st.button("Add"): salvar(pd.concat([df_a, pd.DataFrame([{"Item": na, "Status": "Ativo"}])], ignore_index=True), ARQ_PECAS); st.rerun()
            st.dataframe(df_a)

# --- ABA SAÍDA ---
with tabs[1 + idx_tab]:
    st.header("📤 Registrar Saída")
    df_va = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    vs = st.selectbox("Veículo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_va.iterrows()], key=f"vs_{st.session_state.reset_key}")
    ms = st.session_state.user_logado if st.session_state.perfil == "motorista" else st.selectbox("Motorista", [""] + carregar(ARQ_MOT)['Nome'].tolist(), key=f"ms_{st.session_state.reset_key}")
    if vs and ms:
        stv = get_status_veiculo(vs); vi = df_va[df_va['Placa'] == vs.split('(')[1].replace(')','')].iloc[0]
        sr, mr = calcular_revisao(vi, stv['km']); st.write(f"**Revisão:** {sr} | {mr}")
        if stv["acao"] == "SAÍDA": st.error("Em uso.")
        else:
            kms = st.number_input("KM Inicial", min_value=stv['km'], value=stv['km'], key=f"kms_{st.session_state.reset_key}")
            check = st.multiselect("Avarias:", carregar(ARQ_PECAS)['Item'].tolist(), key=f"chs_{st.session_state.reset_key}")
            fotos = st.file_uploader("Fotos", accept_multiple_files=True, key=f"fs_{st.session_state.reset_key}")
            if st.button("Confirmar Saída"):
                nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "SAÍDA", "Veículo": vs, "Usuário": ms, "KM": kms, "Av_Saida": ", ".join(check), "Av_Totais": ", ".join(check), "Foto_Base64": converter_multiplas_fotos(fotos)}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA CHEGADA ---
with tabs[2 + idx_tab]:
    st.header("📥 Registrar Chegada")
    veic_u = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["acao"] == "SAÍDA"]
    vr = st.selectbox("Veículo retorno", [""] + veic_u, key=f"vr_{st.session_state.reset_key}")
    if vr:
        str_r = get_status_veiculo(vr)
        kmf = st.number_input("KM Final", min_value=str_r['km'], value=str_r['km'], key=f"kmr_{st.session_state.reset_key}")
        if st.button("Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "CHEGADA", "Veículo": vr, "Usuário": str_r['user'], "KM": kmf, "Av_Totais": str_r['av']}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA HISTÓRICO ---
with tabs[4 + idx_tab]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        idx = st.selectbox("ID:", df_h.index)
        if st.session_state.perfil == "admin" and st.button("🗑️ Excluir"): salvar(df_h.drop(idx), ARQ_HIST); st.rerun()
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            for f in str(fb64).split(";"):
                if f: st.image(base64.b64decode(f), width=450)
