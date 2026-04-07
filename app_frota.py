import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import os
import base64
from io import BytesIO
from PIL import Image

# 1. Configuração Inicial
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗", layout="wide")

# 2. Arquivos
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"
ARQ_PECAS = "cadastro_pecas.csv"

# 3. Inicialização e Integridade
def inicializar():
    col_h = ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Valor_Reparo", "Local_Reparo", "Foto_Base64"]
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=col_h).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_MOT):
        pd.DataFrame(columns=["Nome", "Validade_CNH", "Status", "Senha", "Admin"]).to_csv(ARQ_MOT, index=False)
    col_v = ["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Int_KM", "Int_Meses", "Alert_KM", "Alert_Dias", "Status"]
    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=col_v).to_csv(ARQ_VEIC, index=False)
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
        i_km = int(v_info['Int_KM'])
        i_mes = int(v_info['Int_Meses'])
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

# --- LOGIN E CONTROLE DE ESTADO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'user_logado' not in st.session_state: st.session_state.user_logado = None
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0 # Chave para forçar limpeza

if not st.session_state.autenticado:
    st.title("🚗 Gestão de Frota - Login")
    df_m_log = carregar(ARQ_MOT)
    if df_m_log.empty:
        s_mestra = st.text_input("Senha Mestra Inicial", type="password")
        if st.button("Acessar") and s_mestra == "admin123":
            st.session_state.autenticado = True; st.session_state.perfil = "admin"; st.rerun()
    else:
        col_l, _ = st.columns([2, 3])
        with col_l:
            nome_m = st.selectbox("Selecione seu Usuário", [""] + df_m_log[df_m_log['Status'] == "Ativo"]['Nome'].tolist())
            if nome_m:
                dados_m = df_m_log[df_m_log['Nome'] == nome_m].iloc[0]
                if str(dados_m['Senha']).strip() == "":
                    nova_s = st.text_input("Crie sua Senha", type="password")
                    if st.button("Salvar") and nova_s:
                        idx = df_m_log[df_m_log['Nome'] == nome_m].index[0]
                        df_m_log.at[idx, 'Senha'] = str(nova_s); salvar(df_m_log, ARQ_MOT); st.rerun()
                else:
                    senha_i = st.text_input("Senha", type="password")
                    if st.button("Entrar"):
                        if str(senha_i) == str(dados_m['Senha']):
                            st.session_state.autenticado = True
                            st.session_state.perfil = "admin" if dados_m['Admin'] == "Sim" else "motorista"
                            st.session_state.user_logado = nome_m; st.rerun()
                        else: st.error("Incorreta")
    st.stop()

# --- INTERFACE ---
st.title("Gestão de Frota")
if st.sidebar.button("Sair"): st.session_state.autenticado = False; st.rerun()

abas = ["📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"]
if st.session_state.perfil == "admin": abas.insert(0, "⚙️ Gestão & Cadastro")
tabs = st.tabs(abas)
idx_tab = 0 if st.session_state.perfil == "admin" else -1

# --- ABA 0: GESTÃO ---
if st.session_state.perfil == "admin":
    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("🚗 Veículos")
            df_v = carregar(ARQ_VEIC)
            with st.form("f_v"):
                v_mod = st.text_input("Modelo*"); v_pla = st.text_input("Placa*").upper().strip()
                v_km_r = st.number_input("KM Últ. Revisão*", min_value=0)
                v_dt_r = st.date_input("Data Últ. Revisão*", value=date.today())
                v_int_km = st.number_input("Intervalo KM*", value=10000); v_int_m = st.number_input("Intervalo Meses*", value=12)
                v_al_km = st.number_input("Aviso KM antes*", value=500); v_al_d = st.number_input("Aviso Dias antes*", value=30)
                if st.form_submit_button("Salvar"):
                    if v_mod and v_pla:
                        nova = {"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": v_km_r, "Ult_Revisao_Data": str(v_dt_r), "Int_KM": v_int_km, "Int_Meses": v_int_m, "Alert_KM": v_al_km, "Alert_Dias": v_al_d, "Status": "Ativo"}
                        salvar(pd.concat([df_v, pd.DataFrame([nova])], ignore_index=True), ARQ_VEIC); st.rerun()
            for i, r in df_v.iterrows():
                if st.button(f"🗑️ {r['Placa']}", key=f"dv{i}"): salvar(df_v.drop(i), ARQ_VEIC); st.rerun()
        with c2:
            st.subheader("👤 Usuários")
            df_u = carregar(ARQ_MOT)
            with st.form("f_u"):
                un = st.text_input("Nome*"); uc = st.date_input("Validade CNH*"); ua = st.selectbox("Admin?", ["Não", "Sim"])
                if st.form_submit_button("Cadastrar"):
                    if un: salvar(pd.concat([df_u, pd.DataFrame([{"Nome": un, "Validade_CNH": str(uc), "Status": "Ativo", "Senha": "", "Admin": ua}])], ignore_index=True), ARQ_MOT); st.rerun()
            for i, r in df_u.iterrows():
                if st.button(f"🗑️ {r['Nome']}", key=f"du{i}"): salvar(df_u.drop(i), ARQ_MOT); st.rerun()
        with c3:
            st.subheader("📋 Avarias")
            df_a = carregar(ARQ_PECAS)
            na = st.text_input("Nova")
            if st.button("Add"): salvar(pd.concat([df_a, pd.DataFrame([{"Item": na, "Status": "Ativo"}])], ignore_index=True), ARQ_PECAS); st.rerun()
            st.dataframe(df_a)

# --- ABA 1: SAÍDA ---
with tabs[1 + idx_tab]:
    st.header("📤 Registrar Saída")
    # A 'reset_key' garante que os campos voltem ao estado inicial (índice 0 / vazio)
    df_v_at = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    v_s = st.selectbox("Selecione o Veículo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_at.iterrows()], key=f"v_saida_{st.session_state.reset_key}")
    m_s = st.session_state.user_logado if st.session_state.perfil == "motorista" else st.selectbox("Motorista", [""] + carregar(ARQ_MOT)['Nome'].tolist(), key=f"m_saida_{st.session_state.reset_key}")
    
    if v_s and m_s:
        st_v = get_status_veiculo(v_s)
        u_info = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Nome'] == m_s].iloc[0]
        dt_cnh = datetime.strptime(str(u_info['Validade_CNH']), '%Y-%m-%d').date()
        v_info = df_v_at[df_v_at['Placa'] == v_s.split('(')[1].replace(')','')].iloc[0]
        
        s_rev, m_rev = calcular_revisao(v_info, st_v['km'])
        st.info(f"REVISÃO: {s_rev} | {m_rev}")

        if dt_cnh < date.today(): st.error(f"🚫 BLOQUEADO: CNH de {m_s} vencida!")
        elif st_v["acao"] == "SAÍDA": st.error("Veículo em uso.")
        else:
            km_sai = st.number_input("KM Inicial*", min_value=st_v['km'], value=st_v['km'], key=f"km_saida_{st.session_state.reset_key}")
            av_atuais = [x.strip() for x in st_v['av'].replace('|',',').split(',')] if st_v['av'] != "Nenhuma" else []
            checklist = st.multiselect("Confirme as Avarias:", list(set(carregar(ARQ_PECAS)['Item'].tolist() + av_atuais)), default=av_atuais, key=f"check_saida_{st.session_state.reset_key}")
            fotos_s = st.file_uploader("Fotos", accept_multiple_files=True, key=f"foto_saida_{st.session_state.reset_key}")
            
            if st.button("🚀 Confirmar Saída"):
                nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "SAÍDA", "Veículo": v_s, "Usuário": m_s, "KM": km_sai, "CNH": str(dt_cnh), "Av_Saida": ", ".join(checklist), "Av_Totais": ", ".join(checklist), "Foto_Base64": converter_multiplas_fotos(fotos_s)}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST)
                st.session_state.reset_key += 1 # Limpa todos os campos para o próximo
                st.rerun()

# --- ABA 2: CHEGADA ---
with tabs[2 + idx_tab]:
    st.header("📥 Registrar Chegada")
    veic_uso = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["acao"] == "SAÍDA"]
    v_ret = st.selectbox("Veículo retorno", [""] + veic_uso, key=f"v_ret_{st.session_state.reset_key}")
    if v_ret:
        st_ret = get_status_veiculo(v_ret)
        km_f = st.number_input("KM Final*", min_value=st_ret['km'], value=st_ret['km'], key=f"km_ret_{st.session_state.reset_key}")
        fotos_c = st.file_uploader("Fotos", accept_multiple_files=True, key=f"foto_ret_{st.session_state.reset_key}")
        if st.button("🏁 Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "CHEGADA", "Veículo": v_ret, "Usuário": st_ret['user'], "KM": km_f, "Av_Saida": st_ret['av'], "Av_Totais": st_ret['av'], "Foto_Base64": converter_multiplas_fotos(fotos_c)}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST)
            st.session_state.reset_key += 1
            st.rerun()

# --- ABA 3: MANUTENÇÃO ---
with tabs[3 + idx_tab]:
    st.header("🔧 Oficina")
    veic_man = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["av"] != "Nenhuma"]
    v_m = st.selectbox("Veículo reparo", [""] + veic_man, key=f"v_man_{st.session_state.reset_key}")
    if v_m:
        st_man = get_status_veiculo(v_m)
        atuais = [x.strip() for x in st_man['av'].replace('|',',').split(',')]
        reps = st.multiselect("Consertados:", atuais, key=f"reps_{st.session_state.reset_key}")
        loc = st.text_input("Local", key=f"loc_{st.session_state.reset_key}")
        val = st.number_input("Valor", min_value=0.0, key=f"val_{st.session_state.reset_key}")
        if st.button("🛠️ Salvar"):
            rest = [i for i in atuais if i not in reps]
            nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "REPARO", "Veículo": v_m, "Usuário": loc, "KM": st_man['km'], "Av_Totais": " | ".join(rest) if rest else "Nenhuma", "Valor_Reparo": val, "Local_Reparo": loc, "Obs": f"Reparo: {', '.join(reps)}"}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST)
            st.session_state.reset_key += 1
            st.rerun()

# --- ABA 4: HISTÓRICO ---
with tabs[4 + idx_tab]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        idx = st.selectbox("ID:", df_h.index)
        if st.session_state.perfil == "admin" and st.button("🗑️ EXCLUIR"): salvar(df_h.drop(idx), ARQ_HIST); st.rerun()
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            for f in str(fb64).split(";"):
                if f: st.image(base64.b64decode(f), width=400)
