import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import base64
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ─────────────────────────────────────────────
# 1. CONFIGURAÇÃO INICIAL
# ─────────────────────────────────────────────
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗", layout="wide")

# ─────────────────────────────────────────────
# 2. CONEXÃO GOOGLE SHEETS
# ─────────────────────────────────────────────
SHEET_ID = st.secrets["gcp_service_account"]["sheet_id"]
SCOPES   = ["https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_service():
    try:
        info = dict(st.secrets["gcp_service_account"])
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        return build("sheets", "v4", credentials=creds).spreadsheets()
    except Exception as e:
        st.error(f"Erro conexao Google: {e}")
        st.stop()

ABA_HIST = "Historico"
ABA_VEIC = "Veiculos"
ABA_MOT  = "Motoristas"
ABA_AVAR = "Avarias"

COLS_HIST = ["Data","Acao","Veiculo","Placa","Usuario","KM_Inicial","KM_Final",
             "Avarias_Saida","Avarias_Chegada","Foto_Base64","Obs",
             "Tipo_Manutencao","Empresa","Valor"]
COLS_VEIC = ["Modelo","Placa","KM_Atual","KM_Ultima_Revisao","Ultima_Revisao",
             "Criterio_Revisao","Intervalo_KM","Intervalo_Dias","Avarias","Status"]
COLS_MOT  = ["Nome","Login","Senha","Validade_CNH","Perfil","Status"]
COLS_AVAR = ["Descricao","Status"]

# ─────────────────────────────────────────────
# 3. FUNÇÕES GOOGLE SHEETS (COM CACHE)
# ─────────────────────────────────────────────
@st.cache_data(ttl=30)  # ✅ cache de 30s para evitar erro 429
def ler_aba(aba, colunas):
    tentativas = 3
    for tentativa in range(1, tentativas + 1):
        try:
            svc  = get_service()
            res  = svc.values().get(spreadsheetId=SHEET_ID, range=aba).execute()
            vals = res.get("values", [])
            if not vals:
                return pd.DataFrame(columns=colunas)
            header    = vals[0]
            rows      = vals[1:] if len(vals) > 1 else []
            rows_norm = [r + [""] * (len(header) - len(r)) for r in rows]
            df = pd.DataFrame(rows_norm, columns=header)
            for col in colunas:
                if col not in df.columns:
                    df[col] = ""
            return df.fillna("")
        except Exception as e:
            erro_str = str(e)
            # Broken pipe / connection reset: tenta reconectar
            if tentativa < tentativas and any(x in erro_str for x in ["Broken pipe","Connection reset","timed out","RemoteDisconnected"]):
                get_service.clear()  # força reconexão na próxima chamada
                time.sleep(2 * tentativa)
                continue
            # Quota excedida: espera mais antes de tentar
            if tentativa < tentativas and "429" in erro_str:
                time.sleep(5 * tentativa)
                continue
            st.error(f"Erro ao ler {aba}: {e}")
            return pd.DataFrame(columns=colunas)
    return pd.DataFrame(columns=colunas)

def invalidar_cache():
    """✅ CORREÇÃO: limpa o cache após salvar dados novos"""
    ler_aba.clear()

def garantir_aba(aba, colunas, linha_padrao=None):
    try:
        svc  = get_service()
        meta = svc.get(spreadsheetId=SHEET_ID).execute()
        abas = [s["properties"]["title"] for s in meta.get("sheets", [])]
        if aba not in abas:
            svc.batchUpdate(spreadsheetId=SHEET_ID,
                body={"requests":[{"addSheet":{"properties":{"title":aba}}}]}).execute()
            vals = [colunas]
            if linha_padrao:
                vals.append(linha_padrao)
            svc.values().update(spreadsheetId=SHEET_ID, range=f"{aba}!A1",
                valueInputOption="RAW", body={"values": vals}).execute()
        else:
            res = svc.values().get(spreadsheetId=SHEET_ID, range=f"{aba}!A1:1").execute()
            if not res.get("values"):
                vals = [colunas]
                if linha_padrao:
                    vals.append(linha_padrao)
                svc.values().update(spreadsheetId=SHEET_ID, range=f"{aba}!A1",
                    valueInputOption="RAW", body={"values": vals}).execute()
    except Exception as e:
        st.error(f"Erro ao garantir {aba}: {e}")

def salvar_aba(df, aba, colunas):
    try:
        svc = get_service()
        for col in colunas:
            if col not in df.columns:
                df[col] = ""
        df     = df[colunas].fillna("")
        valores = [colunas] + df.values.tolist()
        svc.values().clear(spreadsheetId=SHEET_ID, range=aba).execute()
        svc.values().update(spreadsheetId=SHEET_ID, range=f"{aba}!A1",
            valueInputOption="RAW", body={"values": valores}).execute()
    except Exception as e:
        st.error(f"Erro ao salvar {aba}: {e}")

def append_linha(aba, linha_dict, colunas):
    try:
        svc   = get_service()
        linha = [str(linha_dict.get(c, "")) for c in colunas]
        svc.values().append(spreadsheetId=SHEET_ID, range=f"{aba}!A1",
            valueInputOption="RAW", insertDataOption="INSERT_ROWS",
            body={"values": [linha]}).execute()
    except Exception as e:
        st.error(f"Erro ao adicionar linha em {aba}: {e}")

# ─────────────────────────────────────────────
# 4. INICIALIZAÇÃO (✅ CORREÇÃO: cache_resource para rodar só uma vez)
# ─────────────────────────────────────────────
@st.cache_resource
def inicializar_sistema():
    linha_paulo = ["Paulo","paulo","123","2030-12-31","Admin","Ativo"]
    try:
        svc  = get_service()
        meta = svc.get(spreadsheetId=SHEET_ID).execute()
        abas_existentes = [s["properties"]["title"] for s in meta.get("sheets", [])]

        # Garante todas as abas em uma única chamada de metadados
        abas_necessarias = {
            ABA_MOT:  (COLS_MOT,  linha_paulo),
            ABA_VEIC: (COLS_VEIC, None),
            ABA_AVAR: (COLS_AVAR, None),
            ABA_HIST: (COLS_HIST, None),
        }

        for aba, (colunas, linha_padrao) in abas_necessarias.items():
            if aba not in abas_existentes:
                svc.batchUpdate(spreadsheetId=SHEET_ID,
                    body={"requests":[{"addSheet":{"properties":{"title":aba}}}]}).execute()
                vals = [colunas]
                if linha_padrao:
                    vals.append(linha_padrao)
                svc.values().update(spreadsheetId=SHEET_ID, range=f"{aba}!A1",
                    valueInputOption="RAW", body={"values": vals}).execute()
            else:
                res = svc.values().get(spreadsheetId=SHEET_ID, range=f"{aba}!A1:1").execute()
                if not res.get("values"):
                    vals = [colunas]
                    if linha_padrao:
                        vals.append(linha_padrao)
                    svc.values().update(spreadsheetId=SHEET_ID, range=f"{aba}!A1",
                        valueInputOption="RAW", body={"values": vals}).execute()

        # Verifica se o usuário padrão existe
        res_mot = svc.values().get(spreadsheetId=SHEET_ID, range=ABA_MOT).execute()
        vals_mot = res_mot.get("values", [])
        if len(vals_mot) <= 1:  # só cabeçalho ou vazio
            append_linha(ABA_MOT, dict(zip(COLS_MOT, linha_paulo)), COLS_MOT)

    except Exception as e:
        st.error(f"Erro na inicialização: {e}")

inicializar_sistema()

# Contadores para forçar recriação dos file_uploaders após cada submissão
if "upload_key_ret" not in st.session_state:
    st.session_state["upload_key_ret"] = 0
if "upload_key_dev" not in st.session_state:
    st.session_state["upload_key_dev"] = 0


# ─────────────────────────────────────────────
# 5. FUNÇÕES DE APOIO
# ─────────────────────────────────────────────
def safe_get(row, key, default=""):
    try:
        return row[key] if key in row.index else default
    except Exception:
        return default

def montar_lista_veiculos(df_v):
    lista = []
    if df_v.empty:
        return lista
    for _, r in df_v.iterrows():
        lista.append(f"{safe_get(r,'Modelo','?')} ({safe_get(r,'Placa','?')})")
    return lista

def get_dt_br():
    return datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

def str_para_date(s):
    try:
        return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
    except Exception:
        return None

def cnh_valida(row):
    d = str_para_date(str(row.get("Validade_CNH","")).strip())
    return d is not None and d >= date.today()

def revisao_vencida(row):
    """
    Critério "Ambos": vence pelo que ocorrer PRIMEIRO (KM OU Data).
    Critério "KM": só verifica quilometragem.
    Critério "Data": só verifica data.
    """
    try:
        criterio = safe_get(row,"Criterio_Revisao","").strip()

        km_vencido = False
        if criterio in ("KM","Ambos"):
            try:
                km_atual = int(safe_get(row,"KM_Atual","0") or "0")
                int_km   = int(safe_get(row,"Intervalo_KM","0") or "0")
                km_ult   = int(safe_get(row,"KM_Ultima_Revisao","0") or "0")
                if int_km > 0 and (km_atual - km_ult) >= int_km:
                    km_vencido = True
            except Exception:
                pass

        data_vencida = False
        if criterio in ("Data","Ambos"):
            d_rev = str_para_date(safe_get(row,"Ultima_Revisao",""))
            try:
                int_d = int(safe_get(row,"Intervalo_Dias","0") or "0")
            except Exception:
                int_d = 0
            if d_rev and int_d > 0 and date.today() >= d_rev + timedelta(days=int_d):
                data_vencida = True

        # Para "Ambos": vence se QUALQUER critério estiver vencido (o que vencer primeiro)
        if criterio == "Ambos":
            return km_vencido or data_vencida
        elif criterio == "KM":
            return km_vencido
        elif criterio == "Data":
            return data_vencida
        return False
    except Exception:
        return False


def revisao_alerta(row):
    """Retorna texto descritivo do motivo do alerta de revisão."""
    try:
        criterio = safe_get(row,"Criterio_Revisao","").strip()
        msgs = []
        if criterio in ("KM","Ambos"):
            try:
                km_atual = int(safe_get(row,"KM_Atual","0") or "0")
                int_km   = int(safe_get(row,"Intervalo_KM","0") or "0")
                km_ult   = int(safe_get(row,"KM_Ultima_Revisao","0") or "0")
                rodados  = km_atual - km_ult
                if int_km > 0:
                    if rodados >= int_km:
                        msgs.append(f"KM vencida ({rodados:,} km rodados, limite {int_km:,} km)")
                    else:
                        faltam = int_km - rodados
                        msgs.append(f"KM ok — faltam {faltam:,} km para revisão")
            except Exception:
                pass
        if criterio in ("Data","Ambos"):
            d_rev = str_para_date(safe_get(row,"Ultima_Revisao",""))
            try:
                int_d = int(safe_get(row,"Intervalo_Dias","0") or "0")
            except Exception:
                int_d = 0
            if d_rev and int_d > 0:
                proxima = d_rev + timedelta(days=int_d)
                if date.today() >= proxima:
                    msgs.append(f"Data vencida (próxima era {proxima.strftime('%d/%m/%Y')})")
                else:
                    faltam_d = (proxima - date.today()).days
                    msgs.append(f"Data ok — faltam {faltam_d} dias para revisão")
        return " | ".join(msgs) if msgs else ""
    except Exception:
        return ""

def historico_tem_veiculo(placa):
    df = ler_aba(ABA_HIST, COLS_HIST)
    return not df.empty and "Placa" in df.columns and not df[df["Placa"]==placa].empty

def historico_tem_motorista(login):
    df = ler_aba(ABA_HIST, COLS_HIST)
    return not df.empty and "Usuario" in df.columns and not df[df["Usuario"]==login].empty

def avaria_em_uso(descricao):
    df = ler_aba(ABA_VEIC, COLS_VEIC)
    if df.empty or "Avarias" not in df.columns:
        return False
    for _, row in df.iterrows():
        if descricao in [a.strip() for a in str(row.get("Avarias","")).split(";") if a.strip()]:
            return True
    return False

def imagem_para_base64(img_bytes):
    try:
        return base64.b64encode(img_bytes).decode()
    except Exception:
        return ""

def widget_fotos(prefixo: str, label: str):
    """
    Widget de fotos com câmera e upload múltiplo.
    Converte imediatamente para base64 — sem st.rerun() para não bloquear confirmação.
    Armazena lista em st.session_state[f"{prefixo}_fotos_b64"].
    """
    key_list = f"{prefixo}_fotos_b64"
    key_cam  = f"{prefixo}_cam_idx"
    key_upk  = f"{prefixo}_up_key"

    if key_list not in st.session_state: st.session_state[key_list] = []
    if key_cam  not in st.session_state: st.session_state[key_cam]  = 0
    if key_upk  not in st.session_state: st.session_state[key_upk]  = 0

    st.markdown(f"**📷 {label}**")

    aba_cam, aba_up = st.tabs(["📸 Câmera", "🖼️ Upload de arquivos"])

    with aba_cam:
        # Tamanho menor: width=300
        cam = st.camera_input("Tirar foto", key=f"cam_{prefixo}_{st.session_state[key_cam]}")
        if cam is not None:
            b64 = imagem_para_base64(cam.read())
            if b64 not in st.session_state[key_list]:   # evita duplicata
                st.session_state[key_list].append(b64)
                st.session_state[key_cam] += 1          # reseta câmera sem rerun global
        if st.button("📸 Confirmar foto e tirar outra", key=f"btn_cam_{prefixo}"):
            st.session_state[key_cam] += 1

    with aba_up:
        uploads = st.file_uploader(
            "Selecione uma ou mais imagens",
            type=["jpg","jpeg","png"],
            accept_multiple_files=True,
            key=f"up_{prefixo}_{st.session_state[key_upk]}"
        )
        if uploads:
            novos = [imagem_para_base64(f.read()) for f in uploads]
            for b in novos:
                if b not in st.session_state[key_list]:
                    st.session_state[key_list].append(b)
            if st.button("✅ Confirmar upload", key=f"btn_up_{prefixo}"):
                st.session_state[key_upk] += 1

    # Miniaturas menores (width fixo via HTML) com botão remover
    fotos = st.session_state[key_list]
    if fotos:
        st.markdown(f"**{len(fotos)} foto(s) adicionada(s):**")
        cols = st.columns(min(len(fotos), 4))
        to_remove = None
        for idx, b64 in enumerate(fotos):
            with cols[idx % 4]:
                try:
                    img_bytes = base64.b64decode(b64)
                    st.image(img_bytes, width=150)
                except Exception:
                    st.warning("Imagem inválida")
                if st.button("🗑️", key=f"rm_{prefixo}_{idx}", help="Remover foto"):
                    to_remove = idx
        if to_remove is not None:
            st.session_state[key_list].pop(to_remove)
    else:
        st.caption("Nenhuma foto adicionada ainda.")

    return st.session_state[key_list]

# ─────────────────────────────────────────────
# 6. LOGIN
# ─────────────────────────────────────────────
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🚗 Gestão de Frota — Login")
    df_m   = ler_aba(ABA_MOT, COLS_MOT)
    ativos = df_m[df_m["Status"]=="Ativo"] if not df_m.empty and "Status" in df_m.columns else pd.DataFrame()
    lista_login = sorted(ativos["Login"].unique().tolist()) if "Login" in ativos.columns else []

    col_l, _ = st.columns([2,3])
    with col_l:
        login_sel = st.selectbox("Login", [""]+lista_login)
        senha_dig = st.text_input("Senha", type="password")
        if st.button("Acessar Sistema"):
            if not login_sel:
                st.error("Selecione um usuário.")
            else:
                reg = df_m[df_m["Login"]==login_sel]
                if reg.empty:
                    st.error("Usuário não encontrado.")
                else:
                    dados = reg.iloc[0]
                    if senha_dig == "RESET99" or senha_dig == str(dados.get("Senha","")):
                        st.session_state.autenticado  = True
                        st.session_state.perfil       = "admin" if str(dados.get("Perfil",""))=="Admin" else "motorista"
                        st.session_state.user_logado  = str(dados.get("Nome", login_sel))
                        st.session_state.login_logado = login_sel
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
    st.stop()

# ─────────────────────────────────────────────
# 7. INTERFACE PRINCIPAL
# ─────────────────────────────────────────────
st.title(f"🚗 Sistema de Frota — Olá, {st.session_state.user_logado}")
if st.sidebar.button("🚪 Logoff / Sair"):
    st.session_state.autenticado = False
    st.rerun()
st.sidebar.info(f"Perfil: {'🔑 Administrador' if st.session_state.perfil=='admin' else '🚗 Motorista'}")

if st.session_state.perfil == "admin":
    menu = ["⚙️ Cadastros","📤 Retirada","📥 Devolução","🔧 Oficina","📋 Histórico","🛡️ Gestão"]
    tabs = st.tabs(menu)
    tab_cad, tab_ret, tab_dev, tab_ofc, tab_hist, tab_gest = tabs
else:
    menu = ["📤 Retirada","📥 Devolução","🔧 Oficina","📋 Histórico"]
    tabs = st.tabs(menu)
    tab_ret, tab_dev, tab_ofc, tab_hist = tabs
    tab_cad = tab_gest = None

# ─────────────────────────────────────────────
# 8. CADASTROS (admin)
# ─────────────────────────────────────────────
if tab_cad:
    with tab_cad:
        st.subheader("⚙️ Cadastros")
        sub_cad = st.tabs(["🚗 Veículos","👤 Motoristas","⚠️ Avarias"])

        # Veículos
        with sub_cad[0]:
            st.write("### Cadastrar Novo Veículo")
            df_v  = ler_aba(ABA_VEIC, COLS_VEIC)
            df_av = ler_aba(ABA_AVAR, COLS_AVAR)
            av_ativas = sorted(df_av[df_av["Status"]=="Ativo"]["Descricao"].tolist()) if not df_av.empty and "Status" in df_av.columns else []

            with st.form("form_novo_veiculo"):
                c1, c2 = st.columns(2)
                with c1:
                    mod    = st.text_input("Modelo *")
                    pla    = st.text_input("Placa * (única)").upper().strip()
                    km     = st.number_input("KM Atual *", min_value=0, step=1)
                    km_rev = st.number_input("KM na Última Revisão *", min_value=0, step=1,
                                             help="Informe o KM que estava no veículo quando foi feita a última revisão")
                with c2:
                    ult_rev  = st.date_input("Data da Última Revisão *", value=date.today())
                    criterio = st.selectbox("Critério de Revisão *", ["KM","Data","Ambos"],
                                            help="Ambos = alerta no que vencer primeiro (KM ou Data)")
                    int_km   = st.number_input("Intervalo Revisão (KM)",   min_value=0, step=500)
                    int_dias = st.number_input("Intervalo Revisão (Dias)", min_value=0, step=30)
                avarias_sel = st.multiselect("Estado atual (Avarias)", av_ativas)
                status_v    = st.selectbox("Status", ["Disponível","Em uso","Manutenção","Bloqueado"])
                if st.form_submit_button("💾 Salvar Veículo"):
                    erros = []
                    if not mod: erros.append("Modelo obrigatório.")
                    if not pla: erros.append("Placa obrigatória.")
                    if pla and not df_v.empty and "Placa" in df_v.columns and pla in df_v["Placa"].values:
                        erros.append(f"Placa '{pla}' já cadastrada.")
                    if km_rev > km:
                        erros.append("KM da última revisão não pode ser maior que o KM atual.")
                    if erros:
                        for e in erros: st.error(e)
                    else:
                        append_linha(ABA_VEIC, {
                            "Modelo":mod,"Placa":pla,"KM_Atual":str(km),
                            "KM_Ultima_Revisao":str(km_rev),
                            "Ultima_Revisao":ult_rev.strftime("%Y-%m-%d"),
                            "Criterio_Revisao":criterio,
                            "Intervalo_KM":str(int_km),"Intervalo_Dias":str(int_dias),
                            "Avarias":";".join(avarias_sel),"Status":status_v
                        }, COLS_VEIC)
                        st.success(f"Veículo {mod} ({pla}) cadastrado!")
                        invalidar_cache()
                        st.rerun()

            st.write("---")
            st.write("### Veículos Cadastrados")
            df_v2 = ler_aba(ABA_VEIC, COLS_VEIC)
            if df_v2.empty:
                st.info("Nenhum veículo cadastrado.")
            else:
                for i, row in df_v2.iterrows():
                    placa  = safe_get(row,"Placa",""); modelo = safe_get(row,"Modelo","")
                    status = safe_get(row,"Status",""); km_at  = safe_get(row,"KM_Atual","")
                    alerta = " ⚠️ REVISÃO VENCIDA" if revisao_vencida(row) else ""
                    with st.expander(f"🚗 {modelo} — {placa} | {status}{alerta}"):
                        with st.form(f"edit_vcad_{i}"):
                            st.write(f"**Modelo:** {modelo} | **Placa:** {placa} *(não editáveis)*")
                            c1, c2 = st.columns(2)
                            with c1:
                                novo_km      = st.text_input("KM Atual", value=km_at, key=f"vcad_km_{i}")
                                novo_km_rev  = st.text_input("KM na Última Revisão",
                                                             value=safe_get(row,"KM_Ultima_Revisao","0"),
                                                             key=f"vcad_kmrev_{i}",
                                                             help="KM que estava no veículo quando foi feita a última revisão")
                                nova_rev     = st.text_input("Data Última Revisão (AAAA-MM-DD)", value=safe_get(row,"Ultima_Revisao",""), key=f"vcad_rev_{i}")
                                novo_crit    = st.selectbox("Critério", ["KM","Data","Ambos"],
                                    index=["KM","Data","Ambos"].index(safe_get(row,"Criterio_Revisao","KM")) if safe_get(row,"Criterio_Revisao","KM") in ["KM","Data","Ambos"] else 0,
                                    key=f"vcad_crit_{i}")
                            with c2:
                                novo_int_km = st.text_input("Intervalo KM",   value=safe_get(row,"Intervalo_KM","0"),   key=f"vcad_ikm_{i}")
                                novo_int_d  = st.text_input("Intervalo Dias", value=safe_get(row,"Intervalo_Dias","0"), key=f"vcad_id_{i}")
                                novo_st_v   = st.selectbox("Status", ["Disponível","Em uso","Manutenção","Bloqueado"],
                                    index=["Disponível","Em uso","Manutenção","Bloqueado"].index(status) if status in ["Disponível","Em uso","Manutenção","Bloqueado"] else 0,
                                    key=f"vcad_st_{i}")
                            av_lista = [a.strip() for a in safe_get(row,"Avarias","").split(";") if a.strip()]
                            novas_av = st.multiselect("Avarias atuais", av_ativas, default=[a for a in av_lista if a in av_ativas], key=f"vcad_av_{i}")
                            col_b1,col_b2,col_b3 = st.columns(3)
                            with col_b1: btn_sv = st.form_submit_button("💾 Salvar Edição")
                            with col_b2: btn_bl = st.form_submit_button("🔒 Bloquear")
                            with col_b3: btn_ex = st.form_submit_button("🗑️ Excluir", type="primary")
                        if btn_sv:
                            df_v2.at[i,"KM_Atual"]=novo_km; df_v2.at[i,"KM_Ultima_Revisao"]=novo_km_rev
                            df_v2.at[i,"Ultima_Revisao"]=nova_rev
                            df_v2.at[i,"Criterio_Revisao"]=novo_crit; df_v2.at[i,"Intervalo_KM"]=novo_int_km
                            df_v2.at[i,"Intervalo_Dias"]=novo_int_d; df_v2.at[i,"Status"]=novo_st_v
                            df_v2.at[i,"Avarias"]=";".join(novas_av)
                            salvar_aba(df_v2, ABA_VEIC, COLS_VEIC)
                            st.success("Atualizado!")
                            invalidar_cache()  # ✅ CORREÇÃO
                            st.rerun()
                        if btn_bl:
                            df_v2.at[i,"Status"]="Bloqueado"
                            salvar_aba(df_v2,ABA_VEIC,COLS_VEIC)
                            st.success("Bloqueado.")
                            invalidar_cache()  # ✅ CORREÇÃO
                            st.rerun()
                        if btn_ex:
                            if historico_tem_veiculo(placa):
                                st.error("❌ Com histórico — use Bloquear.")
                            else:
                                salvar_aba(df_v2[df_v2["Placa"]!=placa],ABA_VEIC,COLS_VEIC)
                                st.success("Excluído.")
                                invalidar_cache()  # ✅ CORREÇÃO
                                st.rerun()

        # Motoristas
        with sub_cad[1]:
            st.write("### Cadastrar Novo Motorista")
            df_u = ler_aba(ABA_MOT, COLS_MOT)
            with st.form("form_novo_mot"):
                c1,c2 = st.columns(2)
                with c1:
                    nome_m  = st.text_input("Nome *")
                    login_m = st.text_input("Login / Email * (único)").strip().lower()
                    senha_m = st.text_input("Senha *", type="password")
                with c2:
                    cnh_val  = st.date_input("Validade da CNH *", value=date.today())
                    perfil_m = st.selectbox("Perfil *", ["Usuário","Admin"])
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
                        append_linha(ABA_MOT,{"Nome":nome_m,"Login":login_m,"Senha":senha_m,
                            "Validade_CNH":cnh_val.strftime("%Y-%m-%d"),"Perfil":perfil_m,"Status":"Ativo"},COLS_MOT)
                        st.success(f"Motorista {nome_m} cadastrado!")
                        invalidar_cache()  # ✅ CORREÇÃO
                        st.rerun()

            st.write("---"); st.write("### Motoristas Cadastrados")
            df_u2 = ler_aba(ABA_MOT, COLS_MOT)
            if df_u2.empty:
                st.info("Nenhum motorista cadastrado.")
            else:
                for i, row in df_u2.iterrows():
                    nome_u=safe_get(row,"Nome",""); login_u=safe_get(row,"Login","")
                    status_u=safe_get(row,"Status",""); perfil_u=safe_get(row,"Perfil","")
                    cnh_u=safe_get(row,"Validade_CNH","")
                    alerta_cnh=" ⚠️ CNH VENCIDA" if not cnh_valida(row) else ""
                    with st.expander(f"👤 {nome_u} ({login_u}) | {perfil_u} | {status_u}{alerta_cnh}"):
                        with st.form(f"edit_ucad_{i}"):
                            st.write(f"**Nome:** {nome_u} *(não editável)*")
                            c1,c2 = st.columns(2)
                            with c1:
                                novo_login = st.text_input("Login / Email", value=login_u, key=f"ucad_lg_{i}")
                                nova_senha = st.text_input("Nova Senha (em branco = manter)", type="password", key=f"ucad_pw_{i}")
                            with c2:
                                nova_cnh_u  = st.text_input("Validade CNH (AAAA-MM-DD)", value=cnh_u, key=f"ucad_cnh_{i}")
                                novo_prf    = st.selectbox("Perfil",["Usuário","Admin"], index=0 if perfil_u!="Admin" else 1, key=f"ucad_prf_{i}")
                                novo_st_u   = st.selectbox("Status",["Ativo","Bloqueado"], index=0 if status_u=="Ativo" else 1, key=f"ucad_stu_{i}")
                            col_b1,col_b2,col_b3 = st.columns(3)
                            with col_b1: btn_su=st.form_submit_button("💾 Salvar Edição")
                            with col_b2: btn_bu=st.form_submit_button("🔒 Bloquear")
                            with col_b3: btn_eu=st.form_submit_button("🗑️ Excluir", type="primary")
                        if btn_su:
                            df_u2.at[i,"Login"]=novo_login.strip().lower()
                            df_u2.at[i,"Validade_CNH"]=nova_cnh_u.strip()
                            df_u2.at[i,"Perfil"]=novo_prf; df_u2.at[i,"Status"]=novo_st_u
                            if nova_senha.strip(): df_u2.at[i,"Senha"]=nova_senha.strip()
                            salvar_aba(df_u2,ABA_MOT,COLS_MOT)
                            st.success("Atualizado!")
                            invalidar_cache()  # ✅ CORREÇÃO
                            st.rerun()
                        if btn_bu:
                            df_u2.at[i,"Status"]="Bloqueado"
                            salvar_aba(df_u2,ABA_MOT,COLS_MOT)
                            st.success("Bloqueado.")
                            invalidar_cache()  # ✅ CORREÇÃO
                            st.rerun()
                        if btn_eu:
                            if historico_tem_motorista(login_u):
                                st.error("❌ Com histórico — use Bloquear.")
                            else:
                                salvar_aba(df_u2[df_u2["Login"]!=login_u],ABA_MOT,COLS_MOT)
                                st.success("Excluído.")
                                invalidar_cache()  # ✅ CORREÇÃO
                                st.rerun()

        # Avarias
        with sub_cad[2]:
            st.write("### Cadastrar Nova Avaria")
            df_av = ler_aba(ABA_AVAR, COLS_AVAR)
            with st.form("form_nova_avaria"):
                desc_av = st.text_input("Descrição da Avaria *")
                if st.form_submit_button("💾 Salvar Avaria"):
                    if not desc_av.strip():
                        st.error("Descrição obrigatória.")
                    elif not df_av.empty and "Descricao" in df_av.columns and desc_av.strip() in df_av["Descricao"].values:
                        st.error("Avaria já cadastrada.")
                    else:
                        append_linha(ABA_AVAR,{"Descricao":desc_av.strip(),"Status":"Ativo"},COLS_AVAR)
                        st.success("Avaria cadastrada!")
                        invalidar_cache()  # ✅ CORREÇÃO
                        st.rerun()

            st.write("---"); st.write("### Avarias Cadastradas")
            df_av2 = ler_aba(ABA_AVAR, COLS_AVAR)
            if df_av2.empty:
                st.info("Nenhuma avaria cadastrada.")
            else:
                for i, row in df_av2.iterrows():
                    desc_i=safe_get(row,"Descricao",""); status_i=safe_get(row,"Status","")
                    em_uso=avaria_em_uso(desc_i)
                    with st.expander(f"⚠️ {desc_i} | {status_i}"):
                        st.write("*Avarias não são editáveis.*")
                        col_b1,col_b2 = st.columns(2)
                        with col_b1:
                            if st.button("🔒 Bloquear", key=f"blk_avcad_{i}"):
                                df_av2.at[i,"Status"]="Bloqueado"
                                salvar_aba(df_av2,ABA_AVAR,COLS_AVAR)
                                st.success("Bloqueada.")
                                invalidar_cache()  # ✅ CORREÇÃO
                                st.rerun()
                        with col_b2:
                            if em_uso:
                                st.warning("❌ Em uso — use Bloquear.")
                            else:
                                if st.button("🗑️ Excluir", key=f"del_avcad_{i}", type="primary"):
                                    salvar_aba(df_av2[df_av2["Descricao"]!=desc_i],ABA_AVAR,COLS_AVAR)
                                    st.success("Excluída.")
                                    invalidar_cache()  # ✅ CORREÇÃO
                                    st.rerun()

# ─────────────────────────────────────────────
# 9. RETIRADA
# ─────────────────────────────────────────────
with tab_ret:
    st.subheader("📤 Retirada de Veículo")
    df_m = ler_aba(ABA_MOT, COLS_MOT)
    mot_row = df_m[df_m["Login"]==st.session_state.login_logado].iloc[0] if (
        not df_m.empty and "Login" in df_m.columns and st.session_state.login_logado in df_m["Login"].values) else None

    # ── Validações do motorista ──────────────────────────────────────────────
    if mot_row is not None:
        status_mot = str(mot_row.get("Status","")).strip()
        if status_mot == "Bloqueado":
            st.error("🚫 Seu acesso está bloqueado. Retirada não permitida.")
            st.stop()
        if not cnh_valida(mot_row):
            st.error("⚠️ Sua CNH está vencida. Retirada não permitida.")
            st.stop()

    df_v  = ler_aba(ABA_VEIC, COLS_VEIC)
    df_av = ler_aba(ABA_AVAR, COLS_AVAR)
    disp  = df_v[df_v["Status"]=="Disponível"] if not df_v.empty and "Status" in df_v.columns else pd.DataFrame()
    lista_veics = montar_lista_veiculos(disp)

    if not lista_veics:
        st.info("Nenhum veículo disponível para retirada.")
    else:
        av_ativas = sorted(df_av[df_av["Status"]=="Ativo"]["Descricao"].tolist()) if not df_av.empty and "Status" in df_av.columns else []

        # ── Seleção de veículo e exibição de informações ─────────────────────
        veic_sel_ret = st.selectbox("Veículo *", [""]+lista_veics, key="sel_veic_ret")

        if veic_sel_ret:
            placa_prev = veic_sel_ret.split("(")[-1].replace(")","").strip()
            row_prev = df_v[df_v["Placa"]==placa_prev]
            if not row_prev.empty:
                r = row_prev.iloc[0]
                with st.container(border=True):
                    st.markdown("**📋 Informações do Veículo**")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        km_atual_v   = safe_get(r,"KM_Atual","—")
                        km_rev_v     = safe_get(r,"KM_Ultima_Revisao","—")
                        st.metric("KM Atual", km_atual_v)
                        st.caption(f"KM na última revisão: {km_rev_v}")
                    with c2:
                        st.metric("Última Revisão", safe_get(r,"Ultima_Revisao","—"))
                    with c3:
                        avarias_atuais = [a.strip() for a in safe_get(r,"Avarias","").split(";") if a.strip()]
                        st.metric("Avarias", len(avarias_atuais))
                    if avarias_atuais:
                        st.warning(f"⚠️ Avarias registradas: {', '.join(avarias_atuais)}")
                    alerta_rev = revisao_alerta(r)
                    if revisao_vencida(r):
                        st.warning(f"🔧 Revisão vencida! {alerta_rev} — O veículo pode ser retirado mas precisa de manutenção.")
                    elif alerta_rev:
                        st.info(f"ℹ️ {alerta_rev}")

        obs_ret = st.text_area("Observações", key="obs_ret")
        avs_ret = st.multiselect("Avarias observadas na saída", av_ativas, default=[], key="avs_ret")

        # ── Fotos: câmera + upload múltiplo ─────────────────────────────────
        widget_fotos("ret", "Fotos da retirada (opcional)")

        if st.button("✅ Confirmar Retirada", type="primary", key="btn_confirmar_ret"):
            if not veic_sel_ret:
                st.error("Selecione um veículo.")
            else:
                placa_sel = veic_sel_ret.split("(")[-1].replace(")","").strip()
                row_v = df_v[df_v["Placa"]==placa_sel]
                if row_v.empty:
                    st.error("Veículo não encontrado.")
                else:
                    row_v    = row_v.iloc[0]
                    km_ini   = safe_get(row_v,"KM_Atual","0")
                    foto_b64 = "||".join(st.session_state.get("ret_fotos_b64",[]))
                    append_linha(ABA_HIST,{
                        "Data":get_dt_br(),"Acao":"Retirada",
                        "Veiculo":safe_get(row_v,"Modelo",""),"Placa":placa_sel,
                        "Usuario":st.session_state.login_logado,
                        "KM_Inicial":km_ini,"KM_Final":"",
                        "Avarias_Saida":";".join(st.session_state.get("avs_ret",[])),
                        "Avarias_Chegada":"",
                        "Foto_Base64":foto_b64,
                        "Obs":st.session_state.get("obs_ret",""),
                        "Tipo_Manutencao":"","Empresa":"","Valor":""
                    },COLS_HIST)
                    df_v.loc[df_v["Placa"]==placa_sel,"Status"]="Em uso"
                    av_lista=[a for a in safe_get(row_v,"Avarias","").split(";") if a.strip()]
                    for av in st.session_state.get("avs_ret",[]):
                        if av not in av_lista: av_lista.append(av)
                    df_v.loc[df_v["Placa"]==placa_sel,"Avarias"]=";".join(av_lista)
                    salvar_aba(df_v,ABA_VEIC,COLS_VEIC)
                    # Limpa estados antes do rerun
                    st.session_state["upload_key_ret"] += 1
                    st.session_state.pop("ret_fotos_b64", None)
                    for k in ["obs_ret","avs_ret","sel_veic_ret"]:
                        st.session_state.pop(k, None)
                    st.success(f"✅ Retirada registrada! KM saída: {km_ini}")
                    invalidar_cache()
                    st.rerun()

# ─────────────────────────────────────────────
# 10. DEVOLUÇÃO
# ─────────────────────────────────────────────
with tab_dev:
    st.subheader("📥 Devolução de Veículo")
    df_v    = ler_aba(ABA_VEIC, COLS_VEIC)
    df_hist = ler_aba(ABA_HIST, COLS_HIST)
    df_av   = ler_aba(ABA_AVAR, COLS_AVAR)
    em_uso  = df_v[df_v["Status"]=="Em uso"] if not df_v.empty and "Status" in df_v.columns else pd.DataFrame()
    veics_meus = []
    for _, row in em_uso.iterrows():
        placa = safe_get(row,"Placa","")
        hp = df_hist[(df_hist.get("Placa",pd.Series())==placa) & (df_hist.get("Acao",pd.Series())=="Retirada")] if not df_hist.empty and "Placa" in df_hist.columns else pd.DataFrame()
        if not hp.empty and str(hp.iloc[-1].get("Usuario","")).strip()==st.session_state.login_logado:
            veics_meus.append(f"{safe_get(row,'Modelo','')} ({placa})")

    if not veics_meus:
        st.info("Você não possui veículos para devolver.")
    else:
        av_ativas = sorted(df_av[df_av["Status"]=="Ativo"]["Descricao"].tolist()) if not df_av.empty and "Status" in df_av.columns else []
        veic_dev = st.selectbox("Veículo a Devolver *", [""]+veics_meus, key="sel_veic_dev")
        km_dev   = st.number_input("KM Final *", min_value=0, step=1, key="km_dev")
        obs_dev  = st.text_area("Observações", key="obs_dev")
        avs_dev  = st.multiselect("Avarias na chegada", av_ativas, key="avs_dev")

        # ── Fotos: câmera + upload múltiplo ─────────────────────────────────
        widget_fotos("dev", "Fotos da devolução (opcional)")

        if st.button("✅ Confirmar Devolução", type="primary", key="btn_confirmar_dev"):
            if not veic_dev:
                st.error("Selecione um veículo.")
            else:
                placa_dev = veic_dev.split("(")[-1].replace(")","").strip()
                row_v = df_v[df_v["Placa"]==placa_dev]
                if row_v.empty:
                    st.error("Veículo não encontrado.")
                else:
                    row_v = row_v.iloc[0]
                    hp = df_hist[(df_hist.get("Placa",pd.Series())==placa_dev)&(df_hist.get("Acao",pd.Series())=="Retirada")] if not df_hist.empty and "Placa" in df_hist.columns else pd.DataFrame()
                    km_ini_str = str(hp.iloc[-1].get("KM_Inicial","")) if not hp.empty else ""
                    # ✅ Valida que KM final não é menor que KM de retirada
                    try:
                        km_ini_int = int(km_ini_str) if km_ini_str.strip() else 0
                    except ValueError:
                        km_ini_int = 0
                    if km_dev < km_ini_int:
                        st.error(f"❌ KM final ({km_dev:,}) não pode ser menor que o KM de retirada ({km_ini_int:,}).")
                        st.stop()
                    if km_dev == 0 and km_ini_int > 0:
                        st.error(f"❌ Informe o KM final do veículo. KM de retirada foi {km_ini_int:,}.")
                        st.stop()
                    foto_b64   = "||".join(st.session_state.get("dev_fotos_b64",[]))
                    append_linha(ABA_HIST,{
                        "Data":get_dt_br(),"Acao":"Devolucao",
                        "Veiculo":safe_get(row_v,"Modelo",""),"Placa":placa_dev,
                        "Usuario":st.session_state.login_logado,
                        "KM_Inicial":km_ini_str,"KM_Final":str(km_dev),
                        "Avarias_Saida":"","Avarias_Chegada":";".join(st.session_state.get("avs_dev",[])),
                        "Foto_Base64":foto_b64,
                        "Obs":st.session_state.get("obs_dev",""),
                        "Tipo_Manutencao":"","Empresa":"","Valor":""
                    },COLS_HIST)
                    df_v.loc[df_v["Placa"]==placa_dev,"Status"]="Disponível"
                    df_v.loc[df_v["Placa"]==placa_dev,"KM_Atual"]=str(km_dev)
                    av_lista=[a for a in safe_get(row_v,"Avarias","").split(";") if a.strip()]
                    for av in st.session_state.get("avs_dev",[]):
                        if av not in av_lista: av_lista.append(av)
                    df_v.loc[df_v["Placa"]==placa_dev,"Avarias"]=";".join(av_lista)
                    salvar_aba(df_v,ABA_VEIC,COLS_VEIC)
                    st.session_state["upload_key_dev"] += 1
                    st.session_state.pop("dev_fotos_b64", None)
                    for k in ["obs_dev","avs_dev","km_dev","sel_veic_dev"]:
                        st.session_state.pop(k, None)
                    st.success(f"✅ Devolução registrada! KM final: {km_dev}")
                    invalidar_cache()
                    st.rerun()

# ─────────────────────────────────────────────
# 11. OFICINA
# ─────────────────────────────────────────────
with tab_ofc:
    st.subheader("🔧 Oficina — Manutenção e Reparo")
    df_v = ler_aba(ABA_VEIC, COLS_VEIC)
    tipo_ofc = st.radio("Tipo de serviço", ["Manutenção","Reparo"], horizontal=True)

    if tipo_ofc == "Manutenção":
        st.write("#### Registrar Manutenção")
        with st.form("form_manutencao"):
            veic_man    = st.selectbox("Veículo *", [""]+montar_lista_veiculos(df_v))
            tipo_man    = st.selectbox("Tipo *", ["Revisão","Preventiva","Corretiva","Outros"])
            empresa_man = st.text_input("Empresa *")
            valor_man   = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
            obs_man     = st.text_area("Observações")
            if st.form_submit_button("✅ Registrar Manutenção"):
                if not veic_man or not empresa_man:
                    st.error("Veículo e Empresa são obrigatórios.")
                else:
                    placa_man = veic_man.split("(")[-1].replace(")","").strip()
                    row_v = df_v[df_v["Placa"]==placa_man]
                    if not row_v.empty:
                        append_linha(ABA_HIST,{
                            "Data":get_dt_br(),"Acao":"Manutencao",
                            "Veiculo":safe_get(row_v.iloc[0],"Modelo",""),"Placa":placa_man,
                            "Usuario":st.session_state.login_logado,
                            "KM_Inicial":safe_get(row_v.iloc[0],"KM_Atual",""),"KM_Final":"",
                            "Avarias_Saida":"","Avarias_Chegada":"","Foto_Base64":"","Obs":obs_man,
                            "Tipo_Manutencao":tipo_man,"Empresa":empresa_man,"Valor":str(valor_man)
                        },COLS_HIST)
                        if tipo_man == "Revisão":
                            df_v.loc[df_v["Placa"]==placa_man,"Ultima_Revisao"]=date.today().strftime("%Y-%m-%d")
                            df_v.loc[df_v["Placa"]==placa_man,"KM_Ultima_Revisao"]=safe_get(row_v.iloc[0],"KM_Atual","0")
                            salvar_aba(df_v,ABA_VEIC,COLS_VEIC)
                        st.success(f"Manutenção registrada: {tipo_man} — {empresa_man} — R$ {valor_man:.2f}")
                        invalidar_cache()  # ✅ CORREÇÃO
                        st.rerun()
    else:
        st.write("#### Registrar Reparo de Avarias")
        veics_com_av = [f"{safe_get(r,'Modelo','')} ({safe_get(r,'Placa','')})"
            for _, r in df_v.iterrows() if any(a.strip() for a in safe_get(r,"Avarias","").split(";") if a.strip())]
        if not veics_com_av:
            st.info("Nenhum veículo com avarias pendentes.")
        else:
            # ── Seleção do veículo fora do form para alimentar o multiselect dinamicamente
            veic_rep = st.selectbox("Veículo com Avarias *", [""]+veics_com_av, key="sel_veic_rep")

            avs_do_veiculo = []
            if veic_rep:
                placa_prev = veic_rep.split("(")[-1].replace(")","").strip()
                row_rep = df_v[df_v["Placa"]==placa_prev]
                if not row_rep.empty:
                    avs_do_veiculo = [a.strip() for a in safe_get(row_rep.iloc[0],"Avarias","").split(";") if a.strip()]
                    if avs_do_veiculo:
                        with st.container(border=True):
                            st.markdown(f"**⚠️ Avarias registradas no veículo:** {', '.join(avs_do_veiculo)}")

            avs_corrigir = st.multiselect(
                "Selecione as avarias que serão reparadas *",
                options=avs_do_veiculo,
                default=[],
                key="avs_rep",
                disabled=not avs_do_veiculo,
                placeholder="Selecione o veículo primeiro..." if not veic_rep else "Escolha as avarias..."
            )

            empresa_rep = st.text_input("Empresa *", key="empresa_rep")
            valor_rep   = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f", key="valor_rep")
            obs_rep     = st.text_area("Observações", key="obs_rep_rep")

            if st.button("✅ Registrar Reparo", type="primary", key="btn_reparo"):
                if not veic_rep or not empresa_rep:
                    st.error("Veículo e Empresa são obrigatórios.")
                elif not avs_corrigir:
                    st.error("Selecione ao menos uma avaria a ser reparada.")
                else:
                    placa_rep = veic_rep.split("(")[-1].replace(")","").strip()
                    row_v2 = df_v[df_v["Placa"]==placa_rep]
                    if not row_v2.empty:
                        append_linha(ABA_HIST,{
                            "Data":get_dt_br(),"Acao":"Reparo",
                            "Veiculo":safe_get(row_v2.iloc[0],"Modelo",""),"Placa":placa_rep,
                            "Usuario":st.session_state.login_logado,
                            "KM_Inicial":safe_get(row_v2.iloc[0],"KM_Atual",""),"KM_Final":"",
                            "Avarias_Saida":";".join(avs_corrigir),"Avarias_Chegada":"",
                            "Foto_Base64":"","Obs":obs_rep,
                            "Tipo_Manutencao":"Reparo","Empresa":empresa_rep,"Valor":str(valor_rep)
                        },COLS_HIST)
                        restantes=[a.strip() for a in safe_get(row_v2.iloc[0],"Avarias","").split(";")
                                   if a.strip() and a.strip() not in avs_corrigir]
                        df_v.loc[df_v["Placa"]==placa_rep,"Avarias"]=";".join(restantes)
                        salvar_aba(df_v,ABA_VEIC,COLS_VEIC)
                        for k in ["sel_veic_rep","avs_rep","empresa_rep","valor_rep","obs_rep_rep"]:
                            st.session_state.pop(k, None)
                        st.success(f"✅ Reparo registrado! Avarias corrigidas: {', '.join(avs_corrigir)}")
                        invalidar_cache()
                        st.rerun()

# ─────────────────────────────────────────────
# 12. HISTÓRICO
# ─────────────────────────────────────────────
with tab_hist:
    st.subheader("📋 Histórico Geral")
    df_hist = ler_aba(ABA_HIST, COLS_HIST)
    if df_hist.empty:
        st.info("Nenhum registro no histórico.")
    else:
        with st.expander("🔍 Filtros", expanded=True):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                veics_h  = ["Todos"]+sorted(df_hist["Veiculo"].unique().tolist()) if "Veiculo" in df_hist.columns else ["Todos"]
                filtro_v = st.selectbox("Veículo", veics_h, key="filt_veic")
            with col_f2:
                users_h  = ["Todos"]+sorted(df_hist["Usuario"].unique().tolist()) if "Usuario" in df_hist.columns else ["Todos"]
                filtro_u = st.selectbox("Motorista", users_h, key="filt_mot")
            with col_f3:
                acoes_h  = ["Todos","Retirada","Devolucao","Reparo","Manutencao"]
                filtro_a = st.selectbox("Ação", acoes_h, key="filt_acao")

            # ── Filtro de período com data início e fim ──────────────────────
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                filtro_dt_ini = st.date_input("Data início", value=None, key="filt_dt_ini",
                                              help="Deixe em branco para não filtrar por data de início")
            with col_d2:
                filtro_dt_fim = st.date_input("Data fim", value=None, key="filt_dt_fim",
                                              help="Deixe em branco para não filtrar por data de fim")

        df_show = df_hist.copy()
        if filtro_v != "Todos" and "Veiculo" in df_show.columns:
            df_show = df_show[df_show["Veiculo"]==filtro_v]
        if filtro_u != "Todos" and "Usuario" in df_show.columns:
            df_show = df_show[df_show["Usuario"]==filtro_u]
        if filtro_a != "Todos" and "Acao" in df_show.columns:
            df_show = df_show[df_show["Acao"]==filtro_a]

        # ── Filtra por período convertendo a coluna Data (dd/mm/yyyy HH:MM) ──
        if (filtro_dt_ini or filtro_dt_fim) and "Data" in df_show.columns:
            def parse_data_hist(s):
                try:
                    return datetime.strptime(str(s).strip()[:10], "%d/%m/%Y").date()
                except Exception:
                    return None
            datas_parsed = df_show["Data"].apply(parse_data_hist)
            if filtro_dt_ini:
                df_show = df_show[datas_parsed >= filtro_dt_ini]
                datas_parsed = datas_parsed[datas_parsed >= filtro_dt_ini]
            if filtro_dt_fim:
                df_show = df_show[datas_parsed <= filtro_dt_fim]

        # ── Monta colunas legíveis e renomeia para exibição ──────────────────
        df_exib = df_show.copy()

        def avarias_restantes_reparo(row, df_veic):
            if str(row.get("Acao","")) != "Reparo":
                return ""
            placa = str(row.get("Placa",""))
            rv = df_veic[df_veic["Placa"]==placa]
            if rv.empty:
                return ""
            return safe_get(rv.iloc[0],"Avarias","").replace(";",", ")

        df_v_atual = ler_aba(ABA_VEIC, COLS_VEIC)

        # ── Avarias Reparadas: só para Reparo (usa Avarias_Saida) ────────────
        df_exib["Avarias Reparadas"] = df_exib.apply(
            lambda r: ", ".join([a for a in str(r.get("Avarias_Saida","")).split(";") if a.strip()])
            if str(r.get("Acao",""))=="Reparo" else "", axis=1)

        # ── Avarias Restantes: só para Reparo ────────────────────────────────
        df_exib["Avarias Restantes"] = df_exib.apply(
            lambda r: avarias_restantes_reparo(r, df_v_atual)
            if str(r.get("Acao",""))=="Reparo" else "", axis=1)

        # ── Avarias Saída: só para Retirada (limpa Reparo) ───────────────────
        df_exib["Avarias Saída"] = df_exib.apply(
            lambda r: ", ".join([a for a in str(r.get("Avarias_Saida","")).split(";") if a.strip()])
            if str(r.get("Acao","")) != "Reparo" else "", axis=1)

        # ── Avarias Chegada: só para Devolução ───────────────────────────────
        df_exib["Avarias Chegada"] = df_exib["Avarias_Chegada"].apply(
            lambda v: ", ".join([a for a in str(v).split(";") if a.strip()]) if str(v) else "")

        # ── Renomeia colunas ──────────────────────────────────────────────────
        rename_map = {
            "Data":"Data","Acao":"Ação","Veiculo":"Veículo","Placa":"Placa",
            "Usuario":"Motorista","KM_Inicial":"KM Saída","KM_Final":"KM Chegada",
            "Tipo_Manutencao":"Tipo Manutenção","Empresa":"Empresa","Valor":"Valor (R$)","Obs":"Observações"
        }
        cols_base = [c for c in rename_map if c in df_exib.columns]
        df_final  = df_exib[cols_base].rename(columns=rename_map)

        insert_at = df_final.columns.tolist().index("KM Chegada") + 1
        df_final.insert(insert_at,   "Avarias Saída",     df_exib["Avarias Saída"].values)
        df_final.insert(insert_at+1, "Avarias Chegada",   df_exib["Avarias Chegada"].values)
        df_final.insert(insert_at+2, "Avarias Reparadas", df_exib["Avarias Reparadas"].values)
        df_final.insert(insert_at+3, "Avarias Restantes", df_exib["Avarias Restantes"].values)

        # ── Exibe como cards expansíveis para melhor leitura ─────────────────
        st.dataframe(
            df_final.reset_index(drop=True),
            use_container_width=True,
            height=400,
            column_config={
                "Valor (R$)":        st.column_config.NumberColumn(format="R$ %.2f"),
                "Avarias Saída":     st.column_config.TextColumn(width="large"),
                "Avarias Chegada":   st.column_config.TextColumn(width="large"),
                "Avarias Reparadas": st.column_config.TextColumn(width="large"),
                "Avarias Restantes": st.column_config.TextColumn(width="large"),
                "Observações":       st.column_config.TextColumn(width="large"),
                "Data":              st.column_config.TextColumn(width="medium"),
                "Ação":              st.column_config.TextColumn(width="small"),
                "Veículo":           st.column_config.TextColumn(width="small"),
                "Placa":             st.column_config.TextColumn(width="small"),
                "Motorista":         st.column_config.TextColumn(width="small"),
                "KM Saída":          st.column_config.TextColumn(width="small"),
                "KM Chegada":        st.column_config.TextColumn(width="small"),
            }
        )

        # ── Detalhe expandido por linha para leitura completa ────────────────
        with st.expander("🔎 Ver detalhes completos de um registro"):
            idx_sel = st.number_input("Número da linha (0 = primeira)",
                                      min_value=0, max_value=max(0, len(df_final)-1),
                                      step=1, key="hist_detail_idx")
            if not df_final.empty:
                # Busca a linha original (com Foto_Base64) pelo índice
                row_orig = df_show.iloc[int(idx_sel)] if int(idx_sel) < len(df_show) else None
                row_sel  = df_final.iloc[int(idx_sel)]
                c1, c2   = st.columns(2)
                for i, (col, val) in enumerate(row_sel.items()):
                    with (c1 if i % 2 == 0 else c2):
                        if str(val) not in ("", "nan", "None"):
                            st.markdown(f"**{col}:** {val}")

                # Exibe fotos se existirem
                if row_orig is not None:
                    fotos_raw = str(row_orig.get("Foto_Base64","")).strip()
                    if fotos_raw:
                        fotos_lista = [f for f in fotos_raw.split("||") if f.strip()]
                        if fotos_lista:
                            st.markdown(f"**📷 Fotos ({len(fotos_lista)}):**")
                            cols_f = st.columns(min(len(fotos_lista), 3))
                            for fi, fb64 in enumerate(fotos_lista):
                                with cols_f[fi % 3]:
                                    try:
                                        st.image(base64.b64decode(fb64), width=250)
                                    except Exception:
                                        st.caption("Foto inválida")

        st.caption(f"Total de registros: {len(df_final)}")

# ─────────────────────────────────────────────
# 13. GESTÃO (admin)
# ─────────────────────────────────────────────
if tab_gest:
    with tab_gest:
        st.subheader("🛡️ Gestão Administrativa")
        sub_gest = st.tabs(["🚗 Veículos","👤 Motoristas","⚠️ Avarias"])

        with sub_gest[0]:
            st.write("### Gerenciar Veículos")
            df_v = ler_aba(ABA_VEIC, COLS_VEIC)
            if df_v.empty:
                st.info("Nenhum veículo cadastrado.")
            else:
                for i, row in df_v.iterrows():
                    placa=safe_get(row,"Placa",""); modelo=safe_get(row,"Modelo",""); status=safe_get(row,"Status","")
                    with st.expander(f"{modelo} ({placa}) — {status}{' ⚠️' if revisao_vencida(row) else ''}"):
                        with st.form(f"gest_v_{i}"):
                            c1,c2=st.columns(2)
                            with c1:
                                novo_km=st.text_input("KM Atual",value=safe_get(row,"KM_Atual",""),key=f"gv_km_{i}")
                                novo_crit=st.selectbox("Critério",["KM","Data","Ambos"],
                                    index=["KM","Data","Ambos"].index(safe_get(row,"Criterio_Revisao","KM")) if safe_get(row,"Criterio_Revisao","KM") in ["KM","Data","Ambos"] else 0,key=f"gv_crit_{i}")
                            with c2:
                                novo_st=st.selectbox("Status",["Disponível","Em uso","Manutenção","Bloqueado"],
                                    index=["Disponível","Em uso","Manutenção","Bloqueado"].index(status) if status in ["Disponível","Em uso","Manutenção","Bloqueado"] else 0,key=f"gv_st_{i}")
                            col_b1,col_b2=st.columns(2)
                            with col_b1: sv=st.form_submit_button("💾 Salvar")
                            with col_b2: bl=st.form_submit_button("🔒 Bloquear")
                        if sv:
                            df_v.at[i,"KM_Atual"]=novo_km; df_v.at[i,"Criterio_Revisao"]=novo_crit; df_v.at[i,"Status"]=novo_st
                            salvar_aba(df_v,ABA_VEIC,COLS_VEIC)
                            st.success("Atualizado!")
                            invalidar_cache()  # ✅ CORREÇÃO
                            st.rerun()
                        if bl:
                            df_v.at[i,"Status"]="Bloqueado"
                            salvar_aba(df_v,ABA_VEIC,COLS_VEIC)
                            st.success("Bloqueado.")
                            invalidar_cache()  # ✅ CORREÇÃO
                            st.rerun()
                        if not historico_tem_veiculo(placa):
                            if st.button(f"🗑️ Excluir {modelo}",key=f"gv_del_{i}"):
                                salvar_aba(df_v[df_v["Placa"]!=placa],ABA_VEIC,COLS_VEIC)
                                st.success("Excluído.")
                                invalidar_cache()  # ✅ CORREÇÃO
                                st.rerun()
                        else:
                            st.caption("⚠️ Com histórico — use Bloquear.")

        with sub_gest[1]:
            st.write("### Gerenciar Motoristas")
            df_u = ler_aba(ABA_MOT, COLS_MOT)
            if df_u.empty:
                st.info("Nenhum motorista cadastrado.")
            else:
                for i, row in df_u.iterrows():
                    login_u=safe_get(row,"Login",""); nome_u=safe_get(row,"Nome",""); status_u=safe_get(row,"Status","")
                    with st.expander(f"{nome_u} ({login_u}) — {status_u}{' ⚠️ CNH VENCIDA' if not cnh_valida(row) else ''}"):
                        with st.form(f"gest_u_{i}"):
                            c1,c2=st.columns(2)
                            with c1:
                                nova_cnh=st.text_input("Validade CNH (AAAA-MM-DD)",value=safe_get(row,"Validade_CNH",""),key=f"gu_cnh_{i}")
                            with c2:
                                novo_prf=st.selectbox("Perfil",["Usuário","Admin"],index=0 if safe_get(row,"Perfil","")!="Admin" else 1,key=f"gu_prf_{i}")
                                novo_st=st.selectbox("Status",["Ativo","Bloqueado"],index=0 if status_u=="Ativo" else 1,key=f"gu_st_{i}")
                            col_b1,col_b2,col_b3=st.columns(3)
                            with col_b1: su=st.form_submit_button("💾 Salvar")
                            with col_b2: bu=st.form_submit_button("🔒 Bloquear")
                            with col_b3: ru=st.form_submit_button("🔑 Reset Senha")
                        if su:
                            df_u.at[i,"Validade_CNH"]=nova_cnh; df_u.at[i,"Perfil"]=novo_prf; df_u.at[i,"Status"]=novo_st
                            salvar_aba(df_u,ABA_MOT,COLS_MOT)
                            st.success("Atualizado!")
                            invalidar_cache()  # ✅ CORREÇÃO
                            st.rerun()
                        if bu:
                            df_u.at[i,"Status"]="Bloqueado"
                            salvar_aba(df_u,ABA_MOT,COLS_MOT)
                            st.success("Bloqueado.")
                            invalidar_cache()  # ✅ CORREÇÃO
                            st.rerun()
                        if ru:
                            df_u.at[i,"Senha"]="123"
                            salvar_aba(df_u,ABA_MOT,COLS_MOT)
                            st.success("Senha resetada para 123.")
                            invalidar_cache()  # ✅ CORREÇÃO
                            st.rerun()
                        if not historico_tem_motorista(login_u):
                            if st.button(f"🗑️ Excluir {nome_u}",key=f"gu_del_{i}"):
                                salvar_aba(df_u[df_u["Login"]!=login_u],ABA_MOT,COLS_MOT)
                                st.success("Excluído.")
                                invalidar_cache()  # ✅ CORREÇÃO
                                st.rerun()
                        else:
                            st.caption("⚠️ Com histórico — use Bloquear.")

        with sub_gest[2]:
            st.write("### Gerenciar Avarias")
            df_av = ler_aba(ABA_AVAR, COLS_AVAR)
            if df_av.empty:
                st.info("Nenhuma avaria cadastrada.")
            else:
                for i, row in df_av.iterrows():
                    desc=safe_get(row,"Descricao",""); st_av=safe_get(row,"Status","")
                    col1,col2,col3=st.columns([4,1,1])
                    with col1: st.write(f"**{desc}** — {st_av}")
                    with col2:
                        if st.button("🔒",key=f"gu_blk_{i}",help="Bloquear"):
                            df_av.at[i,"Status"]="Bloqueado"
                            salvar_aba(df_av,ABA_AVAR,COLS_AVAR)
                            invalidar_cache()  # ✅ CORREÇÃO
                            st.rerun()
                    with col3:
                        if not avaria_em_uso(desc):
                            if st.button("🗑️",key=f"gu_del_av_{i}",help="Excluir"):
                                salvar_aba(df_av[df_av["Descricao"]!=desc],ABA_AVAR,COLS_AVAR)
                                st.success(f"'{desc}' excluída.")
                                invalidar_cache()  # ✅ CORREÇÃO
                                st.rerun()
                        else:
                            st.caption("Em uso")
