import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Frota Empresa", page_icon="🚗")
st.title("🚗 Gestão de Frota - Checklist Completo")

# 1. Lista de Veículos Atualizada
veiculos_dados = {
    "Prisma": "FNZ6B39",
    "UP": "GCP3490",
    "Saveiro": "SUO3J14",
    "Strada": "TEQ3I82",
    "Onix": "FPQ7B62"
}
lista_exibicao = [f"{nome} ({placa})" for nome, placa in veiculos_dados.items()]

# 2. Lista de Avarias (Mapa 1 a 15)
mapa_pecas = [
    "Nenhuma (Veículo OK)", "1. Párachoques Dianteiro", "2. Farol Esquerdo", "3. Farol Direito",
    "4. Capô", "5. Para-brisa", "6. Teto", "7. Porta Dianteira Esq.",
    "8. Porta Traseira Esq.", "9. Porta Dianteira Dir.", "10. Porta Traseira Dir.",
    "11. Lateral Traseira Esq.", "12. Lateral Traseira Dir.", "13. Párachoques Traseiro",
    "14. Tampa do Porta-malas", "15. Lanterna Traseira"
]

arquivo_dados = "historico_frota_final.csv"

if not os.path.exists(arquivo_dados):
    df_init = pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "Estado_Veiculo", "Observações"])
    df_init.to_csv(arquivo_dados, index=False)

tab1, tab2, tab3 = st.tabs(["📤 Retirada (Checklist Inicial)", "📥 Devolução (Checklist Final)", "📋 Auditoria"])

# --- ABA DE RETIRADA (Passo 1 e 8) ---
with tab1:
    st.header("Checklist de Saída")
    veiculo_s = st.selectbox("Selecione o Veículo", lista_exibicao, key="sel_s")
    nome_s = st.text_input("Nome do Motorista", key="nom_s")
    km_s = st.number_input("KM Inicial", min_value=0, step=1, key="km_s")
    
    st.subheader("🔍 Estado Inicial do Veículo")
    avaria_s = st.multiselect("Se houver danos prévios, selecione as posições (1-15):", mapa_pecas, key="ava_s")
    obs_s = st.text_area("Observações de saída:", key="obs_s")
    
    if st.button("Confirmar Saída e Gerar Registro"):
        if nome_s:
            estado = ", ".join(avaria_s) if avaria_s else "Nenhum dano"
            nova_linha = [datetime.now().strftime("%d/%m/%Y %H:%M"), "SAÍDA", veiculo_s, nome_s, km_s, estado, obs_s]
            df = pd.read_csv(arquivo_dados)
            df.loc[len(df)] = nova_linha
            df.to_csv(arquivo_dados, index=False)
            st.success(f"Saída do {veiculo_s} autorizada para {nome_s}!")
        else:
            st.error("O nome do motorista é obrigatório.")

# --- ABA DE DEVOLUÇÃO (Passo 4 e 5) ---
with tab2:
    st.header("Checklist de Devolução")
    veiculo_d = st.selectbox("Selecione o Veículo", lista_exibicao, key="sel_d")
    km_d = st.number_input("KM Final", min_value=0, step=1, key="km_d")
    
    st.subheader("🛠️ Reporte de Ocorrências no Uso")
    avaria_d = st.multiselect("Se houver novos danos, selecione as posições:", mapa_pecas, key="ava_d")
    obs_d = st.text_area("Descrição de avarias/limpeza/combustível:", key="obs_d")
    foto = st.file_uploader("Anexar foto do dano (Obrigatório em caso de sinistro)", type=["jpg", "png", "jpeg"], key="foto_d")
    
    if st.button("Confirmar Devolução"):
        estado_d = ", ".join(avaria_d) if avaria_d else "Sem novos danos"
        status_foto = "COM FOTO" if foto else "SEM FOTO"
        nova_linha = [datetime.now().strftime("%d/%m/%Y %H:%M"), "DEVOLUÇÃO", veiculo_d, "N/A", km_d, estado_d, f"{obs_d} ({status_foto})"]
        df = pd.read_csv(arquivo_dados)
        df.loc[len(df)] = nova_linha
        df.to_csv(arquivo_dados, index=False)
        st.success("Devolução registada! O veículo foi verificado.")

# --- ABA DE AUDITORIA (Passo 6) ---
with tab3:
    st.header("Histórico de Uso e Avarias")
    if os.path.exists(arquivo_dados):
        df_log = pd.read_csv(arquivo_dados)
        st.dataframe(df_log)
        csv = df_log.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar Relatório para Auditoria", data=csv, file_name="auditoria_frota.csv", mime="text/csv")
