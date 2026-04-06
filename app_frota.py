import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗")
st.title("🚗 Controlo de Frota com Memória")

# 1. Lista de Veículos
veiculos_dados = {
    "Prisma": "FNZ6B39", "UP": "GCP3490", "Saveiro": "SUO3J14",
    "Strada": "TEQ3I82", "Onix": "FPQ7B62"
}
lista_exibicao = [f"{n} ({p})" for n, p in veiculos_dados.items()]

# 2. Mapa de Peças (1 a 15)
mapa_pecas = [
    "1. Párachoques Dianteiro", "2. Farol Esquerdo", "3. Farol Direito",
    "4. Capô", "5. Para-brisa", "6. Teto", "7. Porta Dianteira Esq.",
    "8. Porta Traseira Esq.", "9. Porta Dianteira Dir.", "10. Porta Traseira Dir.",
    "11. Lateral Traseira Esq.", "12. Lateral Traseira Dir.", "13. Párachoques Traseiro",
    "14. Tampa do Porta-malas", "15. Lanterna Traseira"
]

arquivo_dados = "historico_frota_v5.csv"

# Inicializar arquivo
if not os.path.exists(arquivo_dados):
    pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "Avarias", "Observações"]).to_csv(arquivo_dados, index=False)

# Função para buscar a última avaria registrada do veículo
def buscar_ultima_avaria(veiculo):
    if os.path.exists(arquivo_dados):
        df = pd.read_csv(arquivo_dados)
        filtro = df[df['Veículo'] == veiculo]
        if not filtro.empty:
            ultima_avaria = filtro.iloc[-1]['Avarias']
            if ultima_avaria and ultima_avaria != "Nenhuma":
                return [a.strip() for a in ultima_avaria.split(",")]
    return []

tab1, tab2, tab3 = st.tabs(["📤 Saída", "📥 Chegada", "📋 Histórico"])

# --- ABA DE SAÍDA ---
with tab1:
    st.header("Registar Saída")
    v_s = st.selectbox("Veículo", lista_exibicao, key="vs")
    
    # Busca automática do estado atual
    avarias_anteriores = buscar_ultima_avaria(v_s)
    
    n_s = st.text_input("Motorista", key="ns")
    km_s = st.number_input("KM Inicial", min_value=0, step=1, key="ks")
    
    # O multiselect já começa com o que o carro tinha antes
    av_s = st.multiselect("Estado do veículo na saída (Confirme ou adicione):", 
                          mapa_pecas, default=avarias_anteriores, key="as")
    
    obs_s = st.text_area("Observações de saída:", key="os")
    
    if st.button("Confirmar Saída"):
        if n_s:
            nova_linha = pd.DataFrame([{
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Ação": "SAÍDA", "Veículo": v_s, "Usuário": n_s, "KM": km_s,
                "Avarias": ", ".join(av_s) if av_s else "Nenhuma", "Observações": obs_s
            }])
            df = pd.concat([pd.read_csv(arquivo_dados), nova_linha], ignore_index=True)
            df.to_csv(arquivo_dados, index=False)
            st.success("Saída registada!")
            st.rerun()
        else:
            st.error("Insira o nome do motorista.")

# --- ABA DE CHEGADA ---
with tab2:
    st.header("Registar Chegada")
    v_d = st.selectbox("Veículo", lista_exibicao, key="vd")
    
    # Busca automática do que foi marcado na saída
    avarias_na_saida = buscar_ultima_avaria(v_d)
    
    km_d = st.number_input("KM Final", min_value=0, step=1, key="kd")
    
    # Traz as avarias da saída e permite adicionar novas
    av_d = st.multiselect("Estado do veículo na chegada (Relate novos danos se houver):", 
                          mapa_pecas, default=avarias_na_saida, key="ad")
    
    obs_d = st.text_area("Observações de chegada:", key="od")
    
    if st.button("Confirmar Chegada"):
        nova_linha = pd.DataFrame([{
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Ação": "CHEGADA", "Veículo": v_d, "Usuário": "N/A", "KM": km_d,
            "Avarias": ", ".join(av_d) if av_d else "Nenhuma", "Observações": obs_d
        }])
        df = pd.concat([pd.read_csv(arquivo_dados), nova_linha], ignore_index=True)
        df.to_csv(arquivo_dados, index=False)
        st.success("Chegada registada!")
        st.rerun()

# --- ABA DE HISTÓRICO ---
with tab3:
    st.header("Auditoria")
    if os.path.exists(arquivo_dados):
        st.dataframe(pd.read_csv(arquivo_dados))
