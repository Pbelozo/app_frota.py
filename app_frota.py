import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Frota Empresa", page_icon="🚗")
st.title("🚗 Gestão de Frota - Auditoria de KM")

# 1. Lista de Veículos
veiculos_dados = {
    "Prisma": "FNZ6B39", "UP": "GCP3490", "Saveiro": "SUO3J14",
    "Strada": "TEQ3I82", "Onix": "FPQ7B62"
}
lista_exibicao = [f"{n} ({p})" for n, p in veiculos_dados.items()]

# 2. Mapa de Peças
mapa_pecas = [
    "1. Párachoques Dianteiro", "2. Farol Esquerdo", "3. Farol Direito",
    "4. Capô", "5. Para-brisa", "6. Teto", "7. Porta Dianteira Esq.",
    "8. Porta Traseira Esq.", "9. Porta Dianteira Dir.", "10. Porta Traseira Dir.",
    "11. Lateral Traseira Esq.", "12. Lateral Traseira Dir.", "13. Párachoques Traseiro",
    "14. Tampa do Porta-malas", "15. Lanterna Traseira"
]

arquivo_dados = "historico_frota_v13.csv"

if not os.path.exists(arquivo_dados):
    cols = ["Data", "Ação", "Veículo", "Usuário", "KM", "Avarias_Saida", "Novas_Avarias_Chegada", "Avarias_Totais", "Observações"]
    pd.DataFrame(columns=cols).to_csv(arquivo_dados, index=False)

def buscar_dados_veiculo(veiculo):
    if os.path.exists(arquivo_dados):
        df = pd.read_csv(arquivo_dados)
        filtro = df[df['Veículo'] == veiculo]
        if not filtro.empty:
            ultimo = filtro.iloc[-1]
            return {
                "acao": ultimo['Ação'],
                "motorista": ultimo['Usuário'],
                "km_ultimo": int(ultimo['KM']),
                "avarias_totais": str(ultimo['Avarias_Totais'])
            }
    return {"acao": "CHEGADA", "motorista": "Ninguém", "km_ultimo": 0, "avarias_totais": "Nenhuma"}

tab1, tab2, tab3 = st.tabs(["📤 Saída", "📥 Chegada", "📋 Histórico"])

with tab1:
    st.header("Registar Saída")
    v_s = st.selectbox("Veículo", lista_exibicao, key="vs")
    status_s = buscar_dados_veiculo(v_s)
    
    if status_s["acao"] == "SAÍDA":
        st.error(f"🚫 VEÍCULO EM USO por **{status_s['motorista']}**.")
    else:
        st.info(f"📍 KM de Saída automático (Último KM: {status_s['km_ultimo']})")
        n_s = st.text_input("Motorista", key="ns")
        km_s = st.number_input("KM Inicial", min_value=status_s["km_ultimo"], value=status_s["km_ultimo"], step=1, key="ks")
        av_s = st.multiselect("Avarias identificadas na saída:", mapa_pecas, key="as")
        obs_s = st.text_area("Observações:", key="os")
        
        if st.button("Confirmar Saída"):
            if n_s:
                txt_av_s = ", ".join(av_s) if av_s else "Nenhuma"
                dados = {
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Ação": "SAÍDA", "Veículo": v_s, "Usuário": n_s, "KM": km_s,
                    "Avarias_Saida": txt_av_s, "Novas_Avarias_Chegada": "N/A",
                    "Avarias_Totais": txt_av_s, "Observações": obs_s
                }
                df_atual = pd.read_csv(arquivo_dados)
                df_final = pd.concat([df_atual, pd.DataFrame([dados])], ignore_index=True)
                df_final.to_csv(arquivo_dados, index=False)
                st.success("Saída registada!")
                st.rerun()
            else:
                st.error("Insira o nome do motorista.")

with tab2:
    st.header("Registar Chegada")
    v_d = st.selectbox("Veículo", lista_exibicao, key="vd")
    status_d = buscar_dados_veiculo(v_d)
    
    if status_d["acao"] == "CHEGADA":
        st.info("ℹ️ Veículo disponível no pátio.")
    else:
        st.warning(f"👤 Motor
