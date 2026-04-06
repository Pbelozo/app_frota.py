import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Frota Empresa", page_icon="🚗")
st.title("🚗 Gestão de Frota - Oficial")

# 1. Lista de Veículos
veiculos_dados = {
    "Prisma": "FNZ6B39", "UP": "GCP3490", "Saveiro": "SUO3J14",
    "Strada": "TEQ3I82", "Onix": "FPQ7B62"
}
lista_exibicao = [f"{n} ({p})" for n, p in veiculos_dados.items()]

# 2. Mapa de Peças
mapa_pecas = [
    "1. Paralama dianteiro esquerdo", "2. Paralama dianteiro direito", "3. Párachoque dianteiro",
    "4. Capô", "5. Parabrisa", "6. Teto", "7. Porta dianteiro direito",
    "8. Porta traseira direito", "9. Porta dianteiro esquerdo", "10. Porta traseira esquerdo",
    "11. Paralama traseiro esquerdo", "12. Paralama traseiro direito", "13. Vidro traseiro",
    "14. Párachoque traseiro", "15. Pane mecânica / elétrica"
]

# Nome do arquivo fixo
arquivo_dados = "gestao_frota_oficial.csv"

# Inicializar arquivo se não existir
if not os.path.exists(arquivo_dados):
    cols = ["Data", "Ação", "Veículo", "Usuário", "KM", "Avarias_Saida", "Novas_Avarias_Chegada", "Avarias_Totais", "Observações"]
    pd.DataFrame(columns=cols).to_csv(arquivo_dados, index=False)

def buscar_dados_veiculo_especifico(veiculo_alvo):
    if os.path.exists(arquivo_dados):
        try:
            df = pd.read_csv(arquivo_dados)
            df_veiculo = df[df['Veículo'] == veiculo_alvo]
            if not df_veiculo.empty:
                ultimo = df_veiculo.iloc[-1]
                return {
                    "acao": ultimo['Ação'],
                    "motorista": ultimo['Usuário'],
                    "km_ultimo": int(ultimo['KM']),
                    "avarias_totais": str(ultimo['Avarias_Totais'])
                }
        except:
            pass
    return {"acao": "CHEGADA", "motorista": "Ninguém", "km_ultimo": 0, "avarias_totais": "Nenhuma"}

tab1, tab2, tab3 = st.tabs(["📤 Saída", "📥 Chegada", "📋 Histórico"])

with tab1:
    st.header("Registar Saída")
    v_s = st.selectbox("Selecione o Veículo", lista_exibicao, key="vs")
    status_s = buscar_dados_veiculo_especifico(v_s)
    
    if status_s["acao"] == "SAÍDA":
        st.error(f"🚫 BLOQUEADO: O {v_s} está com {status_s['motorista']}.")
    else:
        st.success(f"✅ Disponível. Último KM: {status_s['km_ultimo']}")
        n_s = st.text_input("Nome do Motorista", key="ns")
        km_s = st.number_input("KM Inicial", min_value=status_s["km_ultimo"], value=status_s["km_ultimo"], step=1, key="ks")
        av_s = st.multiselect("Avarias identificadas na saída:", mapa_pecas, key="as")
        obs_s = st.text_area("Observações:", key="os")
        
        if st.button("Confirmar Saída"):
            if n_s:
                txt_av_s = ", ".join(av_s) if av_s else "Nenhuma"
                dados = {
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Ação": "SAÍDA", "Veículo": v_s, "Usuário": n_s, "KM": km_s,
                    "Avarias_Saida": txt_av_s, "Novas_Avarias_Chegada": "Pendente",
                    "Avarias_Totais": txt_av_s, "Observações": obs_s
                }
                df = pd.read_csv(arquivo_dados)
                df = pd.concat([df, pd.DataFrame([dados])], ignore_index=True)
                df.to_csv(arquivo_dados, index=False)
                st.success("Saída registada!")
                st.rerun()
            else:
                st.error("Insira o nome do motorista.")

with tab2:
    st.header("Registar Chegada")
    v_d = st.selectbox("Selecione o Veículo", lista_exibicao, key="vd")
    status_d = buscar_dados_
