import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

st.set_page_config(page_title="Frota Empresa", page_icon="🚗", layout="wide")
st.title("🚗 Gestão de Frota - Oficial")

carros = {"Prisma": "FNZ6B39", "UP": "GCP3490", "Saveiro": "SUO3J14", "Strada": "TEQ3I82", "Onix": "FPQ7B62"}
lista_v = [n + " (" + p + ")" for n, p in carros.items()]

pecas = ["1. Paralama dianteiro esquerdo", "2. Paralama dianteiro direito", "3. Párachoque dianteiro", "4. Capô", "5. Parabrisa", "6. Teto", "7. Porta dianteiro direito", "8. Porta traseira direito", "9. Porta dianteiro esquerdo", "10. Porta traseira esquerdo", "11. Paralama traseiro esquerdo", "12. Paralama traseiro direito", "13. Vidro traseiro", "14. Párachoque traseiro", "15. Pane mecânica / elétrica"]

arq = "gestao_frota_oficial.csv"

def get_status(v_alvo):
    if os.path.exists(arq):
        try:
            df = pd.read_csv(arq)
            df_v = df[df['Veículo'] == v_alvo]
            if not df_v.empty:
                ult = df_v.iloc[-1]
                return {"acao": ult['Ação'], "user": ult['Usuário'], "km": int(ult['KM']), "av": str(ult['Av_Totais']) if pd.notna(ult['Av_Totais']) else "Nenhuma"}
        except: pass
    return {"acao": "CHEGADA", "user": "Ninguém", "km": 0, "av": "Nenhuma"}

t1, t2, t3, t4 = st.tabs(["📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"])

# --- ABAS DE OPERAÇÃO (Mantidas conforme V26) ---
with t1:
    st.header("Registar Saída")
    v_s = st.selectbox("Veículo", lista_v, key="vs")
    st_s = get_status(v_s)
    if st_s["acao"] == "SAÍDA":
        st.error("🚫 BLOQUEADO: Veículo com " + str(st_s["user"]))
    else:
        val_cnh = st.date_input("Validade CNH", value=date.today(), key="cnh")
        if val_cnh < date.today():
            st.error("❌ CNH Vencida.")
        else:
            n_s = st.text_input("Motorista", key="ns")
            km_s = st.number_input("KM Inicial", min_value=st_s['km'], value=st_s['km'], step=1, key="ks")
            limpo = st_s['av'].replace(' | ', ',').replace('|', ',')
            d_av = [x.strip() for x in limpo.split(',')] if st_s['av'] != "Nenhuma" else []
            av_s = st.multiselect("Checklist Saída:", pecas, default=[x for x in d_av if x in pecas], key="as")
            ob_s = st.text_area("Obs:", key="os")
            if st.button("Confirmar Saída"):
                if n_s:
                    txt_av = ", ".join(av_s) if av_s else "Nenhuma"
                    nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "SAÍDA", "Veículo": v_s, "Usuário": n_s, "KM": km_s, "CNH": val_cnh.strftime("%d/%m/%Y"), "Av_Saida": txt_av, "Av_Chegada": "Pendente", "Av_Totais": txt_av, "Obs": ob_s}])
                    pd.concat([pd.read_csv(arq), nova], ignore_index=True).to_csv(arq, index=False)
                    st.success("Saída Ok!"); st.rerun()

with t2:
    st.header("Registar Chegada")
    v_d = st.selectbox("Veículo", lista_v, key="vd")
    st_d = get_status(v_d)
    if st_d["acao"] != "SAÍDA": st.info("ℹ️ No pátio.")
    else:
        km_d = st.number_input("KM Final", min_value=st_d['km'], value=st_d['km'], step=1, key="kd")
        n_av = st.multiselect("Novas avarias:", pecas, key="ad")
        if st.button("Confirmar Chegada"):
            txt_n = ", ".join(n_av) if n_av else "Nenhuma"
            l_b = [st_d['av']] if st_d['av'] != "Nenhuma" else []
            if txt_n != "Nenhuma": l_b.append(txt_n)
            nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "CHEGADA", "Veículo": v_d, "Usuário": st_d['user'], "KM": km_d, "CNH": "", "Av_Saida": st_d['av'], "Av_Chegada": txt_n, "Av_Totais": " | ".join(l_b) if l_b else "Nenhuma", "Obs": "Retorno"}])
            pd.concat([pd.read_csv(arq), nova], ignore_index=True).to_csv(arq, index=False)
            st.success("Chegada Ok!"); st.rerun()

with t3:
    st.header("🔧 Reparos")
    v_m = st.selectbox("Veículo", lista_v, key="vm")
    st_m = get_status(v_m)
    if st_m["av"] == "Nenhuma": st.success("✅ Sem avarias.")
    else:
        lista_at = [x.strip() for x in st_m['av'].replace('|', ',').split(',')]
        reparados = st.multiselect("Itens consertados:", lista_at, key="reparo")
        mec = st.text_input("Responsável", key="mec")
        if st.button("Registar Reparo"):
            if reparados and mec:
                rest = [i for i in lista_at if i not in reparados]
                n_av_t = " | ".join(rest) if rest else "Nenhuma"
                nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "REPARO", "Veículo": v_m, "Usuário": mec, "KM": st_m["km"], "CNH": "", "Av_Saida": "Reparo: " + ", ".join(reparados), "Av_Chegada": "", "Av_Totais": n_av_t, "Obs": "Manutenção"}])
                pd.concat([pd.read_csv(arq), nova], ignore_index=True).to_csv(arq, index=False)
                st.success("Reparo Ok!"); st.rerun()

# --- ABA 4: HISTÓRICO AJUSTADO ---
with t4:
    st.header("📋 Histórico de Auditoria")
    if os.path.exists(arq):
        df_visualizacao = pd.read_csv(arq)
        
        # 1. Selecionar apenas as colunas atuais (remove as antigas com erro de nome)
        colunas_certas = ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs"]
        df_visualizacao = df_visualizacao[colunas_certas]
        
        # 2. Limpeza: Substituir 'None', 'nan', 'N/A' e 'Pendente' por vazio para melhor leitura
        df_visualizacao = df_visualizacao.fillna("")
        df_visualizacao = df_visualizacao.replace(["None", "nan", "N/A", "Pendente"], "")
        
        # 3. Exibir com ajuste de largura por coluna
        st.dataframe(
            df_visualizacao,
            use_container_width=True,
            column_config={
                "Data": st.column_config.TextColumn("Data", width="medium"),
                "Av_Saida": st.column_config.TextColumn("Estado na Saída", width="large"),
                "Av_Chegada": st.column_config.TextColumn("Novos Danos", width="large"),
                "Av_Totais": st.column_config.TextColumn("Avarias Atuais (Soma)", width="large"),
                "Obs": st.column_config.TextColumn("Observações", width="medium"),
            }
        )
