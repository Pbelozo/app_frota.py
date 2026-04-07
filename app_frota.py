import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import os
import base64
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="Frota Empresa", page_icon="🚗", layout="wide")
st.title("🚗 Gestão de Frota - Oficial V48")

# --- AJUSTE DEFINITIVO DE HORÁRIO BRASÍLIA (UTC-3) ---
def get_data_hora_br():
    fuso_br = timezone(timedelta(hours=-3))
    agora_br = datetime.now(fuso_br)
    return agora_br.strftime("%d/%m/%Y %H:%M")

# --- CONFIGURAÇÃO DE ARQUIVOS ---
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"
ARQ_PECAS = "cadastro_pecas.csv"

def inicializar():
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Foto_Base64"]).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_MOT):
        pd.DataFrame(columns=["Nome", "Validade_CNH", "Status"]).to_csv(ARQ_MOT, index=False)
    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Intervalo_KM", "Status"]).to_csv(ARQ_VEIC, index=False)
    if not os.path.exists(ARQ_PECAS):
        pecas_p = ["1. Capô", "2. Parabrisa", "3. Parachoque Dianteiro", "4. Parachoque Traseiro", "5. Pneus", "6. Teto", "7. Portas Dir", "8. Portas Esq"]
        pd.DataFrame({"Item": pecas_p, "Status": ["Ativo"] * len(pecas_p)}).to_csv(ARQ_PECAS, index=False)
    else:
        # Garante que a coluna Status exista no arquivo de peças
        df_p_check = pd.read_csv(ARQ_PECAS)
        if "Status" not in df_p_check.columns:
            df_p_check["Status"] = "Ativo"
            df_p_check.to_csv(ARQ_PECAS, index=False)

inicializar()

# --- FUNÇÕES CORE ---
def carregar(arq): return pd.read_csv(arq).fillna("")
def salvar(df, arq): df.to_csv(arq, index=False)

def get_status_veiculo(v_alvo):
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        df_v = df_h[df_h['Veículo'] == v_alvo]
        if not df_v.empty:
            ult = df_v.iloc[-1]
            return {"acao": ult['Ação'], "user": ult['Usuário'], "km": int(ult['KM']), "av": str(ult['Av_Totais']) if str(ult['Av_Totais']).strip() != "" else "Nenhuma"}
    df_c = carregar(ARQ_VEIC)
    v_info = df_c[df_c['Veículo'] + " (" + df_c['Placa'] + ")" == v_alvo]
    km_ini = int(v_info.iloc[0]['Ult_Revisao_KM']) if not v_info.empty else 0
    return {"acao": "CHEGADA", "user": "Ninguém", "km": km_ini, "av": "Nenhuma"}

def converter_multiplas_fotos(uploaded_files):
    lista_b64 = []
    if uploaded_files:
        for file in uploaded_files:
            img = Image.open(file)
            img.thumbnail((800, 800))
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=70)
            lista_b64.append(base64.b64encode(buf.getvalue()).decode())
    return ";".join(lista_b64)

# Estados de Edição
if 'edit_v_idx' not in st.session_state: st.session_state.edit_v_idx = -1
if 'edit_m_idx' not in st.session_state: st.session_state.edit_m_idx = -1
if 'edit_p_idx' not in st.session_state: st.session_state.edit_p_idx = -1

tabs = st.tabs(["⚙️ Gestão & Cadastro", "📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"])

# --- ABA 1: GESTÃO ---
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    df_h = carregar(ARQ_HIST)
    
    with c1:
        st.subheader("🚗 Veículos")
        df_v = carregar(ARQ_VEIC)
        with st.expander("➕ Novo/Editar", expanded=(st.session_state.edit_v_idx != -1)):
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
                col_b1, col_b2 = st.columns(2)
                if col_b1.button("📝 Editar", key=f"ev{i}"): st.session_state.edit_v_idx = i; st.rerun()
                if col_b2.button("🚫 Bloquear", key=f"bv{i}"):
                    df_v.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_v, ARQ_VEIC); st.rerun()

    with c2:
        st.subheader("👤 Motoristas")
        df_m = carregar(ARQ_MOT)
        with st.expander("➕ Novo/Editar", expanded=(st.session_state.edit_m_idx != -1)):
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
                col_m1, col_m2 = st.columns(2)
                if col_m1.button("📝 Editar", key=f"em{i}"): st.session_state.edit_m_idx = i; st.rerun()
                if col_m2.button("🚫 Bloquear", key=f"bm{i}"):
                    df_m.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_m, ARQ_MOT); st.rerun()

    with c3:
        st.subheader("📋 Checklist")
        df_p = carregar(ARQ_PECAS)
        with st.expander("➕ Novo/Editar Item", expanded=(st.session_state.edit_p_idx != -1)):
            p_idx = st.session_state.edit_p_idx
            with st.form("f_p"):
                p_v = df_p.iloc[p_idx]['Item'] if p_idx != -1 else ""
                n_p_desc = st.text_input("Descrição da Avaria", value=p_v)
                if st.form_submit_button("Salvar Item"):
                    if n_p_desc:
                        nova_p = {"Item": n_p_desc, "Status": "Ativo"}
                        if p_idx == -1: df_p = pd.concat([df_p, pd.DataFrame([nova_p])], ignore_index=True)
                        else:
                            df_p.at[p_idx, "Item"] = n_p_desc
                        salvar(df_p, ARQ_PECAS); st.session_state.edit_p_idx = -1; st.rerun()
        
        for i, r in df_p.iterrows():
            # Verifica se o item de checklist já foi usado em algum registro
            item_usado = any(r['Item'] in str(hist) for hist in df_h['Av_Totais'])
            with st.container(border=True):
                st.write(f"**{r['Item']}**\nStatus: {r['Status']}")
                cp1, cp2, cp3 = st.columns(3)
                if cp1.button("📝", key=f"ep{i}"): st.session_state.edit_p_idx = i; st.rerun()
                if cp2.button("🚫", key=f"bp{i}"):
                    df_p.at[i, 'Status'] = "Inativo" if r['Status'] == "Ativo" else "Ativo"
                    salvar(df_p, ARQ_PECAS); st.rerun()
                if not item_usado and cp3.button("🗑️", key=f"dp{i}"):
                    salvar(df_p.drop(i), ARQ_PECAS); st.rerun()

# --- ABA 2: SAÍDA ---
with tabs[1]:
    st.header("📤 Registrar Saída")
    df_v_at = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    df_m_at = carregar(ARQ_MOT)[carregar(ARQ_MOT)['Status'] == "Ativo"]
    # Somente itens de checklist ATIVOS aparecem para novos registros
    p_lista = carregar(ARQ_PECAS)[carregar(ARQ_PECAS)['Status'] == "Ativo"]['Item'].tolist()
    
    v_s = st.selectbox("Selecione o Veículo", ["Selecione..."] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_at.iterrows()])
    m_s = st.selectbox("Selecione o Motorista", ["Selecione..."] + df_m_at['Nome'].tolist(), index=0)

    if v_s != "Selecione..." and m_s != "Selecione...":
        st_v = get_status_veiculo(v_s)
        info_m = df_m_at[df_m_at['Nome'] == m_s].iloc[0]
        dt_cnh = datetime.strptime(str(info_m['Validade_CNH']), '%Y-%m-%d').date()
        
        v_info = df_v_at[df_v_at['Placa'] == v_s.split("(")[1].replace(")", "")].iloc[0]
        prox_km = int(v_info['Ult_Revisao_KM']) + int(v_info['Intervalo_KM'])
        if st_v['km'] >= (prox_km - 500): st.warning(f"⚠️ Revisão Próxima: {prox_km} KM")
        
        if dt_cnh < date.today(): st.error("🚫 BLOQUEADO: CNH Vencida!")
        elif st_v["acao"] == "SAÍDA": st.error(f"🚫 BLOQUEADO: Com {st_v['user']}")
        else:
            st.success(f"KM Atual: {st_v['km']} | Avarias Atuais: {st_v['av']}")
            km_sai = st.number_input("KM Inicial", value=st_v['km'], min_value=st_v['km'])
            fotos_s = st.file_uploader("📷 Foto(s) da Saída", type=['jpg','png','jpeg'], accept_multiple_files=True)
            av_bruto = st_v['av'].replace(' | ', ',').replace('|', ',')
            d_av = [x.strip() for x in av_bruto.split(',')] if st_v['av'] != "Nenhuma" else []
            # Combina itens atuais com a lista de ativos para o checklist
            checklist = st.multiselect("Confirmar Avarias Existentes:", list(set(p_lista + d_av)), default=[x for x in d_av])
            
            if st.button("🚀 Confirmar Saída"):
                nova = pd.DataFrame([{
                    "Data": get_data_hora_br(), "Ação": "SAÍDA", "Veículo": v_s, "Usuário": m_s, "KM": km_sai, "CNH": dt_cnh,
                    "Av_Saida": ", ".join(checklist) if checklist else "Nenhuma", "Av_Chegada": "Pendente", "Av_Totais": ", ".join(checklist) if checklist else "Nenhuma", "Obs": "", "Foto_Base64": converter_multiplas_fotos(fotos_s)
                }])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.success("Registrado!"); st.rerun()

# --- ABA 3: CHEGADA ---
with tabs[2]:
    st.header("📥 Registrar Chegada")
    df_hist_atual = carregar(ARQ_HIST)
    veiculos_em_uso = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["acao"] == "SAÍDA"]

    v_ret = st.selectbox("Veículo retornando", ["Selecione..."] + veiculos_em_uso, key="chegada_sel")
    if v_ret != "Selecione...":
        st_ret = get_status_veiculo(v_ret)
        st.warning(f"👤 Motorista: {st_ret['user']} | 📏 KM de Saída: {st_ret['km']}")
        km_f = st.number_input("KM Final", min_value=st_ret['km'], value=st_ret['km'])
        fotos_c = st.file_uploader("📷 Foto(s) da Chegada", type=['jpg','png','jpeg'], accept_multiple_files=True)
        n_av = st.multiselect("Novas Avarias detectadas:", carregar(ARQ_PECAS)[carregar(ARQ_PECAS)['Status'] == "Ativo"]['Item'].tolist())
        
        if st.button("🏁 Confirmar Chegada"):
            txt_n = ", ".join(n_av) if n_av else "Nenhuma"
            l_total = [st_ret['av']] if st_ret['av'] != "Nenhuma" else []
            if txt_n != "Nenhuma": l_total.append(txt_n)
            nova = pd.DataFrame([{
                "Data": get_data_hora_br(), "Ação": "CHEGADA", "Veículo": v_ret, "Usuário": st_ret['user'], "KM": km_f, "CNH": "",
                "Av_Saida": st_ret['av'], "Av_Chegada": txt_n, "Av_Totais": " | ".join(l_total) if l_total else "Nenhuma", "Obs": "Retorno", "Foto_Base64": converter_multiplas_fotos(fotos_c)
            }])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.success("Registrado!"); st.rerun()
    elif not veiculos_em_uso: st.info("✅ Todos os veículos estão no pátio.")

# --- ABA 4: MANUTENÇÃO ---
with tabs[3]:
    st.header("🔧 Oficina / Reparo")
    v_m = st.selectbox("Veículo na oficina", ["Selecione..."] + [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()], key="oficina_sel")
    if v_m != "Selecione...":
        st_m = get_status_veiculo(v_m)
        if st_m["av"] == "Nenhuma": st.success("✅ Sem avarias.")
        else:
            st.warning(f"⚠️ Avarias Atuais: {st_m['av']}")
            av_limpo = st_m['av'].replace(' | ', ',').replace('|', ',')
            lista_atuais = [x.strip() for x in av_limpo.split(',')]
            reparados = st.multiselect("Itens consertados:", lista_atuais)
            if st.button("🛠️ Confirmar Reparo"):
                if reparados:
                    restantes = [item for item in lista_atuais if item not in reparados]
                    nova_av_totais = " | ".join(restantes) if restantes else "Nenhuma"
                    nova = pd.DataFrame([{"Data": get_data_hora_br(), "Ação": "REPARO", "Veículo": v_m, "Usuário": "Oficina", "KM": st_m['km'], "CNH": "", "Av_Saida": f"Reparados: {', '.join(reparados)}", "Av_Chegada": "", "Av_Totais": nova_av_totais, "Obs": "Manutenção", "Foto_Base64": ""}])
                    salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.success("Reparo gravado!"); st.rerun()

# --- ABA 5: HISTÓRICO ---
with tabs[4]:
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        idx_reg = st.selectbox("Ver fotos do registro (ID):", df_h.index)
        col_t, col_f = st.columns([2, 1])
        with col_t: st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        with col_f:
            fotos_b64 = df_h.iloc[idx_reg]["Foto_Base64"]
            if fotos_b64:
                for f in str(fotos_b64).split(";"):
                    if f: st.image(base64.b64decode(f), use_container_width=True)
            else: st.info("Sem fotos.")
