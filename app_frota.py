import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os

st.set_page_config(page_title="Frota Empresa", page_icon="🚗", layout="wide")
st.title("🚗 Gestão de Frota - Oficial V29")

# --- ARQUIVOS DE BANCO DE DATA ---
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"

# --- INICIALIZAÇÃO DE ARQUIVOS ---
for arq, cols in [
    (ARQ_HIST, ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Foto"]),
    (ARQ_VEIC, ["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Intervalo_KM"]),
    (ARQ_MOT,  ["Nome", "Validade_CNH"])
]:
    if not os.path.exists(arq):
        pd.DataFrame(columns=cols).to_csv(arq, index=False)

# --- FUNÇÕES DE APOIO ---
def carregar_dados(arq):
    return pd.read_csv(arq).fillna("").replace(["None", "nan"], "")

def get_status_veiculo(v_alvo):
    if os.path.exists(ARQ_HIST):
        df = pd.read_csv(ARQ_HIST)
        df_v = df[df['Veículo'] == v_alvo]
        if not df_v.empty:
            ult = df_v.iloc[-1]
            return {"acao": ult['Ação'], "user": ult['Usuário'], "km": int(ult['KM']), "av": str(ult['Av_Totais'])}
    
    # Se não tem histórico, busca KM inicial do cadastro
    df_c = pd.read_csv(ARQ_VEIC)
    carro_c = df_c[df_c['Veículo'] + " (" + df_c['Placa'] + ")" == v_alvo]
    km_ini = int(carro_c.iloc[0]['Ult_Revisao_KM']) if not carro_c.empty else 0
    return {"acao": "CHEGADA", "user": "Ninguém", "km": km_ini, "av": "Nenhuma"}

# --- INTERFACE ---
tabs = st.tabs(["📤 Saída", "📥 Chegada", "🔧 Manutenção", "⚙️ Gestão & Cadastro", "📋 Histórico"])

# --- ABA: GESTÃO & CADASTRO ---
with tabs[3]:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("➕ Cadastrar Veículo")
        with st.form("form_veiculo"):
            v_nome = st.text_input("Modelo (ex: Prisma)")
            v_placa = st.text_input("Placa")
            v_km_rev = st.number_input("KM da Última Revisão", min_value=0, step=1)
            v_dt_rev = st.date_input("Data da Última Revisão")
            v_int_km = st.number_input("Intervalo para Revisão (KM)", value=10000)
            if st.form_submit_button("Salvar Veículo"):
                novo_v = pd.DataFrame([{"Veículo": v_nome, "Placa": v_placa, "Ult_Revisao_KM": v_km_rev, "Ult_Revisao_Data": v_dt_rev, "Intervalo_KM": v_int_km}])
                pd.concat([pd.read_csv(ARQ_VEIC), novo_v], ignore_index=True).to_csv(ARQ_VEIC, index=False)
                st.success("Veículo Cadastrado!")
                st.rerun()

    with col2:
        st.subheader("👤 Cadastrar Motorista")
        with st.form("form_motorista"):
            m_nome = st.text_input("Nome Completo")
            m_cnh = st.date_input("Validade da CNH")
            if st.form_submit_button("Salvar Motorista"):
                novo_m = pd.DataFrame([{"Nome": m_nome, "Validade_CNH": m_cnh}])
                pd.concat([pd.read_csv(ARQ_MOT), novo_m], ignore_index=True).to_csv(ARQ_MOT, index=False)
                st.success("Motorista Cadastrado!")
                st.rerun()

    st.divider()
    st.write("### 📜 Frota Cadastrada")
    st.dataframe(carregar_dados(ARQ_VEIC), use_container_width=True)
    st.write("### 📜 Motoristas Autorizados")
    st.dataframe(carregar_dados(ARQ_MOT), use_container_width=True)

# --- ABA: SAÍDA ---
with tabs[0]:
    st.header("Registar Saída")
    df_v_cad = carregar_dados(ARQ_VEIC)
    df_m_cad = carregar_dados(ARQ_MOT)
    
    if df_v_cad.empty or df_m_cad.empty:
        st.warning("⚠️ Cadastre veículos e motoristas na aba 'Gestão' antes de operar.")
    else:
        opcoes_v = [row['Veículo'] + " (" + row['Placa'] + ")" for _, row in df_v_cad.iterrows()]
        v_sel = st.selectbox("Veículo", opcoes_v, key="sel_v_s")
        st_s = get_status_veiculo(v_sel)
        
        # Alerta Revisão
        v_info = df_v_cad[df_v_cad['Placa'] == v_sel.split("(")[1].replace(")", "")].iloc[0]
        prox_km = int(v_info['Ult_Revisao_KM']) + int(v_info['Intervalo_KM'])
        if st_s["km"] >= (prox_km - 500):
            st.error(f"🚨 REVISÃO NECESSÁRIA! Próxima com: {prox_km} KM (Atual: {st_s['km']})")

        if st_s["acao"] == "SAÍDA":
            st.error(f"🚫 Veículo em uso por {st_s['user']}")
        else:
            m_sel = st.selectbox("Motorista", df_m_cad['Nome'].tolist())
            m_info = df_m_cad[df_m_cad['Nome'] == m_sel].iloc[0]
            val_cnh = datetime.strptime(str(m_info['Validade_CNH']), '%Y-%m-%d').date()
            
            if val_cnh < date.today():
                st.error(f"❌ BLOQUEADO: CNH de {m_sel} vencida em {val_cnh.strftime('%d/%m/%Y')}")
            else:
                st.success(f"✅ Motorista Autorizado (CNH ok). Último KM: {st_s['km']}")
                km_s = st.number_input("KM Inicial", min_value=st_s['km'], value=st_s['km'])
                
                # Herança de avarias
                pecas = ["1. Capô", "2. Parabrisa", "3. Parachoque", "4. Porta", "5. Teto"] # Resumido para exemplo
                limpo = st_s['av'].replace('|', ',')
                d_av = [x.strip() for x in limpo.split(',')] if st_s['av'] != "Nenhuma" else []
                av_s = st.multiselect("Checklist Avarias:", pecas, default=[x for x in d_av if x in pecas])
                
                foto = st.file_uploader("Foto Saída", type=['jpg', 'png'])
                if st.button("Confirmar Saída"):
                    nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "SAÍDA", "Veículo": v_sel, "Usuário": m_sel, "KM": km_s, "CNH": val_cnh, "Av_Saida": ", ".join(av_s), "Av_Chegada": "Pendente", "Av_Totais": ", ".join(av_s), "Obs": "", "Foto": "Sim" if foto else "Não"}])
                    pd.concat([pd.read_csv(ARQ_HIST), nova], ignore_index=True).to_csv(ARQ_HIST, index=False)
                    st.success("Saída Registrada!"); st.rerun()

# --- ABA: CHEGADA ---
with tabs[1]:
    st.header("Registar Chegada")
    opcoes_v = [row['Veículo'] + " (" + row['Placa'] + ")" for _, row in carregar_dados(ARQ_VEIC).iterrows()]
    v_sel_d = st.selectbox("Veículo", opcoes_v, key="sel_v_d")
    st_d = get_status_veiculo(v_sel_d)
    
    if st_d["acao"] != "SAÍDA":
        st.info("ℹ️ Veículo no pátio.")
    else:
        km_d = st.number_input("KM Final", min_value=st_d['km'], value=st_d['km'])
        if st.button("Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "CHEGADA", "Veículo": v_sel_d, "Usuário": st_d['user'], "KM": km_d, "CNH": "", "Av_Saida": st_d['av'], "Av_Chegada": "Nenhuma", "Av_Totais": st_d['av'], "Obs": "Retorno", "Foto": "Não"}])
            pd.concat([pd.read_csv(ARQ_HIST), nova], ignore_index=True).to_csv(ARQ_HIST, index=False)
            st.success("Chegada Registrada!"); st.rerun()

# --- ABA: MANUTENÇÃO ---
with tabs[2]:
    st.header("🔧 Reparos")
    opcoes_v = [row['Veículo'] + " (" + row['Placa'] + ")" for _, row in carregar_dados(ARQ_VEIC).iterrows()]
    v_sel_m = st.selectbox("Veículo", opcoes_v, key="sel_v_m")
    st_m = get_status_veiculo(v_sel_m)
    if st_m["av"] == "Nenhuma": st.success("✅ Sem avarias.")
    else:
        st.warning(f"Avarias: {st_m['av']}")
        if st.button("Registrar Reparo Total"):
            nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "REPARO", "Veículo": v_sel_m, "Usuário": "Manutenção", "KM": st_m["km"], "CNH": "", "Av_Saida": "Conserto Geral", "Av_Chegada": "", "Av_Totais": "Nenhuma", "Obs": "Reparo", "Foto": ""}])
            pd.concat([pd.read_csv(ARQ_HIST), nova], ignore_index=True).to_csv(ARQ_HIST, index=False)
            st.success("Veículo Reparado!"); st.rerun()

# --- ABA: HISTÓRICO ---
with tabs[4]:
    st.header("📋 Histórico Geral")
    st.dataframe(carregar_dados(ARQ_HIST), use_container_width=True)
