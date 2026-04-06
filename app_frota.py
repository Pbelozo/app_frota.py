import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗")
st.title("🚗 Controlo de Frota - Checklist Digital")

# 1. LISTA DE VEÍCULOS ATUALIZADA
veiculos_dados = {
    "Prisma": "FNZ6B39",
    "UP": "GCP3490",
    "Saveiro": "SUO3J14",
    "Strada": "TEQ3I82",
    "Onix": "FPQ7B62"
}
lista_exibicao = [f"{nome} ({placa})" for nome, placa in veiculos_dados.items()]

# 2. LISTA DE AVARIAS (MAPA 1 A 15)
mapa_pecas = [
    "1. Párachoques Dianteiro", "2. Farol Esquerdo", "3. Farol Direito",
    "4. Capô", "5. Para-brisa", "6. Teto", "7. Porta Dianteira Esq.",
    "8. Porta Traseira Esq.", "9. Porta Dianteira Dir.", "10. Porta Traseira Dir.",
    "11. Lateral Traseira Esq.", "12. Lateral Traseira Dir.", "13. Párachoques Traseiro",
    "14. Tampa do Porta-malas", "15. Lanterna Traseira"
]

arquivo_dados = "historico_frota_v3.csv"

# Criar arquivo se não existir
if not os.path.exists(arquivo_dados):
    df_init = pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "Peça_Avaria", "Observações"])
    df_init.to_csv(arquivo_dados, index=False)

# --- INTERFACE ---
tab1, tab2, tab3 = st.tabs(["📤 Retirada", "📥 Devolução", "📋 Histórico/Auditoria"])

with tab1:
    st.header("Registar Saída")
    veiculo_sel = st.selectbox("Selecione o Veículo", lista_exibicao, key="saida_v")
    nome = st.text_input("Nome do Colaborador", key="saida_n")
    km_ini = st.number_input("KM Inicial", min_value=0, step=1, key="km_i")
    
    st.info("💡 Realize o checklist visual antes de sair.")
    if st.button("Confirmar Retirada"):
        if nome:
            nova_linha = [datetime.now().strftime("%d/%m/%Y %H:%M"), "SAÍDA", veiculo_sel, nome, km_ini, "Nenhum", "Saída OK"]
            df = pd.read_csv(arquivo_dados)
            df.loc[len(df)] = nova_linha
            df.to_csv(arquivo_dados, index=False)
            st.success(f"Saída de {veiculo_sel} registada com sucesso!")
        else:
            st.error("Por favor, insira o nome do motorista.")

with tab2:
    st.header("Registar Devolução")
    veiculo_dev = st.selectbox("Selecione o Veículo", lista_exibicao, key="dev_v")
    km_fim = st.number_input("KM Final", min_value=0, step=1, key="km_f")
    
    st.subheader("🛠️ Reporte de Avarias")
    houve_dano = st.radio("Houve algum dano ou ocorrência?", ["Não", "Sim"])
    
    peca_sel = "Nenhum"
    if houve_dano == "Sim":
        peca_sel = st.selectbox("Selecione a posição da avaria (1 a 15):", mapa_pecas)
    
    obs = st.text_area("Descrição detalhada (Opcional):")
    foto = st.file_uploader("Anexe a foto da avaria (se houver)", type=["jpg", "png", "jpeg"])
    
    if st.button("Confirmar Devolução"):
        status_foto = "COM FOTO" if foto else "SEM FOTO"
        nova_linha = [datetime.now().strftime("%d/%m/%Y %H:%M"), "DEVOLUÇÃO", veiculo_dev, "N/A", km_fim, peca_sel, f"{obs} ({status_foto})"]
        df = pd.read_csv(arquivo_dados)
        df.loc[len(df)] = nova_linha
        df.to_csv(arquivo_dados, index=False)
        st.success("Devolução concluída e dados guardados!")

with tab3:
    st.header("Auditoria de Frota")
    if os.path.exists(arquivo_dados):
        df_log = pd.read_csv(arquivo_dados)
        st.dataframe(df_log)
        
        # Botão para exportar
        csv = df_log.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar Relatório em Excel (CSV)", data=csv, file_name="relatorio_frota.csv", mime="text/csv")
