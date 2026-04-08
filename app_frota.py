import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import os
import base64
from io import BytesIO
from PIL import Image

# 1. Configurações Iniciais
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗", layout="wide")

# 2. Arquivos de Dados
ARQ_HIST = "gestao_frota_oficial.csv"
ARQ_VEIC = "cadastro_veiculos.csv"
ARQ_MOT  = "cadastro_motoristas.csv"
ARQ_PECAS = "cadastro_pecas.csv"

# 3. Inicialização e Integridade
def inicializar():
    col_h = ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Valor_Reparo", "Local_Reparo", "Foto_Base64"]
    if not os.path.exists(ARQ_HIST): pd.DataFrame(columns=col_h).to_csv(ARQ_HIST, index=False)
    if not os.path.exists(ARQ_MOT): pd.DataFrame(columns=["Nome", "Validade_CNH", "Status", "Senha", "Admin"]).to_csv(ARQ_MOT, index=False)
    if not os.path.exists(ARQ_VEIC): pd.DataFrame(columns=["Veículo", "Placa", "Ult_Revisao_KM", "Ult_Revisao_Data", "Int_KM", "Int_Meses", "Status"]).to_csv(ARQ_VEIC, index=False)
    if not os.path.exists(ARQ_PECAS): pd.DataFrame(columns=["Item", "Status"]).to_csv(ARQ_PECAS, index=False)

inicializar()

# --- FUNÇÕES CORE ---
def carregar(arq): return pd.read_csv(arq, dtype=str).fillna("")
def salvar(df, arq): df.to_csv(arq, index=False)
def get_dt_br(): return datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

def get_status_veiculo(v_alvo):
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        df_v = df_h[df_h['Veículo'] == v_alvo]
        if not df_v.empty:
            ult = df_v.iloc[-1]
            try: km_val = int(float(ult['KM']))
            except: km_val = 0
            return {"acao": ult['Ação'], "user": ult['Usuário'], "km": km_val, "av": str(ult['Av_Totais'])}
    return {"acao": "CHEGADA", "user": "Ninguém", "km": 0, "av": "Nenhuma"}

def converter_multiplas_fotos(uploaded_files):
    lista_b64 = []
    if uploaded_files:
        for f in uploaded_files:
            img = Image.open(f); img.thumbnail((800, 800))
            buf = BytesIO(); img.save(buf, format="JPEG", quality=70)
            lista_b64.append(base64.b64encode(buf.getvalue()).decode())
    return ";".join(lista_b64)

# --- CONTROLE DE LOGIN ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

if not st.session_state.autenticado:
    st.title("🚗 Gestão de Frota - Login")
    df_m = carregar(ARQ_MOT)
    lista_nomes = sorted(df_m[df_m['Status'] == "Ativo"]['Nome'].unique().tolist())
    if not lista_nomes:
        if st.text_input("Senha Mestra", type="password") == "admin123":
            if st.button("Configurar Primeiro Acesso"):
                st.session_state.autenticado = True; st.session_state.perfil = "admin"; st.session_state.user_logado = "Paulo"; st.rerun()
    else:
        n_sel = st.selectbox("Usuário", [""] + lista_nomes)
        if n_sel:
            dados = df_m[df_m['Nome'] == n_sel].iloc[0]
            senha_dig = st.text_input("Senha", type="password")
            if st.button("Entrar"):
                if senha_dig == "RESET99" or senha_dig == str(dados['Senha']):
                    st.session_state.autenticado = True
                    st.session_state.perfil = "admin" if str(dados['Admin']) == "Sim" else "motorista"
                    st.session_state.user_logado = n_sel; st.rerun()
                else: st.error("Senha Incorreta")
    st.stop()

# --- INTERFACE PRINCIPAL ---
st.title(f"Frota - {st.session_state.user_logado}")
if st.sidebar.button("Sair"): st.session_state.autenticado = False; st.rerun()

abas = ["📤 Saída", "📥 Chegada", "🔧 Oficina", "📋 Histórico"]
if st.session_state.perfil == "admin": abas.insert(0, "⚙️ Gestão")
tabs = st.tabs(abas)
idx_off = 1 if st.session_state.perfil == "admin" else 0

# --- ABA GESTÃO ---
if st.session_state.perfil == "admin":
    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("🚗 Veículos")
            df_v = carregar(ARQ_VEIC)
            with st.form("f_veic"):
                v_mod = st.text_input("Modelo*"); v_pla = st.text_input("Placa*").upper().strip()
                if st.form_submit_button("Cadastrar"):
                    if v_pla in df_v['Placa'].values: st.error("Registro já existente no sistema.")
                    elif v_mod and v_pla:
                        nv = {"Veículo": v_mod, "Placa": v_pla, "Ult_Revisao_KM": "0", "Ult_Revisao_Data": str(date.today()), "Int_KM": "10000", "Int_Meses": "12", "Status": "Ativo"}
                        salvar(pd.concat([df_v, pd.DataFrame([nv])], ignore_index=True), ARQ_VEIC); st.rerun()
            
            for i, r in df_v.iterrows():
                with st.container(border=True):
                    st.write(f"{r['Veículo']} - {r['Placa']} ({r['Status']})")
                    colb1, colb2 = st.columns(2)
                    if colb1.button("🚫 Bloquear" if r['Status']=="Ativo" else "✅ Ativar", key=f"blkv{i}"):
                        df_v.at[i, 'Status'] = "Inativo" if r['Status']=="Ativo" else "Ativo"; salvar(df_v, ARQ_VEIC); st.rerun()
                    if colb2.button("🗑️ Excluir", key=f"delv{i}"):
                        if not carregar(ARQ_HIST)[carregar(ARQ_HIST)['Veículo'].str.contains(r['Placa'])].empty:
                            st.warning("Veículo com histórico não pode ser excluído. Utilize a função de bloqueio.")
                        else: salvar(df_v.drop(i), ARQ_VEIC); st.rerun()

        with c2:
            st.subheader("👤 Usuários")
            df_u = carregar(ARQ_MOT)
            with st.form("f_user"):
                u_n = st.text_input("Nome*"); u_adm = st.selectbox("Admin", ["Não", "Sim"])
                if st.form_submit_button("Cadastrar"):
                    if u_n in df_u['Nome'].values: st.error("Registro já existente no sistema.")
                    elif u_n:
                        nu = {"Nome": u_n, "Validade_CNH": str(date.today() + timedelta(days=365)), "Status": "Ativo", "Senha": "123", "Admin": u_adm}
                        salvar(pd.concat([df_u, pd.DataFrame([nu])], ignore_index=True), ARQ_MOT); st.rerun()
            
            for i, r in df_u.iterrows():
                with st.container(border=True):
                    st.write(f"{r['Nome']} ({r['Status']})")
                    b1, b2, b3 = st.columns(3)
                    if b1.button("🚫", key=f"bu{i}", help="Bloquear"):
                        df_u.at[i, 'Status'] = "Inativo" if r['Status']=="Ativo" else "Ativo"; salvar(df_u, ARQ_MOT); st.rerun()
                    if b2.button("🔑", key=f"rs{i}", help="Reset Senha"):
                        df_u.at[i, 'Senha'] = "123"; salvar(df_u, ARQ_MOT); st.success("Senha: 123")
                    if b3.button("🗑️", key=f"du{i}"): salvar(df_u.drop(i), ARQ_MOT); st.rerun()

        with c3:
            st.subheader("📋 Avarias")
            df_p = carregar(ARQ_PECAS)
            with st.form("f_av"):
                n_p = st.text_input("Nova Avaria")
                if st.form_submit_button("Adicionar"):
                    if n_p in df_p['Item'].values: st.error("Registro já existente no sistema.")
                    elif n_p:
                        salvar(pd.concat([df_p, pd.DataFrame([{"Item": n_p, "Status": "Ativo"}])], ignore_index=True), ARQ_PECAS); st.rerun()
            for i, r in df_p.iterrows():
                if st.button(f"🗑️ {r['Item']}", key=f"dp{i}"): salvar(df_p.drop(i), ARQ_PECAS); st.rerun()

# --- ABAS DE REGISTRO ---
with tabs[0 + idx_off]: # SAÍDA
    st.header("📤 Registrar Saída")
    df_v_disponiveis = carregar(ARQ_VEIC)[carregar(ARQ_VEIC)['Status'] == "Ativo"]
    vs = st.selectbox("Selecione o Veículo", [""] + [f"{r['Veículo']} ({r['Placa']})" for _, r in df_v_disponiveis.iterrows()], key=f"vs_{st.session_state.reset_key}")
    if vs:
        status_atual = get_status_veiculo(vs)
        if status_atual["acao"] == "SAÍDA":
            st.error("Veículo indisponível. Existe uma saída em aberto para este veículo.")
        else:
            ms = st.selectbox("Motorista", [""] + carregar(ARQ_MOT)[carregar(ARQ_MOT)['Status']=="Ativo"]['Nome'].tolist(), key=f"ms_{st.session_state.reset_key}")
            kms = st.number_input("KM Inicial", min_value=status_atual['km'], value=status_atual['km'], key=f"kms_{st.session_state.reset_key}")
            st.info(f"Estado Atual: {status_atual['av']}")
            chk = st.multiselect("Novas Avarias Identificadas", carregar(ARQ_PECAS)['Item'].tolist(), key=f"chk_{st.session_state.reset_key}")
            fts = st.file_uploader("Fotos do Veículo", accept_multiple_files=True, key=f"fts_{st.session_state.reset_key}")
            if st.button("Confirmar Saída"):
                av_finais = list(set([x.strip() for x in status_atual['av'].split(",") if x.strip() != "Nenhuma"] + chk))
                nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "SAÍDA", "Veículo": vs, "Usuário": ms, "KM": str(kms), "Av_Saida": ", ".join(chk), "Av_Totais": ", ".join(av_finais), "Foto_Base64": converter_multiplas_fotos(fts)}])
                salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

with tabs[1 + idx_off]: # CHEGADA
    st.header("📥 Registrar Chegada")
    veic_rua = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["acao"] == "SAÍDA"]
    vr = st.selectbox("Veículo retorno", [""] + veic_rua, key=f"vr_{st.session_state.reset_key}")
    if vr:
        st_r = get_status_veiculo(vr)
        kmf = st.number_input("KM Final", min_value=st_r['km'], value=st_r['km'], key=f"kmf_{st.session_state.reset_key}")
        av_cheg = st.multiselect("Novas Avarias identificadas no retorno", carregar(ARQ_PECAS)['Item'].tolist(), key=f"avc_{st.session_state.reset_key}")
        fts_c = st.file_uploader("Fotos Chegada", accept_multiple_files=True, key=f"ftsc_{st.session_state.reset_key}")
        if st.button("Confirmar Chegada"):
            av_tot = list(set([x.strip() for x in st_r['av'].split(",") if x.strip() != "Nenhuma"] + av_cheg))
            nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "CHEGADA", "Veículo": vr, "Usuário": st_r['user'], "KM": str(kmf), "Av_Chegada": ", ".join(av_cheg), "Av_Totais": ", ".join(av_tot), "Foto_Base64": converter_multiplas_fotos(fts_c)}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

with tabs[2 + idx_off]: # OFICINA
    st.header("🔧 Registro de Oficina")
    df_av = [v for v in [f"{r['Veículo']} ({r['Placa']})" for _, r in carregar(ARQ_VEIC).iterrows()] if get_status_veiculo(v)["av"] != "Nenhuma"]
    v_of = st.selectbox("Veículo para manutenção", [""] + df_av, key=f"vof_{st.session_state.reset_key}")
    if v_of:
        st_of = get_status_veiculo(v_of)
        itens_av = [x.strip() for x in st_of['av'].split(",") if x.strip() != "Nenhuma"]
        reparados = st.multiselect("Itens Reparados", itens_av)
        empresa = st.text_input("Empresa responsável pelo reparo")
        valor = st.number_input("Valor do reparo (R$)", min_value=0.0)
        if st.button("Registrar Reparo na Oficina"):
            restam = [p for p in itens_av if p not in reparados]
            obs_r = f"Reparo realizado por {empresa}. Itens: {', '.join(reparados)}"
            nova = pd.DataFrame([{"Data": get_dt_br(), "Ação": "OFICINA", "Veículo": v_of, "Usuário": st.session_state.user_logado, "KM": str(st_of['km']), "Av_Totais": ", ".join(restam) if restam else "Nenhuma", "Local_Reparo": empresa, "Valor_Reparo": str(valor), "Obs": obs_r}])
            salvar(pd.concat([carregar(ARQ_HIST), nova]), ARQ_HIST); st.session_state.reset_key += 1; st.rerun()

with tabs[3 + idx_off]: # HISTÓRICO
    st.header("📋 Histórico")
    df_h = carregar(ARQ_HIST)
    if not df_h.empty:
        idx = st.selectbox("Detalhes ID:", df_h.index)
        st.dataframe(df_h.drop(columns=["Foto_Base64"]), use_container_width=True)
        fb64 = df_h.iloc[idx]["Foto_Base64"]
        if fb64:
            for f in str(fb64).split(";"):
                if f: st.image(base64.b64decode(f), width=400)
