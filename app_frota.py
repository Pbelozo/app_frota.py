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

arquivo_dados = "historico_frota_v9.csv"

# Inicializar arquivo
if not os.path.exists(arquivo_dados):
    pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "Avarias_Saida", "Avarias_Chegada", "Observações"]).to_csv(arquivo_dados, index=False)

# Função para verificar o status atual do veículo
def verificar_status_veiculo(veiculo):
    if os.path.exists(arquivo_dados):
        df = pd.read_csv(arquivo_dados)
        filtro = df[df['Veículo'] == veiculo]
        if not filtro.empty:
            ultimo = filtro.iloc[-1]
            # Se o último registro do carro foi SAÍDA, ele está na rua
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
    v_s = st.selectbox("Selecione o Veículo para Saída", lista_exibicao, key="vs")
    
    status_s = verificar_status_veiculo(v_s)
    
    if status_s["acao"] == "SAÍDA":
        st.error(f"🚫 VEÍCULO EM USO: Este carro foi retirado por **{status_s['motorista']}**. É necessário registar a chegada antes de uma nova saída.")
    else:
        st.success("✅ Veículo disponível no pátio.")
        n_s = st.text_input("Nome do Motorista", key="ns")
        km_s = st.number_input("KM Inicial", min_value=0, step=1, key="ks")
        av_s = st.multiselect("Avarias identificadas na saída:", mapa_pecas, key="as", default=status_s["avarias"])
        obs_s = st.text_area("Observações de Saída:", key="os")
        
        if st.button("Confirmar Saída"):
            if n_s:
                nova_l = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Ação": "SAÍDA", "Veículo": v_s, "Usuário": n_s, "KM": km_s,
                    "Avarias_Saida": ", ".join(av_s) if av_s else "Nenhuma",
                    "Avarias_Chegada": "Pendente", "Observações": obs_s
                }])
                df_atual = pd.read_csv(arquivo_dados)
                df_final = pd.concat([df_atual, nova_l], ignore_index=True)
                df_final.to_csv(arquivo_dados, index=False)
                st.success("Saída registada com sucesso!")
                st.rerun()
            else:
                st.error("Por favor, insira o nome do motorista.")

# --- ABA DE CHEGADA ---
with tab2:
    st.header("Registar Chegada")
    v_d = st.selectbox("Selecione o Veículo para Chegada", lista_exibicao, key="vd")
    
    status_d = verificar_status_veiculo(v_d)
    
    if status_d["acao"] == "CHEGADA":
        st.info("ℹ️ Este veículo já se encontra no pátio.")
    else:
        st.warning(f"👤 Motorista que retirou: **{status_d['motorista']}**")
        km_d = st.number_input("KM Final", min_value=0, step=1, key="kd")
        # Traz as avarias da saída como padrão
        av_d = st.multiselect("Estado na chegada (Confirme se há algo novo):", mapa_pecas, default=status_d["avarias"], key="ad")
        obs_d = st.text_area("Observações de Chegada:", key="od")
        
        if st.button("Confirmar Chegada"):
            nova_l = pd.DataFrame([{
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Ação": "CHEGADA", "Veículo": v_d, "Usuário": status_d["motorista"],
                "KM": km_d, "Avarias_Saida": ", ".join(status_d["avarias"]) if status_d["avarias"] else "Nenhuma",
                "Avarias_Chegada": ", ".join(av_d) if av_d else "Nenhuma", "Observações": obs_d
            }])
            df_atual = pd.read_csv(arquivo_dados)
            df_final = pd.concat([df_atual, nova_l], ignore_index=True)
            df_final.to_csv(arquivo_dados, index=False)
            st.success("Chegada concluída!")
            st.rerun()

# --- ABA DE HISTÓRICO ---
with tab3:
    st.header("Auditoria de Frota")
    if os.path.exists(arquivo_dados):
        st.dataframe(pd.read_csv(arquivo_dados))
