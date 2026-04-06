import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Frota Empresa", page_icon="🚗")
st.title("🚗 Gestão de Frota - Auditoria Individual")

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

arquivo_dados = "historico_frota_v15.csv"

# Inicializar arquivo se não existir
if not os.path.exists(arquivo_dados):
    cols = ["Data", "Ação", "Veículo", "Usuário", "KM", "Avarias_Saida", "Novas_Avarias_Chegada", "Avarias_Totais", "Observações"]
    pd.DataFrame(columns=cols).to_csv(arquivo_dados, index=False)

# --- FUNÇÃO CORRIGIDA: BUSCA DADOS APENAS DO VEÍCULO ESPECÍFICO ---
def buscar_dados_veiculo_especifico(veiculo_alvo):
    if os.path.exists(arquivo_dados):
        df = pd.read_csv(arquivo_dados)
        # FILTRO CRÍTICO: Isola apenas as linhas do veículo selecionado
        df_veiculo = df[df['Veículo'] == veiculo_alvo]
        
        if not df_veiculo.empty:
            ultimo = df_veiculo.iloc[-1] # Pega o último registo DESTE carro
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
    v_s = st.selectbox("Selecione o Veículo", lista_exibicao, key="vs")
    
    # Busca dados APENAS do veículo selecionado no selectbox acima
    status_s = buscar_dados_veiculo_especifico(v_s)
    
    if status_s["acao"] == "SAÍDA":
        st.error(f"🚫 BLOQUEADO: O {v_s} está com {status_s['motorista']}.")
    else:
        st.success(f"✅ Disponível. Último KM deste veículo: {status_s['km_ultimo']}")
        n_s = st.text_input("Nome do Motorista", key="ns")
        
        # O KM Inicial agora é blindado para cada carro individualmente
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
                df_f = pd.concat([pd.read_csv(arquivo_dados), pd.DataFrame([dados])], ignore_index=True)
                df_f.to_csv(arquivo_dados, index=False)
                st.success("Saída registada!")
                st.rerun()
            else:
                st.error("Insira o nome do motorista.")

with tab2:
    st.header("Registar Chegada")
    v_d = st.selectbox("Selecione o Veículo", lista_exibicao, key="vd")
    status_d = buscar_dados_veiculo_especifico(v_d)
    
    if status_d["acao"] == "CHEGADA":
        st.info(f"ℹ️ O {v_d} já está no pátio.")
    else:
        st.warning(f"👤 Motorista: {status_d['motorista']} | 🕒 Saída com KM: {status_d['km_ultimo']}")
        km_d = st.number_input("KM Final", min_value=status_d["km_ultimo"], value=status_d["km_ultimo"] + 1, step=1, key="kd")
        st.markdown(f"**⚠️ Avarias registadas na saída:** {status_d['avarias_totais']}")
        novas_av_d = st.multiselect("Novas avarias desta viagem:", mapa_pecas, key="ad")
        obs_d = st.text_area("Observações:", key="od")
        
        if st.button("Confirmar Chegada"):
            txt_novas = ", ".join(novas_av_d) if novas_av_d else "Nenhuma"
            lista_t = [status_d['avarias_totais']] if status_d['avarias_totais'] != "Nenhuma" else []
            if txt_novas != "Nenhuma": lista_t.append(txt_novas)
            
            dados_ch = {
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Ação": "CHEGADA", "Veículo": v_d, "Usuário": status_d["motorista"], "KM": km_d,
                "Avarias_Saida": status_d['avarias_totais'], "Novas_Avarias_Chegada": txt_novas,
                "Avarias_Totais": " | ".join(lista_t) if lista_t else "Nenhuma", "Observações": obs_d
            }
            df_f = pd.concat([pd.read_csv(arquivo_dados), pd.DataFrame([dados_ch])], ignore_index=True)
            df_f.to_csv(arquivo_dados, index=False)
            st.success("Chegada registada!")
