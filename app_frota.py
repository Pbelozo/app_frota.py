import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# Configuração da página
st.set_page_config(page_title="Frota Empresa", page_icon="🚗", layout="wide")
st.title("🚗 Gestão de Frota - Oficial")

# 1. Lista de Veículos (Simplificada para evitar erros de NameError)
carros = {
    "Prisma": "FNZ6B39", "UP": "GCP3490", "Saveiro": "SUO3J14",
    "Strada": "TEQ3I82", "Onix": "FPQ7B62"
}
# LINHA 13 CORRIGIDA (SEM F-STRING COMPLEXA)
lista_v = [n + " (" + p + ")" for n, p in carros.items()]

# 2. Mapa de Peças
pecas = [
    "1. Paralama dianteiro esquerdo", "2. Paralama dianteiro direito", "3. Párachoque dianteiro",
    "4. Capô", "5. Parabrisa", "6. Teto", "7. Porta dianteiro direito",
    "8. Porta traseira direito", "9. Porta dianteiro esquerdo", "10. Porta traseira esquerdo",
    "11. Paralama traseiro esquerdo", "12. Paralama traseiro direito", "13. Vidro traseiro",
    "14. Párachoque traseiro", "15. Pane mecânica / elétrica"
]

arq = "gestao_frota_oficial.csv"

# Inicializar banco de dados
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

# --- ABA 1: SAÍDA ---
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
                brutos = [x.strip() for x in st_s['av'].replace('|', ',').split(',')]
                d_av = [x for x in brutos if x in pecas]

            av_s = st.multiselect("Checklist de Avarias (Estado Atual):", pecas, default=d_av, key="as")
            ob_s = st.text_area("Observações de Saída:", key="os")
