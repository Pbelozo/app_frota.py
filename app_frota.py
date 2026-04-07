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

# 3. Funções de Sistema
def inicializar():
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Foto_Base64"]).to_csv(ARQ_HIST, index=False)
    
    if not os.path.exists(ARQ_MOT):
        # Adicionada coluna 'Admin' no cadastro de motoristas
        pd.DataFrame(columns=["Nome", "Validade_CNH", "Status", "Senha", "Admin"]).to_csv(ARQ_MOT, index=False)
    else:
        dfm = pd.read_csv(ARQ_MOT)
        if "Admin" not in dfm.columns:
            dfm["Admin"] = "Não"
            dfm.to_csv(ARQ_MOT, index=False)

    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Intervalo_KM", "Status"]).to_csv(ARQ_VEIC, index=False)
    
    if not os.path.exists(ARQ_PECAS):
        pecas_p = ["1. Paralama dianteiro esquerdo", "2. Paralama dianteiro direito", "3. Párachoque dianteiro", "4. Capô", "5. Parabrisa", "6. Teto", "7. Porta dianteira direita", "8. Porta traseira direita", "9. Porta dianteira esquerda", "10. Porta traseira esquerda"]
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

# --- LOGIN ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'perfil' not in st.session_state: st.session_state.perfil = "motorista"
if 'user_logado' not in st.session_state: st.session_state.user_logado = None

def login():
    st.title("🚗 Gestão de Frota - Acesso")
    # Caso não existam motoristas (primeiro uso), permite criar o primeiro admin com senha mestra
    df_m = carregar(ARQ_MOT)
    if df_m.empty:
        st.warning("Nenhum usuário cadastrado. Use a senha mestra para configurar o primeiro Administrador.")
        s_mestra = st.text_input("Senha Mestra", type="password")
        if st.button("Acessar como Super Admin") and s_mestra == "admin123":
            st.session_state.autenticado = True
            st.session_state.perfil = "admin"
            st.rerun()
        return

    df_m_ativos = df_m[df_m['Status'] == "Ativo"]
    nome_m = st.selectbox("Selecione seu Usuário", [""] + df_m_ativos['Nome'].tolist())
    
    if nome_m:
        dados_m = df_m[df_m['Nome'] == nome_m].iloc[0]
        if dados_m['Senha'] == "":
            nova_senha = st.text_input("Cadastre sua Senha", type="password")
            if st.button("Salvar e Entrar"):
                idx = df_m[df_m['Nome'] == nome_m].index[0]
                df_m.at[idx, 'Senha'] = nova_senha
                salvar(df_m, ARQ_MOT)
                st.session_state.autenticado = True
                st.session_state.perfil = "admin" if dados_m['Admin'] == "Sim" else "motorista"
                st.session_state.user_logado = nome_m
                st.rerun()
        else:
            senha_m = st.text_input("Sua Senha", type="password")
            if st.button("Entrar"):
                if str(senha_m) == str(dados_m['Senha']):
                    st.session_state.autenticado = True
                    st.session_state.perfil = "admin" if dados_m['Admin'] == "Sim" else "motorista"
                    st.session_state.user_logado = nome_m
                    st.rerun()
                else: st.error("Senha incorreta")

if not st.session_state.autenticado:
    login()
    st.stop()

# --- INTERFACE PRINCIPAL ---
st.title("Gestão de Frota")
st.sidebar.write(f"Logado como: **{st.session_state.user_logado or 'SuperAdmin'}**")
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

abas = ["📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"]
if st.session_state.perfil == "admin":
    abas.insert(0, "⚙️ Gestão & Cadastro")

tabs = st.tabs(abas)
idx_tab = 0 if st.session_state.perfil == "admin" else -1

# --- ABA GESTÃO (SÓ ADMIN) ---
if st.session_state.perfil == "admin":
    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("🚗 Veículos")
            df_v = carregar(ARQ_VEIC)
            with st.form("f_v"):
                v_mod = st.text_input("Modelo")
                v_pla = st.text_input("Placa").upper()
                v_dt = st.date_input("Data Últ. Revisão", value=None)
                if st.form_submit_button("Salvar Veículo"):
                    salvar(pd.concat([df_v, pd.DataFrame([{"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": 0, "Ult_Revisao_Data": v_dt, "Intervalo_KM": 10000, "Status": "Ativo"}])], ignore_index=True), ARQ_VEIC)
                    st.rerun()
            for i, r in df_v.iterrows():
                with st.container(border=True):
                    st.write(f"{r['Veículo']} ({r['Placa']})")
                    if st.button("Ativar/Bloquear", key=f"bv{i}"):
                        df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                        salvar(df_v, ARQ_VEIC); st.rerun()

        with c2:
            st.subheader("👤 Usuários / Motoristas")
            df_m = carregar(ARQ_MOT)
            with st.form("f_m"):
                m_nome = st.text_input("Nome Completo")
                m_val = st.date_input("Validade CNH", value=None)
                m_adm = st.selectbox("Administrador?", ["Não", "Sim"])
                if st.form_submit_button("Cadastrar Usuário"):
                    if m_nome:
                        salvar(pd.concat([df_m, pd.DataFrame([{"Nome": m_nome, "Validade_CNH": m_val, "Status": "Ativo", "Senha": "", "Admin": m_adm}])], ignore_index=True), ARQ_MOT)
                        st.rerun()
            for i, r in df_m.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Nome']}** (Adm: {r['Admin']})")
                    c_b1, c_b2 = st.columns(2)
                    if c_b1.button("Reset Senha", key=f"rs{i}"):
                        df_m.at[i, 'Senha'] = ""; salvar(df_m, ARQ_MOT); st.rerun()
                    if c_b2.button("Bloquear", key=f"bm{i}"):
                        df_m.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                        salvar(df_m, ARQ_MOT); st.rerun()

        with c3:
            st.subheader("📋 Checklist")
            df_p = carregar(ARQ_PECAS)
            n_p = st.text_input("Novo Item de Avaria")
            if st.button("Adicionar"):
                salvar(pd.concat([df_p, pd.DataFrame([{"Item": n_p, "Status": "Ativo"}])], ignore_index=True), ARQ_PECAS); st.rerun()
            st.dataframe(df_p)

# --- ABA SAÍDA ---
with tabs[1 + idx_tab]:
    st.header("📤 Registrar Saída")
    df_v_ativos = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    v_s = st.selectbox("Selecione o Veículo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_ativos.iterrows()], index=0)
    
    if st.session_state.perfil == "admin":
        m_s = st.selectbox("Selecione o Motorista", [""] + carregar(ARQ_MOT)['Nome'].tolist(), index=0)
    else:
        m_s = st.session_state.user_logado

    if v_s != "" and m_s != "":
        st_v = get_status_veiculo(v_s)
        if st_v["acao"] == "SAÍDA": st.error(f"Veículo com {st_v['user']}")
        else:
            # KM Inicial em branco (0 para forçar preenchimento)
            km_sai = st.number_input("Informe o KM Inicial", min_value=st_v['km'], value=st_v['km'])
            fotos_s = st.file_uploader("Fotos", accept_multiple_files=True)
            av_bruto = st_v['av'].replace(' | ', ',').replace('|', ',')
            d_av = [x.strip() for x in av_bruto.split(',')] if st_v['av'] != "Nenhuma" else []
            p_lista = carregar(ARQ_PECAS)[carregar(ARQ_PECAS)['Status'] == "Ativo"]['Item'].tolist()
            checklist = st.multiselect("Confirme as Avarias Atuais:", list(set(p_lista + d_av)), default=d_av)
            
            if st.button("Confirmar Saída"):
                if km_sai > 0:
                    nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "SAÍDA", "Veículo": v_s, "Usuário": m_s, "KM": km_sai, "Av_Saida": ", ".join(checklist), "Av_Chegada": "Pendente", "Av_Totais": ", ".join(checklist), "Foto_Base64": converter_multiplas_fotos(fotos_s)}])
                    salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()
                else: st.error("Informe a quilometragem.")

# --- ABA CHEGADA ---
with tabs[2 + idx_tab]:
    st.header("📥 Registrar Chegada")
    veiculos_uso = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["acao"] == "SAÍDA"]
    v_ret = st.selectbox("Veículo para retorno", [""] + veiculos_uso, index=0)
    if v_ret != "":
        st_ret = get_status_veiculo(v_ret)
        km_f = st.number_input("KM Final", min_value=st_ret['km'], value=st_ret['km'])
        fotos_c = st.file_uploader("Fotos Chegada", accept_multiple_files=True)
        if st.button("Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "CHEGADA", "Veículo": v_ret, "Usuário": st_ret['user'], "KM": km_f, "Av_Saida": st_ret['av'], "Av_Totais": st_ret['av'], "Foto_Base64": converter_multiplas_fotos(fotos_c)}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA MANUTENÇÃO ---
with tabs[3 + idx_tab]:
    st.header("🔧 Oficina")
    # Filtro: Só exibe veículos que possuem avarias no histórico (Av_Totais != "Nenhuma")
    todos_veic = [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()]
    veiculos_com_avaria = [v for v in todos_veic if get_status_veiculo(v)["av"] != "Nenhuma"]
    
    v_m = st.selectbox("Veículo na oficina", [""] + veiculos_com_avaria, index=0)
    if v_m != "":
        st_man = get_status_veiculo(v_m)
        av_limpo = st_man['av'].replace(' | ', ',').replace('|', ',')
        lista_atuais = [x.strip() for x in av_limpo.split(',')]
        reparados = st.multiselect("Quais avarias foram consertadas?", lista_atuais)
        if st.button("Salvar Manutenção"):
            restantes = [i for i in lista_atuais if i not in reparados]
            nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "REPARO", "Veículo": v_m, "Usuário": "Oficina", "KM": st_man['km'], "Av_Totais": " | ".join(restantes) if restantes else "Nenhuma"}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA HISTÓRICO ---
with tabs[4 + idx_tab]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        idx = st.selectbox("ID para fotos:", df_h.index)
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            for f in str(fb64).split(";"):
                if f: st.image(base64.b64decode(f), width=400)
