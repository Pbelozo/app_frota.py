import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import os
import base64
from io import BytesIO
from PIL import Image

# 1. Títulos e Configuração
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗", layout="wide")

# 2. Caminhos dos Arquivos
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"
ARQ_PECAS = "cadastro_pecas.csv"
ARQ_LOGO = "logo_empresa.txt" # Onde o logo será salvo em texto

# 3. Funções de Sistema
def inicializar():
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Foto_Base64"]).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_MOT):
        pd.DataFrame(columns=["Nome", "Validade_CNH", "Status"]).to_csv(ARQ_MOT, index=False)
    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Intervalo_KM", "Status"]).to_csv(ARQ_VEIC, index=False)
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
    df_c = carregar(ARQ_VEIC)
    v_info = df_c[df_c['Veículo'] + " (" + df_c['Placa'] + ")" == v_alvo]
    km_ini = int(v_info.iloc[0]['Ult_Revisao_KM']) if not v_info.empty else 0
    return {"acao": "CHEGADA", "user": "Ninguém", "km": km_ini, "av": "Nenhuma"}

def converter_multiplas_fotos(uploaded_files):
    lista_b64 = []
    if uploaded_files:
        for file in uploaded_files:
            img = Image.open(file); img.thumbnail((800, 800))
            buf = BytesIO(); img.save(buf, format="JPEG", quality=70)
            lista_b64.append(base64.b64encode(buf.getvalue()).decode())
    return ";".join(lista_b64)

# 4. Cabeçalho com Logo Automático
col_l1, col_l2 = st.columns([1, 4])
if os.path.exists(ARQ_LOGO):
    with open(ARQ_LOGO, "r") as f:
        logo_data = f.read()
    col_l1.image(base64.b64decode(logo_data), width=200)
col_l2.title("Gestão de Frota")

# 5. Gerenciamento de Interface
if 'edit_v_idx' not in st.session_state: st.session_state.edit_v_idx = -1
if 'edit_m_idx' not in st.session_state: st.session_state.edit_m_idx = -1
if 'edit_p_idx' not in st.session_state: st.session_state.edit_p_idx = -1

tabs = st.tabs(["⚙️ Gestão & Cadastro", "📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"])

# --- ABA 1: GESTÃO ---
with tabs[0]:
    # Seção para carregar o Logo
    with st.expander("🖼️ Configurar Logotipo da Empresa"):
        logo_up = st.file_uploader("Upload do Logo (PNG ou JPG)", type=['png', 'jpg', 'jpeg'])
        if st.button("Salvar Logotipo"):
            if logo_up:
                img = Image.open(logo_up); img.thumbnail((400, 400))
                buf = BytesIO(); img.save(buf, format="PNG")
                b64_logo = base64.b64encode(buf.getvalue()).decode()
                with open(ARQ_LOGO, "w") as f: f.write(b64_logo)
                st.success("Logo salvo! Atualize a página."); st.rerun()

    c1, c2, c3 = st.columns(3)
    df_h = carregar(ARQ_HIST)
    
    with c1:
        st.subheader("🚗 Veículos")
        df_v = carregar(ARQ_VEIC)
        with st.expander("➕ Novo/Editar", expanded=(st.session_state.edit_v_idx != -1)):
            v_idx = st.session_state.edit_v_idx
            with st.form("f_v"):
                v_m = df_v.iloc[v_idx]['Veículo'] if v_idx != -1 else ""
                v_p = df_v.iloc[v_idx]['Placa'] if v_idx != -1 else ""
                v_k = int(df_v.iloc[v_idx]['Ult_Revisao_KM']) if v_idx != -1 else 0
                v_d_val = datetime.strptime(str(df_v.iloc[v_idx]['Ult_Revisao_Data']), '%Y-%m-%d').date() if v_idx != -1 else None
                v_mod = st.text_input("Modelo", value=v_m)
                v_pla = st.text_input("Placa", value=v_p).upper().strip()
                v_km_r = st.number_input("KM Última Revisão", value=v_k)
                v_dt_r = st.date_input("Data Última Revisão", value=v_d_val, format="DD/MM/YYYY")
                if st.form_submit_button("Salvar"):
                    if v_mod and v_pla and v_dt_r:
                        nova = {"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": v_km_r, "Ult_Revisao_Data": v_dt_r, "Intervalo_KM": 10000, "Status": "Ativo"}
                        if v_idx == -1: df_v = pd.concat([df_v, pd.DataFrame([nova])], ignore_index=True)
                        else: [df_v.at[v_idx, k] for k, v in nova.items() if (df_v.at[v_idx, k] := v) or True]
                        salvar(df_v, ARQ_VEIC); st.session_state.edit_v_idx = -1; st.rerun()
        for i, r in df_v.iterrows():
            with st.container(border=True):
                st.write(f"**{r['Veículo']} ({r['Placa']})**")
                col_b1, col_b2 = st.columns(2)
                if col_b1.button("📝 Editar", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()
                if col_b2.button("🚫 Bloquear", key=f"bv{i}"):
                    df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_v, ARQ_VEIC); st.rerun()

    with c2:
        st.subheader("👤 Motoristas")
        df_m = carregar(ARQ_MOT)
        with st.expander("➕ Novo/Editar", expanded=(st.session_state.edit_m_idx != -1)):
            m_idx = st.session_state.edit_m_idx
            with st.form("f_m"):
                m_n = df_m.iloc[m_idx]['Nome'] if m_idx != -1 else ""
                m_v_val = datetime.strptime(str(df_m.iloc[m_idx]['Validade_CNH']), '%Y-%m-%d').date() if m_idx != -1 else None
                m_nome = st.text_input("Nome", value=m_n)
                m_cnh = st.date_input("Validade CNH", value=m_v_val, format="DD/MM/YYYY")
                if st.form_submit_button("Salvar"):
                    if m_nome and m_cnh:
                        nova = {"Nome": m_nome, "Validade_CNH": m_cnh, "Status": "Ativo"}
                        if m_idx == -1: df_m = pd.concat([df_m, pd.DataFrame([nova])], ignore_index=True)
                        else: [df_m.at[m_idx, k] for k, v in nova.items() if (df_m.at[m_idx, k] := v) or True]
                        salvar(df_m, ARQ_MOT); st.session_state.edit_m_idx = -1; st.rerun()
        for i, r in df_m.iterrows():
            with st.container(border=True):
                st.write(f"**{r['Nome']}**")
                col_m1, col_m2 = st.columns(2)
                if col_m1.button("📝 Editar", key=f"em{i}"): st.session_state.edit_m_idx = i; st.rerun()
                if col_m2.button("🚫 Bloquear", key=f"bm{i}"):
                    df_m.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_m, ARQ_MOT); st.rerun()

    with c3:
        st.subheader("📋 Checklist")
        df_p = carregar(ARQ_PECAS)
        with st.expander("➕ Novo/Editar Item", expanded=(st.session_state.edit_p_idx != -1)):
            p_idx = st.session_state.edit_p_idx
            with st.form("f_p"):
                p_v = df_p.iloc[p_idx]['Item'] if p_idx != -1 else ""
                n_p_desc = st.text_input("Descrição", value=p_v)
                if st.form_submit_button("Salvar Item"):
                    if n_p_desc:
                        if p_idx == -1: df_p = pd.concat([df_p, pd.DataFrame([{"Item": n_p_desc, "Status": "Ativo"}])], ignore_index=True)
                        else: df_p.at[p_idx, "Item"] = n_p_desc
                        salvar(df_p, ARQ_PECAS); st.session_state.edit_p_idx = -1; st.rerun()
        for i, r in df_p.iterrows():
            with st.container(border=True):
                st.write(f"**{r['Item']}**")
                cp1, cp2 = st.columns(2)
                if cp1.button("📝", key=f"ep{i}"): st.session_state.edit_p_idx = i; st.rerun()
                if cp2.button("🚫", key=f"bp{i}"):
                    df_p.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_p, ARQ_PECAS); st.rerun()

# --- ABA 2: SAÍDA ---
with tabs[1]:
    st.header("📤 Registrar Saída")
    df_v_at = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    df_m_at = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Status'] == "Ativo"]
    p_lista = carregar(ARQ_PECAS)[carregar(ARQ_PECAS)['Status'] == "Ativo"]['Item'].tolist()
    v_s = st.selectbox("Veículo", ["Selecione..."] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_at.iterrows()])
    m_s = st.selectbox("Motorista", ["Selecione..."] + df_m_at['Nome'].tolist())
    if v_s != "Selecione..." and m_s != "Selecione...":
        st_v = get_status_veiculo(v_s)
        if st_v["acao"] == "SAÍDA": st.error(f"Bloqueado: Com {st_v['user']}")
        else:
            km_sai = st.number_input("KM Inicial", value=st_v['km'], min_value=st_v['km'])
            fotos_s = st.file_uploader("Fotos", accept_multiple_files=True)
            av_bruto = st_v['av'].replace(' | ', ',').replace('|', ',')
            d_av = [x.strip() for x in av_bruto.split(',')] if st_v['av'] != "Nenhuma" else []
            checklist = st.multiselect("Avarias Atuais", list(set(p_lista + d_av)), default=d_av)
            if st.button("🚀 Confirmar"):
                nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "SAÍDA", "Veículo": v_s, "Usuário": m_s, "KM": km_sai, "Av_Saida": ", ".join(checklist), "Av_Chegada": "Pendente", "Av_Totais": ", ".join(checklist), "Foto_Base64": converter_multiplas_fotos(fotos_s)}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA 3: CHEGADA ---
with tabs[2]:
    st.header("📥 Registrar Chegada")
    veiculos_uso = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["acao"] == "SAÍDA"]
    v_ret = st.selectbox("Veículo", ["Selecione..."] + veiculos_uso)
    if v_ret != "Selecione...":
        st_ret = get_status_veiculo(v_ret)
        km_f = st.number_input("KM Final", min_value=st_ret['km'], value=st_ret['km'])
        fotos_c = st.file_uploader("Fotos Chegada", accept_multiple_files=True)
        if st.button("🏁 Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "CHEGADA", "Veículo": v_ret, "Usuário": st_ret['user'], "KM": km_f, "Av_Saida": st_ret['av'], "Av_Totais": st_ret['av'], "Foto_Base64": converter_multiplas_fotos(fotos_c)}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA 4: MANUTENÇÃO ---
with tabs[3]:
    st.header("🔧 Reparos")
    v_m = st.selectbox("Veículo oficina", ["Selecione..."] + [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()])
    if v_m != "Selecione...":
        st_man = get_status_veiculo(v_m)
        av_limpo = st_man['av'].replace(' | ', ',').replace('|', ',')
        lista_atuais = [x.strip() for x in av_limpo.split(',')] if st_man['av'] != "Nenhuma" else []
        reparados = st.multiselect("Consertados:", lista_atuais)
        if st.button("🛠️ Salvar Reparo"):
            restantes = [i for i in lista_atuais if i not in reparados]
            nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "REPARO", "Veículo": v_m, "Usuário": "Oficina", "KM": st_man['km'], "Av_Totais": " | ".join(restantes) if restantes else "Nenhuma"}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- ABA 5: HISTÓRICO ---
with tabs[4]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        idx = st.selectbox("ID:", df_h.index)
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            for f in str(fb64).split(";"):
                if f: st.image(base64.b64decode(f), width=400)
