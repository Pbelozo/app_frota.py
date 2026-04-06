import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os

st.set_page_config(page_title="Frota Empresa", page_icon="🚗", layout="wide")
st.title("🚗 Gestão de Frota - V31")

# --- ARQUIVOS ---
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"

# --- INICIALIZAÇÃO E CORREÇÃO DE COLUNAS ---
def inicializar_arquivos():
    config = [
        (ARQ_HIST, ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Foto"]),
        (ARQ_VEIC, ["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Intervalo_KM", "Status"]),
        (ARQ_MOT,  ["Nome", "Validade_CNH", "Status"])
    ]
    for arq, cols in config:
        if not os.path.exists(arq):
            pd.DataFrame(columns=cols).to_csv(arq, index=False)
        else:
            # CORREÇÃO: Se o arquivo existe mas não tem a coluna Status, adiciona agora
            df = pd.read_csv(arq)
            if "Status" not in df.columns and arq != ARQ_HIST:
                df["Status"] = "Ativo"
                df.to_csv(arq, index=False)

inicializar_arquivos()

def carregar(arq):
    return pd.read_csv(arq).fillna("")

def salvar(df, arq):
    df.to_csv(arq, index=False)

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

# --- ABA 1: GESTÃO & CADASTRO ---
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🚗 Gestão de Veículos")
        with st.expander("➕ Novo Veículo"):
            with st.form("add_v"):
                nv_mod = st.text_input("Modelo")
                nv_pla = st.text_input("Placa")
                nv_km = st.number_input("Última Revisão (KM)", min_value=0)
                nv_dt = st.date_input("Data Última Revisão")
                if st.form_submit_button("Salvar Veículo"):
                    df_v = carregar(ARQ_VEIC)
                    novo = pd.DataFrame([{"Veículo": nv_mod, "Placa": nv_pla, "Ult_Revisao_KM": nv_km, "Ult_Revisao_Data": nv_dt, "Intervalo_KM": 10000, "Status": "Ativo"}])
                    salvar(pd.concat([df_v, novo]), ARQ_VEIC)
                    st.rerun()

        df_v = carregar(ARQ_VEIC)
        df_h = carregar(ARQ_HIST)
        for i, r in df_v.iterrows():
            nome_full = f"{r['Veículo']} ({r['Placa']})"
            tem_hist = nome_full in df_h['Veículo'].values
            
            with st.container(border=True):
                col_a, col_b, col_c = st.columns([3, 1, 1])
                st_cor = "green" if r['Status'] == "Ativo" else "red"
                col_a.markdown(f"**{nome_full}** \nStatus: :{st_cor}[{r['Status']}]")
                
                if col_b.button("Bloquear" if r['Status'] == "Ativo" else "Ativar", key=f"v_st_{i}"):
                    df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_v, ARQ_VEIC)
                    st.rerun()
                
                if not tem_hist:
                    if col_c.button("🗑️", key=f"v_del_{i}"):
                        salvar(df_v.drop(i), ARQ_VEIC)
                        st.rerun()

    with c2:
        st.subheader("👤 Gestão de Motoristas")
        with st.expander("➕ Novo Motorista"):
            with st.form("add_m"):
                nm_nome = st.text_input("Nome")
                nm_cnh = st.date_input("Validade CNH")
                if st.form_submit_button("Salvar Motorista"):
                    df_m = carregar(ARQ_MOT)
                    novo = pd.DataFrame([{"Nome": nm_nome, "Validade_CNH": nm_cnh, "Status": "Ativo"}])
                    salvar(pd.concat([df_m, novo]), ARQ_MOT)
                    st.rerun()

        df_m = carregar(ARQ_MOT)
        for i, r in df_m.iterrows():
            tem_hist = r['Nome'] in df_h['Usuário'].values
            with st.container(border=True):
                col_a, col_b, col_c = st.columns([3, 1, 1])
                st_cor = "green" if r['Status'] == "Ativo" else "red"
                col_a.markdown(f"**{r['Nome']}** \nCNH: {r['Validade_CNH']} | Status: :{st_cor}[{r['Status']}]")
                
                if col_b.button("Bloquear" if r['Status'] == "Ativo" else "Ativar", key=f"m_st_{i}"):
                    df_m.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_m, ARQ_MOT)
                    st.rerun()
                    
                if not tem_hist:
                    if col_c.button("🗑️", key=f"m_del_{i}"):
                        salvar(df_m.drop(i), ARQ_MOT)
                        st.rerun()

# --- ABA 2: SAÍDA ---
with tabs[1]:
    st.header("Registar Saída")
    df_v = carregar(ARQ_VEIC)
    df_m = carregar(ARQ_MOT)
    v_ativos = df_v[df_v['Status'] == "Ativo"]
    m_ativos = df_m[df_m['Status'] == "Ativo"]
    
    if v_ativos.empty or m_ativos.empty:
        st.warning("Cadastre e ative veículos/motoristas na primeira aba.")
    else:
        op_v = [f"{r['Veículo']} ({r['Placa']})" for _, r in v_ativos.iterrows()]
        v_sel = st.selectbox("Veículo", op_v)
        st_s = get_status_veiculo(v_sel)
        m_sel = st.selectbox("Motorista", m_ativos['Nome'].tolist())
        
        m_info = m_ativos[m_ativos['Nome'] == m_sel].iloc[0]
        dt_cnh = datetime.strptime(str(m_info['Validade_CNH']), '%Y-%m-%d').date()
        
        if dt_cnh < date.today():
            st.error(f"Bloqueado: CNH de {m_sel} vencida.")
        elif st_s["acao"] == "SAÍDA":
            st.error(f"Bloqueado: Veículo com {st_s['user']}")
        else:
            st.success(f"KM Atual: {st_s['km']}")
            km_s = st.number_input("KM Inicial", value=st_s['km'], min_value=st_s['km'])
            pecas = ["Capô", "Pneus", "Parachoque", "Portas", "Vidros"]
            limpo = st_s['av'].replace('|', ',')
            d_av = [x.strip() for x in limpo.split(',')] if st_s['av'] != "Nenhuma" else []
            av_s = st.multiselect("Checklist:", pecas, default=[x for x in d_av if x in pecas])
            
            if st.button("Confirmar Saída"):
                nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "SAÍDA", "Veículo": v_sel, "Usuário": m_sel, "KM": km_s, "CNH": dt_cnh, "Av_Saida": ", ".join(av_s), "Av_Chegada": "Pendente", "Av_Totais": ", ".join(av_s), "Obs": "", "Foto": "Não"}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST)
                st.success("Saída Ok!"); st.rerun()

# --- ABA 3: CHEGADA ---
with tabs[2]:
    st.header("Registar Chegada")
    df_v_all = carregar(ARQ_VEIC)
    v_op = [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_all.iterrows()]
    v_sel_d = st.selectbox("Veículo", v_op, key="vd")
    st_d = get_status_veiculo(v_sel_d)
    if st_d["acao"] != "SAÍDA": st.info("Veículo no pátio.")
    else:
        km_d = st.number_input("KM Final", min_value=st_d['km'], value=st_d['km'])
        if st.button("Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "CHEGADA", "Veículo": v_sel_d, "Usuário": st_d['user'], "KM": km_d, "CNH": "", "Av_Saida": st_d['av'], "Av_Chegada": "Nenhuma", "Av_Totais": st_d['av'], "Obs": "Retorno", "Foto": ""}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST)
            st.success("Chegada Ok!"); st.rerun()

# --- ABA 4: MANUTENÇÃO ---
with tabs[3]:
    st.header("🔧 Reparos")
    v_op_m = [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()]
    v_m = st.selectbox("Veículo", v_op_m, key="vm")
    st_m = get_status_veiculo(v_m)
    if st_m["av"] == "Nenhuma": st.success("Sem avarias.")
    else:
        if st.button("Registrar Reparo Total"):
            nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "REPARO", "Veículo": v_m, "Usuário": "Oficina", "KM": st_m["km"], "CNH": "", "Av_Saida": "Reparo Geral", "Av_Chegada": "", "Av_Totais": "Nenhuma", "Obs": "Manutenção", "Foto": ""}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST)
            st.success("Reparado!"); st.rerun()

# --- ABA 5: HISTÓRICO ---
with tabs[4]:
    st.header("📋 Histórico Geral")
    st.dataframe(carregar(ARQ_HIST), use_container_width=True)
