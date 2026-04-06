import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração
st.set_page_config(page_title="Gestão de Frota", page_icon="🚗")
st.title("🚗 Sistema de Memória de Frota")

# 1. Dados dos Veículos
veiculos_dados = {
    "Prisma": "FNZ6B39", "UP": "GCP3490", "Saveiro": "SUO3J14",
    "Strada": "TEQ3I82", "Onix": "FPQ7B62"
}
lista_exibicao = [f"{n} ({p})" for n, p in veiculos_dados.items()]

# 2. Mapa de Peças com Código 0
mapa_pecas = [
    "0. Veículo Reparado / Sem Avarias", "1. Párachoques Dianteiro", "2. Farol Esquerdo", 
    "3. Farol Direito", "4. Capô", "5. Para-brisa", "6. Teto", "7. Porta Dianteira Esq.",
    "8. Porta Traseira Esq.", "9. Porta Dianteira Dir.", "10. Porta Traseira Dir.",
    "11. Lateral Traseira Esq.", "12. Lateral Traseira Dir.", "13. Párachoques Traseiro",
    "14. Tampa do Porta-malas", "15. Lanterna Traseira"
]

# Arquivos de Dados
arq_historico = "historico_geral.csv"
arq_estado_atual = "estado_atual_veiculos.csv"

# Inicializar arquivos se não existirem
if not os.path.exists(arq_estado_atual):
    df_estado = pd.DataFrame({"Veículo": lista_exibicao, "Avarias_Atuais": "Sem Avarias"})
    df_estado.to_csv(arq_estado_atual, index=False)

if not os.path.exists(arq_historico):
    pd.DataFrame(columns=["Data", "Ação", "Veículo", "Usuário", "KM", "Danos_Registrados"]).to_csv(arq_historico, index=False)

def atualizar_estado_fixo(veiculo, novos_danos):
    df_est = pd.read_csv(arq_estado_atual)
    # Se selecionar Código 0, limpa tudo
    if "0. Veículo Reparado / Sem Avarias" in novos_danos:
        danos_finais = "Sem Avarias"
    else:
        # Pega o que já tinha e soma o novo (removendo duplicados)
        estado_antigo = df_est.loc[df_est['Veículo'] == veiculo, 'Avarias_Atuais'].values[0]
        lista_antiga = [] if estado_antigo == "Sem Avarias" else estado_antigo.split(" | ")
        danos_finais = " | ".join(sorted(list(set(lista_antiga + novos_danos))))
    
    df_est.loc[df_est['Veículo'] == veiculo, 'Avarias_Atuais'] = danos_finais
    df_est.to_csv(arq_estado_atual, index=False)

tab1, tab2, tab3 = st.tabs(["📤 Saída", "📥 Chegada", "📋 Auditoria"])

# --- FUNÇÃO PARA MOSTRAR ESTADO ATUAL ---
def mostrar_status(v):
    df_est = pd.read_csv(arq_estado_atual)
    status = df_est.loc[df_est['Veículo'] == v, 'Avarias_Atuais'].values[0]
    st.warning(f"**Estado Atual do {v}:** {status}")

with tab1:
    st.header("Checklist de Saída")
    v_s = st.selectbox("Selecione o Veículo", lista_exibicao, key="vs")
    mostrar_status(v_s) # Campo logo abaixo do veículo
    
    n_s = st.text_input("Motorista", key="ns")
    km_s = st.number_input("KM Inicial", min_value=0, key="ks")
    novas_av_s = st.multiselect("Registrar NOVOS danos na saída:", mapa_pecas, key="as")
    
    if st.button("Confirmar Saída"):
        if n_s:
            atualizar_estado_fixo(v_s, novas_av_s)
            nova_l = [datetime.now().strftime("%d/%m/%Y %H:%M"), "SAÍDA", v_s, n_s, km_s, ", ".join(novas_av_s) if novas_av_s else "Nenhum"]
            pd.read_csv(arq_historico).append(pd.Series(nova_l, index=pd.read_csv(arq_historico).columns), ignore_index=True).to_csv(arq_historico, index=False)
            st.success("Saída Registrada!")
            st.rerun()

with tab2:
    st.header("Checklist de Chegada")
    v_d = st.selectbox("Selecione o Veículo", lista_exibicao, key="vd")
    mostrar_status(v_d) # Campo logo abaixo do veículo
    
    km_d = st.number_input("KM Final", min_value=0, key="kd")
    novas_av_d = st.multiselect("Registrar NOVOS danos na chegada:", mapa_pecas, key="ad")
    
    if st.button("Confirmar Devolução"):
        atualizar_estado_fixo(v_d, novas_av_d)
        nova_l = [datetime.now().strftime("%d/%m/%Y %H:%M"), "DEVOLUÇÃO", v_d, "N/A", km_d, ", ".join(novas_av_d) if novas_av_d else "Nenhum"]
        pd.read_csv(arq_historico).append(pd.Series(nova_l, index=pd.read_csv(arq_historico).columns), ignore_index=True).to_csv(arq_historico, index=False)
        st.success("Devolução Registrada!")
        st.rerun()

with tab3:
    st.header("Auditoria")
    st.subheader("Situação Atual da Frota")
    st.table(pd.read_csv(arq_estado_atual))
    st.subheader("Histórico de Movimentações")
    st.dataframe(pd.read_csv(arq_historico))
