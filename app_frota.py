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
    colunas_h = ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Valor_Reparo", "Local_Reparo", "Foto_Base64"]
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=colunas_h).to_csv(ARQ_HIST, index=False)
    
    if not os.path.exists(ARQ_MOT):
        pd.DataFrame(columns=["Nome", "Validade_CNH", "Status", "Senha", "Admin"]).to_csv(ARQ_MOT, index=False)
    
    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Status"]).to_csv(ARQ_VEIC, index=False)
    
    if not os.path.exists(ARQ_PECAS):
        pecas_p = ["1. Paralama dianteiro esquerdo", "2. Paralama dianteiro direito", "3. Párachoque dianteiro", "4. Capô", "5. Parabrisa", "6. Teto"]
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

# 4. Controle de Sessão e Login
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'perfil' not in st.session_state: st.session_state.perfil = "motorista"
if 'user_logado' not in st.session_state: st.session_state.user_logado = None
if 'edit_v_idx' not in st.session_state: st.session_state.edit_v_idx = -1
if 'edit_m_idx' not in st.session_state: st.session_state.edit_m_idx = -1
if 'edit_p_idx' not in st.session_state: st.session_state.edit_p_idx = -1

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
                if dados_m['Senha'] == "":
                    nova_s = st.text_input("Crie sua Senha", type="password")
                    if st.button("Cadastrar e Entrar"):
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

# --- ABA 0: GESTÃO & CADASTRO (Admin) ---
if st.session_state.perfil == "admin":
    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        
        # VEÍCULOS
        with c1:
            st.subheader("🚗 Veículos")
            df_v = carregar(ARQ_VEIC)
            with st.expander("➕ Novo / Editar", expanded=(st.session_state.edit_v_idx != -1)):
                v_idx = st.session_state.edit_v_idx
                v_m = df_v.iloc[v_idx]['Veículo'] if v_idx != -1 else ""
                v_p = df_v.iloc[v_idx]['Placa'] if v_idx != -1 else ""
                v_k = int(df_v.iloc[v_idx]['Ult_Revisao_KM']) if v_idx != -1 else 0
                with st.form("f_veic"):
                    v_mod = st.text_input("Modelo", value=v_m)
                    v_pla = st.text_input("Placa", value=v_p).upper()
                    v_km = st.number_input("KM Atual", value=v_k)
                    if st.form_submit_button("Salvar Veículo"):
                        nova = {"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": v_km, "Status": "Ativo"}
                        if v_idx == -1: df_v = pd.concat([df_v, pd.DataFrame([nova])], ignore_index=True)
                        else:
                            for k, v in nova.items(): df_v.at[v_idx, k] = v
                        salvar(df_v, ARQ_VEIC); st.session_state.edit_v_idx = -1; st.rerun()
            for i, r in df_v.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Veículo']}** ({r['Placa']}) - {r['Status']}")
                    b1, b2 = st.columns(2)
                    if b1.button("📝 Editar", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()
                    if b2.button("🚫 Bloquear", key=f"bv{i}"):
                        df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                        salvar(df_v, ARQ_VEIC); st.rerun()

        # USUÁRIOS
        with c2:
            st.subheader("👤 Usuários")
            df_m = carregar(ARQ_MOT)
            with st.expander("➕ Novo / Editar", expanded=(st.session_state.edit_m_idx != -1)):
                m_idx = st.session_state.edit_m_idx
                m_n = df_m.iloc[m_idx]['Nome'] if m_idx != -1 else ""
                m_a = df_m.iloc[m_idx]['Admin'] if m_idx != -1 else "Não"
                with st.form("f_user"):
                    m_nome = st.text_input("Nome Completo", value=m_n)
                    m_adm = st.selectbox("Administrador?", ["Não", "Sim"], index=(0 if m_a=="Não" else 1))
                    if st.form_submit_button("Salvar Usuário"):
                        nova = {"Nome": m_nome, "Status": "Ativo", "Senha": "", "Admin": m_adm}
                        if m_idx == -1: df_m = pd.concat([df_m, pd.DataFrame([nova])], ignore_index=True)
                        else:
                            df_m.at[m_idx, 'Nome'] = m_nome
                            df_m.at[m_idx, 'Admin'] = m_adm
                        salvar(df_m, ARQ_MOT); st.session_state.edit_m_idx = -1; st.rerun()
            for i, r in df_m.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Nome']}** (Adm: {r['Admin']})")
                    b1, b2, b3 = st.columns(3)
                    if b1.button("📝", key=f"em{i}", help="Editar"): st.session_state.edit_m_idx = i; st.rerun()
                    if b2.button("🚫", key=f"bm{i}", help="Bloquear"):
                        df_m.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                        salvar(df_m, ARQ_MOT); st.rerun()
                    if b3.button("🔑", key=f"rs{i}", help="Reset Senha"):
                        df_m.at[i, 'Senha'] = ""; salvar(df_m, ARQ_MOT); st.success("Senha resetada!")

        # AVARIAS
        with c3:
            st.subheader("📋 Avarias")
            df_p = carregar(ARQ_PECAS)
            with st.expander("➕ Nova / Editar", expanded=(st.session_state.edit_p_idx != -1)):
                p_idx = st.session_state.edit_p_idx
                p_v = df_p.iloc[p_idx]['Item'] if p_idx != -1 else ""
                with st.form("f_av"):
                    n_p = st.text_input("Descrição da Avaria", value=p_v)
                    if st.form_submit_button("Salvar Avaria"):
                        if p_idx == -1: df_p = pd.concat([df_p, pd.DataFrame([{"Item": n_p, "Status": "Ativo"}])], ignore_index=True)
                        else: df_p.at[p_idx, 'Item'] = n_p
                        salvar(df_p, ARQ_PECAS); st.session_state.edit_p_idx = -1; st.rerun()
            for i, r in df_p.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Item']}** ({r['Status']})")
                    b1, b2 = st.columns(2)
                    if b1.button("📝", key=f"ep{i}"): st.session_state.edit_p_idx = i; st.rerun()
                    if b2.button("🚫", key=f"bp{i}"):
                        df_p.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                        salvar(df_p, ARQ_PECAS); st.rerun()

# --- ABA 1: SAÍDA ---
with tabs[1 + idx_tab]:
    st.header("📤 Registrar Saída")
    col_s, _ = st.columns([2, 3])
    with col_s:
        df_v_at = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
        v_s = st.selectbox("Selecione o Veículo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_at.iterrows()])
        m_s = st.session_state.user_logado if st.session_state.perfil == "motorista" else st.selectbox("Motorista", [""] + carregar(ARQ_MOT)['Nome'].tolist())
        
        if v_s and m_s:
            st_v = get_status_veiculo(v_s)
            if st_v["acao"] == "SAÍDA": st.error(f"Em uso por {st_v['user']}")
            else:
                km_sai = st.number_input("KM Inicial", min_value=st_v['km'], value=st_v['km'])
                fotos_s = st.file_uploader("Anexar Fotos", accept_multiple_files=True)
                p_lista = carregar(ARQ_PECAS)[carregar(ARQ_PECAS)['Status'] == "Ativo"]['Item'].tolist()
                av_atuais = [x.strip() for x in st_v['av'].replace('|',',').split(',')] if st_v['av'] != "Nenhuma" else []
                checklist = st.multiselect("Avarias Atuais", list(set(p_lista + av_atuais)), default=av_atuais)
                if st.button("🚀 Confirmar Saída"):
                    nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "SAÍDA", "Veículo": v_s, "Usuário": m_s, "KM": km_sai, "Av_Saida": ", ".join(checklist), "Av_Totais": ", ".join(checklist), "Foto_Base64": converter_multiplas_fotos(fotos_s)}])
                    salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA 2: CHEGADA ---
with tabs[2 + idx_tab]:
    st.header("📥 Registrar Chegada")
    veiculos_uso = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["acao"] == "SAÍDA"]
    col_c, _ = st.columns([2, 3])
    with col_c:
        v_ret = st.selectbox("Veículo retorno", [""] + veiculos_uso)
        if v_ret:
            st_ret = get_status_veiculo(v_ret)
            km_f = st.number_input("KM Final", min_value=st_ret['km'], value=st_ret['km'])
            fotos_c = st.file_uploader("Fotos Chegada", accept_multiple_files=True)
            n_av = st.multiselect("Novas Avarias", carregar(ARQ_PECAS)[carregar(ARQ_PECAS)['Status'] == "Ativo"]['Item'].tolist())
            if st.button("🏁 Confirmar Chegada"):
                txt_n = ", ".join(n_av) if n_av else "Nenhuma"
                l_total = [st_ret['av']] if st_ret['av'] != "Nenhuma" else []
                if txt_n != "Nenhuma": l_total.append(txt_n)
                nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "CHEGADA", "Veículo": v_ret, "Usuário": st_ret['user'], "KM": km_f, "Av_Saida": st_ret['av'], "Av_Chegada": txt_n, "Av_Totais": " | ".join(l_total) if l_total else "Nenhuma", "Foto_Base64": converter_multiplas_fotos(fotos_c)}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA 3: MANUTENÇÃO ---
with tabs[3 + idx_tab]:
    st.header("🔧 Oficina")
    veiculos_com_avaria = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["av"] != "Nenhuma"]
    col_m, _ = st.columns([2, 3])
    with col_m:
        v_m = st.selectbox("Veículo para manutenção", [""] + veiculos_com_avaria)
        if v_m:
            st_man = get_status_veiculo(v_m)
            lista_atuais = [x.strip() for x in st_man['av'].replace('|',',').split(',')]
            reparados = st.multiselect("Itens consertados:", lista_atuais)
            local = st.text_input("Oficina / Local")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            if st.button("🛠️ Salvar Manutenção"):
                if reparados and local:
                    restantes = [i for i in lista_atuais if i not in reparados]
                    nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "REPARO", "Veículo": v_m, "Usuário": local, "KM": st_man['km'], "Av_Totais": " | ".join(restantes) if restantes else "Nenhuma", "Valor_Reparo": valor, "Local_Reparo": local, "Obs": f"Conserto de: {', '.join(reparados)}"}])
                    salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA 4: HISTÓRICO ---
with tabs[4 + idx_tab]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        col_h, _ = st.columns([2, 3])
        with col_h: idx = st.selectbox("Visualizar Fotos (ID):", df_h.index)
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            for f in str(fb64).split(";"):
                if f: st.image(base64.b64decode(f), width=500)
