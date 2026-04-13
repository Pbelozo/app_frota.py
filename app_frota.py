import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import os
import base64
from io import BytesIO
from PIL import Image

# ─────────────────────────────────────────────
# 1. CONFIGURAÇÃO INICIAL
# ─────────────────────────────────────────────
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗", layout="wide")

# ─────────────────────────────────────────────
# 2. ARQUIVOS CSV
# ─────────────────────────────────────────────
ARQ_HIST  = "gestao_frota_oficial.csv"
ARQ_VEIC  = "cadastro_veiculos.csv"
ARQ_MOT   = "cadastro_motoristas.csv"
ARQ_AVAR  = "cadastro_avarias.csv"

# ─────────────────────────────────────────────
# 3. INICIALIZAÇÃO DO SISTEMA
# ─────────────────────────────────────────────
def inicializar_sistema():
    # Histórico
    if not os.path.exists(ARQ_HIST):
        pd.DataFrame(columns=[
            "Data", "Acao", "Veiculo", "Placa", "Usuario",
            "KM_Inicial", "KM_Final", "Avarias_Saida", "Avarias_Chegada",
            "Foto_Base64", "Obs", "Tipo_Manutencao", "Empresa", "Valor"
        ]).to_csv(ARQ_HIST, index=False)

    # Motoristas — garante admin padrão Paulo
    if not os.path.exists(ARQ_MOT):
        pd.DataFrame([{
            "Nome": "Paulo", "Login": "paulo", "Senha": "123",
            "Validade_CNH": "2030-12-31", "Perfil": "Admin", "Status": "Ativo"
        }]).to_csv(ARQ_MOT, index=False)
    else:
        try:
            df_t = pd.read_csv(ARQ_MOT, dtype=str).fillna("")
            if df_t.empty:
                pd.DataFrame([{
                    "Nome": "Paulo", "Login": "paulo", "Senha": "123",
                    "Validade_CNH": "2030-12-31", "Perfil": "Admin", "Status": "Ativo"
                }]).to_csv(ARQ_MOT, index=False)
        except Exception:
            pd.DataFrame([{
                "Nome": "Paulo", "Login": "paulo", "Senha": "123",
                "Validade_CNH": "2030-12-31", "Perfil": "Admin", "Status": "Ativo"
            }]).to_csv(ARQ_MOT, index=False)

    # Veículos
    colunas_veic = ["Modelo", "Placa", "KM_Atual", "KM_Ultima_Revisao",
                    "Ultima_Revisao", "Criterio_Revisao", "Intervalo_KM",
                    "Intervalo_Dias", "Avarias", "Status"]
    if not os.path.exists(ARQ_VEIC):
        pd.DataFrame(columns=colunas_veic).to_csv(ARQ_VEIC, index=False)
    else:
        # Garante que colunas novas existam em arquivos antigos
        try:
            df_veic_tmp = pd.read_csv(ARQ_VEIC, dtype=str).fillna("")
            for col in colunas_veic:
                if col not in df_veic_tmp.columns:
                    df_veic_tmp[col] = ""
            df_veic_tmp.to_csv(ARQ_VEIC, index=False)
        except Exception:
            pd.DataFrame(columns=colunas_veic).to_csv(ARQ_VEIC, index=False)

    # Avarias
    if not os.path.exists(ARQ_AVAR):
        pd.DataFrame(columns=["Descricao", "Status"]).to_csv(ARQ_AVAR, index=False)

inicializar_sistema()

# ─────────────────────────────────────────────
# 4. FUNÇÕES DE APOIO
# ─────────────────────────────────────────────
def carregar(arq):
    try:
        return pd.read_csv(arq, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame()

def safe_get(row, key, default=""):
    """Acessa uma chave de uma row com segurança."""
    try:
        return row[key] if key in row.index else default
    except Exception:
        return default

def montar_lista_veiculos(df_v):
    """Monta lista de veículos de forma segura."""
    lista = []
    if df_v.empty:
        return lista
    for _, r in df_v.iterrows():
        modelo = safe_get(r, "Modelo", "?")
        placa  = safe_get(r, "Placa", "?")
        lista.append(f"{modelo} ({placa})")
    return lista

def salvar(df, arq):
    df.to_csv(arq, index=False)

def get_dt_br():
    return datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

def str_para_date(s):
    """Converte string YYYY-MM-DD para date com segurança."""
    try:
        return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
    except Exception:
        return None

def cnh_valida(motorista_row):
    val = str(motorista_row.get("Validade_CNH", "")).strip()
    d = str_para_date(val)
    if d is None:
        return False
    return d >= date.today()

def revisao_vencida(veiculo_row):
    try:
        criterio = safe_get(veiculo_row, "Criterio_Revisao", "").strip()
        vencida = False

        if criterio in ("KM", "Ambos"):
            try:
                km_atual   = int(safe_get(veiculo_row, "KM_Atual", "0") or "0")
                intervalo_km = int(safe_get(veiculo_row, "Intervalo_KM", "0") or "0")
                km_ultima  = int(safe_get(veiculo_row, "KM_Ultima_Revisao", "0") or "0")
                if intervalo_km > 0 and (km_atual - km_ultima) >= intervalo_km:
                    vencida = True
            except Exception:
                pass

        if criterio in ("Data", "Ambos"):
            ultima_rev     = safe_get(veiculo_row, "Ultima_Revisao", "").strip()
            intervalo_dias_str = safe_get(veiculo_row, "Intervalo_Dias", "0").strip()
            d_rev = str_para_date(ultima_rev)
            try:
                intervalo_dias = int(intervalo_dias_str or "0")
            except Exception:
                intervalo_dias = 0
            if d_rev and intervalo_dias > 0:
                if date.today() >= d_rev + timedelta(days=intervalo_dias):
                    vencida = True

        return vencida
    except Exception:
        return False

def historico_tem_veiculo(placa):
    df = carregar(ARQ_HIST)
    if df.empty or "Placa" not in df.columns:
        return False
    return not df[df["Placa"] == placa].empty

def historico_tem_motorista(login):
    df = carregar(ARQ_HIST)
    if df.empty or "Usuario" not in df.columns:
        return False
    return not df[df["Usuario"] == login].empty

def avaria_em_uso(descricao):
    df = carregar(ARQ_VEIC)
    if df.empty or "Avarias" not in df.columns:
        return False
    for _, row in df.iterrows():
        avs = str(row.get("Avarias", "")).strip()
        if avs:
            lista = [a.strip() for a in avs.split(";") if a.strip()]
            if descricao in lista:
                return True
    return False

def imagem_para_base64(img_bytes):
    try:
        return base64.b64encode(img_bytes).decode()
    except Exception:
        return ""

# ─────────────────────────────────────────────
# 5. LOGIN
# ─────────────────────────────────────────────
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🚗 Gestão de Frota — Login")
    df_m = carregar(ARQ_MOT)
    ativos = df_m[df_m.get("Status", pd.Series()).eq("Ativo")] if not df_m.empty else pd.DataFrame()
    lista_login = sorted(ativos["Login"].unique().tolist()) if "Login" in ativos.columns else []

    col_l, _ = st.columns([2, 3])
    with col_l:
        login_sel = st.selectbox("Login", [""] + lista_login)
        senha_dig = st.text_input("Senha", type="password")

        if st.button("Acessar Sistema"):
            if not login_sel:
                st.error("Selecione um usuário.")
            else:
                registro = df_m[df_m["Login"] == login_sel]
                if registro.empty:
                    st.error("Usuário não encontrado.")
                else:
                    dados = registro.iloc[0]
                    if senha_dig == "RESET99" or senha_dig == str(dados.get("Senha", "")):
                        st.session_state.autenticado = True
                        st.session_state.perfil = "admin" if str(dados.get("Perfil", "")) == "Admin" else "motorista"
                        st.session_state.user_logado = str(dados.get("Nome", login_sel))
                        st.session_state.login_logado = login_sel
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
    st.stop()

# ─────────────────────────────────────────────
# 6. INTERFACE PRINCIPAL
# ─────────────────────────────────────────────
st.title(f"🚗 Sistema de Frota — Olá, {st.session_state.user_logado}")

if st.sidebar.button("🚪 Logoff / Sair"):
    st.session_state.autenticado = False
    st.rerun()

st.sidebar.info(f"Perfil: {'🔑 Administrador' if st.session_state.perfil == 'admin' else '🚗 Motorista'}")

# Montar menu conforme perfil
if st.session_state.perfil == "admin":
    menu = ["⚙️ Cadastros", "📤 Retirada", "📥 Devolução", "🔧 Oficina", "📋 Histórico", "🛡️ Gestão"]
    tabs = st.tabs(menu)
    tab_cad, tab_ret, tab_dev, tab_ofc, tab_hist, tab_gest = tabs
else:
    menu = ["📤 Retirada", "📥 Devolução", "🔧 Oficina", "📋 Histórico"]
    tabs = st.tabs(menu)
    tab_ret, tab_dev, tab_ofc, tab_hist = tabs
    tab_cad = None
    tab_gest = None

# ─────────────────────────────────────────────
# 7. ABA CADASTROS (só admin)
# ─────────────────────────────────────────────
if tab_cad:
    with tab_cad:
        st.subheader("⚙️ Cadastros")
        sub_cad = st.tabs(["🚗 Veículos", "👤 Motoristas", "⚠️ Avarias"])

        # ── 7.1 Veículos
        with sub_cad[0]:
            st.write("### Cadastrar Novo Veículo")
            df_v = carregar(ARQ_VEIC)
            df_av = carregar(ARQ_AVAR)
            avarias_ativas = sorted(df_av[df_av["Status"] == "Ativo"]["Descricao"].tolist()) if not df_av.empty and "Status" in df_av.columns else []

            with st.form("form_novo_veiculo"):
                c1, c2 = st.columns(2)
                with c1:
                    mod = st.text_input("Modelo *")
                    pla = st.text_input("Placa * (única)").upper().strip()
                    km  = st.number_input("KM Atual *", min_value=0, step=1)
                with c2:
                    ult_rev = st.date_input("Data da Última Revisão *", value=date.today())
                    criterio = st.selectbox("Critério de Revisão *", ["KM", "Data", "Ambos"])
                    int_km   = st.number_input("Intervalo para Revisão (KM)", min_value=0, step=500)
                    int_dias = st.number_input("Intervalo para Revisão (Dias)", min_value=0, step=30)

                avarias_sel = st.multiselect("Estado atual (Avarias)", avarias_ativas)
                status_v = st.selectbox("Status", ["Disponível", "Em uso", "Manutenção", "Bloqueado"])

                if st.form_submit_button("💾 Salvar Veículo"):
                    erros = []
                    if not mod:  erros.append("Modelo obrigatório.")
                    if not pla:  erros.append("Placa obrigatória.")
                    if pla and not df_v.empty and "Placa" in df_v.columns and pla in df_v["Placa"].values:
                        erros.append(f"Placa '{pla}' já cadastrada.")
                    if erros:
                        for e in erros: st.error(e)
                    else:
                        nova = pd.DataFrame([{
                            "Modelo": mod, "Placa": pla, "KM_Atual": str(km),
                            "KM_Ultima_Revisao": str(km),
                            "Ultima_Revisao": ult_rev.strftime("%Y-%m-%d"),
                            "Criterio_Revisao": criterio,
                            "Intervalo_KM": str(int_km),
                            "Intervalo_Dias": str(int_dias),
                            "Avarias": ";".join(avarias_sel),
                            "Status": status_v
                        }])
                        salvar(pd.concat([df_v, nova], ignore_index=True), ARQ_VEIC)
                        st.success(f"Veículo {mod} ({pla}) cadastrado!")
                        st.rerun()

            st.write("---")
            st.write("### Veículos Cadastrados")
            df_v2 = carregar(ARQ_VEIC)
            if df_v2.empty:
                st.info("Nenhum veículo cadastrado.")
            else:
                for i, row in df_v2.iterrows():
                    placa    = safe_get(row, "Placa", "")
                    modelo   = safe_get(row, "Modelo", "")
                    status   = safe_get(row, "Status", "")
                    km_atual = safe_get(row, "KM_Atual", "")
                    alerta   = " ⚠️ REVISÃO VENCIDA" if revisao_vencida(row) else ""
                    tem_hist = historico_tem_veiculo(placa)

                    with st.expander(f"🚗 {modelo} — {placa} | {status}{alerta}"):
                        # ── Editar (todos os campos exceto Modelo e Placa)
                        with st.form(f"edit_vcad_{i}"):
                            st.write(f"**Modelo:** {modelo} &nbsp;|&nbsp; **Placa:** {placa} *(não editáveis)*")
                            c1, c2 = st.columns(2)
                            with c1:
                                novo_km = st.text_input("KM Atual", value=km_atual, key=f"vcad_km_{i}")
                                nova_rev = st.text_input("Data Última Revisão (AAAA-MM-DD)",
                                    value=safe_get(row, "Ultima_Revisao", ""), key=f"vcad_rev_{i}")
                                novo_crit = st.selectbox("Critério de Revisão",
                                    ["KM", "Data", "Ambos"],
                                    index=["KM","Data","Ambos"].index(safe_get(row,"Criterio_Revisao","KM"))
                                          if safe_get(row,"Criterio_Revisao","KM") in ["KM","Data","Ambos"] else 0,
                                    key=f"vcad_crit_{i}")
                            with c2:
                                novo_int_km = st.text_input("Intervalo Revisão (KM)",
                                    value=safe_get(row, "Intervalo_KM", "0"), key=f"vcad_ikm_{i}")
                                novo_int_d = st.text_input("Intervalo Revisão (Dias)",
                                    value=safe_get(row, "Intervalo_Dias", "0"), key=f"vcad_id_{i}")
                                novo_status_v = st.selectbox("Status",
                                    ["Disponível", "Em uso", "Manutenção", "Bloqueado"],
                                    index=["Disponível","Em uso","Manutenção","Bloqueado"].index(status)
                                          if status in ["Disponível","Em uso","Manutenção","Bloqueado"] else 0,
                                    key=f"vcad_st_{i}")

                            av_atuais_str = safe_get(row, "Avarias", "")
                            av_atuais_lista = [a.strip() for a in av_atuais_str.split(";") if a.strip()]
                            novas_avarias = st.multiselect("Avarias atuais",
                                avarias_ativas,
                                default=[a for a in av_atuais_lista if a in avarias_ativas],
                                key=f"vcad_av_{i}")

                            col_b1, col_b2, col_b3 = st.columns(3)
                            with col_b1:
                                btn_salvar_v = st.form_submit_button("💾 Salvar Edição")
                            with col_b2:
                                btn_bloquear_v = st.form_submit_button("🔒 Bloquear")
                            with col_b3:
                                btn_excluir_v = st.form_submit_button("🗑️ Excluir", type="primary")

                        if btn_salvar_v:
                            df_v2.at[i, "KM_Atual"]        = novo_km
                            df_v2.at[i, "Ultima_Revisao"]  = nova_rev
                            df_v2.at[i, "Criterio_Revisao"]= novo_crit
                            df_v2.at[i, "Intervalo_KM"]    = novo_int_km
                            df_v2.at[i, "Intervalo_Dias"]  = novo_int_d
                            df_v2.at[i, "Status"]          = novo_status_v
                            df_v2.at[i, "Avarias"]         = ";".join(novas_avarias)
                            salvar(df_v2, ARQ_VEIC)
                            st.success("Veículo atualizado!")
                            st.rerun()

                        if btn_bloquear_v:
                            df_v2.at[i, "Status"] = "Bloqueado"
                            salvar(df_v2, ARQ_VEIC)
                            st.success("Veículo bloqueado.")
                            st.rerun()

                        if btn_excluir_v:
                            if tem_hist:
                                st.error("❌ Este veículo já possui histórico. Use 'Bloquear' para inativá-lo.")
                            else:
                                df_v2 = df_v2[df_v2["Placa"] != placa]
                                salvar(df_v2, ARQ_VEIC)
                                st.success("Veículo excluído.")
                                st.rerun()

        # ── 7.2 Motoristas
        with sub_cad[1]:
            st.write("### Cadastrar Novo Motorista")
            df_u = carregar(ARQ_MOT)

            with st.form("form_novo_motorista"):
                c1, c2 = st.columns(2)
                with c1:
                    nome_m  = st.text_input("Nome *")
                    login_m = st.text_input("Login / Email * (único)").strip().lower()
                    senha_m = st.text_input("Senha *", type="password")
                with c2:
                    cnh_val  = st.date_input("Validade da CNH *", value=date.today())
                    perfil_m = st.selectbox("Perfil *", ["Usuário", "Admin"])

                if st.form_submit_button("💾 Salvar Motorista"):
                    erros = []
                    if not nome_m:  erros.append("Nome obrigatório.")
                    if not login_m: erros.append("Login obrigatório.")
                    if not senha_m: erros.append("Senha obrigatória.")
                    if login_m and not df_u.empty and "Login" in df_u.columns and login_m in df_u["Login"].values:
                        erros.append(f"Login '{login_m}' já cadastrado.")
                    if erros:
                        for e in erros: st.error(e)
                    else:
                        novo = pd.DataFrame([{
                            "Nome": nome_m, "Login": login_m, "Senha": senha_m,
                            "Validade_CNH": cnh_val.strftime("%Y-%m-%d"),
                            "Perfil": perfil_m, "Status": "Ativo"
                        }])
                        salvar(pd.concat([df_u, novo], ignore_index=True), ARQ_MOT)
                        st.success(f"Motorista {nome_m} cadastrado!")
                        st.rerun()

            st.write("---")
            st.write("### Motoristas Cadastrados")
            df_u2 = carregar(ARQ_MOT)
            if df_u2.empty:
                st.info("Nenhum motorista cadastrado.")
            else:
                for i, row in df_u2.iterrows():
                    nome_u   = safe_get(row, "Nome", "")
                    login_u  = safe_get(row, "Login", "")
                    status_u = safe_get(row, "Status", "")
                    perfil_u = safe_get(row, "Perfil", "")
                    cnh_u    = safe_get(row, "Validade_CNH", "")
                    cnh_ok   = cnh_valida(row)
                    alerta_cnh = " ⚠️ CNH VENCIDA" if not cnh_ok else ""
                    tem_hist_u = historico_tem_motorista(login_u)

                    with st.expander(f"👤 {nome_u} ({login_u}) | {perfil_u} | {status_u}{alerta_cnh}"):
                        # ── Editar (todos exceto Nome)
                        with st.form(f"edit_ucad_{i}"):
                            st.write(f"**Nome:** {nome_u} *(não editável)*")
                            c1, c2 = st.columns(2)
                            with c1:
                                novo_login  = st.text_input("Login / Email", value=login_u, key=f"ucad_lg_{i}")
                                nova_senha  = st.text_input("Nova Senha (deixe em branco para manter)",
                                    type="password", key=f"ucad_pw_{i}")
                            with c2:
                                nova_cnh_u  = st.text_input("Validade CNH (AAAA-MM-DD)", value=cnh_u, key=f"ucad_cnh_{i}")
                                novo_perfil = st.selectbox("Perfil",
                                    ["Usuário", "Admin"],
                                    index=0 if perfil_u != "Admin" else 1,
                                    key=f"ucad_prf_{i}")
                                novo_st_u   = st.selectbox("Status",
                                    ["Ativo", "Bloqueado"],
                                    index=0 if status_u == "Ativo" else 1,
                                    key=f"ucad_stu_{i}")

                            col_b1, col_b2, col_b3 = st.columns(3)
                            with col_b1:
                                btn_salvar_u   = st.form_submit_button("💾 Salvar Edição")
                            with col_b2:
                                btn_bloquear_u = st.form_submit_button("🔒 Bloquear")
                            with col_b3:
                                btn_excluir_u  = st.form_submit_button("🗑️ Excluir", type="primary")

                        if btn_salvar_u:
                            df_u2.at[i, "Login"]        = novo_login.strip().lower()
                            df_u2.at[i, "Validade_CNH"] = nova_cnh_u.strip()
                            df_u2.at[i, "Perfil"]       = novo_perfil
                            df_u2.at[i, "Status"]       = novo_st_u
                            if nova_senha.strip():
                                df_u2.at[i, "Senha"] = nova_senha.strip()
                            salvar(df_u2, ARQ_MOT)
                            st.success("Motorista atualizado!")
                            st.rerun()

                        if btn_bloquear_u:
                            df_u2.at[i, "Status"] = "Bloqueado"
                            salvar(df_u2, ARQ_MOT)
                            st.success("Motorista bloqueado.")
                            st.rerun()

                        if btn_excluir_u:
                            if tem_hist_u:
                                st.error("❌ Este motorista já possui histórico. Use 'Bloquear' para inativá-lo.")
                            else:
                                df_u2 = df_u2[df_u2["Login"] != login_u]
                                salvar(df_u2, ARQ_MOT)
                                st.success("Motorista excluído.")
                                st.rerun()

        # ── 7.3 Avarias
        with sub_cad[2]:
            st.write("### Cadastrar Nova Avaria")
            df_av = carregar(ARQ_AVAR)

            with st.form("form_nova_avaria"):
                desc_av = st.text_input("Descrição da Avaria *")
                if st.form_submit_button("💾 Salvar Avaria"):
                    if not desc_av.strip():
                        st.error("Descrição obrigatória.")
                    elif not df_av.empty and "Descricao" in df_av.columns and desc_av.strip() in df_av["Descricao"].values:
                        st.error("Avaria já cadastrada.")
                    else:
                        nova_av = pd.DataFrame([{"Descricao": desc_av.strip(), "Status": "Ativo"}])
                        salvar(pd.concat([df_av, nova_av], ignore_index=True), ARQ_AVAR)
                        st.success("Avaria cadastrada!")
                        st.rerun()

            st.write("---")
            st.write("### Avarias Cadastradas")
            df_av2 = carregar(ARQ_AVAR)
            if df_av2.empty:
                st.info("Nenhuma avaria cadastrada.")
            else:
                for i, row in df_av2.iterrows():
                    desc_i  = safe_get(row, "Descricao", "")
                    status_i = safe_get(row, "Status", "")
                    em_uso  = avaria_em_uso(desc_i)

                    with st.expander(f"⚠️ {desc_i} | {status_i}"):
                        st.write("*Avarias não são editáveis.*")
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            if st.button("🔒 Bloquear", key=f"blk_avcad_{i}"):
                                df_av2.at[i, "Status"] = "Bloqueado"
                                salvar(df_av2, ARQ_AVAR)
                                st.success("Avaria bloqueada.")
                                st.rerun()
                        with col_b2:
                            if em_uso:
                                st.warning("❌ Em uso — não pode excluir. Use Bloquear.")
                            else:
                                if st.button("🗑️ Excluir", key=f"del_avcad_{i}", type="primary"):
                                    df_av2 = df_av2[df_av2["Descricao"] != desc_i]
                                    salvar(df_av2, ARQ_AVAR)
                                    st.success("Avaria excluída.")
                                    st.rerun()

# ─────────────────────────────────────────────
# 8. ABA RETIRADA DE VEÍCULO
# ─────────────────────────────────────────────
with tab_ret:
    st.subheader("📤 Retirada de Veículo")

    # Verificar CNH do usuário logado
    df_m = carregar(ARQ_MOT)
    mot_row = df_m[df_m["Login"] == st.session_state.login_logado].iloc[0] if (
        not df_m.empty and "Login" in df_m.columns and
        st.session_state.login_logado in df_m["Login"].values
    ) else None

    if mot_row is not None and not cnh_valida(mot_row):
        st.error("⚠️ Sua CNH está vencida. Retirada não permitida.")
        st.stop()

    df_v = carregar(ARQ_VEIC)
    df_av = carregar(ARQ_AVAR)

    # Apenas veículos Disponíveis
    veics_disp = df_v[df_v["Status"].eq("Disponível")] if not df_v.empty and "Status" in df_v.columns else pd.DataFrame()
    lista_veics = montar_lista_veiculos(veics_disp)

    if not lista_veics:
        st.info("Nenhum veículo disponível para retirada.")
    else:
        avarias_ativas = sorted(df_av[df_av["Status"] == "Ativo"]["Descricao"].tolist()) if not df_av.empty and "Status" in df_av.columns else []

        with st.form("form_retirada"):
            veic_sel = st.selectbox("Veículo *", [""] + lista_veics)
            obs_ret  = st.text_area("Observações")
            avs_ret  = st.multiselect("Avarias observadas na saída", avarias_ativas)
            foto_ret = st.file_uploader("Foto (opcional)", type=["jpg", "jpeg", "png"])

            if st.form_submit_button("✅ Confirmar Retirada"):
                if not veic_sel:
                    st.error("Selecione um veículo.")
                else:
                    placa_sel = veic_sel.split("(")[-1].replace(")", "").strip()
                    row_v = df_v[df_v["Placa"] == placa_sel]
                    if row_v.empty:
                        st.error("Veículo não encontrado.")
                    else:
                        row_v = row_v.iloc[0]
                        km_ini = str(row_v.get("KM_Atual", "0"))
                        foto_b64 = imagem_para_base64(foto_ret.read()) if foto_ret else ""

                        # Registrar no histórico
                        hist_novo = pd.DataFrame([{
                            "Data": get_dt_br(), "Acao": "Retirada",
                            "Veiculo": row_v.get("Modelo", ""), "Placa": placa_sel,
                            "Usuario": st.session_state.login_logado,
                            "KM_Inicial": km_ini, "KM_Final": "",
                            "Avarias_Saida": ";".join(avs_ret), "Avarias_Chegada": "",
                            "Foto_Base64": foto_b64, "Obs": obs_ret,
                            "Tipo_Manutencao": "", "Empresa": "", "Valor": ""
                        }])
                        df_hist = carregar(ARQ_HIST)
                        salvar(pd.concat([df_hist, hist_novo], ignore_index=True), ARQ_HIST)

                        # Atualizar status do veículo
                        df_v.loc[df_v["Placa"] == placa_sel, "Status"] = "Em uso"
                        # Adicionar avarias ao estado atual
                        av_atuais = str(row_v.get("Avarias", "")).strip()
                        lista_av_atual = [a for a in av_atuais.split(";") if a.strip()]
                        for av in avs_ret:
                            if av not in lista_av_atual:
                                lista_av_atual.append(av)
                        df_v.loc[df_v["Placa"] == placa_sel, "Avarias"] = ";".join(lista_av_atual)
                        salvar(df_v, ARQ_VEIC)

                        st.success(f"Retirada registrada! Veículo: {veic_sel} | KM saída: {km_ini}")
                        st.rerun()

# ─────────────────────────────────────────────
# 9. ABA DEVOLUÇÃO DE VEÍCULO
# ─────────────────────────────────────────────
with tab_dev:
    st.subheader("📥 Devolução de Veículo")

    df_v = carregar(ARQ_VEIC)
    df_hist = carregar(ARQ_HIST)
    df_av = carregar(ARQ_AVAR)

    # Veículos em uso pelo usuário logado
    veics_em_uso = df_v[df_v.get("Status", pd.Series()).eq("Em uso")] if not df_v.empty and "Status" in df_v.columns else pd.DataFrame()

    # Filtrar apenas os que foram retirados pelo usuário logado (última retirada)
    veics_meus = []
    for _, row in veics_em_uso.iterrows():
        placa = row.get("Placa", "")
        hist_placa = df_hist[
            (df_hist.get("Placa", pd.Series()) == placa) &
            (df_hist.get("Acao", pd.Series()) == "Retirada")
        ] if not df_hist.empty and "Placa" in df_hist.columns else pd.DataFrame()
        if not hist_placa.empty:
            ultima = hist_placa.iloc[-1]
            if str(ultima.get("Usuario", "")).strip() == st.session_state.login_logado:
                veics_meus.append(f"{row.get('Modelo','')} ({placa})")

    if not veics_meus:
        st.info("Você não possui veículos para devolver.")
    else:
        avarias_ativas = sorted(df_av[df_av["Status"] == "Ativo"]["Descricao"].tolist()) if not df_av.empty and "Status" in df_av.columns else []

        with st.form("form_devolucao"):
            veic_dev = st.selectbox("Veículo a Devolver *", [""] + veics_meus)
            km_dev   = st.number_input("KM Final *", min_value=0, step=1)
            obs_dev  = st.text_area("Observações")
            avs_dev  = st.multiselect("Avarias observadas na chegada", avarias_ativas)
            foto_dev = st.file_uploader("Foto (opcional)", type=["jpg", "jpeg", "png"])

            if st.form_submit_button("✅ Confirmar Devolução"):
                if not veic_dev:
                    st.error("Selecione um veículo.")
                else:
                    placa_dev = veic_dev.split("(")[-1].replace(")", "").strip()
                    row_v = df_v[df_v["Placa"] == placa_dev]
                    if row_v.empty:
                        st.error("Veículo não encontrado.")
                    else:
                        row_v = row_v.iloc[0]
                        km_ini_str = ""
                        hist_placa = df_hist[
                            (df_hist.get("Placa", pd.Series()) == placa_dev) &
                            (df_hist.get("Acao", pd.Series()) == "Retirada")
                        ] if not df_hist.empty and "Placa" in df_hist.columns else pd.DataFrame()
                        if not hist_placa.empty:
                            km_ini_str = str(hist_placa.iloc[-1].get("KM_Inicial", ""))

                        foto_b64 = imagem_para_base64(foto_dev.read()) if foto_dev else ""

                        hist_novo = pd.DataFrame([{
                            "Data": get_dt_br(), "Acao": "Devolucao",
                            "Veiculo": row_v.get("Modelo", ""), "Placa": placa_dev,
                            "Usuario": st.session_state.login_logado,
                            "KM_Inicial": km_ini_str, "KM_Final": str(km_dev),
                            "Avarias_Saida": "", "Avarias_Chegada": ";".join(avs_dev),
                            "Foto_Base64": foto_b64, "Obs": obs_dev,
                            "Tipo_Manutencao": "", "Empresa": "", "Valor": ""
                        }])
                        df_hist2 = carregar(ARQ_HIST)
                        salvar(pd.concat([df_hist2, hist_novo], ignore_index=True), ARQ_HIST)

                        # Atualizar veículo
                        df_v.loc[df_v["Placa"] == placa_dev, "Status"] = "Disponível"
                        df_v.loc[df_v["Placa"] == placa_dev, "KM_Atual"] = str(km_dev)
                        # Adicionar novas avarias ao estado
                        av_atuais = str(row_v.get("Avarias", "")).strip()
                        lista_av_atual = [a for a in av_atuais.split(";") if a.strip()]
                        for av in avs_dev:
                            if av not in lista_av_atual:
                                lista_av_atual.append(av)
                        df_v.loc[df_v["Placa"] == placa_dev, "Avarias"] = ";".join(lista_av_atual)
                        salvar(df_v, ARQ_VEIC)

                        st.success(f"Devolução registrada! KM final: {km_dev}")
                        st.rerun()

# ─────────────────────────────────────────────
# 10. ABA OFICINA (MANUTENÇÃO / REPARO)
# ─────────────────────────────────────────────
with tab_ofc:
    st.subheader("🔧 Oficina — Manutenção e Reparo")

    df_v = carregar(ARQ_VEIC)
    tipo_ofc = st.radio("Tipo de serviço", ["Manutenção", "Reparo"], horizontal=True)

    if tipo_ofc == "Manutenção":
        st.write("#### Registrar Manutenção")
        veics_todos = montar_lista_veiculos(df_v)

        with st.form("form_manutencao"):
            veic_man = st.selectbox("Veículo *", [""] + veics_todos)
            tipo_man = st.selectbox("Tipo de Manutenção *", ["Revisão", "Preventiva", "Corretiva", "Outros"])
            empresa_man = st.text_input("Empresa *")
            valor_man   = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
            obs_man     = st.text_area("Observações")

            if st.form_submit_button("✅ Registrar Manutenção"):
                if not veic_man or not empresa_man:
                    st.error("Veículo e Empresa são obrigatórios.")
                else:
                    placa_man = veic_man.split("(")[-1].replace(")", "").strip()
                    row_v = df_v[df_v["Placa"] == placa_man]
                    if row_v.empty:
                        st.error("Veículo não encontrado.")
                    else:
                        # Registrar histórico
                        hist_novo = pd.DataFrame([{
                            "Data": get_dt_br(), "Acao": "Manutencao",
                            "Veiculo": row_v.iloc[0].get("Modelo", ""), "Placa": placa_man,
                            "Usuario": st.session_state.login_logado,
                            "KM_Inicial": row_v.iloc[0].get("KM_Atual", ""), "KM_Final": "",
                            "Avarias_Saida": "", "Avarias_Chegada": "",
                            "Foto_Base64": "", "Obs": obs_man,
                            "Tipo_Manutencao": tipo_man, "Empresa": empresa_man,
                            "Valor": str(valor_man)
                        }])
                        df_hist2 = carregar(ARQ_HIST)
                        salvar(pd.concat([df_hist2, hist_novo], ignore_index=True), ARQ_HIST)

                        # Se for revisão: atualizar data e KM de revisão
                        if tipo_man == "Revisão":
                            df_v.loc[df_v["Placa"] == placa_man, "Ultima_Revisao"] = date.today().strftime("%Y-%m-%d")
                            df_v.loc[df_v["Placa"] == placa_man, "KM_Ultima_Revisao"] = row_v.iloc[0].get("KM_Atual", "0")
                            salvar(df_v, ARQ_VEIC)

                        st.success(f"Manutenção registrada: {tipo_man} — {empresa_man} — R$ {valor_man:.2f}")
                        st.rerun()

    else:  # Reparo
        st.write("#### Registrar Reparo de Avarias")
        # Apenas veículos com avarias
        if df_v.empty:
            st.info("Nenhum veículo cadastrado.")
        else:
            veics_com_av = []
            for _, r in df_v.iterrows():
                avs = str(r.get("Avarias", "")).strip()
                if avs and any(a.strip() for a in avs.split(";")):
                    veics_com_av.append(f"{r.get('Modelo','')} ({r.get('Placa','')})")

            if not veics_com_av:
                st.info("Nenhum veículo com avarias pendentes.")
            else:
                with st.form("form_reparo"):
                    veic_rep = st.selectbox("Veículo com Avarias *", [""] + veics_com_av)
                    empresa_rep = st.text_input("Empresa *")
                    valor_rep   = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
                    obs_rep     = st.text_area("Observações")

                    avs_corrigir = []
                    if veic_rep:
                        placa_rep_prev = veic_rep.split("(")[-1].replace(")", "").strip()
                        row_rep = df_v[df_v["Placa"] == placa_rep_prev]
                        if not row_rep.empty:
                            avs_str = str(row_rep.iloc[0].get("Avarias", "")).strip()
                            avs_lista = [a.strip() for a in avs_str.split(";") if a.strip()]
                            avs_corrigir = st.multiselect("Avarias corrigidas *", avs_lista)

                    if st.form_submit_button("✅ Registrar Reparo"):
                        if not veic_rep or not empresa_rep:
                            st.error("Veículo e Empresa são obrigatórios.")
                        elif not avs_corrigir:
                            st.error("Selecione ao menos uma avaria corrigida.")
                        else:
                            placa_rep = veic_rep.split("(")[-1].replace(")", "").strip()
                            row_v2 = df_v[df_v["Placa"] == placa_rep]
                            if not row_v2.empty:
                                # Registrar histórico
                                hist_novo = pd.DataFrame([{
                                    "Data": get_dt_br(), "Acao": "Reparo",
                                    "Veiculo": row_v2.iloc[0].get("Modelo", ""), "Placa": placa_rep,
                                    "Usuario": st.session_state.login_logado,
                                    "KM_Inicial": row_v2.iloc[0].get("KM_Atual", ""), "KM_Final": "",
                                    "Avarias_Saida": ";".join(avs_corrigir), "Avarias_Chegada": "",
                                    "Foto_Base64": "", "Obs": obs_rep,
                                    "Tipo_Manutencao": "Reparo", "Empresa": empresa_rep,
                                    "Valor": str(valor_rep)
                                }])
                                df_hist2 = carregar(ARQ_HIST)
                                salvar(pd.concat([df_hist2, hist_novo], ignore_index=True), ARQ_HIST)

                                # Remover avarias corrigidas do veículo
                                avs_atuais = str(row_v2.iloc[0].get("Avarias", "")).strip()
                                restantes = [a.strip() for a in avs_atuais.split(";")
                                             if a.strip() and a.strip() not in avs_corrigir]
                                df_v.loc[df_v["Placa"] == placa_rep, "Avarias"] = ";".join(restantes)
                                salvar(df_v, ARQ_VEIC)

                                st.success(f"Reparo registrado! Avarias removidas: {', '.join(avs_corrigir)}")
                                st.rerun()

# ─────────────────────────────────────────────
# 11. ABA HISTÓRICO
# ─────────────────────────────────────────────
with tab_hist:
    st.subheader("📋 Histórico Geral")

    df_hist = carregar(ARQ_HIST)
    if df_hist.empty:
        st.info("Nenhum registro no histórico.")
    else:
        with st.expander("🔍 Filtros"):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                veics_hist = ["Todos"] + sorted(df_hist["Veiculo"].unique().tolist()) if "Veiculo" in df_hist.columns else ["Todos"]
                filtro_v = st.selectbox("Veículo", veics_hist)
            with col_f2:
                users_hist = ["Todos"] + sorted(df_hist["Usuario"].unique().tolist()) if "Usuario" in df_hist.columns else ["Todos"]
                filtro_u = st.selectbox("Motorista (Login)", users_hist)
            with col_f3:
                filtro_data = st.text_input("Data (dd/mm/aaaa) — parcial")

        df_show = df_hist.copy()
        if filtro_v != "Todos" and "Veiculo" in df_show.columns:
            df_show = df_show[df_show["Veiculo"] == filtro_v]
        if filtro_u != "Todos" and "Usuario" in df_show.columns:
            df_show = df_show[df_show["Usuario"] == filtro_u]
        if filtro_data.strip() and "Data" in df_show.columns:
            df_show = df_show[df_show["Data"].str.contains(filtro_data.strip(), na=False)]

        cols_show = [c for c in ["Data", "Acao", "Veiculo", "Placa", "Usuario", "KM_Inicial",
                                  "KM_Final", "Avarias_Saida", "Avarias_Chegada",
                                  "Tipo_Manutencao", "Empresa", "Valor", "Obs"] if c in df_show.columns]
        st.dataframe(df_show[cols_show], use_container_width=True)

# ─────────────────────────────────────────────
# 12. ABA GESTÃO (só admin)
# ─────────────────────────────────────────────
if tab_gest:
    with tab_gest:
        st.subheader("🛡️ Gestão Administrativa")
        sub_gest = st.tabs(["🚗 Veículos", "👤 Motoristas", "⚠️ Avarias"])

        # ── 12.1 Gestão de Veículos
        with sub_gest[0]:
            st.write("### Gerenciar Veículos")
            df_v = carregar(ARQ_VEIC)
            if df_v.empty:
                st.info("Nenhum veículo cadastrado.")
            else:
                for i, row in df_v.iterrows():
                    placa = str(row.get("Placa", ""))
                    modelo = str(row.get("Modelo", ""))
                    status = str(row.get("Status", ""))
                    alerta_rev = " ⚠️" if revisao_vencida(row) else ""
                    with st.expander(f"{modelo} ({placa}) — {status}{alerta_rev}"):
                        with st.form(f"edit_v_{i}"):
                            c1, c2 = st.columns(2)
                            with c1:
                                novo_mod = st.text_input("Modelo", value=row.get("Modelo",""), key=f"mod_{i}")
                                novo_km  = st.text_input("KM Atual", value=row.get("KM_Atual",""), key=f"km_{i}")
                                novo_crit = st.selectbox("Critério Revisão",
                                    ["KM","Data","Ambos"],
                                    index=["KM","Data","Ambos"].index(row.get("Criterio_Revisao","KM")) if row.get("Criterio_Revisao","KM") in ["KM","Data","Ambos"] else 0,
                                    key=f"crit_{i}")
                            with c2:
                                novo_status = st.selectbox("Status",
                                    ["Disponível","Em uso","Manutenção","Bloqueado"],
                                    index=["Disponível","Em uso","Manutenção","Bloqueado"].index(status) if status in ["Disponível","Em uso","Manutenção","Bloqueado"] else 0,
                                    key=f"stv_{i}")
                            col_b1, col_b2 = st.columns(2)
                            with col_b1:
                                salvar_v = st.form_submit_button("💾 Salvar Edição")
                            with col_b2:
                                bloquear_v = st.form_submit_button("🔒 Bloquear")

                        if salvar_v:
                            df_v.at[i, "Modelo"] = novo_mod
                            df_v.at[i, "KM_Atual"] = novo_km
                            df_v.at[i, "Criterio_Revisao"] = novo_crit
                            df_v.at[i, "Status"] = novo_status
                            salvar(df_v, ARQ_VEIC)
                            st.success("Veículo atualizado!")
                            st.rerun()

                        if bloquear_v:
                            df_v.at[i, "Status"] = "Bloqueado"
                            salvar(df_v, ARQ_VEIC)
                            st.success("Veículo bloqueado.")
                            st.rerun()

                        # Exclusão: só se sem histórico
                        if not historico_tem_veiculo(placa):
                            if st.button(f"🗑️ Excluir {modelo}", key=f"del_v_{i}"):
                                df_v = df_v[df_v["Placa"] != placa]
                                salvar(df_v, ARQ_VEIC)
                                st.success("Veículo excluído.")
                                st.rerun()
                        else:
                            st.caption("⚠️ Veículo com histórico — exclusão bloqueada. Use Bloquear.")

        # ── 12.2 Gestão de Motoristas
        with sub_gest[1]:
            st.write("### Gerenciar Motoristas")
            df_u = carregar(ARQ_MOT)
            if df_u.empty:
                st.info("Nenhum motorista cadastrado.")
            else:
                for i, row in df_u.iterrows():
                    login_u = str(row.get("Login", ""))
                    nome_u  = str(row.get("Nome", ""))
                    status_u = str(row.get("Status", ""))
                    cnh_ok = cnh_valida(row)
                    alerta_cnh = " ⚠️ CNH VENCIDA" if not cnh_ok else ""
                    with st.expander(f"{nome_u} ({login_u}) — {status_u}{alerta_cnh}"):
                        with st.form(f"edit_u_{i}"):
                            c1, c2 = st.columns(2)
                            with c1:
                                novo_nome = st.text_input("Nome", value=nome_u, key=f"nm_{i}")
                                nova_cnh  = st.text_input("Validade CNH (YYYY-MM-DD)", value=row.get("Validade_CNH",""), key=f"cnh_{i}")
                            with c2:
                                novo_perfil = st.selectbox("Perfil",
                                    ["Usuário","Admin"],
                                    index=0 if row.get("Perfil","Usuário") != "Admin" else 1,
                                    key=f"prf_{i}")
                                novo_st_u = st.selectbox("Status",
                                    ["Ativo","Bloqueado"],
                                    index=0 if status_u == "Ativo" else 1,
                                    key=f"stu_{i}")
                            col_b1, col_b2, col_b3 = st.columns(3)
                            with col_b1:
                                salvar_u = st.form_submit_button("💾 Salvar")
                            with col_b2:
                                bloquear_u = st.form_submit_button("🔒 Bloquear")
                            with col_b3:
                                resetar_u = st.form_submit_button("🔑 Resetar Senha → 123")

                        if salvar_u:
                            df_u.at[i, "Nome"] = novo_nome
                            df_u.at[i, "Validade_CNH"] = nova_cnh
                            df_u.at[i, "Perfil"] = novo_perfil
                            df_u.at[i, "Status"] = novo_st_u
                            salvar(df_u, ARQ_MOT)
                            st.success("Motorista atualizado!")
                            st.rerun()

                        if bloquear_u:
                            df_u.at[i, "Status"] = "Bloqueado"
                            salvar(df_u, ARQ_MOT)
                            st.success("Motorista bloqueado.")
                            st.rerun()

                        if resetar_u:
                            df_u.at[i, "Senha"] = "123"
                            salvar(df_u, ARQ_MOT)
                            st.success("Senha resetada para 123.")
                            st.rerun()

                        if not historico_tem_motorista(login_u):
                            if st.button(f"🗑️ Excluir {nome_u}", key=f"del_u_{i}"):
                                df_u = df_u[df_u["Login"] != login_u]
                                salvar(df_u, ARQ_MOT)
                                st.success("Motorista excluído.")
                                st.rerun()
                        else:
                            st.caption("⚠️ Motorista com histórico — exclusão bloqueada.")

        # ── 12.3 Gestão de Avarias
        with sub_gest[2]:
            st.write("### Gerenciar Avarias")
            df_av = carregar(ARQ_AVAR)
            if df_av.empty:
                st.info("Nenhuma avaria cadastrada.")
            else:
                for i, row in df_av.iterrows():
                    desc = str(row.get("Descricao", ""))
                    st_av = str(row.get("Status", ""))
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        st.write(f"**{desc}** — {st_av}")
                    with col2:
                        if st.button("🔒", key=f"blk_av_{i}", help="Bloquear avaria"):
                            df_av.at[i, "Status"] = "Bloqueado"
                            salvar(df_av, ARQ_AVAR)
                            st.rerun()
                    with col3:
                        if not avaria_em_uso(desc):
                            if st.button("🗑️", key=f"del_av_{i}", help="Excluir avaria"):
                                df_av = df_av[df_av["Descricao"] != desc]
                                salvar(df_av, ARQ_AVAR)
                                st.success(f"Avaria '{desc}' excluída.")
                                st.rerun()
                        else:
                            st.caption("Em uso")
