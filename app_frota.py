import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os

st.set_page_config(page_title="Frota Empresa", page_icon="🚗", layout="wide")
st.title("🚗 Gestão de Frota - V30")

# --- ARQUIVOS ---
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"

# --- INICIALIZAÇÃO COM NOVA COLUNA 'STATUS' ---
for arq, cols in [
    (ARQ_HIST, ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Foto"]),
    (ARQ_VEIC, ["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Intervalo_KM", "Status"]),
    (ARQ_MOT,  ["Nome", "Validade_CNH", "Status"])
]:
    if not os.path.exists(arq):
        pd.DataFrame(columns=cols).to_csv(arq, index=False)

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
    # Procura no cadastro o KM inicial caso não haja histórico
    v_info = df_c[df_c['Veículo'] + " (" + df_c['Placa'] + ")" == v_alvo]
    km_ini = int(v_info.iloc[0]['Ult_Revisao_KM']) if not v_info.empty else 0
    return {"acao": "CHEGADA", "user": "Ninguém", "km": km_ini, "av": "Nenhuma"}

# --- ORDEM DAS ABAS ATUALIZADA ---
tabs = st.tabs(["⚙️ Gestão & Cadastro", "📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"])

# --- ABA 1: GESTÃO & CADASTRO ---
with tabs[0]:
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🚗 Gestão de Veículos")
        with st.expander("Novo Veículo"):
            with st.form("add_v"):
                nv_mod = st.text_input("Modelo")
                nv_pla = st.text_input("Placa")
                nv_km = st.number_input("Última Revisão (KM)", min_value=0)
                nv_dt = st.date_input("Data Última Revisão")
                if st.form_submit_button("Cadastrar"):
                    df_v = carregar(ARQ_VEIC)
                    novo = pd.DataFrame([{"Veículo": nv_mod, "Placa": nv_pla, "Ult_Revisao_KM": nv_km, "Ult_Revisao_Data": nv_dt, "Intervalo_KM": 10000, "Status": "Ativo"}])
                    salvar(pd.concat([df_v, novo]), ARQ_VEIC)
                    st.rerun()

        df_v = carregar(ARQ_VEIC)
        df_h = carregar(ARQ_HIST)
        for i, r in df_v.iterrows():
            nome_full = f"{r['Veículo']} ({r['Placa']})"
            tem_hist = nome_full in df_h['Veículo'].values
            
            col_a, col_b, col_c = st.columns([3, 1, 1])
            col_a.write(f"**{nome_full}** - Status: {r['Status']}")
            
            if col_b.button("Inativar" if r['Status'] == "Ativo" else "Ativar", key=f"btn_v_{i}"):
                df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                salvar(df_v, ARQ_VEIC)
                st.rerun()
            
            if not tem_hist:
                if col_c.button("🗑️", key=f"del_v_{i}"):
                    salvar(df_v.drop(i), ARQ_VEIC)
                    st.rerun()

    with c2:
        st.subheader("👤 Gestão de Motoristas")
        with st.expander("Novo Motorista"):
            with st.form("add_m"):
                nm_nome = st.text_input("Nome")
                nm_cnh = st.date_input("Validade CNH")
                if st.form_submit_button("Cadastrar"):
                    df_m = carregar(ARQ_MOT)
                    novo = pd.DataFrame([{"Nome": nm_nome, "Validade_CNH": nm_cnh, "Status": "Ativo"}])
                    salvar(pd.concat([df_m, novo]), ARQ_MOT)
                    st.rerun()

        df_m = carregar(ARQ_MOT)
        for i, r in df_m.iterrows():
            tem_hist = r['Nome'] in df_h['Usuário'].values
            col_a, col_b, col_c = st.columns([3, 1, 1])
            col_a.write(f"**{r['Nome']}** - CNH: {r['Validade_CNH']}")
            
            if col_b.button("Inativar" if r['Status'] == "Ativo" else "Ativar", key=f"btn_m_{i}"):
                df_m.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                salvar(df_m, ARQ_MOT)
                st.rerun()
                
            if not tem_hist:
                if col_c.button("🗑️", key=f"del_m_{i}"):
                    salvar(df_m.drop(i), ARQ_MOT)
                    st.rerun()

# --- ABA 2: SAÍDA (COM FILTROS DE STATUS) ---
with tabs[1]:
    st.header("Registar Saída")
    df_v = carregar(ARQ_VEIC)
    df_m = carregar(ARQ_MOT)
    
    # Filtra apenas ATIVOS para a operação
    v_ativos = df_v[df_v['Status'] == "Ativo"]
    m_ativos = df_m[df_m['Status'] == "Ativo"]
    
    if v_ativos.empty or m_ativos.empty:
        st.warning("Verifique se há veículos e motoristas cadastrados e ATIVOS.")
    else:
        opcoes_v = [row['Veículo'] + " (" + row['Placa'] + ")" for _, row in v_ativos.iterrows()]
        v_sel = st.selectbox("Veículo", opcoes_v)
        st_s = get_status_veiculo(v_sel)
        
        m_sel = st.selectbox("Motorista", m_ativos['Nome'].tolist())
        m_info = m_ativos[m_ativos['Nome'] == m_sel].iloc[0]
        
        # Validação automática da CNH baseada no cadastro
        dt_cnh = datetime.strptime(str(m_info['Validade_CNH']), '%Y-%m-%d').date()
        
        if dt_cnh < date.today():
            st.error(f"❌ CNH de {m_sel} vencida em {dt_cnh.strftime('%d/%m/%Y')}")
        elif st_s["acao"] == "SAÍDA":
            st.error(f"🚫 Veículo em uso por {st_s['user']}")
        else:
            st.success(f"KM Atual: {st_s['km']} | CNH OK")
            km_s = st.number_input("KM Inicial", value=st_s['km'], min_value=st_s['km'])
            
            # Herança de avarias simplificada
            limpo = st_s['av'].replace('|', ',')
            d_av = [x.strip() for x in limpo.split(',')] if st_s['av'] != "Nenhuma" else []
            pecas = ["Capô", "Parachoque", "Porta", "Parabrisa", "Pneus"]
            av_s = st.multiselect("Checklist:", pecas, default=[x for x in d_av if x in pecas])
            
            if st.button("Confirmar Saída"):
                nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "SAÍDA", "Veículo": v_sel, "Usuário": m_sel, "KM": km_s, "CNH": dt_cnh, "Av_Saida": ", ".join(av_s), "Av_Chegada": "Pendente", "Av_Totais": ", ".join(av_s), "Obs": "", "Foto": "Não"}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST)
                st.success("Saída Ok!"); st.rerun()

# --- ABA 3: CHEGADA ---
with tabs[2]:
    st.header("Registar Chegada")
    df_v_all = carregar(ARQ_VEIC)
    v_opcoes = [row['Veículo'] + " (" + row['Placa'] + ")" for _, row in df_v_all.iterrows()]
    v_sel_d = st.selectbox("Veículo", v_opcoes, key="vd")
    st_d = get_status_veiculo(v_sel_d)
    
    if st_d["acao"] != "SAÍDA":
        st.info("Veículo no pátio.")
    else:
        km_d = st.number_input("KM Final", min_value=st_d['km'], value=st_d['km'])
        if st.button("Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "CHEGADA", "Veículo": v_sel_d, "Usuário": st_d['user'], "KM": km_d, "CNH": "", "Av_Saida": st_d['av'], "Av_Chegada": "Nenhuma", "Av_Totais": st_d['av'], "Obs": "Retorno", "Foto": ""}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST)
            st.success("Chegada Ok!"); st.rerun()

# --- ABA 4: MANUTENÇÃO ---
with tabs[3]:
    st.header("🔧 Reparos")
    df_v_all = carregar(ARQ_VEIC)
    v_opcoes = [row['Veículo'] + " (" + row['Placa'] + ")" for _, row in df_v_all.iterrows()]
    v_m = st.selectbox("Veículo", v_opcoes, key="vm")
    st_m = get_status_veiculo(v_m)
    if st_m["av"] == "Nenhuma": st.success("Sem avarias.")
    else:
        if st.button("Limpar Avarias (Reparo Total)"):
            nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "REPARO", "Veículo": v_m, "Usuário": "Oficina", "KM": st_m["km"], "CNH": "", "Av_Saida": "Reparo Geral", "Av_Chegada": "", "Av_Totais": "Nenhuma", "Obs": "Manutenção", "Foto": ""}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST)
            st.success("Reparado!"); st.rerun()

# --- ABA 5: HISTÓRICO ---
with tabs[4]:
    st.header("📋 Histórico Geral")
    st.dataframe(carregar(ARQ_HIST), use_container_width=True)
