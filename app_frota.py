import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

st.set_page_config(page_title="Frota Empresa", page_icon="🚗", layout="wide")
st.title("🚗 Gestão de Frota - V32")

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

tabs = st.tabs(["⚙️ Gestão & Cadastro", "📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"])

# --- ABA 1: GESTÃO & CADASTRO (EDIÇÃO E DUPLICIDADE) ---
with tabs[0]:
    c1, c2 = st.columns(2)
    df_h = carregar(ARQ_HIST)
    
    with c1:
        st.subheader("🚗 Veículos")
        with st.expander("➕ Novo / Editar Veículo"):
            with st.form("form_v"):
                v_idx = st.number_input("ID para Edição (deixe -1 para novo)", value=-1, step=1)
                v_mod = st.text_input("Modelo")
                v_pla = st.text_input("Placa").upper().strip()
                v_km = st.number_input("Última Revisão (KM)", min_value=0)
                v_dt = st.date_input("Data Última Revisão")
                if st.form_submit_button("Salvar Veículo"):
                    df_v = carregar(ARQ_VEIC)
                    # Validação de Duplicidade (Placa)
                    if v_idx == -1 and v_pla in df_v['Placa'].values:
                        st.error(f"Erro: Veículo com placa {v_pla} já está cadastrado!")
                    elif v_mod and v_pla:
                        novo = {"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": v_km, "Ult_Revisao_Data": v_dt, "Intervalo_KM": 10000, "Status": "Ativo"}
                        if v_idx == -1: df_v = pd.concat([df_v, pd.DataFrame([novo])])
                        else: df_v.iloc[v_idx] = novo
                        salvar(df_v, ARQ_VEIC)
                        st.success("Dados salvos!"); st.rerun()

        df_v = carregar(ARQ_VEIC)
        for i, r in df_v.iterrows():
            nome_f = f"{r['Veículo']} ({r['Placa']})"
            tem_h = nome_f in df_h['Veículo'].values
            with st.container(border=True):
                col_a, col_b = st.columns([3, 2])
                col_a.write(f"**{nome_f}**\nStatus: {r['Status']}")
                if col_b.button("Bloquear/Ativar", key=f"vst{i}"):
                    df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_v, ARQ_VEIC); st.rerun()
                if not tem_h and col_b.button("🗑️ Excluir", key=f"vdel{i}"):
                    salvar(df_v.drop(i), ARQ_VEIC); st.rerun()
                st.caption(f"ID para edição: {i}")

    with c2:
        st.subheader("👤 Motoristas")
        with st.expander("➕ Novo / Editar Motorista"):
            with st.form("form_m"):
                m_idx = st.number_input("ID para Edição (deixe -1 para novo)", value=-1, step=1)
                m_nome = st.text_input("Nome")
                m_cnh = st.date_input("Validade CNH")
                if st.form_submit_button("Salvar Motorista"):
                    df_m = carregar(ARQ_MOT)
                    # Validação de Duplicidade (Nome + Data)
                    duplicado = df_m[(df_m['Nome'] == m_nome) & (df_m['Validade_CNH'] == str(m_cnh))]
                    if m_idx == -1 and not duplicado.empty:
                        st.error("Erro: Este motorista já está cadastrado com esta mesma validade!")
                    elif m_nome:
                        novo = {"Nome": m_nome, "Validade_CNH": m_cnh, "Status": "Ativo"}
                        if m_idx == -1: df_m = pd.concat([df_m, pd.DataFrame([novo])])
                        else: df_m.iloc[m_idx] = novo
                        salvar(df_m, ARQ_MOT)
                        st.success("Dados salvos!"); st.rerun()

        df_m = carregar(ARQ_MOT)
        for i, r in df_m.iterrows():
            tem_h = r['Nome'] in df_h['Usuário'].values
            with st.container(border=True):
                col_a, col_b = st.columns([3, 2])
                col_a.write(f"**{r['Nome']}**\nCNH: {r['Validade_CNH']}")
                if col_b.button("Bloquear/Ativar", key=f"mst{i}"):
                    df_m.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_m, ARQ_MOT); st.rerun()
                if not tem_h and col_b.button("🗑️ Excluir", key=f"mdel{i}"):
                    salvar(df_m.drop(i), ARQ_MOT); st.rerun()
                st.caption(f"ID para edição: {i}")

# --- DEMAIS ABAS (Mantidas com filtros de Ativo) ---
with tabs[1]:
    st.header("Registar Saída")
    v_at = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    m_at = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Status'] == "Ativo"]
    if not v_at.empty and not m_at.empty:
        v_sel = st.selectbox("Veículo", [f"{r['Veículo']} ({r['Placa']})" for _, r in v_at.iterrows()])
        st_s = get_status_veiculo(v_sel)
        m_sel = st.selectbox("Motorista", m_at['Nome'].tolist())
        # Validação CNH
        info_m = m_at[m_at['Nome'] == m_sel].iloc[0]
        val_cnh = datetime.strptime(str(info_m['Validade_CNH']), '%Y-%m-%d').date()
        if val_cnh < date.today(): st.error(f"CNH de {m_sel} vencida!")
        elif st_s["acao"] == "SAÍDA": st.error(f"Veículo com {st_s['user']}")
        else:
            km_s = st.number_input("KM Inicial", value=st_s['km'], min_value=st_s['km'])
            av_s = st.multiselect("Avarias:", ["Capô", "Pneus", "Vidros"], default=[x.strip() for x in st_s['av'].split(',') if x.strip() != "Nenhuma"])
            if st.button("Confirmar Saída"):
                nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "SAÍDA", "Veículo": v_sel, "Usuário": m_sel, "KM": km_s, "CNH": val_cnh, "Av_Saida": ", ".join(av_s), "Av_Chegada": "Pendente", "Av_Totais": ", ".join(av_s), "Obs": "", "Foto": "Não"}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.rerun()
    else: st.warning("Cadastre itens ativos na Gestão.")

with tabs[2]:
    st.header("Registar Chegada")
    v_all = carregar(ARQ_VEIC)
    v_sel_d = st.selectbox("Veículo", [f"{r['Veículo']} ({r['Placa']})" for _, r in v_all.iterrows()], key="vd")
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
