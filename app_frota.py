import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import base64
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="Frota Empresa", page_icon="🚗", layout="wide")
st.title("🚗 Gestão de Frota - Oficial V40")

# --- ARQUIVOS ---
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"
ARQ_PECAS = "cadastro_pecas.csv"

def inicializar():
    padr_h = ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Foto_Base64"]
    if not os.path.exists(ARQ_HIST): pd.DataFrame(columns=padr_h).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_MOT): pd.DataFrame(columns=["Nome", "Validade_CNH", "Status"]).to_csv(ARQ_MOT, index=False)
    if not os.path.exists(ARQ_VEIC): pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Intervalo_KM", "Status"]).to_csv(ARQ_VEIC, index=False)
    if not os.path.exists(ARQ_PECAS):
        pd.DataFrame({"Item": ["1. Capô", "2. Pneus", "3. Vidros", "4. Portas", "5. Motor"]}).to_csv(ARQ_PECAS, index=False)

inicializar()

# --- FUNÇÕES DE IMAGEM ---
def converter_foto(uploaded_file):
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        img.thumbnail((800, 800)) # Reduz para não sobrecarregar o CSV
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=70)
        return base64.b64encode(buffered.getvalue()).decode()
    return ""

def exibir_foto(b64_string):
    if b64_string:
        st.image(base64.b64decode(b64_string), use_container_width=True)

# --- FUNÇÕES CORE ---
def carregar(arq): return pd.read_csv(arq).fillna("")
def salvar(df, arq): df.to_csv(arq, index=False)

def get_status_veiculo(v_alvo):
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        df_v = df_h[df_h['Veículo'] == v_alvo]
        if not df_v.empty:
            ult = df_v.iloc[-1]
            return {"acao": ult['Ação'], "user": ult['Usuário'], "km": int(ult['KM']), "av": str(ult['Av_Totais'])}
    df_c = carregar(ARQ_VEIC)
    v_info = df_c[df_c['Veículo'] + " (" + df_c['Placa'] + ")" == v_alvo]
    km_ini = int(v_info.iloc[0]['Ult_Revisao_KM']) if not v_info.empty else 0
    return {"acao": "CHEGADA", "user": "Ninguém", "km": km_ini, "av": "Nenhuma"}

tabs = st.tabs(["⚙️ Gestão & Cadastro", "📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"])

# --- ABA 1: GESTÃO (VEÍCULOS, MOTORISTAS, AVARIAS) ---
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("🚗 Veículos")
        df_v = carregar(ARQ_VEIC)
        with st.form("f_v"):
            v_mod = st.text_input("Modelo")
            v_pla = st.text_input("Placa").upper()
            v_dt = st.date_input("Data Últ. Revisão", value=None)
            if st.form_submit_button("Salvar"):
                if v_mod and v_pla and v_dt:
                    n = pd.DataFrame([{"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": 0, "Ult_Revisao_Data": v_dt, "Intervalo_KM": 10000, "Status": "Ativo"}])
                    salvar(pd.concat([df_v, n]), ARQ_VEIC); st.rerun()
    with c2:
        st.subheader("👤 Motoristas")
        df_m = carregar(ARQ_MOT)
        with st.form("f_m"):
            m_nome = st.text_input("Nome")
            m_cnh = st.date_input("Validade CNH", value=None)
            if st.form_submit_button("Salvar"):
                if m_nome and m_cnh:
                    n = pd.DataFrame([{"Nome": m_nome, "Validade_CNH": m_cnh, "Status": "Ativo"}])
                    salvar(pd.concat([df_m, n]), ARQ_MOT); st.rerun()
    with c3:
        st.subheader("📋 Checklist")
        df_p = carregar(ARQ_PECAS)
        n_peca = st.text_input("Novo Item")
        if st.button("Adicionar Item"):
            salvar(pd.concat([df_p, pd.DataFrame([{"Item": n_peca}])]), ARQ_PECAS); st.rerun()
        st.dataframe(df_p, use_container_width=True)

# --- ABA 2: SAÍDA (COM FOTO) ---
with tabs[1]:
    st.header("📤 Registrar Saída")
    df_v_at = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    df_m_at = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Status'] == "Ativo"]
    
    v_sel = st.selectbox("Veículo", ["Selecione..."] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_at.iterrows()])
    m_sel = st.selectbox("Motorista", ["Selecione..."] + df_m_at['Nome'].tolist())

    if v_sel != "Selecione..." and m_sel != "Selecione...":
        st_v = get_status_veiculo(v_sel)
        info_m = df_m_at[df_m_at['Nome'] == m_sel].iloc[0]
        if datetime.strptime(str(info_m['Validade_CNH']), '%Y-%m-%d').date() < date.today():
            st.error("🚫 CNH Vencida!")
        else:
            km_sai = st.number_input("KM Inicial", value=st_v['km'], min_value=st_v['km'])
            foto_s = st.file_uploader("📷 Foto da Saída", type=['jpg', 'jpeg', 'png'])
            if st.button("🚀 Confirmar Saída"):
                b64 = converter_foto(foto_s)
                nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "SAÍDA", "Veículo": v_sel, "Usuário": m_sel, "KM": km_sai, "CNH": info_m['Validade_CNH'], "Av_Saida": st_v['av'], "Av_Chegada": "", "Av_Totais": st_v['av'], "Obs": "Saída", "Foto_Base64": b64}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.success("Saída Ok!"); st.rerun()

# --- ABA 3: CHEGADA (COM FOTO) ---
with tabs[2]:
    st.header("📥 Registrar Chegada")
    v_ret = st.selectbox("Veículo", ["Selecione..."] + [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()], key="cheg")
    if v_ret != "Selecione...":
        st_ret = get_status_veiculo(v_ret)
        if st_ret["acao"] == "SAÍDA":
            km_f = st.number_input("KM Final", min_value=st_ret['km'], value=st_ret['km'])
            foto_c = st.file_uploader("📷 Foto da Chegada", type=['jpg', 'jpeg', 'png'])
            if st.button("🏁 Confirmar Chegada"):
                b64 = converter_foto(foto_c)
                nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "CHEGADA", "Veículo": v_ret, "Usuário": st_ret['user'], "KM": km_f, "CNH": "", "Av_Saida": st_ret['av'], "Av_Chegada": "", "Av_Totais": st_ret['av'], "Obs": "Chegada", "Foto_Base64": b64}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.success("Chegada Ok!"); st.rerun()

# --- ABA 4: MANUTENÇÃO ---
with tabs[3]:
    st.header("🔧 Oficina")
    v_m = st.selectbox("Veículo", ["Selecione..."] + [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()], key="man")
    if v_m != "Selecione...":
        st_man = get_status_veiculo(v_m)
        if st.button("🛠️ Limpar Avarias"):
            nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "REPARO", "Veículo": v_m, "Usuário": "Oficina", "KM": st_man['km'], "CNH": "", "Av_Saida": "", "Av_Chegada": "", "Av_Totais": "Nenhuma", "Obs": "Reparo", "Foto_Base64": ""}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.success("Reparado!"); st.rerun()

# --- ABA 5: HISTÓRICO COM VISUALIZADOR E EXCLUSÃO DE FOTO ---
with tabs[4]:
    st.header("📋 Histórico e Galeria")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        # Exibe a tabela sem a coluna gigante de texto da foto para não poluir
        st.write("Selecione uma linha para ver a foto:")
        sel_row = st.selectbox("Escolha o registro pelo ID (Linha)", df_h.index)
        
        col_tab, col_foto = st.columns([2, 1])
        
        with col_tab:
            st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        
        with col_foto:
            registro = df_h.iloc[sel_row]
            if registro["Foto_Base64"]:
                st.subheader("🖼️ Foto do Registro")
                exibir_foto(registro["Foto_Base64"])
                if st.button("🗑️ Excluir esta Imagem"):
                    df_h.at[sel_row, "Foto_Base64"] = ""
                    salvar(df_h, ARQ_HIST)
                    st.success("Imagem removida!"); st.rerun()
            else:
                st.info("Nenhuma imagem anexada a este registro.")
