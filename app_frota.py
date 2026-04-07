import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import os
import base64
from io import BytesIO
from PIL import Image

# 1. Configuração e Título
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗", layout="wide")

# 2. Caminhos dos Arquivos
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"
ARQ_PECAS = "cadastro_pecas.csv"

# 3. Funções de Sistema e Migração de Colunas
def inicializar():
    colunas_h = ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Valor_Reparo", "Local_Reparo", "Foto_Base64"]
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=colunas_h).to_csv(ARQ_HIST, index=False)
    else:
        df_h_check = pd.read_csv(ARQ_HIST)
        # Migração automática para incluir novas colunas se não existirem
        for col in ["Valor_Reparo", "Local_Reparo"]:
            if col not in df_h_check.columns:
                df_h_check[col] = ""
                df_h_check.to_csv(ARQ_HIST, index=False)
    
    if not os.path.exists(ARQ_MOT):
        pd.DataFrame(columns=["Nome", "Validade_CNH", "Status", "Senha", "Admin"]).to_csv(ARQ_MOT, index=False)
    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Intervalo_KM", "Status"]).to_csv(ARQ_VEIC, index=False)
    if not os.path.exists(ARQ_PECAS):
        pecas_p = ["1. Capô", "2. Parabrisa", "3. Parachoque Dianteiro", "4. Parachoque Traseiro", "5. Pneus", "6. Teto"]
        pd.DataFrame({"Item": pecas_p, "Status": ["Ativo"] * len(pecas_p)}).to_csv(ARQ_PECAS, index=False)

inicializar()

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
            return {"acao": ult['Ação'], "user": ult['Usuário'], "km": int(ult['KM']), "av": str(ult['Av_Totais']) if str(ult['Av_Totais']).strip() != "" else "Nenhuma"}
    return {"acao": "CHEGADA", "user": "Ninguém", "km": 0, "av": "Nenhuma"}

def converter_multiplas_fotos(uploaded_files):
    lista_b64 = []
    if uploaded_files:
        for file in uploaded_files:
            img = Image.open(file); img.thumbnail((800, 800))
            buf = BytesIO(); img.save(buf, format="JPEG", quality=70)
            lista_b64.append(base64.b64encode(buf.getvalue()).decode())
    return ";".join(lista_b64)

# --- CONTROLE DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'perfil' not in st.session_state: st.session_state.perfil = "motorista"
if 'user_logado' not in st.session_state: st.session_state.user_logado = None

if not st.session_state.autenticado:
    st.title("🚗 Gestão de Frota - Login")
    df_m_log = carregar(ARQ_MOT)
    if df_m_log.empty:
        s_mestra = st.text_input("Configuração Inicial - Senha Mestra", type="password")
        if st.button("Acessar") and s_mestra == "admin123":
            st.session_state.autenticado = True; st.session_state.perfil = "admin"; st.rerun()
    else:
        col_login, _ = st.columns([2, 3])
        with col_login:
            nome_m = st.selectbox("Usuário", [""] + df_m_log[df_m_log['Status'] == "Ativo"]['Nome'].tolist())
            if nome_m:
                dados_m = df_m_log[df_m_log['Nome'] == nome_m].iloc[0]
                if dados_m['Senha'] == "":
                    nova_s = st.text_input("Cadastre sua Senha", type="password")
                    if st.button("Salvar Senha"):
                        idx = df_m_log[df_m_log['Nome'] == nome_m].index[0]
                        df_m_log.at[idx, 'Senha'] = nova_s; salvar(df_m_log, ARQ_MOT); st.rerun()
                else:
                    senha_i = st.text_input("Senha", type="password")
                    if st.button("Entrar"):
                        if str(senha_i) == str(dados_m['Senha']):
                            st.session_state.autenticado = True
                            st.session_state.perfil = "admin" if dados_m['Admin'] == "Sim" else "motorista"
                            st.session_state.user_logado = nome_m; st.rerun()
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
            with st.form("f_v"):
                v_mod = st.text_input("Modelo")
                v_pla = st.text_input("Placa").upper()
                v_km_ini = st.number_input("KM Atual", min_value=0)
                if st.form_submit_button("Salvar"):
                    salvar(pd.concat([df_v, pd.DataFrame([{"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": v_km_ini, "Status": "Ativo"}])], ignore_index=True), ARQ_VEIC); st.rerun()
            st.dataframe(df_v[["Veículo", "Placa", "Status"]])
        with c2:
            st.subheader("👤 Usuários")
            df_m = carregar(ARQ_MOT)
            with st.form("f_m"):
                n_u = st.text_input("Nome")
                a_u = st.selectbox("Admin?", ["Não", "Sim"])
                if st.form_submit_button("Cadastrar"):
                    salvar(pd.concat([df_m, pd.DataFrame([{"Nome": n_u, "Status": "Ativo", "Senha": "", "Admin": a_u}])], ignore_index=True), ARQ_MOT); st.rerun()
            st.dataframe(df_m[["Nome", "Admin", "Status"]])
        with c3:
            st.subheader("📋 Checklist")
            df_p = carregar(ARQ_PECAS)
            n_p = st.text_input("Nova Avaria")
            if st.button("Adicionar"):
                salvar(pd.concat([df_p, pd.DataFrame([{"Item": n_p, "Status": "Ativo"}])], ignore_index=True), ARQ_PECAS); st.rerun()
            st.dataframe(df_p)

# --- ABA SAÍDA ---
with tabs[1 + idx_tab]:
    st.header("📤 Registrar Saída")
    col_s, _ = st.columns([2, 3])
    with col_s:
        df_v_ativos = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
        v_s = st.selectbox("Veículo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_ativos.iterrows()])
        m_s = st.session_state.user_logado if st.session_state.perfil == "motorista" else st.selectbox("Motorista", [""] + carregar(ARQ_MOT)['Nome'].tolist())
        
        if v_s and m_s:
            st_v = get_status_veiculo(v_s)
            if st_v["acao"] == "SAÍDA": st.error(f"Em uso por {st_v['user']}")
            else:
                km_sai = st.number_input("KM Inicial", min_value=st_v['km'], value=st_v['km'])
                fotos_s = st.file_uploader("Fotos", accept_multiple_files=True)
                p_lista = carregar(ARQ_PECAS)[carregar(ARQ_PECAS)['Status'] == "Ativo"]['Item'].tolist()
                av_atuais = [x.strip() for x in st_v['av'].replace('|',',').split(',')] if st_v['av'] != "Nenhuma" else []
                checklist = st.multiselect("Avarias Atuais", list(set(p_lista + av_atuais)), default=av_atuais)
                if st.button("Confirmar Saída"):
                    nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "SAÍDA", "Veículo": v_s, "Usuário": m_s, "KM": km_sai, "Av_Saida": ", ".join(checklist), "Av_Totais": ", ".join(checklist), "Foto_Base64": converter_multiplas_fotos(fotos_s)}])
                    salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA CHEGADA ---
with tabs[2 + idx_tab]:
    st.header("📥 Registrar Chegada")
    veiculos_uso = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["acao"] == "SAÍDA"]
    col_c, _ = st.columns([2, 3])
    with col_c:
        v_ret = st.selectbox("Veículo retorno", [""] + veiculos_uso)
        if v_ret:
            st_ret = get_status_veiculo(v_ret)
            km_f = st.number_input("KM Final", min_value=st_ret['km'], value=st_ret['km'])
            fotos_c = st.file_uploader("Fotos", accept_multiple_files=True)
            if st.button("Confirmar Chegada"):
                nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "CHEGADA", "Veículo": v_ret, "Usuário": st_ret['user'], "KM": km_f, "Av_Saida": st_ret['av'], "Av_Totais": st_ret['av'], "Foto_Base64": converter_multiplas_fotos(fotos_c)}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA MANUTENÇÃO ---
with tabs[3 + idx_tab]:
    st.header("🔧 Oficina")
    veiculos_com_avaria = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["av"] != "Nenhuma"]
    col_m, _ = st.columns([2, 3])
    with col_m:
        v_m = st.selectbox("Veículo para manutenção", [""] + veiculos_com_avaria)
        if v_m:
            st_man = get_status_veiculo(v_m)
            lista_atuais = [x.strip() for x in st_man['av'].replace('|',',').split(',')]
            reparados = st.multiselect("Quais itens foram consertados?", lista_atuais)
            local = st.text_input("Oficina / Local do Reparo")
            valor = st.number_input("Valor do Reparo (R$)", min_value=0.0, step=0.01)
            if st.button("Salvar Manutenção"):
                if reparados and local:
                    restantes = [i for i in lista_atuais if i not in reparados]
                    # Preenche Usuário com o Local do Reparo conforme solicitado
                    nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "REPARO", "Veículo": v_m, "Usuário": local, "KM": st_man['km'], "Av_Totais": " | ".join(restantes) if restantes else "Nenhuma", "Valor_Reparo": valor, "Local_Reparo": local, "Obs": f"Conserto de: {', '.join(reparados)}"}])
                    salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()
                else: st.warning("Informe os itens e o local.")

# --- ABA HISTÓRICO ---
with tabs[4 + idx_tab]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        col_h1, _ = st.columns([2, 3])
        with col_h1:
            idx = st.selectbox("Visualizar Detalhes (ID):", df_h.index)
        
        # Tabela sem a coluna de fotos para não poluir
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        
        # Galeria Lateral
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            st.write("### 🖼️ Fotos do Registro")
            for f in str(fb64).split(";"):
                if f: st.image(base64.b64decode(f), width=500)
