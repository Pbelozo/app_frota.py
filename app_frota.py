import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import os
import base64
from io import BytesIO
from PIL import Image

# 1. Configuração e Título
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗", layout="wide")

# --- SENHA DO ADMINISTRADOR ---
# Você pode alterar a senha abaixo se desejar
SENHA_ADMIN_MESTRA = "admin123"

# 2. Caminhos dos Arquivos
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"
ARQ_PECAS = "cadastro_pecas.csv"

# 3. Funções de Sistema (Correção de Integridade)
def inicializar():
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Foto_Base64"]).to_csv(ARQ_HIST, index=False)
    
    if not os.path.exists(ARQ_MOT):
        pd.DataFrame(columns=["Nome", "Validade_CNH", "Status", "Senha"]).to_csv(ARQ_MOT, index=False)
    else:
        dfm = pd.read_csv(ARQ_MOT)
        if "Senha" not in dfm.columns:
            dfm["Senha"] = ""
            dfm.to_csv(ARQ_MOT, index=False)
        if "Status" not in dfm.columns:
            dfm["Status"] = "Ativo"
            dfm.to_csv(ARQ_MOT, index=False)

    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Intervalo_KM", "Status"]).to_csv(ARQ_VEIC, index=False)
    else:
        dfv = pd.read_csv(ARQ_VEIC)
        if "Status" not in dfv.columns:
            dfv["Status"] = "Ativo"
            dfv.to_csv(ARQ_VEIC, index=False)
    
    if not os.path.exists(ARQ_PECAS):
        pecas_p = ["1. Capô", "2. Parabrisa", "3. Parachoque Dianteiro", "4. Parachoque Traseiro", "5. Pneus", "6. Teto", "7. Portas Dir", "8. Portas Esq"]
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

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'perfil' not in st.session_state: st.session_state.perfil = None
if 'user_logado' not in st.session_state: st.session_state.user_logado = None

def login():
    st.title("🚗 Gestão de Frota - Acesso")
    tipo_acesso = st.radio("Tipo de Acesso", ["Motorista", "Administrador"])
    
    if tipo_acesso == "Administrador":
        senha_adm = st.text_input("Senha Admin", type="password")
        if st.button("Entrar como Admin"):
            if senha_adm == SENHA_ADMIN_MESTRA:
                st.session_state.autenticado = True
                st.session_state.perfil = "admin"
                st.rerun()
            else: st.error("Senha incorreta")
    else:
        df_m = carregar(ARQ_MOT)
        df_m_ativos = df_m[df_m['Status'] == "Ativo"]
        nome_m = st.selectbox("Selecione seu Nome", [""] + df_m_ativos['Nome'].tolist())
        if nome_m:
            dados_m = df_m[df_m['Nome'] == nome_m].iloc[0]
            if dados_m['Senha'] == "":
                st.info("Primeiro acesso? Cadastre uma senha:")
                nova_senha = st.text_input("Criar Senha", type="password")
                if st.button("Cadastrar e Entrar"):
                    idx = df_m[df_m['Nome'] == nome_m].index[0]
                    df_m.at[idx, 'Senha'] = nova_senha
                    salvar(df_m, ARQ_MOT)
                    st.session_state.autenticado = True
                    st.session_state.perfil = "motorista"
                    st.session_state.user_logado = nome_m
                    st.rerun()
            else:
                senha_m = st.text_input("Sua Senha", type="password")
                if st.button("Entrar"):
                    if str(senha_m) == str(dados_m['Senha']):
                        st.session_state.autenticado = True
                        st.session_state.perfil = "motorista"
                        st.session_state.user_logado = nome_m
                        st.rerun()
                    else: st.error("Senha incorreta")

if not st.session_state.autenticado:
    login()
    st.stop()

# --- INTERFACE PRINCIPAL ---
st.title("Gestão de Frota")
if st.sidebar.button("Sair/Logoff"):
    st.session_state.autenticado = False
    st.rerun()

# Definição das abas conforme o perfil
if st.session_state.perfil == "admin":
    abas_nomes = ["⚙️ Gestão & Cadastro", "📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"]
else:
    abas_nomes = ["📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"]

tabs = st.tabs(abas_nomes)
offset = 0 if st.session_state.perfil == "admin" else -1

# --- ABA: GESTÃO & CADASTRO (Admin) ---
if st.session_state.perfil == "admin":
    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("🚗 Veículos")
            df_v = carregar(ARQ_VEIC)
            with st.form("f_v"):
                v_mod = st.text_input("Modelo")
                v_pla = st.text_input("Placa").upper().strip()
                v_km_r = st.number_input("KM Última Revisão", min_value=0)
                v_dt_r = st.date_input("Data Última Revisão", value=None)
                if st.form_submit_button("Salvar Veículo"):
                    if v_mod and v_pla and v_dt_r:
                        salvar(pd.concat([df_v, pd.DataFrame([{"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": v_km_r, "Ult_Revisao_Data": v_dt_r, "Intervalo_KM": 10000, "Status": "Ativo"}])], ignore_index=True), ARQ_VEIC)
                        st.rerun()
            for i, r in df_v.iterrows():
                with st.container(border=True):
                    st.write(f"{r['Veículo']} ({r['Placa']})")
                    if st.button("🚫 Bloquear/Ativar", key=f"bv{i}"):
                        df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                        salvar(df_v, ARQ_VEIC); st.rerun()
        with c2:
            st.subheader("👤 Motoristas")
            df_m = carregar(ARQ_MOT)
            for i, r in df_m.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Nome']}** - {r['Status']}")
                    col1, col2 = st.columns(2)
                    if col1.button("Reset Senha", key=f"rs{i}"):
                        df_m.at[i, 'Senha'] = ""; salvar(df_m, ARQ_MOT); st.success("Resetada")
                    if col2.button("🚫 Bloquear", key=f"bm{i}"):
                        df_m.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                        salvar(df_m, ARQ_MOT); st.rerun()
        with c3:
            st.subheader("📋 Checklist")
            df_p = carregar(ARQ_PECAS)
            n_p = st.text_input("Novo Item")
            if st.button("Adicionar"):
                salvar(pd.concat([df_p, pd.DataFrame([{"Item": n_p, "Status": "Ativo"}])], ignore_index=True), ARQ_PECAS); st.rerun()
            st.dataframe(df_p)

# --- ABA: SAÍDA ---
with tabs[1 + offset]:
    st.header("📤 Registrar Saída")
    df_v_ativos = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    p_lista = carregar(ARQ_PECAS)[carregar(ARQ_PECAS)['Status'] == "Ativo"]['Item'].tolist()
    v_s = st.selectbox("Selecione o Veículo", ["Selecione..."] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_ativos.iterrows()])
    m_s = st.session_state.user_logado if st.session_state.perfil == "motorista" else st.selectbox("Motorista", carregar(ARQ_MOT)['Nome'].tolist())
    if v_s != "Selecione...":
        st_v = get_status_veiculo(v_s)
        if st_v["acao"] == "SAÍDA": st.error(f"Bloqueado: Com {st_v['user']}")
        else:
            km_sai = st.number_input("KM Inicial", value=st_v['km'], min_value=st_v['km'])
            fotos_s = st.file_uploader("Fotos", accept_multiple_files=True)
            av_bruto = st_v['av'].replace(' | ', ',').replace('|', ',')
            d_av = [x.strip() for x in av_bruto.split(',')] if st_v['av'] != "Nenhuma" else []
            checklist = st.multiselect("Avarias", list(set(p_lista + d_av)), default=d_av)
            if st.button("🚀 Confirmar"):
                nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "SAÍDA", "Veículo": v_s, "Usuário": m_s, "KM": km_sai, "Av_Saida": ", ".join(checklist), "Av_Chegada": "Pendente", "Av_Totais": ", ".join(checklist), "Foto_Base64": converter_multiplas_fotos(fotos_s)}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA: CHEGADA ---
with tabs[2 + offset]:
    st.header("📥 Registrar Chegada")
    veiculos_uso = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["acao"] == "SAÍDA"]
    v_ret = st.selectbox("Veículo retornando", ["Selecione..."] + veiculos_uso)
    if v_ret != "Selecione...":
        st_ret = get_status_veiculo(v_ret)
        km_f = st.number_input("KM Final", min_value=st_ret['km'], value=st_ret['km'])
        fotos_c = st.file_uploader("Fotos Chegada", accept_multiple_files=True)
        if st.button("🏁 Confirmar"):
            nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "CHEGADA", "Veículo": v_ret, "Usuário": st_ret['user'], "KM": km_f, "Av_Saida": st_ret['av'], "Av_Totais": st_ret['av'], "Foto_Base64": converter_multiplas_fotos(fotos_c)}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA: MANUTENÇÃO ---
with tabs[3 + offset]:
    st.header("🔧 Oficina")
    v_m = st.selectbox("Veículo", ["Selecione..."] + [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()])
    if v_m != "Selecione...":
        st_man = get_status_veiculo(v_m)
        av_limpo = st_man['av'].replace(' | ', ',').replace('|', ',')
        lista_atuais = [x.strip() for x in av_limpo.split(',')] if st_man['av'] != "Nenhuma" else []
        reparados = st.multiselect("Consertados:", lista_atuais)
        if st.button("🛠️ Salvar"):
            restantes = [i for i in lista_atuais if i not in reparados]
            nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "REPARO", "Veículo": v_m, "Usuário": "Oficina", "KM": st_man['km'], "Av_Totais": " | ".join(restantes) if restantes else "Nenhuma"}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA: HISTÓRICO ---
with tabs[4 + offset]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        idx = st.selectbox("ID:", df_h.index)
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            for f in str(fb64).split(";"):
                if f: st.image(base64.b64decode(f), width=400)
