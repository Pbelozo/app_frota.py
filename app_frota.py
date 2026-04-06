import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os

st.set_page_config(page_title="Frota Empresa", page_icon="🚗", layout="wide")
st.title("🚗 Gestão de Frota - Oficial V34")

# --- ARQUIVOS ---
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"

def inicializar():
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Foto"]).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Intervalo_KM", "Status"]).to_csv(ARQ_VEIC, index=False)
    if not os.path.exists(ARQ_MOT):
        pd.DataFrame(columns=["Nome", "Validade_CNH", "Status"]).to_csv(ARQ_MOT, index=False)

inicializar()

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

# --- GERENCIAMENTO DE ESTADO PARA EDIÇÃO ---
if 'edit_v_idx' not in st.session_state: st.session_state.edit_v_idx = -1
if 'edit_m_idx' not in st.session_state: st.session_state.edit_m_idx = -1

tabs = st.tabs(["⚙️ Gestão & Cadastro", "📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"])

# --- ABA 1: GESTÃO & CADASTRO (CORREÇÃO DE EDIÇÃO) ---
with tabs[0]:
    c1, c2 = st.columns(2)
    df_h = carregar(ARQ_HIST)
    
    with c1:
        st.subheader("🚗 Veículos")
        df_v = carregar(ARQ_VEIC)
        
        with st.expander("➕ Cadastrar / Editar Veículo", expanded=(st.session_state.edit_v_idx != -1)):
            v_idx = st.session_state.edit_v_idx
            with st.form("form_v"):
                # Valores padrão baseados no índice de edição
                v_m = df_v.iloc[v_idx]['Veículo'] if v_idx != -1 else ""
                v_p = df_v.iloc[v_idx]['Placa'] if v_idx != -1 else ""
                v_k = int(df_v.iloc[v_idx]['Ult_Revisao_KM']) if v_idx != -1 else 0
                v_d = datetime.strptime(str(df_v.iloc[v_idx]['Ult_Revisao_Data']), '%Y-%m-%d').date() if v_idx != -1 else date.today()
                
                v_mod = st.text_input("Modelo", value=v_m)
                v_pla = st.text_input("Placa", value=v_p).upper().strip()
                v_km_rev = st.number_input("KM da Última Revisão", value=v_k)
                v_dt_rev = st.date_input("Data da Última Revisão", value=v_d)
                v_int = st.number_input("Intervalo Revisão (KM)", value=10000)
                
                if st.form_submit_button("Salvar Veículo"):
                    if v_idx == -1 and v_pla in df_v['Placa'].values:
                        st.error("Placa já cadastrada!")
                    elif v_mod and v_pla:
                        nova_linha = {"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": v_km_rev, "Ult_Revisao_Data": v_dt_rev, "Intervalo_KM": v_int, "Status": "Ativo"}
                        if v_idx == -1: # Novo
                            df_v = pd.concat([df_v, pd.DataFrame([nova_linha])], ignore_index=True)
                        else: # Edição - Forma segura de atualizar sem erro de tipo
                            for chave, valor in nova_linha.items():
                                df_v.at[v_idx, chave] = valor
                        salvar(df_v, ARQ_VEIC)
                        st.session_state.edit_v_idx = -1
                        st.success("Salvo com sucesso!"); st.rerun()
            if st.button("Limpar Edição", key="clean_v"): st.session_state.edit_v_idx = -1; st.rerun()

        for i, r in df_v.iterrows():
            nome_f = r['Veículo'] + " (" + r['Placa'] + ")"
            with st.container(border=True):
                ca, cb = st.columns([3, 2])
                ca.write("**" + nome_f + "**\nKM Revisão: " + str(r['Ult_Revisao_KM']))
                if cb.button("📝 Editar", key="ev" + str(i)): st.session_state.edit_v_idx = i; st.rerun()
                if cb.button("Ativar/Inativar", key="sv" + str(i)):
                    df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_v, ARQ_VEIC); st.rerun()
                if nome_f not in df_h['Veículo'].values and cb.button("🗑️", key="dv" + str(i)):
                    salvar(df_v.drop(i), ARQ_VEIC); st.rerun()

    with c2:
        st.subheader("👤 Motoristas")
        df_m = carregar(ARQ_MOT)
        with st.expander("➕ Cadastrar / Editar Motorista", expanded=(st.session_state.edit_m_idx != -1)):
            m_idx = st.session_state.edit_m_idx
            with st.form("form_m"):
                m_n = df_m.iloc[m_idx]['Nome'] if m_idx != -1 else ""
                m_v = datetime.strptime(str(df_m.iloc[m_idx]['Validade_CNH']), '%Y-%m-%d').date() if m_idx != -1 else date.today()
                
                m_nome = st.text_input("Nome", value=m_n)
                m_cnh = st.date_input("Validade CNH", value=m_v)
                
                if st.form_submit_button("Salvar Motorista"):
                    if m_nome:
                        nova_m = {"Nome": m_nome, "Validade_CNH": m_cnh, "Status": "Ativo"}
                        if m_idx == -1:
                            df_m = pd.concat([df_m, pd.DataFrame([nova_m])], ignore_index=True)
                        else:
                            for c, v in nova_m.items(): df_m.at[m_idx, c] = v
                        salvar(df_m, ARQ_MOT)
                        st.session_state.edit_m_idx = -1
                        st.success("Salvo!"); st.rerun()
            if st.button("Limpar Edição", key="clean_m"): st.session_state.edit_m_idx = -1; st.rerun()

        for i, r in df_m.iterrows():
            with st.container(border=True):
                ca, cb = st.columns([3, 2])
                ca.write("**" + r['Nome'] + "**\nCNH: " + str(r['Validade_CNH']))
                if cb.button("📝 Editar", key="em" + str(i)): st.session_state.edit_m_idx = i; st.rerun()
                if cb.button("Inativar/Ativar", key="sm" + str(i)):
                    df_m.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_m, ARQ_MOT); st.rerun()
                if r['Nome'] not in df_h['Usuário'].values and cb.button("🗑️", key="dm" + str(i)):
                    salvar(df_m.drop(i), ARQ_MOT); st.rerun()

# --- ABA 2: SAÍDA (ALERTAS DE REVISÃO ATIVOS) ---
with tabs[1]:
    st.header("Registar Saída")
    df_v_cad = carregar(ARQ_VEIC)
    v_ativos = df_v_cad[df_v_cad['Status'] == "Ativo"]
    m_ativos = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Status'] == "Ativo"]
    
    if not v_ativos.empty and not m_ativos.empty:
        v_sel = st.selectbox("Veículo", [n + " (" + p + ")" for n, p in zip(v_ativos['Veículo'], v_ativos['Placa'])])
        st_s = get_status_veiculo(v_sel)
        
        # Alerta de Revisão
        placa_v = v_sel.split("(")[1].replace(")", "")
        info_v = df_v_cad[df_v_cad['Placa'] == placa_v].iloc[0]
        limite_km = int(info_v['Ult_Revisao_KM']) + int(info_v['Intervalo_KM'])
        falta = limite_km - st_s["km"]
        
        if falta <= 500: st.warning(f"⚠️ Revisão próxima: {limite_km} KM. Faltam {falta} KM.")
        if falta <= 0: st.error(f"🚨 REVISÃO VENCIDA EM {abs(falta)} KM!")
        
        m_sel = st.selectbox("Motorista", m_ativos['Nome'].tolist())
        cnh_val = datetime.strptime(str(m_ativos[m_ativos['Nome'] == m_sel].iloc[0]['Validade_CNH']), '%Y-%m-%d').date()
        
        if cnh_val < date.today(): st.error("CNH Vencida!")
        elif st_s["acao"] == "SAÍDA": st.error("Em uso por " + st_s["user"])
        else:
            km_s = st.number_input("KM Inicial", value=st_s['km'], min_value=st_s['km'])
            pecas = ["Capô", "Pneus", "Parachoque", "Vidros", "Lanternas"]
            limpo = st_s['av'].replace('|', ',')
            d_av = [x.strip() for x in limpo.split(',')] if st_s['av'] != "Nenhuma" else []
            av_s = st.multiselect("Checklist:", pecas, default=[x for x in d_av if x in pecas])
            
            if st.button("Confirmar Saída"):
                nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "SAÍDA", "Veículo": v_sel, "Usuário": m_sel, "KM": km_s, "CNH": cnh_val, "Av_Saida": ", ".join(av_s), "Av_Chegada": "Pendente", "Av_Totais": ", ".join(av_s), "Obs": "", "Foto": "Não"}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- DEMAIS ABAS ---
with tabs[2]:
    v_all = carregar(ARQ_VEIC)
    v_d = st.selectbox("Veículo", [n + " (" + p + ")" for n, p in zip(v_all['Veículo'], v_all['Placa'])], key="vd")
    st_d = get_status_veiculo(v_d)
    if st_d["acao"] == "SAÍDA":
        km_f = st.number_input("KM Final", min_value=st_d['km'], value=st_d['km'])
        if st.button("Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "CHEGADA", "Veículo": v_d, "Usuário": st_d['user'], "KM": km_f, "CNH": "", "Av_Saida": st_d['av'], "Av_Chegada": "Nenhuma", "Av_Totais": st_d['av'], "Obs": "Retorno", "Foto": ""}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()
    else: st.info("Veículo no pátio.")

with tabs[3]:
    v_m = st.selectbox("Veículo", [n + " (" + p + ")" for n, p in zip(carregar(ARQ_VEIC)['Veículo'], carregar(ARQ_VEIC)['Placa'])], key="vm")
    st_m = get_status_veiculo(v_m)
    if st_m["av"] != "Nenhuma" and st.button("Limpar Avarias"):
        nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "REPARO", "Veículo": v_m, "Usuário": "Oficina", "KM": st_m["km"], "CNH": "", "Av_Saida": "Reparo", "Av_Chegada": "", "Av_Totais": "Nenhuma", "Obs": "Manutenção", "Foto": ""}])
        salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

with tabs[4]:
    st.dataframe(carregar(ARQ_HIST).replace(["None", "nan"], ""), use_container_width=True)
