import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import os
import base64
from io import BytesIO
from PIL import Image

# 1. Configuração da Página
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
    col_v = ["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Int_KM", "Int_Meses", "Alert_KM", "Alert_Dias", "Status"]
    if not os.path.exists(ARQ_VEIC): pd.DataFrame(columns=col_v).to_csv(ARQ_VEIC, index=False)
    if not os.path.exists(ARQ_PECAS):
        p_std = ["1. Capô", "2. Parabrisa", "3. Párachoque dianteiro", "4. Teto"]
        pd.DataFrame({"Item": p_std, "Status": ["Ativo"] * len(p_std)}).to_csv(ARQ_PECAS, index=False)

inicializar()

# --- FUNÇÕES CORE ---
def carregar(arq): return pd.read_csv(arq).fillna("")
def salvar(df, arq): df.to_csv(arq, index=False)
def get_data_hora_br(): return datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

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
        km_alerta = km_limite - int(v_info['Alert_KM'])
        dt_ult = datetime.strptime(str(v_info['Ult_Revisao_Data']), '%Y-%m-%d').date()
        dt_limite = dt_ult + timedelta(days=int(v_info['Int_Meses']) * 30)
        dt_alerta = dt_limite - timedelta(days=int(v_info['Alert_Dias']))
        hoje = date.today()
        if km_atual >= km_limite: return "🔴 VENCIDA (KM)", f"Limite {km_limite} KM"
        if hoje >= dt_limite: return "🔴 VENCIDA (Prazo)", f"Venceu {dt_limite.strftime('%d/%m/%Y')}"
        if km_atual >= km_alerta: return "🟡 A VENCER (KM)", f"Faltam {km_limite - km_atual} KM"
        if hoje >= dt_alerta: return "🟡 A VENCER (Prazo)", f"Vence em {(dt_limite - hoje).days} dias"
        return "🟢 EM DIA", "Manutenção OK"
    except: return "⚪ DADOS INCOMPLETOS", "Configure os intervalos na Gestão"

def converter_multiplas_fotos(uploaded_files):
    lista_b64 = []
    if uploaded_files:
        for f in uploaded_files:
            img = Image.open(f); img.thumbnail((800, 800))
            buf = BytesIO(); img.save(buf, format="JPEG", quality=70)
            lista_b64.append(base64.b64encode(buf.getvalue()).decode())
    return ";".join(lista_b64)

# --- LOGIN E ESTADO ---
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
            if str(dados['Senha']).strip() == "":
                nova_s = st.text_input("Cadastre sua Senha", type="password")
                if st.button("Salvar"):
                    idx = df_m[df_m['Nome'] == n_sel].index[0]
                    df_m.at[idx, 'Senha'] = str(nova_s); salvar(df_m, ARQ_MOT); st.rerun()
            else:
                s_i = st.text_input("Senha", type="password")
                if st.button("Entrar"):
                    if str(s_i) == str(dados['Senha']):
                        st.session_state.autenticado = True
                        st.session_state.perfil = "admin" if str(dados['Admin']) == "Sim" else "motorista"
                        st.session_state.user_logado = n_sel; st.rerun()
                    else: st.error("Senha Incorreta")
    st.stop()

# --- INTERFACE PRINCIPAL ---
st.title("Gestão de Frota")
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
            df_v = carregar(ARQ_VEIC)
            with st.form("f_veic"):
                v_idx = st.session_state.edit_v_idx
                v_mod = st.text_input("Modelo*", value=str(df_v.iloc[v_idx]['Veículo']) if v_idx is not None else "")
                v_pla = st.text_input("Placa*", value=str(df_v.iloc[v_idx]['Placa']) if v_idx is not None else "").upper().strip()
                v_km_r = st.number_input("KM Últ. Revisão*", value=int(df_v.iloc[v_idx]['Ult_Revisao_KM']) if v_idx is not None else 0)
                v_dt_r = st.date_input("Data Últ. Revisão*", value=datetime.strptime(str(df_v.iloc[v_idx]['Ult_Revisao_Data']), '%Y-%m-%d').date() if v_idx is not None else date.today())
                v_i_km = st.number_input("Intervalo KM*", value=int(df_v.iloc[v_idx]['Int_KM']) if v_idx is not None else 10000)
                v_i_m = st.number_input("Intervalo Meses*", value=int(df_v.iloc[v_idx]['Int_Meses']) if v_idx is not None else 12)
                v_a_km = st.number_input("Alerta KM antes*", value=int(df_v.iloc[v_idx]['Alert_KM']) if v_idx is not None else 500)
                v_a_d = st.number_input("Alerta Dias antes*", value=int(df_v.iloc[v_idx]['Alert_Dias']) if v_idx is not None else 30)
                if st.form_submit_button("Salvar"):
                    if v_mod and v_pla:
                        nova = {"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": v_km_r, "Ult_Revisao_Data": str(v_dt_r), "Int_KM": v_i_km, "Int_Meses": v_i_m, "Alert_KM": v_a_km, "Alert_Dias": v_a_d, "Status": "Ativo"}
                        if v_idx is not None: df_v.iloc[v_idx] = nova
                        else: df_v = pd.concat([df_v, pd.DataFrame([nova])], ignore_index=True)
                        salvar(df_v, ARQ_VEIC); st.session_state.edit_v_idx = None; st.rerun()
            for i, r in df_v.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Veículo']}** ({r['Placa']})")
                    if st.button("📝 Editar", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()
                    if st.button("🗑️ Excluir", key=f"dv{i}"): salvar(df_v.drop(i), ARQ_VEIC); st.rerun()

        with c2:
            st.subheader("👤 Usuários")
            df_u = carregar(ARQ_MOT)
            with st.form("f_user"):
                u_idx = st.session_state.edit_u_idx
                u_n = st.text_input("Nome*", value=str(df_u.iloc[u_idx]['Nome']) if u_idx is not None else "")
                u_c = st.date_input("CNH*", value=datetime.strptime(str(df_u.iloc[u_idx]['Validade_CNH']), '%Y-%m-%d').date() if u_idx is not None else date.today())
                u_a = st.selectbox("Admin?", ["Não", "Sim"], index=0 if u_idx is None or str(df_u.iloc[u_idx]['Admin'])=="Não" else 1)
                if st.form_submit_button("Salvar"):
                    if u_idx is not None: df_u.iloc[u_idx] = {"Nome": u_n, "Validade_CNH": str(u_c), "Status": "Ativo", "Senha": df_u.iloc[u_idx]['Senha'], "Admin": u_a}
                    else: df_u = pd.concat([df_u, pd.DataFrame([{"Nome": u_n, "Validade_CNH": str(u_c), "Status": "Ativo", "Senha": "", "Admin": u_a}])], ignore_index=True)
                    salvar(df_u, ARQ_MOT); st.session_state.edit_u_idx = None; st.rerun()
            for i, r in df_u.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Nome']}** ({r['Admin']})")
                    if st.button("📝 Editar", key=f"eu{i}"): st.session_state.edit_u_idx = i; st.rerun()
                    if st.button("🗑️ Excluir", key=f"du{i}"): salvar(df_u.drop(i), ARQ_MOT); st.rerun()

# --- ABA SAÍDA ---
with tabs[1 + idx_tab]:
    st.header("📤 Registrar Saída")
    df_v_at = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    v_s = st.selectbox("Selecione o Veículo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_at.iterrows()], key=f"vs_{st.session_state.reset_key}")
    m_s = st.session_state.user_logado if st.session_state.perfil == "motorista" else st.selectbox("Motorista", [""] + carregar(ARQ_MOT)['Nome'].tolist(), key=f"ms_{st.session_state.reset_key}")
    if v_s and m_s:
        st_v = get_status_veiculo(v_s); u_i = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Nome'] == m_s].iloc[0]
        dt_cnh = datetime.strptime(str(u_i['Validade_CNH']), '%Y-%m-%d').date()
        v_i = df_v_at[df_v_at['Placa'] == v_s.split('(')[1].replace(')','')].iloc[0]
        s_rev, m_rev = calcular_revisao(v_i, st_v['km'])
        st.write(f"**Revisão:** {s_rev} | {m_rev}")
        if dt_cnh < date.today(): st.error("🚫 CNH VENCIDA! Bloqueado.")
        elif st_v["acao"] == "SAÍDA": st.error("Em uso.")
        else:
            km_s = st.number_input("KM Inicial*", min_value=st_v['km'], value=st_v['km'], key=f"kms_{st.session_state.reset_key}")
            av_at = [x.strip() for x in st_v['av'].replace('|',',').split(',')] if st_v['av'] != "Nenhuma" else []
            check = st.multiselect("Avarias:", list(set(carregar(ARQ_PECAS)['Item'].tolist() + av_at)), default=av_at, key=f"chs_{st.session_state.reset_key}")
            fotos = st.file_uploader("Fotos", accept_multiple_files=True, key=f"fs_{st.session_state.reset_key}")
            if st.button("Confirmar Saída"):
                nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "SAÍDA", "Veículo": v_s, "Usuário": m_s, "KM": km_s, "CNH": str(dt_cnh), "Av_Saida": ", ".join(check), "Av_Totais": ", ".join(check), "Foto_Base64": converter_multiplas_fotos(fotos)}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA CHEGADA ---
with tabs[2 + idx_tab]:
    st.header("📥 Registrar Chegada")
    veic_uso = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["acao"] == "SAÍDA"]
    v_r = st.selectbox("Veículo retorno", [""] + veic_uso, key=f"vr_{st.session_state.reset_key}")
    if v_r:
        st_r = get_status_veiculo(v_r)
        km_f = st.number_input("KM Final*", min_value=st_r['km'], value=st_r['km'], key=f"kmr_{st.session_state.reset_key}")
        fotos_c = st.file_uploader("Fotos Chegada", accept_multiple_files=True, key=f"fr_{st.session_state.reset_key}")
        if st.button("Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "CHEGADA", "Veículo": v_r, "Usuário": st_r['user'], "KM": km_f, "Av_Saida": st_r['av'], "Av_Totais": st_r['r_av'] if 'r_av' in st_r else st_r['av'], "Foto_Base64": converter_multiplas_fotos(fotos_c)}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA MANUTENÇÃO ---
with tabs[3 + idx_tab]:
    st.header("🔧 Oficina")
    v_m = st.selectbox("Veículo reparo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows() if get_status_veiculo(f"{r['Veículo']} ({r['Placa']})")["av"] != "Nenhuma"], key=f"vm_{st.session_state.reset_key}")
    if v_m:
        st_m = get_status_veiculo(v_m); atuais = [x.strip() for x in st_m['av'].replace('|',',').split(',')]
        reps = st.multiselect("Consertados:", atuais, key=f"reps_{st.session_state.reset_key}")
        loc = st.text_input("Local", key=f"loc_{st.session_state.reset_key}"); val = st.number_input("Valor", min_value=0.0, key=f"val_{st.session_state.reset_key}")
        if st.button("Salvar Manutenção"):
            rest = [i for i in atuais if i not in reps]
            nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "REPARO", "Veículo": v_m, "Usuário": loc, "KM": st_m['km'], "Av_Totais": " | ".join(rest) if rest else "Nenhuma", "Valor_Reparo": val, "Local_Reparo": loc, "Obs": f"Conserto: {', '.join(reps)}"}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA HISTÓRICO ---
with tabs[4 + idx_tab]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        idx = st.selectbox("Detalhes ID:", df_h.index)
        if st.session_state.perfil == "admin" and st.button("🗑️ Excluir"): salvar(df_h.drop(idx), ARQ_HIST); st.rerun()
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            for f in str(fb64).split(";"):
                if f: st.image(base64.b64decode(f), width=450)
