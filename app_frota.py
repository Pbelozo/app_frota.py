import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# Configuração da página
st.set_page_config(page_title="Frota Empresa", page_icon="🚗")
st.title("🚗 Gestão de Frota - Oficial")

# 1. Lista de Veículos
carros = {
    "Prisma": "FNZ6B39", "UP": "GCP3490", "Saveiro": "SUO3J14",
    "Strada": "TEQ3I82", "Onix": "FPQ7B62"
}
lista_v = [f"{n} ({p})" for n, p in carros.items()]

# 2. Mapa de Peças
pecas = [
    "1. Paralama dianteiro esquerdo", "2. Paralama dianteiro direito", "3. Párachoque dianteiro",
    "4. Capô", "5. Parabrisa", "6. Teto", "7. Porta dianteiro direito",
    "8. Porta traseira direito", "9. Porta dianteiro esquerdo", "10. Porta traseira esquerdo",
    "11. Paralama traseiro esquerdo", "12. Paralama traseiro direito", "13. Vidro traseiro",
    "14. Párachoque traseiro", "15. Pane mecânica / elétrica"
]

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
                # Pegamos as 'Avarias Totais' para serem as novas 'Avarias de Saída'
                return {"acao": u['Ação'], "user": u['Usuário'], "km": int(u['KM']), "av": str(u['Av_Totais'])}
        except: pass
    return {"acao": "CHEGADA", "user": "Ninguém", "km": 0, "av": "Nenhuma"}

t1, t2, t3 = st.tabs(["📤 Saída", "📥 Chegada", "📋 Histórico"])

with t1:
    st.header("Registar Saída")
    v_s = st.selectbox("Veículo", lista_v, key="vs")
    st_s = get_status(v_s)
    
    if st_s["acao"] == "SAÍDA":
        st.error(f"🚫 BLOQUEADO: O veículo está com {st_s['user']}.")
    else:
        val_cnh = st.date_input("Validade da CNH", key="cnh")
        if val_cnh < date.today():
            st.error("❌ MOTORISTA NÃO AUTORIZADO: CNH Vencida.")
        else:
            st.success(f"✅ Último KM: {st_s['km']}")
            # EXIBIÇÃO DO ESTADO ATUAL HERDADO
            st.info(f"🔍 Estado atual herdado: {st_s['av']}")
            
            n_s = st.text_input("Motorista", key="ns")
            km_s = st.number_input("KM Inicial", min_value=st_s['km'], value=st_s['km'], step=1, key="ks")
            
            # Converte o texto herdado de volta para uma lista que o multiselect entende
            default_av = []
            if st_s['av'] != "Nenhuma":
                # Limpa espaços e separa por vírgula ou barra vertical
                default_av = [x.strip() for x in st_s['av'].replace('|', ',').split(',')]
                # Filtra para garantir que apenas itens da lista oficial sejam pré-selecionados
                default_av = [x for x in default_av if x in pecas]

            av_s = st.multiselect("Confirme as avarias na saída (ou adicione):", pecas, default=default_av, key="as")
            ob_s = st.text_area("Observações:", key="os")
