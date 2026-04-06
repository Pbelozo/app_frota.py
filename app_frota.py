import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Frota Empresa", page_icon="🚗")
st.title("🚗 Gestão de Frota - Auditoria Blindada")

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

arquivo_dados = "historico_frota_v12.csv"

# Inicializar arquivo se não existir
if not os.path.exists(arquivo_dados):
    cols = ["Data", "Ação", "Veículo", "Usuário", "KM", "Avarias_Saida", "Novas_Avarias_Chegada", "Avarias_Totais", "Observações"]
    pd.DataFrame(columns=cols).to_csv(arquivo_dados, index=False)

def verificar_status_veiculo(veiculo):
    if os.path.exists(arquivo_dados):
        df = pd.read_csv(arquivo_dados)
        filtro = df[df['Veículo'] == veiculo]
        if not filtro.empty:
            ultimo = filtro.iloc[-1]
            av_saida_str = str(ultimo['Avarias_Saida'])
            return {
                "acao": ultimo['Ação'],
                "motorista": ultimo['Usuário'],
                "avarias_saida": av_saida_str if av_saida_str != "Nenhuma" else "Nenhuma"
            }
    return {"acao": "CHEGADA", "motorista": "Ninguém", "avarias_saida": "Nenhuma"}

tab1, tab2, tab3 = st.tabs(["📤 Saída", "📥 Chegada", "📋 Histórico"])

with tab1:
    st.header("Registar Saída")
    v_s = st.selectbox("Veículo", lista_exibicao, key="vs")
    status_s = verificar_status_veiculo(v_s)
    
    if status_s["acao"] == "SAÍDA":
        st.error(f"🚫 VEÍCULO EM USO por **{status_s['motorista']}**.")
    else:
        n_s = st.text_input("Motorista", key="ns")
        km_s = st.number_input("KM Inicial", min_value=0, step=1, key="ks")
        av_s = st.multiselect("Avarias identificadas na saída:", mapa_pecas, key="as")
        obs_s = st.text_area("Observações:", key="os")
        
        if st.button("Confirmar Saída"):
            if n_s:
                txt_av_s = ", ".join(av_s) if av_s else "Nenhuma"
                dados_nova_l = {
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Ação": "SAÍDA", 
                    "Veículo": v_s, 
                    "Usuário": n_s, 
                    "KM": km_s,
                    "Avarias_Saida": txt_av_s, 
                    "Novas_Avarias_Chegada": "N/A",
                    "Avarias_Totais": txt_av_s, 
                    "Observações": obs_s
                }
                nova_l = pd.DataFrame([dados_nova_l])
                df_f = pd.concat([pd.read_csv(arquivo_dados), nova_l], ignore_index=True)
                df_f.to_csv(arquivo_dados, index=False)
                st.success("Saída registada!")
                st.rerun()
            else:
                st.error("Insira o nome do motorista.")

with tab2:
    st.header("Registar Chegada")
    v_d = st.selectbox("Veículo", lista_exibicao, key="vd")
    status_d = verificar_status_veiculo(v_d)
    
    if status_d["acao"] == "CHEGADA":
        st.info("ℹ️ Veículo disponível no pátio.")
    else:
        st.warning(f"👤 Motorista Responsável: **{status_d['motorista']}**")
        st.markdown(f"**⚠️ Avarias registadas na saída:** {status_d['avarias_saida']}")
        
        km_d = st.number_input("KM Final", min_value=0, step=1, key="kd")
        novas_av_d = st.multiselect("Registrar APENAS NOVOS danos desta viagem:", mapa_pecas, key="ad")
        obs_d = st.text_area("Observações de Chegada:", key="od")
        
        if st.button("Confirmar Chegada"):
            txt_novas = ", ".join(novas_av_d) if novas_av_d else "Nenhuma"
            
            # Soma inteligente para a coluna Avarias Totais
            lista_total = []
            if status_d['avarias_saida'] != "Nenhuma":
                lista_total.append(status_d['avarias_saida'])
            if txt_novas != "Nenhuma":
                lista_total.append(txt_novas)
            
            av_totais = " | ".join(lista_total) if lista_total else "Nenhuma"

            dados_chegada = {
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Ação": "CHEGADA", 
                "Veículo": v_d, 
                "Usuário": status_d["motorista"], 
                "KM": km_d,
                "Avarias_Saida": status_d['avarias_saida'],
                "Novas_Avarias_Chegada": txt_novas,
                "Avarias_Totais": av_totais,
                "Observações": obs_d
            }
            nova_l = pd.DataFrame([dados_chegada])
            df_f = pd.concat([pd.read_csv(arquivo_dados), nova_l], ignore_index=True)
            df_f.to_csv(arquivo_dados, index=False)
            st.success("Chegada concluída!")
            st.rerun()

with tab3:
    st.header("Histórico para Auditoria")
    if os.path.exists(arquivo_dados):
        st.dataframe(pd.read_csv(arquivo_dados))
