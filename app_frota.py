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

if not os.path.exists(arq):
    cols = ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs"]
    pd.DataFrame(columns=cols).to_csv(arq, index=False)

def get_status(v_alvo):
    if os.path.exists(arq):
        try:
            df = pd.read_csv(arq)
            df_v = df[df['Veículo'] == v_alvo]
            if not df_v.empty:
                u = df_v.iloc[-1]
                return {"acao": u['Ação'], "user": u['Usuário'], "km": int(u['KM']), "av": str(u['Av_Totais'])}
        except: pass
    return {"acao": "CHEGADA", "user": "Ninguém", "km": 0, "av": "Nenhuma"}

t1, t2, t3, t4 = st.tabs(["📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"])

with t1:
    st.header("Registar Saída")
    v_s = st.selectbox("Selecione o Veículo", lista_v, key="vs")
    st_s = get_status(v_s)
    if st_s["acao"] == "SAÍDA":
        st.error("🚫 BLOQUEADO: Veículo em uso por " + str(st_s["user"]))
    else:
        val_cnh = st.date_input("Validade da CNH", value=date.today(), key="cnh")
        if val_cnh < date.today():
            st.error("❌ CNH Vencida. Saída bloqueada.")
        else:
            st.success("✅ Último KM: " + str(st_s["km"]))
            n_s = st.text_input("Nome do Motorista", key="ns")
            km_s = st.number_input("KM Inicial", min_value=st_s['km'], value=st_s['km'], step=1, key="ks")
            d_av = []
            if st_s['av'] != "Nenhuma":
                itens = [x.strip() for x in st_s['av'].replace('|', ',').split(',')]
                d_av = [x for x in itens if x in pecas]
            av_s = st.multiselect("Checklist de Avarias:", pecas, default=d_av, key="as")
            ob_s = st.text_area("Observações:", key="os")
            if st.button("Confirmar Saída"):
                if n_s:
                    txt_av = ", ".join(av_s) if av_s else "Nenhuma"
                    nova_l = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "SAÍDA", "Veículo": v_s, "Usuário": n_s, "KM": km_s, "CNH": val_cnh.strftime("%d/%m/%Y"), "Av_Saida": txt_av, "Av_Chegada": "Pendente", "Av_Totais": txt_av, "Obs": ob_s}])
                    pd.concat([pd.read_csv(arq), nova_l], ignore_index=True).to_csv(arq, index=False)
                    st.success("Saída registada!")
                    st.rerun()
                else: st.error("Insira o nome.")

with t2:
    st.header("Registar Chegada")
    v_d = st.selectbox("Selecione o Veículo", lista_v, key="vd")
    st_d = get_status(v_d)
    if st_d["acao"] == "CHEGADA":
        st.info("ℹ️ Veículo no pátio.")
    else:
        st.warning("👤 Motorista: " + str(st_d["user"]))
        km_d = st.number_input("KM Final", min_value=st_d['km'], value=st_d
