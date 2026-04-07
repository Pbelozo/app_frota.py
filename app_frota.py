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
        pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Valor_Reparo", "Local_Reparo", "Foto_Base64"]).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_MOT):
        pd.DataFrame(columns=["Nome", "Validade_CNH", "Status", "Senha", "Admin"]).to_csv(ARQ_MOT, index=False)
    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Criterio_Revisao", "Valor_Criterio", "Status"]).to_csv(ARQ_VEIC, index=False)
    if not os.path.exists(ARQ_PECAS):
        pecas_p = ["1. Capô", "2. Parabrisa", "3. Párachoque dianteiro", "4. Teto"]
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
            try: km_val = int(float(ult['KM']))
            except: km_val = 0
            return {"acao": ult['Ação'], "user": ult['Usuário'], "km": km_val, "av": str(ult['Av_Totais']) if str(ult['Av_Totais']).strip() != "" else "Nenhuma"}
    return {"acao": "CHEGADA", "user": "Ninguém", "km": 0, "av": "Nenhuma"}

def converter_multiplas_fotos(uploaded_files):
    lista_b64 = []
    if uploaded_files:
        for f in uploaded_files:
            img = Image.open(f); img.thumbnail((800, 800))
            buf = BytesIO(); img.save(buf, format="JPEG", quality=70)
            lista_b64.append(base64.b64encode(buf.getvalue()).decode())
    return ";".join(lista_b64)

# --- CONTROLE DE EDIÇÃO ---
if 'edit_v_idx' not in st.session_state: st.session_state.edit_v_idx = None
if 'edit_u_idx' not in st.session_state: st.session_state.edit_u_idx = None
if 'edit_a_idx' not in st.session_state: st.session_state.edit_a_idx = None

# --- LOGIN ---
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
        col_l, _ = st.columns([2, 3])
        with col_l:
            nome_m = st.selectbox("Selecione seu Usuário", [""] + df_m_log[df_m_log['Status'] == "Ativo"]['Nome'].tolist())
            if nome_m:
                dados_m = df_m_log[df_m_log['Nome'] == nome_m].iloc[0]
                if str(dados_m['Senha']).strip() == "":
                    nova_s = st.text_input("Cadastre sua Senha", type="password")
                    if st.button("Salvar"):
                        idx = df_m_log[df_m_log['Nome'] == nome_m].index[0]
                        df_m_log.at[idx, 'Senha'] = str(nova_s); salvar(df_m_log, ARQ_MOT); st.rerun()
                else:
                    senha_i = st.text_input("Senha", type="password")
                    if st.button("Entrar"):
                        if str(senha_i) == str(dados_m['Senha']):
                            st.session_state.autenticado = True
                            st.session_state.perfil = "admin" if dados_m['Admin'] == "Sim" else "motorista"
                            st.session_state.user_logado = nome_m; st.rerun()
                        else: st.error("Senha Incorreta")
    st.stop()

# --- INTERFACE ---
st.title("Gestão de Frota")
if st.sidebar.button("Sair"): st.session_state.autenticado = False; st.rerun()

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
            idx_v = st.session_state.edit_v_idx
            with st.form("f_veic"):
                v_mod = st.text_input("Modelo", value=str(df_v.iloc[idx_v]['Veículo']) if idx_v is not None else "")
                v_pla = st.text_input("Placa", value=str(df_v.iloc[idx_v]['Placa']) if idx_v is not None else "").upper().strip()
                v_km_r = st.number_input("KM Últ. Revisão", min_value=0, value=int(df_v.iloc[idx_v]['Ult_Revisao_KM']) if idx_v is not None else 0)
                try: v_dt_val = datetime.strptime(str(df_v.iloc[idx_v]['Ult_Revisao_Data']), '%Y-%m-%d').date() if idx_v is not None else date.today()
                except: v_dt_val = date.today()
                v_dt_r = st.date_input("Data Últ. Revisão", value=v_dt_val)
                v_crit = st.selectbox("Critério de Próxima Revisão", ["Quilometragem", "Data (Prazo)"], index=0 if idx_v is None or str(df_v.iloc[idx_v]['Criterio_Revisao']) == "Quilometragem" else 1)
                v_val_crit = st.text_input("Valor do Critério (KM ou Data DD/MM/AAAA)", value=str(df_v.iloc[idx_v]['Valor_Criterio']) if idx_v is not None else "")
                
                if st.form_submit_button("Salvar Veículo"):
                    if not v_mod or not v_pla or not v_val_crit:
                        st.error("Campos pendentes: Modelo, Placa e Valor do Critério são obrigatórios.")
                    elif idx_v is None and v_pla in df_v['Placa'].values:
                        st.error(f"Veículo com placa {v_pla} já existe!")
                    else:
                        nova_v = {"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": v_km_r, "Ult_Revisao_Data": str(v_dt_r), "Criterio_Revisao": v_crit, "Valor_Criterio": v_val_crit, "Status": "Ativo"}
                        if idx_v is not None: df_v.iloc[idx_v] = nova_v
                        else: df_v = pd.concat([df_v, pd.DataFrame([nova_v])], ignore_index=True)
                        salvar(df_v, ARQ_VEIC); st.session_state.edit_v_idx = None; st.rerun()

            for i, r in df_v.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Veículo']}** ({r['Placa']})")
                    b1, b2, b3 = st.columns(3)
                    if b1.button("📝", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()
                    if b2.button("🚫", key=f"bv{i}"): df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"; salvar(df_v, ARQ_VEIC); st.rerun()
                    if b3.button("🗑️", key=f"dv{i}"): salvar(df_v.drop(i), ARQ_VEIC); st.rerun()

        with c2:
            st.subheader("👤 Usuários")
            df_u = carregar(ARQ_MOT)
            idx_u = st.session_state.edit_u_idx
            with st.form("f_user"):
                u_nome = st.text_input("Nome Completo", value=str(df_u.iloc[idx_u]['Nome']) if idx_u is not None else "")
                try: u_cnh_val = datetime.strptime(str(df_u.iloc[idx_u]['Validade_CNH']), '%Y-%m-%d').date() if idx_u is not None else date.today()
                except: u_cnh_val = date.today()
                u_cnh = st.date_input("Validade CNH", value=u_cnh_val)
                u_adm = st.selectbox("Admin?", ["Não", "Sim"], index=0 if idx_u is None or str(df_u.iloc[idx_u]['Admin']) == "Não" else 1)
                
                if st.form_submit_button("Salvar Usuário"):
                    if not u_nome or not u_cnh:
                        st.error("Campos pendentes: Nome e Validade da CNH são obrigatórios.")
                    elif idx_u is None and u_nome in df_u['Nome'].values:
                        st.error("Este nome já está cadastrado!")
                    else:
                        if idx_u is not None:
                            df_u.at[idx_u, 'Nome'] = u_nome
                            df_u.at[idx_u, 'Validade_CNH'] = str(u_cnh)
                            df_u.at[idx_u, 'Admin'] = u_adm
                        else:
                            df_u = pd.concat([df_u, pd.DataFrame([{"Nome": u_nome, "Validade_CNH": str(u_cnh), "Status": "Ativo", "Senha": "", "Admin": u_adm}])], ignore_index=True)
                        salvar(df_u, ARQ_MOT); st.session_state.edit_u_idx = None; st.rerun()

            for i, r in df_u.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Nome']}** (CNH: {r['Validade_CNH']})")
                    b1, b2, b3 = st.columns(3)
                    if b1.button("📝", key=f"eu{i}"): st.session_state.edit_u_idx = i; st.rerun()
                    if b2.button("🔑", key=f"ru{i}"): df_u.at[i, 'Senha'] = ""; salvar(df_u, ARQ_MOT); st.rerun()
                    if b3.button("🗑️", key=f"du{i}"): salvar(df_u.drop(i), ARQ_MOT); st.rerun()

        with c3:
            st.subheader("📋 Avarias")
            df_a = carregar(ARQ_PECAS)
            idx_a = st.session_state.edit_a_idx
            with st.form("f_av"):
                val_av = str(df_a.iloc[idx_a]['Item']) if idx_a is not None else ""
                n_av = st.text_input("Descrição da Avaria", value=val_av)
                if st.form_submit_button("Salvar Avaria"):
                    if not n_av: st.error("A descrição não pode estar vazia.")
                    else:
                        if idx_a is not None: df_a.at[idx_a, 'Item'] = n_av
                        else: df_a = pd.concat([df_a, pd.DataFrame([{"Item": n_av, "Status": "Ativo"}])], ignore_index=True)
                        salvar(df_a, ARQ_PECAS); st.session_state.edit_a_idx = None; st.rerun()
            for i, r in df_a.iterrows():
                with st.container(border=True):
                    st.write(r['Item'])
                    if st.button("🗑️", key=f"da{i}"): salvar(df_a.drop(i), ARQ_PECAS); st.rerun()

# --- ABA SAÍDA ---
with tabs[1 + idx_tab]:
    st.header("📤 Registrar Saída")
    df_v_ativos = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    df_m_ativos = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Status'] == "Ativo"]
    
    col_sel1, _ = st.columns([2, 3])
    with col_sel1:
        v_s = st.selectbox("Selecione o Veículo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_ativos.iterrows()])
        m_s = st.session_state.user_logado if st.session_state.perfil == "motorista" else st.selectbox("Motorista", [""] + df_m_ativos['Nome'].tolist())
    
    if v_s and m_s:
        st_v = get_status_veiculo(v_s)
        u_info = df_m_ativos[df_m_ativos['Nome'] == m_s].iloc[0]
        dt_cnh = datetime.strptime(str(u_info['Validade_CNH']), '%Y-%m-%d').date()
        v_info = df_v_ativos[df_v_ativos['Placa'] == v_s.split('(')[1].replace(')','')].iloc[0]
        
        # Lógica de Alerta de Revisão
        revisao_vencida = False
        if v_info['Criterio_Revisao'] == "Quilometragem":
            if st_v['km'] >= int(v_info['Valor_Criterio']): revisao_vencida = True
        else:
            try:
                dt_rev = datetime.strptime(str(v_info['Valor_Criterio']), '%d/%m/%Y').date()
                if date.today() >= dt_rev: revisao_vencida = True
            except: pass
        
        if revisao_vencida: st.warning("⚠️ ALERTA: Este veículo está com a REVISÃO VENCIDA. O uso é permitido, mas realize a manutenção em breve.")
        
        if dt_cnh < date.today():
            st.error(f"🚫 BLOQUEADO: CNH de {m_s} vencida em {dt_cnh.strftime('%d/%m/%Y')}.")
        elif st_v["acao"] == "SAÍDA":
            st.error(f"Veículo já em uso por {st_v['user']}.")
        else:
            km_sai = st.number_input("KM Inicial", min_value=st_v['km'], value=st_v['km'])
            fotos_s = st.file_uploader("Fotos", accept_multiple_files=True)
            p_lista = carregar(ARQ_PECAS)[carregar(ARQ_PECAS)['Status'] == "Ativo"]['Item'].tolist()
            av_atuais = [x.strip() for x in st_v['av'].replace('|',',').split(',')] if st_v['av'] != "Nenhuma" else []
            checklist = st.multiselect("Confirme as Avarias:", list(set(p_lista + av_atuais)), default=av_atuais)
            
            if st.button("Confirmar Saída"):
                nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "SAÍDA", "Veículo": v_s, "Usuário": m_s, "KM": km_sai, "CNH": str(dt_cnh), "Av_Saida": ", ".join(checklist), "Av_Totais": ", ".join(checklist), "Foto_Base64": converter_multiplas_fotos(fotos_s)}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA CHEGADA ---
with tabs[2 + idx_tab]:
    st.header("📥 Registrar Chegada")
    veiculos_uso = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["acao"] == "SAÍDA"]
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
    veiculos_man = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["av"] != "Nenhuma"]
    v_m = st.selectbox("Veículo oficina", [""] + veiculos_man)
    if v_m:
        st_man = get_status_veiculo(v_m)
        lista_atuais = [x.strip() for x in st_man['av'].replace('|',',').split(',')]
        reparados = st.multiselect("Itens consertados:", lista_atuais)
        local = st.text_input("Oficina / Local")
        valor = st.number_input("Valor (R$)", min_value=0.0)
        if st.button("Salvar Manutenção"):
            if not reparados or not local: st.error("Selecione os itens e informe o local.")
            else:
                restantes = [i for i in lista_atuais if i not in reparados]
                nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "REPARO", "Veículo": v_m, "Usuário": local, "KM": st_man['man_km'] if 'man_km' in st_man else st_man['km'], "Av_Totais": " | ".join(restantes) if restantes else "Nenhuma", "Valor_Reparo": valor, "Local_Reparo": local, "Obs": f"Conserto: {', '.join(reparados)}"}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA HISTÓRICO ---
with tabs[4 + idx_tab]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        idx = st.selectbox("Ver fotos ID:", df_h.index)
        if st.session_state.perfil == "admin" and st.button("🗑️ EXCLUIR REGISTRO"):
            salvar(df_h.drop(idx), ARQ_HIST); st.rerun()
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            for f in str(fb64).split(";"):
                if f: st.image(base64.b64decode(f), width=450)
