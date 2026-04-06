import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Frota Empresa", page_icon="🚗")
st.title("🚗 Gestão de Frota - Auditoria Digital")

# 1. Lista de Veículos Atualizada
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

arquivo_dados = "historico_frota_v7.csv"

# Inicializar arquivo se não existir
if not os.path.exists(arquivo_dados):
    df_init = pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "Avarias_Saida", "Avarias_Chegada", "Observações"])
    df_init.to_csv(arquivo_dados, index=False)

# Função para buscar os dados da última saída
def buscar_dados_saida(veiculo):
    if os.path.exists(arquivo_dados):
        df = pd.read_csv(arquivo_dados)
        filtro = df[(df['Veículo'] == veiculo) & (df['Ação'] == "SAÍDA")]
        if not filtro.empty:
            ultimo = filtro.iloc[-1]
            av_s = str(ultimo['Avarias_Saida']).split(", ") if ultimo['Avarias_Saida'] != "Nenhuma" else []
            return {"motorista": ultimo['Usuário'], "avarias": av_s}
    return {"motorista": "Não identificado", "avarias": []}

tab1, tab2, tab3 = st.tabs(["📤 Saída", "📥 Chegada", "📋 Histórico"])

# --- ABA DE SAÍDA ---
with tab1:
    st.header("Registar Saída")
    v_s = st.selectbox("Veículo", lista_exibicao, key="vs")
    n_s = st.text_input("Motorista", key="ns")
    km_s = st.number_input("KM Inicial", min_value=0, step=1, key="ks")
    av_s = st.multiselect("Avarias na saída:", mapa_pecas, key="as")
    obs_s = st.text_area("Observações:", key="os")
    
    if st.button("Confirmar Saída"):
        if n_s:
            nova_l = pd.DataFrame([{
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Ação": "SAÍDA", "Veículo": v_s, "Usuário": n_s, "KM": km_s,
                "Avarias_Saida": ", ".join(av_s) if av_s else "Nenhuma",
                "Avarias_Chegada": "Pendente", "Observações": obs_s
            }])
            df_atual = pd.read_csv(arquivo_dados)
            df_final = pd.concat([df_atual, nova_l], ignore_index=True) # CORREÇÃO DO BUG
            df_final.to_csv(arquivo_dados, index=False)
            st.success("Saída registada!")
            st.rerun()
        else:
            st.error("Insira o nome do motorista.")

# --- ABA DE CHEGADA ---
with tab2:
    st.header("Registar Chegada")
    v_d = st.selectbox("Veículo", lista_exibicao, key="vd")
    
    dados = buscar_dados_saida(v_d)
    st.info(f"👤 **Motorista Responsável:** {dados['motorista']}")
    
    km_d = st.number_input("KM Final", min_value=0, step=1, key="kd")
    av_d = st.multiselect("Estado na chegada (Confirme os danos):", 
                          mapa_pecas, default=dados['avarias'], key="ad")
    
    obs_d = st.text_area("Observações de chegada:", key="od")
    
    if st.button("Confirmar Chegada"):
        nova_l = pd.DataFrame([{
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Ação": "CHEGADA", "Veículo": v_d, "Usuário": dados['motorista'],
            "KM": km_d, "Avarias_Saida": ", ".join(dados['avarias']) if dados['avarias'] else "Nenhuma",
            "Avarias_Chegada": ", ".join(av_d) if av_d else "Nenhuma", "Observações": obs_d
        }])
        df_atual = pd.read_csv(arquivo_dados)
        df_final = pd.concat([df_atual, nova_l], ignore_index=True) # CORREÇÃO DO BUG
        df_final.to_csv(arquivo_dados, index=False)
        st.success("Chegada vinculada ao motorista!")
        st.rerun()

# --- ABA DE HISTÓRICO ---
with tab3:
    st.header("Histórico de Auditoria")
    if os.path.exists(arquivo_dados):
        st.dataframe(pd.read_csv(arquivo_dados))
