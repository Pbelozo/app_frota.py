import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Frota Empresa", page_icon="🚗")
st.title("🚗 Gestão de Frota - Controlo de Fluxo")

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

arquivo_dados = "historico_frota_v8.csv"

# Inicializar arquivo
if not os.path.exists(arquivo_dados):
    pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "Avarias_Saida", "Avarias_Chegada", "Observações"]).to_csv(arquivo_dados, index=False)

# --- FUNÇÃO DE VERIFICAÇÃO DE STATUS ---
def verificar_status_veiculo(veiculo):
    if os.path.exists(arquivo_dados):
        df = pd.read_csv(arquivo_dados)
        filtro = df[df['Veículo'] == veiculo]
        if not filtro.empty:
            ultimo = filtro.iloc[-1]
            return {
                "acao": ultimo['Ação'],
                "motorista": ultimo['Usuário'],
                "avarias": str(ultimo['Avarias_Saida']).split(", ") if ultimo['Avarias_Saida'] != "Nenhuma" else []
            }
    return {"acao": "CHEGADA", "motorista": "Ninguém", "avarias": []}

tab1, tab2, tab3 = st.tabs(["📤 Saída", "📥 Chegada", "📋 Histórico"])

# --- ABA DE SAÍDA ---
with tab1:
    st.header("Registar Saída")
    v_s = st.selectbox("Veículo", lista_exibicao, key="vs")
    
    status_s = verificar_status_veiculo(v_s)
    
    if status_s["acao"] == "SAÍDA":
        st.error(f"🚫 BLOQUEADO: Este veículo foi retirado por **{status_s['motorista']}** e ainda não retornou.")
    else:
        st.success("✅ Veículo disponível para saída.")
        n_s = st.text_input("Motorista", key="ns")
        km_s = st.number_input("KM Inicial", min_value=0, step=1, key="ks")
        av_s = st.multiselect("Avarias na saída:", mapa_pecas, key="as", default=status_s["avarias"])
        obs_s = st.text_area("Observações:", key="os")
        
        if st.button("Confirmar Saída"):
            if n_s
