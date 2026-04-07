import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

st.set_page_config(page_title="Frota Empresa", page_icon="🚗", layout="wide")
st.title("🚗 Gestão de Frota - Oficial V37")

# --- ARQUIVOS ---
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"

def inicializar_e_limpar():
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Foto"]).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_MOT):
        pd.DataFrame(columns=["Nome", "Validade_CNH", "Status"]).to_csv(ARQ_MOT, index=False)
    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Intervalo_KM", "Status"]).to_csv(ARQ_VEIC, index=False)
    else:
        df_v = pd.read_csv(ARQ_VEIC)
        df_v = df_v.drop_duplicates(subset=['Placa'], keep='first')
        df_v.to_csv(ARQ_VEIC, index=False)

inicializar_e_limpar()

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

if 'edit_v_idx' not in st.session_state: st.session_state.edit_v_idx = -1
if 'edit_m_idx' not in st.session_state: st.session_state.edit_m_idx = -1

tabs = st.tabs(["⚙️ Gestão & Cadastro", "📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"])

# --- ABA 1: GESTÃO (COM DATAS EM BRANCO) ---
with tabs[0]:
    c1, c2 = st.columns(2)
    df_h = carregar(ARQ_HIST)
    
    with c1:
        st.subheader("🚗 Veículos")
        df_v = carregar(ARQ_VEIC)
        with st.expander("➕ Cadastrar/Editar Veículo", expanded=(st.session_state.edit_v_idx != -1)):
            v_idx = st.session_state.edit_v_idx
            with st.form("f_v"):
                # Se for novo registro, valor é None (vazio). Se for edição, carrega a data salva.
                v_m = df_v.iloc[v_idx]['Veículo'] if v_idx != -1 else ""
                v_p = df_v.iloc[v_idx]['Placa'] if v_idx != -1 else ""
                v_k = int(df_v.iloc[v_idx]['Ult_Revisao_KM']) if v_idx != -1 else 0
                v_d_val = datetime.strptime(str(df_v.iloc[v_idx]['Ult_Revisao_Data']), '%Y-%m-%d').date() if v_idx != -1 else None
                
                v_mod = st.text_input("Modelo", value=v_m)
                v_pla = st.text_input("Placa", value=v_p).upper().strip()
                v_km_r = st.number_input("KM Última Revisão", value=v_k)
                # CAMPO EM BRANCO (value=None)
                v_dt_r = st.date_input("Data Última Revisão", value=v_d_val, format="DD/MM/YYYY")
                v_int = st.number_input("Intervalo (KM)", value=10000)
                
                if st.form_submit_button("Salvar"):
                    if not v_dt_r:
                        st.error("Por favor, selecione a Data da Última Revisão.")
                    elif v_idx == -1 and v_pla in df_v['Placa'].values: 
                        st.error("Erro: Placa já cadastrada.")
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
                col_a.write(f"**{nome_f}**\nÚlt. Rev: {r['Ult_Revisao_KM']} KM | Status: {r['Status']}")
                if col_b.button("📝 Editar", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()
                if col_b.button("Bloquear/Ativar", key=f"bv{i}"):
                    df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_v, ARQ_VEIC); st.rerun()

    with c2:
        st.subheader("👤 Motoristas")
        df_m = carregar(ARQ_MOT)
        with st.expander("➕ Cadastrar/Editar Motorista", expanded=(st.session_state.edit_m_idx != -1)):
            m_idx = st.session_state.edit_m_idx
            with st.form("f_m"):
                m_n = df_m.iloc[m_idx]['Nome'] if m_idx != -1 else ""
                m_v_val = datetime.strptime(str(df_m.iloc[m_idx]['Validade_CNH']), '%Y-%m-%d').date() if m_idx != -1 else None
                
                m_nome = st.text_input("Nome", value=m_n)
                # CAMPO EM BRANCO (value=None)
                m_cnh = st.date_input("Validade CNH", value=m_v_val, format="DD/MM/YYYY")
                
                if st.form_submit_button("Salvar"):
                    if not m_cnh:
                        st.error("Por favor, selecione a Data de Validade da CNH.")
                    elif m_nome:
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
                if col_b.button("Bloquear/Ativar", key=f"bm{i}"):
                    df_m.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_m, ARQ_MOT); st.rerun()

# --- ABAS DE OPERAÇÃO (IGUAIS À V36) ---
with tabs[1]:
    st.header("📤 Registrar Saída")
    df_v_ativos = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    df_m_ativos = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Status'] == "Ativo"]
    
    if df_v_ativos.empty or df_m_ativos.empty:
        st.warning("Cadastre veículos e motoristas ativos na aba de Gestão.")
    else:
        v_escolhido = st.selectbox("Selecione o Veículo", [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_ativos.iterrows()])
        st_v = get_status_veiculo(v_escolhido)
        
        info_v = df_v_ativos[df_v_ativos['Placa'] == v_escolhido.split("(")[1].replace(")", "")].iloc[0]
        limite_km = int(info_v['Ult_Revisao_KM']) + int(info_v['Intervalo_KM'])
        saldo = limite_km - st_v['km']
        
        if saldo <= 500 and saldo > 0: st.warning(f"⚠️ Revisão em {saldo} KM.")
        elif saldo <= 0: st.error(f"🚨 REVISÃO VENCIDA HÁ {abs(saldo)} KM!")

        m_escolhido = st.selectbox("Selecione o Motorista", df_m_ativos['Nome'].tolist())
        info_m = df_m_ativos[df_m_ativos['Nome'] == m_escolhido].iloc[0]
        dt_cnh = datetime.strptime(str(info_m['Validade_CNH']), '%Y-%m-%d').date()
        
        if dt_cnh < date.today():
            st.error(f"🚫 BLOQUEADO: CNH de {m_escolhido} vencida.")
        elif st_v["acao"] == "SAÍDA":
            st.error(f"🚫 VEÍCULO EM USO por {st_v['user']}.")
        else:
            st.success(f"KM Atual: {st_v['km']} | CNH Ok")
            km_saida = st.number_input("KM Inicial", value=st_v['km'], min_value=st_s['km'] if 'st_s' in locals() else st_v['km'])
            pecas = ["Capô", "Pneus", "Vidros", "Parachoques", "Portas"]
            limpo = st_v['av'].replace('|', ',')
            d_av = [x.strip() for x in limpo.split(',')] if st_v['av'] != "Nenhuma" else []
            checklist = st.multiselect("Avarias (Saída):", pecas, default=[x for x in d_av if x in pecas])
            
            if st.button("🚀 Confirmar Saída"):
                nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "SAÍDA", "Veículo": v_escolhido, "Usuário": m_escolhido, "KM": km_saida, "CNH": dt_cnh, "Av_Saida": ", ".join(checklist), "Av_Chegada": "Pendente", "Av_Totais": ", ".join(checklist), "Obs": "", "Foto": "Não"}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST)
                st.success("Saída registrada!"); st.rerun()

with tabs[2]:
    st.header("📥 Registrar Chegada")
    v_ret = st.selectbox("Veículo", [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()], key="chegada")
    st_ret = get_status_veiculo(v_ret)
    if st_ret["acao"] == "SAÍDA":
        km_f = st.number_input("KM Final", min_value=st_ret['km'], value=st_ret['km'])
        if st.button("🏁 Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "CHEGADA", "Veículo": v_ret, "Usuário": st_ret['user'], "KM": km_f, "CNH": "", "Av_Saida": st_ret['av'], "Av_Chegada": "Nenhuma", "Av_Totais": st_ret['retorno' if 'retorno' in locals() else 'av'], "Obs": "Retorno", "Foto": ""}])
            # Correção rápida para o campo Av_Totais na chegada
            nova.at[0, "Av_Totais"] = st_ret['av']
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()
    else: st.info("Veículo no pátio.")

with tabs[3]:
    st.header("🔧 Oficina")
    v_man = st.selectbox("Veículo", [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()], key="manut")
    st_man = get_status_veiculo(v_man)
    if st_man["av"] != "Nenhuma":
        st.warning(f"Avarias: {st_man['av']}")
        if st.button("🛠️ Reparar"):
            nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "REPARO", "Veículo": v_man, "Usuário": "Oficina", "KM": st_man['km'], "CNH": "", "Av_Saida": "Reparo", "Av_Chegada": "", "Av_Totais": "Nenhuma", "Obs": "Reparo", "Foto": ""}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

with tabs[4]:
    st.header("📋 Histórico")
    st.dataframe(carregar(ARQ_HIST).replace(["None", "nan"], ""), use_container_width=True)
