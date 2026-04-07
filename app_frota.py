import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import os
import base64
from io import BytesIO
from PIL import Image

# 1. Configuração da Página
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗", layout="wide")

# 2. Definição de Arquivos (Banco de Dados)
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"
ARQ_PECAS = "cadastro_pecas.csv"

# 3. Inicialização do Sistema (Garante que as colunas existam)
def inicializar():
    col_h = ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Valor_Reparo", "Local_Reparo", "Foto_Base64"]
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=col_h).to_csv(ARQ_HIST, index=False)
    
    if not os.path.exists(ARQ_MOT):
        pd.DataFrame(columns=["Nome", "Validade_CNH", "Status", "Senha", "Admin"]).to_csv(ARQ_MOT, index=False)
    
    col_v = ["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Int_KM", "Int_Meses", "Alert_KM", "Alert_Dias", "Status"]
    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=col_v).to_csv(ARQ_VEIC, index=False)
    else:
        dfv = pd.read_csv(ARQ_VEIC)
        for c in ["Int_KM", "Int_Meses", "Alert_KM", "Alert_Dias"]:
            if c not in dfv.columns: dfv[c] = 0
        dfv.to_csv(ARQ_VEIC, index=False)

    if not os.path.exists(ARQ_PECAS):
        pecas = ["1. Capô", "2. Parabrisa", "3. Párachoque dianteiro", "4. Teto"]
        pd.DataFrame({"Item": pecas, "Status": ["Ativo"] * len(pecas)}).to_csv(ARQ_PECAS, index=False)

inicializar()

# --- FUNÇÕES CORE ---
def carregar(arq): return pd.read_csv(arq).fillna("")
def salvar(df, arq): df.to_csv(arq, index=False)

def get_data_hora_br():
    fuso_br = timezone(timedelta(hours=-3))
    return datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")

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
        i_km = int(v_info['Int_KM']); i_mes = int(v_info['Int_Meses'])
        km_limite = int(v_info['Ult_Revisao_KM']) + i_km
        dt_ult = datetime.strptime(str(v_info['Ult_Revisao_Data']), '%Y-%m-%d').date()
        dt_limite = dt_ult + timedelta(days=i_mes * 30)
        hoje = date.today()
        if i_km > 0 and km_atual >= km_limite: return "🔴 VENCIDA (KM)", f"Limite {km_limite} KM"
        if i_mes > 0 and hoje >= dt_limite: return "🔴 VENCIDA (Prazo)", f"Venceu {dt_limite.strftime('%d/%m/%Y')}"
        return "🟢 EM DIA", "OK"
    except: return "⚪ AGUARDANDO DADOS", "-"

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
if 'user_logado' not in st.session_state: st.session_state.user_logado = None
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0
if 'edit_v_idx' not in st.session_state: st.session_state.edit_v_idx = None
if 'edit_u_idx' not in st.session_state: st.session_state.edit_u_idx = None

if not st.session_state.autenticado:
    st.title("🚗 Gestão de Frota - Login")
    df_m_log = carregar(ARQ_MOT)
    if df_m_log.empty:
        s_mestra = st.text_input("Configuração Inicial - Senha Mestra", type="password")
        if st.button("Acessar") and s_mestra == "admin123":
            st.session_state.autenticado = True; st.session_state.perfil = "admin"; st.rerun()
    else:
        col_l, _ = st.columns([2, 3])
        with col_l:
            # Força a limpeza de nomes vazios ou nulos para garantir que apareçam na lista
            lista_nomes = sorted(df_m_log[df_m_log['Status'] == "Ativo"]['Nome'].str.strip().unique().tolist())
            nome_m = st.selectbox("Selecione seu Usuário", [""] + lista_nomes)
            if nome_m:
                dados_m = df_m_log[df_m_log['Nome'].str.strip() == nome_m].iloc[0]
                if str(dados_m['Senha']).strip() == "":
                    nova_s = st.text_input("Cadastre sua Senha Pessoal", type="password")
                    if st.button("Salvar Senha"):
                        idx = df_m_log[df_m_log['Nome'].str.strip() == nome_m].index[0]
                        df_m_log.at[idx, 'Senha'] = str(nova_s); salvar(df_m_log, ARQ_MOT); st.rerun()
                else:
                    senha_i = st.text_input("Senha", type="password")
                    if st.button("Entrar"):
                        if str(senha_i) == str(dados_m['Senha']):
                            st.session_state.autenticado = True
                            st.session_state.perfil = "admin" if str(dados_m['Admin']) == "Sim" else "motorista"
                            st.session_state.user_logado = nome_m; st.rerun()
                        else: st.error("Senha Incorreta")
    st.stop()

# --- INTERFACE PRINCIPAL ---
st.title("Gestão de Frota")
if st.sidebar.button("Logoff / Sair"): st.session_state.autenticado = False; st.rerun()

abas = ["📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"]
if st.session_state.perfil == "admin": abas.insert(0, "⚙️ Gestão & Cadastro")
tabs = st.tabs(abas)
idx_tab = 0 if st.session_state.perfil == "admin" else -1

# --- ABA GESTÃO (ADMIN) ---
if st.session_state.perfil == "admin":
    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("🚗 Veículos")
            df_v = carregar(ARQ_VEIC)
            v_idx = st.session_state.edit_v_idx
            with st.form("f_v"):
                v_mod = st.text_input("Modelo*", value=str(df_v.iloc[v_idx]['Veículo']) if v_idx is not None else "")
                v_pla = st.text_input("Placa*", value=str(df_v.iloc[v_idx]['Placa']) if v_idx is not None else "").upper().strip()
                v_km_r = st.number_input("KM Últ. Revisão", value=int(df_v.iloc[v_idx]['Ult_Revisao_KM']) if v_idx is not None else 0)
                v_int_km = st.number_input("Intervalo KM", value=int(df_v.iloc[v_idx]['Int_KM']) if v_idx is not None else 10000)
                v_int_m = st.number_input("Intervalo Meses", value=int(df_v.iloc[v_idx]['Int_Meses']) if v_idx is not None else 12)
                if st.form_submit_button("Salvar Veículo"):
                    if v_mod and v_pla:
                        nova_v = {"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": v_km_r, "Ult_Revisao_Data": str(date.today()), "Int_KM": v_int_km, "Int_Meses": v_int_m, "Alert_KM": 500, "Alert_Dias": 30, "Status": "Ativo"}
                        if v_idx is not None: df_v.iloc[v_idx] = nova_v
                        else: df_v = pd.concat([df_v, pd.DataFrame([nova_v])], ignore_index=True)
                        salvar(df_v, ARQ_VEIC); st.session_state.edit_v_idx = None; st.rerun()
            for i, r in df_v.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Veículo']}** ({r['Placa']})")
                    b1, b2 = st.columns(2)
                    if b1.button("📝 Editar", key=f"edit_v_{i}"): st.session_state.edit_v_idx = i; st.rerun()
                    if b2.button("🗑️ Excluir", key=f"del_v_{i}"): salvar(df_v.drop(i), ARQ_VEIC); st.rerun()

        with c2:
            st.subheader("👤 Usuários")
            df_u = carregar(ARQ_MOT)
            u_idx = st.session_state.edit_u_idx
            with st.form("f_u"):
                u_n = st.text_input("Nome*", value=str(df_u.iloc[u_idx]['Nome']) if u_idx is not None else "")
                try: cnh_dt = datetime.strptime(str(df_u.iloc[u_idx]['Validade_CNH']), '%Y-%m-%d').date() if u_idx is not None else date.today()
                except: cnh_dt = date.today()
                u_c = st.date_input("CNH*", value=cnh_dt)
                u_a = st.selectbox("Admin?", ["Não", "Sim"], index=0 if u_idx is None or str(df_u.iloc[u_idx]['Admin'])=="Não" else 1)
                if st.form_submit_button("Salvar Usuário"):
                    if u_n:
                        nova_u = {"Nome": u_n, "Validade_CNH": str(u_c), "Status": "Ativo", "Senha": str(df_u.iloc[u_idx]['Senha']) if u_idx is not None else "", "Admin": u_a}
                        if u_idx is not None: df_u.iloc[u_idx] = nova_u
                        else: df_u = pd.concat([df_u, pd.DataFrame([nova_u])], ignore_index=True)
                        salvar(df_u, ARQ_MOT); st.session_state.edit_u_idx = None; st.rerun()
            for i, r in df_u.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Nome']}** ({r['Admin']})")
                    b1, b2 = st.columns(2)
                    if b1.button("📝 Editar", key=f"edit_u_{i}"): st.session_state.edit_u_idx = i; st.rerun()
                    if b2.button("🗑️ Excluir", key=f"del_u_{i}"): salvar(df_u.drop(i), ARQ_MOT); st.rerun()

        with c3:
            st.subheader("📋 Avarias")
            df_a = carregar(ARQ_PECAS)
            na = st.text_input("Nova Avaria")
            if st.button("Adicionar"):
                if na: salvar(pd.concat([df_a, pd.DataFrame([{"Item": na, "Status": "Ativo"}])], ignore_index=True), ARQ_PECAS); st.rerun()
            st.dataframe(df_a, use_container_width=True)

# --- ABA SAÍDA ---
with tabs[1 + idx_tab]:
    st.header("📤 Registrar Saída")
    df_v_at = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    v_s = st.selectbox("Selecione o Veículo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_at.iterrows()], key=f"vs_{st.session_state.reset_key}")
    m_s = st.session_state.user_logado if st.session_state.perfil == "motorista" else st.selectbox("Motorista", [""] + carregar(ARQ_MOT)['Nome'].tolist(), key=f"ms_{st.session_state.reset_key}")
    
    if v_s and m_s:
        st_v = get_status_veiculo(v_s)
        u_info = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Nome'].str.strip() == m_s].iloc[0]
        dt_cnh = datetime.strptime(str(u_info['Validade_CNH']), '%Y-%m-%d').date()
        v_info = df_v_at[df_v_at['Placa'] == v_s.split('(')[1].replace(')','')].iloc[0]
        
        s_rev, m_rev = calcular_revisao(v_info, st_v['km'])
        st.info(f"STATUS REVISÃO: {s_rev} | {m_rev}")

        if dt_cnh < date.today(): st.error("🚫 CNH VENCIDA! Bloqueado.")
        elif st_v["acao"] == "SAÍDA": st.error("Veículo em uso.")
        else:
            km_sai = st.number_input("KM Inicial*", min_value=st_v['km'], value=st_v['km'], key=f"kms_{st.session_state.reset_key}")
            av_atuais = [x.strip() for x in st_v['av'].replace('|',',').split(',')] if st_v['av'] != "Nenhuma" else []
            checklist = st.multiselect("Avarias:", list(set(carregar(ARQ_PECAS)['Item'].tolist() + av_atuais)), default=av_atuais, key=f"chs_{st.session_state.reset_key}")
            fotos_s = st.file_uploader("Fotos", accept_multiple_files=True, key=f"fs_{st.session_state.reset_key}")
            if st.button("Confirmar Saída"):
                nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "SAÍDA", "Veículo": v_s, "Usuário": m_s, "KM": km_sai, "CNH": str(dt_cnh), "Av_Saida": ", ".join(checklist), "Av_Totais": ", ".join(checklist), "Foto_Base64": converter_multiplas_fotos(fotos_s)}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA CHEGADA ---
with tabs[2 + idx_tab]:
    st.header("📥 Registrar Chegada")
    veic_uso = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["acao"] == "SAÍDA"]
    v_ret = st.selectbox("Veículo retorno", [""] + veic_uso, key=f"vr_{st.session_state.reset_key}")
    if v_ret:
        st_ret = get_status_veiculo(v_ret)
        km_f = st.number_input("KM Final*", min_value=st_ret['km'], value=st_ret['km'], key=f"kmr_{st.session_state.reset_key}")
        fotos_c = st.file_uploader("Fotos", accept_multiple_files=True, key=f"fr_{st.session_state.reset_key}")
        if st.button("Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "CHEGADA", "Veículo": v_ret, "Usuário": st_ret['user'], "KM": km_f, "Av_Saida": st_ret['av'], "Av_Totais": st_ret['av'], "Foto_Base64": converter_multiplas_fotos(fotos_c)}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

# --- ABA HISTÓRICO ---
with tabs[4 + idx_tab]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        idx = st.selectbox("Detalhes (ID):", df_h.index)
        if st.session_state.perfil == "admin" and st.button("🗑️ EXCLUIR REGISTRO"): salvar(df_h.drop(idx), ARQ_HIST); st.rerun()
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            for f in str(fb64).split(";"):
                if f: st.image(base64.b64decode(f), width=450)
