import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os

st.set_page_config(page_title="Frota Empresa", page_icon="🚗", layout="wide")
st.title("🚗 Gestão de Frota - Oficial V33")

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

# --- ABA 1: GESTÃO & CADASTRO ---
with tabs[0]:
    c1, c2 = st.columns(2)
    df_h = carregar(ARQ_HIST)
    
    with c1:
        st.subheader("🚗 Veículos")
        df_v = carregar(ARQ_VEIC)
        
        # Formulário de Cadastro/Edição
        with st.expander("➕ Cadastrar / Editar Veículo", expanded=(st.session_state.edit_v_idx != -1)):
            with st.form("form_v"):
                v_edit = st.session_state.edit_v_idx
                # Preencher se estiver editando
                val_mod = df_v.iloc[v_edit]['Veículo'] if v_edit != -1 else ""
                val_pla = df_v.iloc[v_edit]['Placa'] if v_edit != -1 else ""
                val_km = int(df_v.iloc[v_edit]['Ult_Revisao_KM']) if v_edit != -1 else 0
                val_dt = datetime.strptime(str(df_v.iloc[v_edit]['Ult_Revisao_Data']), '%Y-%m-%d').date() if v_edit != -1 else date.today()
                
                v_mod = st.text_input("Modelo", value=val_mod)
                v_pla = st.text_input("Placa", value=val_pla).upper().strip()
                v_km_rev = st.number_input("KM da Última Revisão", value=val_km)
                v_dt_rev = st.date_input("Data da Última Revisão", value=val_dt)
                v_intervalo = st.number_input("Intervalo Revisão (KM)", value=10000)
                
                btn_txt = "Atualizar Veículo" if v_edit != -1 else "Salvar Novo Veículo"
                if st.form_submit_button(btn_txt):
                    # Validação duplicidade placa (exceto se for o próprio editando)
                    if v_edit == -1 and v_pla in df_v['Placa'].values:
                        st.error("Erro: Placa já cadastrada!")
                    elif v_mod and v_pla:
                        novo = {"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": v_km_rev, "Ult_Revisao_Data": v_dt_rev, "Intervalo_KM": v_intervalo, "Status": "Ativo"}
                        if v_edit == -1: df_v = pd.concat([df_v, pd.DataFrame([novo])], ignore_index=True)
                        else: df_v.iloc[v_edit] = novo
                        salvar(df_v, ARQ_VEIC)
                        st.session_state.edit_v_idx = -1
                        st.success("Salvo!"); st.rerun()
            if st.button("Cancelar Edição", key="can_v"): 
                st.session_state.edit_v_idx = -1; st.rerun()

        # Listagem de Veículos
        for i, r in df_v.iterrows():
            nome_f = f"{r['Veículo']} ({r['Placa']})"
            tem_h = nome_f in df_h['Veículo'].values
            with st.container(border=True):
                col_a, col_b = st.columns([3, 2])
                col_a.write(f"**{nome_f}**\nÚltima Rev: {r['Ult_Revisao_KM']} KM")
                if col_b.button("📝 Editar", key=f"edit_v_{i}"):
                    st.session_state.edit_v_idx = i; st.rerun()
                if col_b.button("Bloquear/Ativar", key=f"vst{i}"):
                    df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_v, ARQ_VEIC); st.rerun()
                if not tem_h and col_b.button("🗑️", key=f"vdel{i}"):
                    salvar(df_v.drop(i), ARQ_VEIC); st.rerun()

    with c2:
        st.subheader("👤 Motoristas")
        df_m = carregar(ARQ_MOT)
        with st.expander("➕ Cadastrar / Editar Motorista", expanded=(st.session_state.edit_m_idx != -1)):
            with st.form("form_m"):
                m_edit = st.session_state.edit_m_idx
                val_nom = df_m.iloc[m_edit]['Nome'] if m_edit != -1 else ""
                val_cnh = datetime.strptime(str(df_m.iloc[m_edit]['Validade_CNH']), '%Y-%m-%d').date() if m_edit != -1 else date.today()
                
                m_nome = st.text_input("Nome", value=val_nom)
                m_venc = st.date_input("Validade CNH", value=val_cnh)
                
                if st.form_submit_button("Salvar"):
                    if m_nome:
                        novo = {"Nome": m_nome, "Validade_CNH": m_venc, "Status": "Ativo"}
                        if m_edit == -1: df_m = pd.concat([df_m, pd.DataFrame([novo])], ignore_index=True)
                        else: df_m.iloc[m_edit] = novo
                        salvar(df_m, ARQ_MOT)
                        st.session_state.edit_m_idx = -1
                        st.success("Salvo!"); st.rerun()
            if st.button("Cancelar Edição", key="can_m"): 
                st.session_state.edit_m_idx = -1; st.rerun()

        for i, r in df_m.iterrows():
            tem_h = r['Nome'] in df_h['Usuário'].values
            with st.container(border=True):
                col_a, col_b = st.columns([3, 2])
                col_a.write(f"**{r['Nome']}**\nCNH: {r['Validade_CNH']}")
                if col_b.button("📝 Editar", key=f"edit_m_{i}"):
                    st.session_state.edit_m_idx = i; st.rerun()
                if col_b.button("Inativar/Ativar", key=f"mst{i}"):
                    df_m.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_m, ARQ_MOT); st.rerun()
                if not tem_h and col_b.button("🗑️", key=f"mdel{i}"):
                    salvar(df_m.drop(i), ARQ_MOT); st.rerun()

# --- ABA 2: SAÍDA (COM ALERTAS DE REVISÃO RESTAURADOS) ---
with tabs[1]:
    st.header("Registar Saída")
    df_v_cad = carregar(ARQ_VEIC)
    v_at = df_v_cad[df_v_cad['Status'] == "Ativo"]
    m_at = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Status'] == "Ativo"]
    
    if not v_at.empty and not m_at.empty:
        v_sel = st.selectbox("Veículo", [f"{r['Veículo']} ({r['Placa']})" for _, r in v_at.iterrows()])
        st_s = get_status_veiculo(v_sel)
        
        # --- LÓGICA DE REVISÃO RESTAURADA ---
        v_info = df_v_cad[df_v_cad['Placa'] == v_sel.split("(")[1].replace(")", "")].iloc[0]
        prox_km = int(v_info['Ult_Revisao_KM']) + int(v_info['Intervalo_KM'])
        km_restante = prox_km - st_s["km"]
        
        if km_restante <= 500:
            st.warning(f"⚠️ ATENÇÃO: Revisão próxima ({prox_km} KM). Faltam {km_restante} KM.")
        if km_restante <= 0:
            st.error(f"🚨 REVISÃO VENCIDA! Veículo ultrapassou o limite de {prox_km} KM.")
        
        m_sel = st.selectbox("Motorista", m_at['Nome'].tolist())
        info_m = m_at[m_at['Nome'] == m_sel].iloc[0]
        dt_cnh = datetime.strptime(str(info_m['Validade_CNH']), '%Y-%m-%d').date()
        
        if dt_cnh < date.today(): st.error(f"CNH de {m_sel} vencida!")
        elif st_s["acao"] == "SAÍDA": st.error(f"Veículo com {st_s['user']}")
        else:
            km_s = st.number_input("KM Inicial", value=st_s['km'], min_value=st_s['km'])
            pecas = ["1. Capô", "2. Pneus", "3. Parachoque", "4. Vidros", "5. Lanternas"]
            limpo = st_s['av'].replace('|', ',')
            d_av = [x.strip() for x in limpo.split(',')] if st_s['av'] != "Nenhuma" else []
            av_s = st.multiselect("Checklist Avarias:", pecas, default=[x for x in d_av if x in pecas])
            
            if st.button("Confirmar Saída"):
                nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "SAÍDA", "Veículo": v_sel, "Usuário": m_sel, "KM": km_s, "CNH": dt_cnh, "Av_Saida": ", ".join(av_s), "Av_Chegada": "Pendente", "Av_Totais": ", ".join(av_s), "Obs": "", "Foto": "Não"}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

# --- DEMAIS ABAS ---
with tabs[2]:
    st.header("Registar Chegada")
    v_sel_d = st.selectbox("Veículo", [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()], key="vd")
    st_d = get_status_veiculo(v_sel_d)
    if st_d["acao"] == "SAÍDA":
        km_d = st.number_input("KM Final", min_value=st_d['km'], value=st_d['km'])
        if st.button("Confirmar Chegada"):
            nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "CHEGADA", "Veículo": v_sel_d, "Usuário": st_d['user'], "KM": km_d, "CNH": "", "Av_Saida": st_d['av'], "Av_Chegada": "Nenhuma", "Av_Totais": st_d['av'], "Obs": "Retorno", "Foto": ""}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()
    else: st.info("Veículo no pátio.")

with tabs[3]:
    st.header("🔧 Reparos")
    v_m = st.selectbox("Veículo", [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()], key="vm")
    st_m = get_status_veiculo(v_m)
    if st_m["av"] != "Nenhuma" and st.button("Limpar Avarias"):
        nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "REPARO", "Veículo": v_m, "Usuário": "Oficina", "KM": st_m["km"], "CNH": "", "Av_Saida": "Reparo", "Av_Chegada": "", "Av_Totais": "Nenhuma", "Obs": "Manutenção", "Foto": ""}])
        salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()

with tabs[4]:
    st.header("📋 Histórico")
    st.dataframe(carregar(ARQ_HIST).replace(["None", "nan"], ""), use_container_width=True)
