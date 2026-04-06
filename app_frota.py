import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

st.set_page_config(page_title="Frota Empresa", page_icon="🚗", layout="wide")
st.title("🚗 Gestão de Frota - Oficial V35")

# --- BANCO DE DADOS (CSV) ---
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
    # Tenta encontrar o KM inicial no cadastro caso não haja histórico
    v_info = df_c[df_c['Veículo'] + " (" + df_c['Placa'] + ")" == v_alvo]
    km_ini = int(v_info.iloc[0]['Ult_Revisao_KM']) if not v_info.empty else 0
    return {"acao": "CHEGADA", "user": "Ninguém", "km": km_ini, "av": "Nenhuma"}

# Estados de Edição
if 'edit_v_idx' not in st.session_state: st.session_state.edit_v_idx = -1
if 'edit_m_idx' not in st.session_state: st.session_state.edit_m_idx = -1

tabs = st.tabs(["⚙️ Gestão & Cadastro", "📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"])

# --- ABA 1: GESTÃO E EDIÇÃO ---
with tabs[0]:
    c1, c2 = st.columns(2)
    df_h = carregar(ARQ_HIST)
    
    with c1:
        st.subheader("🚗 Veículos")
        df_v = carregar(ARQ_VEIC)
        with st.expander("➕ Cadastrar/Editar Veículo", expanded=(st.session_state.edit_v_idx != -1)):
            v_idx = st.session_state.edit_v_idx
            with st.form("f_v"):
                v_m = df_v.iloc[v_idx]['Veículo'] if v_idx != -1 else ""
                v_p = df_v.iloc[v_idx]['Placa'] if v_idx != -1 else ""
                v_k = int(df_v.iloc[v_idx]['Ult_Revisao_KM']) if v_idx != -1 else 0
                v_d = datetime.strptime(str(df_v.iloc[v_idx]['Ult_Revisao_Data']), '%Y-%m-%d').date() if v_idx != -1 else date.today()
                
                v_mod = st.text_input("Modelo", value=v_m)
                v_pla = st.text_input("Placa", value=v_p).upper().strip()
                v_km_r = st.number_input("KM Última Revisão", value=v_k)
                v_dt_r = st.date_input("Data Última Revisão", value=v_d)
                v_int = st.number_input("Intervalo (KM)", value=10000)
                
                if st.form_submit_button("Salvar"):
                    if v_idx == -1 and v_pla in df_v['Placa'].values: st.error("Placa já existe!")
                    elif v_mod and v_pla:
                        nova = {"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": v_km_r, "Ult_Revisao_Data": v_dt_r, "Intervalo_KM": v_int, "Status": "Ativo"}
                        if v_idx == -1: df_v = pd.concat([df_v, pd.DataFrame([nova])], ignore_index=True)
                        else: 
                            for k, v in nova.items(): df_v.at[v_idx, k] = v
                        salvar(df_v, ARQ_VEIC); st.session_state.edit_v_idx = -1; st.rerun()
        
        for i, r in df_v.iterrows():
            nome_f = f"{r['Veículo']} ({r['Placa']})"
            with st.container(border=True):
                col_a, col_b = st.columns([3, 2])
                col_a.write(f"**{nome_f}**\nStatus: {r['Status']}")
                if col_b.button("📝 Editar", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()
                if col_b.button("Bloquear/Ativar", key=f"bv{i}"):
                    df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_v, ARQ_VEIC); st.rerun()
                if nome_f not in df_h['Veículo'].values and col_b.button("🗑️", key=f"dv{i}"):
                    salvar(df_v.drop(i), ARQ_VEIC); st.rerun()

    with c2:
        st.subheader("👤 Motoristas")
        df_m = carregar(ARQ_MOT)
        with st.expander("➕ Cadastrar/Editar Motorista", expanded=(st.session_state.edit_m_idx != -1)):
            m_idx = st.session_state.edit_m_idx
            with st.form("f_m"):
                m_n = df_m.iloc[m_idx]['Nome'] if m_idx != -1 else ""
                m_v = datetime.strptime(str(df_m.iloc[m_idx]['Validade_CNH']), '%Y-%m-%d').date() if m_idx != -1 else date.today()
                m_nome = st.text_input("Nome", value=m_n)
                m_cnh = st.date_input("Validade CNH", value=m_v)
                if st.form_submit_button("Salvar"):
                    nova = {"Nome": m_nome, "Validade_CNH": m_cnh, "Status": "Ativo"}
                    if m_idx == -1: df_m = pd.concat([df_m, pd.DataFrame([nova])], ignore_index=True)
                    else: 
                        for k, v in nova.items(): df_m.at[m_idx, k] = v
                    salvar(df_m, ARQ_MOT); st.session_state.edit_m_idx = -1; st.rerun()
        
        for i, r in df_m.iterrows():
            with st.container(border=True):
                col_a, col_b = st.columns([3, 2])
                col_a.write(f"**{r['Nome']}**\nValidade: {r['Validade_CNH']}")
                if col_b.button("📝 Editar", key=f"em{i}"): st.session_state.edit_m_idx = i; st.rerun()
                if col_b.button("Bloquear", key=f"bm{i}"):
                    df_m.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_m, ARQ_MOT); st.rerun()
                if r['Nome'] not in df_h['Usuário'].values and col_b.button("🗑️", key=f"dm{i}"):
                    salvar(df_m.drop(i), ARQ_MOT); st.rerun()

# --- ABA 2: SAÍDA COM ALERTAS DE SEGURANÇA ---
with tabs[1]:
    st.header("📤 Registrar Saída")
    df_v_ativos = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    df_m_ativos = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Status'] == "Ativo"]
    
    if df_v_ativos.empty or df_m_ativos.empty:
        st.warning("Verifique se há veículos e motoristas ativos no cadastro.")
    else:
        # Seleção de Veículo
        lista_v = [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_ativos.iterrows()]
        v_escolhido = st.selectbox("Selecione o Veículo", lista_v)
        st_v = get_status_veiculo(v_escolhido)
        
        # --- ALERTA DE REVISÃO ---
        info_v = df_v_ativos[df_v_ativos['Placa'] == v_escolhido.split("(")[1].replace(")", "")].iloc[0]
        limite_km = int(info_v['Ult_Revisao_KM']) + int(info_v['Intervalo_KM'])
        km_atual = st_v['km']
        saldo_km = limite_km - km_atual
        
        if saldo_km <= 500 and saldo_km > 0:
            st.warning(f"⚠️ REVISÃO PRÓXIMA: Faltam {saldo_km} KM para a revisão de {limite_km} KM.")
        elif saldo_km <= 0:
            st.error(f"🚨 REVISÃO VENCIDA! Veículo ultrapassou o limite de {limite_km} KM por {abs(saldo_km)} KM.")

        # Seleção de Motorista
        m_escolhido = st.selectbox("Selecione o Motorista", df_m_ativos['Nome'].tolist())
        info_m = df_m_ativos[df_m_ativos['Nome'] == m_escolhido].iloc[0]
        dt_cnh = datetime.strptime(str(info_m['Validade_CNH']), '%Y-%m-%d').date()
        
        # --- ALERTA DE CNH ---
        if dt_cnh < date.today():
            st.error(f"🚫 BLOQUEADO: CNH de {m_escolhido} venceu em {dt_cnh.strftime('%d/%m/%Y')}. Saída não permitida.")
        elif st_v["acao"] == "SAÍDA":
            st.error(f"🚫 VEÍCULO EM USO por {st_v['user']}.")
        else:
            st.success(f"KM Atual: {km_atual} | CNH válida até {dt_cnh.strftime('%d/%m/%Y')}")
            km_saida = st.number_input("Informe o KM de Saída", value=km_atual, min_value=km_atual)
            
            # Checklist de Avarias
            opcoes_av = ["Capô", "Parachoque Dianteiro", "Parachoque Traseiro", "Portas Dir", "Portas Esq", "Pneus", "Vidros"]
            av_atuais = [x.strip() for x in st_v['av'].split(',') if x.strip() in opcoes_av]
            checklist = st.multiselect("Checklist de Avarias (Saída):", opcoes_av, default=av_atuais)
            
            if st.button("🚀 Confirmar Saída"):
                nova_saida = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Ação": "SAÍDA",
                    "Veículo": v_escolhido,
                    "Usuário": m_escolhido,
                    "KM": km_saida,
                    "CNH": dt_cnh,
                    "Av_Saida": ", ".join(checklist),
                    "Av_Chegada": "Pendente",
                    "Av_Totais": ", ".join(checklist),
                    "Obs": "", "Foto": "Não"
                }])
                salvar(pd.concat([carregar(ARQ_HIST), nova_saida]), ARQ_HIST)
                st.success("Saída registrada com sucesso!"); st.rerun()

# --- ABAS DE CHEGADA, MANUTENÇÃO E HISTÓRICO (SIMPLIFICADAS) ---
with tabs[2]:
    st.header("📥 Registrar Chegada")
    v_retorno = st.selectbox("Veículo retornando", [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()], key="chegada")
    st_ret = get_status_veiculo(v_retorno)
    if st_ret["acao"] == "SAÍDA":
        km_chegada = st.number_input("KM na Chegada", min_value=st_ret['km'], value=st_ret['km'])
        if st.button("🏁 Confirmar Chegada"):
            nova_chegada = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "CHEGADA", "Veículo": v_retorno, "Usuário": st_ret['user'], "KM": km_chegada, "CNH": "", "Av_Saida": st_ret['av'], "Av_Chegada": "Nenhuma", "Av_Totais": st_ret['av'], "Obs": "Retorno", "Foto": ""}])
            salvar(pd.concat([carregar(ARQ_HIST), nova_chegada]), ARQ_HIST); st.rerun()
    else: st.info("Este veículo já está no pátio.")

with tabs[3]:
    st.header("🔧 Oficina / Manutenção")
    v_manut = st.selectbox("Veículo para manutenção", [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()], key="manut")
    st_manut = get_status_veiculo(v_manut)
    if st_manut["av"] != "Nenhuma":
        st.warning(f"Avarias detectadas: {st_manut['av']}")
        if st.button("🛠️ Registrar Reparo das Avarias"):
            nova_manut = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "REPARO", "Veículo": v_manut, "Usuário": "Oficina", "KM": st_manut["km"], "CNH": "", "Av_Saida": "Conserto", "Av_Chegada": "", "Av_Totais": "Nenhuma", "Obs": "Reparo de Avarias", "Foto": ""}])
            salvar(pd.concat([carregar(ARQ_HIST), nova_manut]), ARQ_HIST); st.rerun()

with tabs[4]:
    st.header("📋 Histórico de Movimentação")
    st.dataframe(carregar(ARQ_HIST).replace(["None", "nan"], ""), use_container_width=True)
