import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

st.set_page_config(page_title="Frota Empresa", page_icon="🚗", layout="wide")
st.title("🚗 Gestão de Frota - Oficial V39")

# --- ARQUIVOS ---
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"
ARQ_PECAS = "cadastro_pecas.csv"

def inicializar():
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Foto"]).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_MOT):
        pd.DataFrame(columns=["Nome", "Validade_CNH", "Status"]).to_csv(ARQ_MOT, index=False)
    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Intervalo_KM", "Status"]).to_csv(ARQ_VEIC, index=False)
    
    # Inicializa as 15 peças padrão se o arquivo não existir
    if not os.path.exists(ARQ_PECAS):
        pecas_padrao = [
            "1. Paralama dianteiro esquerdo", "2. Paralama dianteiro direito", "3. Párachoque dianteiro",
            "4. Capô", "5. Parabrisa", "6. Teto", "7. Porta dianteiro direito",
            "8. Porta traseira direito", "9. Porta dianteiro esquerdo", "10. Porta traseira esquerdo",
            "11. Paralama traseiro esquerdo", "12. Paralama traseiro direito", "13. Vidro traseiro",
            "14. Párachoque traseiro", "15. Pane mecânica / elétrica"
        ]
        pd.DataFrame({"Item": pecas_padrao}).to_csv(ARQ_PECAS, index=False)

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

# Estados de Edição
if 'edit_v_idx' not in st.session_state: st.session_state.edit_v_idx = -1
if 'edit_m_idx' not in st.session_state: st.session_state.edit_m_idx = -1

tabs = st.tabs(["⚙️ Gestão & Cadastro", "📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"])

# --- ABA 1: GESTÃO & CADASTRO (VEÍCULOS, MOTORISTAS E AVARIAS) ---
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    df_h = carregar(ARQ_HIST)
    
    with c1:
        st.subheader("🚗 Veículos")
        df_v = carregar(ARQ_VEIC)
        with st.expander("➕ Novo/Editar Veículo", expanded=(st.session_state.edit_v_idx != -1)):
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
                        else: 
                            for k, v in nova.items(): df_v.at[v_idx, k] = v
                        salvar(df_v, ARQ_VEIC); st.session_state.edit_v_idx = -1; st.rerun()

        for i, r in df_v.iterrows():
            with st.container(border=True):
                st.write(f"**{r['Veículo']} ({r['Placa']})**")
                cb1, cb2 = st.columns(2)
                if cb1.button("📝", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()
                if cb2.button("🚫", key=f"bv{i}"):
                    df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_v, ARQ_VEIC); st.rerun()

    with c2:
        st.subheader("👤 Motoristas")
        df_m = carregar(ARQ_MOT)
        with st.expander("➕ Novo/Editar Motorista", expanded=(st.session_state.edit_m_idx != -1)):
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
                        else:
                            for k, v in nova.items(): df_m.at[m_idx, k] = v
                        salvar(df_m, ARQ_MOT); st.session_state.edit_m_idx = -1; st.rerun()
        for i, r in df_m.iterrows():
            with st.container(border=True):
                st.write(f"**{r['Nome']}**")
                cm1, cm2 = st.columns(2)
                if cm1.button("📝", key=f"em{i}"): st.session_state.edit_m_idx = i; st.rerun()
                if cm2.button("🚫", key=f"bm{i}"):
                    df_m.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_m, ARQ_MOT); st.rerun()

    with c3:
        st.subheader("📋 Itens de Avaria")
        df_p = carregar(ARQ_PECAS)
        with st.expander("➕ Novo Item de Checklist"):
            with st.form("f_p"):
                n_peca = st.text_input("Descrição do Item (ex: 16. Retrovisor)")
                if st.form_submit_button("Adicionar"):
                    if n_peca:
                        df_p = pd.concat([df_p, pd.DataFrame([{"Item": n_peca}])], ignore_index=True)
                        salvar(df_p, ARQ_PECAS); st.rerun()
        
        for i, r in df_p.iterrows():
            with st.container(border=True):
                cp1, cp2 = st.columns([4, 1])
                cp1.write(r['Item'])
                if cp2.button("🗑️", key=f"dp{i}"):
                    salvar(df_p.drop(i), ARQ_PECAS); st.rerun()

# --- ABA 2: SAÍDA ---
with tabs[1]:
    st.header("📤 Registrar Saída")
    df_v_at = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    df_m_at = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Status'] == "Ativo"]
    pecas_lista = carregar(ARQ_PECAS)['Item'].tolist()
    
    v_escolhido = st.selectbox("Veículo", ["Selecione..."] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_at.iterrows()], index=0)
    m_escolhido = st.selectbox("Motorista", ["Selecione..."] + df_m_at['Nome'].tolist(), index=0)

    if v_escolhido != "Selecione..." and m_escolhido != "Selecione...":
        st.divider()
        st_v = get_status_veiculo(v_escolhido)
        
        # Alertas de Revisão
        placa = v_escolhido.split("(")[1].replace(")", "")
        v_info = df_v_at[df_v_at['Placa'] == placa].iloc[0]
        prox_km = int(v_info['Ult_Revisao_KM']) + int(v_info['Intervalo_KM'])
        saldo_km = prox_km - st_v['km']
        if saldo_km <= 500: st.warning(f"⚠️ Revisão próxima: {prox_km} KM. Faltam {saldo_km} KM.")
        
        # Alerta CNH
        m_info = df_m_at[df_m_at['Nome'] == m_escolhido].iloc[0]
        dt_c = datetime.strptime(str(m_info['Validade_CNH']), '%Y-%m-%d').date()
        if dt_c < date.today(): st.error(f"🚫 CNH vencida em {dt_c.strftime('%d/%m/%Y')}")
        elif st_v["acao"] == "SAÍDA": st.error(f"🚫 Veículo com {st_v['user']}")
        else:
            st.success(f"KM Atual: {st_v['km']}")
            km_sai = st.number_input("KM Inicial", value=st_v['km'], min_value=st_v['km'])
            # Herança dinâmica de avarias baseada na lista da Gestão
            av_bruto = st_v['av'].replace('|', ',')
            d_av = [x.strip() for x in av_bruto.split(',')] if st_v['av'] != "Nenhuma" else []
            checklist = st.multiselect("Checklist de Avarias:", pecas_lista, default=[x for x in d_av if x in pecas_lista])
            
            if st.button("🚀 Confirmar Saída"):
                nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "SAÍDA", "Veículo": v_escolhido, "Usuário": m_escolhido, "KM": km_sai, "CNH": dt_c, "Av_Saida": ", ".join(checklist), "Av_Chegada": "Pendente", "Av_Totais": ", ".join(checklist), "Obs": "", "Foto": "Não"}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.success("Registrado!"); st.rerun()

# --- ABA 3: CHEGADA ---
with tabs[2]:
    st.header("📥 Registrar Chegada")
    v_op = ["Selecione..."] + [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()]
    v_ret = st.selectbox("Veículo", v_op, index=0, key="cheg")
    if v_ret != "Selecione...":
        st_ret = get_status_veiculo(v_ret)
        if st_ret["acao"] == "SAÍDA":
            km_f = st.number_input("KM Final", min_value=st_ret['km'], value=st_ret['km'])
            n_av = st.multiselect("Novas Avarias detectadas:", carregar(ARQ_PECAS)['Item'].tolist())
            if st.button("🏁 Confirmar Chegada"):
                txt_n = ", ".join(n_av) if n_av else "Nenhuma"
                l_b = [st_ret['av']] if st_ret['av'] != "Nenhuma" else []
                if txt_n != "Nenhuma": l_b.append(txt_n)
                nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "CHEGADA", "Veículo": v_ret, "Usuário": st_ret['user'], "KM": km_f, "CNH": "", "Av_Saida": st_ret['av'], "Av_Chegada": txt_n, "Av_Totais": " | ".join(l_b) if l_b else "Nenhuma", "Obs": "Retorno", "Foto": ""}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.success("Registrado!"); st.rerun()
        else: st.info("Veículo no pátio.")

# --- DEMAIS ABAS ---
with tabs[3]:
    st.header("🔧 Oficina")
    v_man = st.selectbox("Veículo", ["Selecione..."] + [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()], key="man")
    if v_man != "Selecione...":
        st_man = get_status_veiculo(v_man)
        if st_man["av"] != "Nenhuma":
            st.warning(f"Avarias: {st_man['av']}")
            if st.button("🛠️ Reparar Tudo"):
                nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "REPARO", "Veículo": v_man, "Usuário": "Oficina", "KM": st_man['km'], "CNH": "", "Av_Saida": "Reparo Geral", "Av_Chegada": "", "Av_Totais": "Nenhuma", "Obs": "Manutenção", "Foto": ""}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.success("Reparado!"); st.rerun()

with tabs[4]:
    st.header("📋 Histórico")
    st.dataframe(carregar(ARQ_HIST).replace(["None", "nan"], ""), use_container_width=True)
