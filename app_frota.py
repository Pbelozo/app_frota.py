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

# Função simplificada para evitar erros de digitação
def check_status(v_alvo):
    if os.path.exists(arquivo_dados):
        try:
            df = pd.read_csv(arquivo_dados)
            df_v = df[df['Veículo'] == v_alvo]
            if not df_v.empty:
                ult = df_v.iloc[-1]
                return {
                    "acao": ult['Ação'],
                    "motorista": ult['Usuário'],
                    "km_u": int(ult['KM']),
                    "av_t": str(ult['Avarias_Totais'])
                }
        except:
            pass
    return {"acao": "CHEGADA", "motorista": "Ninguém", "km_u": 0, "av_t": "Nenhuma"}

tab1, tab2, tab3 = st.tabs(["📤 Saída", "📥 Chegada", "📋 Histórico"])

with tab1:
    st.header("Registar Saída")
    v_s = st.selectbox("Selecione o Veículo", lista_exibicao, key="vs")
    status_s = check_status(v_s)
    
    if status_s["acao"] == "SAÍDA":
        st.error(f"🚫 BLOQUEADO: O {v_s} está com {status_s['motorista']}.")
    else:
        st.success(f"✅ Disponível. Último KM: {status_s['km_u']}")
        n_s = st.text_input("Nome do Motorista", key="ns")
        km_s = st.number_input("KM Inicial", min_value=status_s["km_u"], value=status_s["km_u"], step=1, key="ks")
        av_s = st.multiselect("Avarias identificadas na saída:", mapa_pecas, key="as")
        obs_s = st.text_area("Observações:", key="os")
        
        if st.button("Confirmar Saída"):
            if n_s:
                t_av_s = ", ".join(av_s) if av_s else "Nenhuma"
                d_s = {
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Ação": "SAÍDA", "Veículo": v_s, "Usuário": n_s, "KM": km_s,
                    "Avarias_Saida": t_av_s, "Novas_Avarias_Chegada": "Pendente",
                    "Avarias_Totais": t_av_s, "Observações": obs_s
                }
                df_at = pd.read_csv(arquivo_dados)
                df_fn = pd.concat([df_at, pd.DataFrame([d_s])], ignore_index=True)
                df_fn.to_csv(arquivo_dados, index=False)
                st.success("Saída registada!")
                st.rerun()
            else:
                st.error("Insira o nome do motorista.")

with tab2:
    st.header("Registar Chegada")
    v_d = st.selectbox("Selecione o Veículo", lista_exibicao, key="vd")
    status_d = check_status(v_d)
    
    if status_d["acao"] == "CHEGADA":
        st.info(f"ℹ️ O {v_d} já está no pátio.")
    else:
        st.warning(f"👤 Motorista: {status_d['motorista']} | Saída com KM: {status_d['km_u']}")
        km_d = st.number_input("KM Final", min_value=status_d["km_u"], value=status_d["km_u"] + 1, step=1, key="kd")
        st.markdown(f"**⚠️ Avarias na saída:** {status_d['av_t']}")
        n_av_d = st.multiselect("Novas avarias desta viagem:", mapa_pecas, key="ad")
        obs_d = st.text_area("Observações de Chegada:", key="od")
        
        if st.button("Confirmar Chegada"):
            t_novas = ", ".join(n_av_d) if n_av_d else "Nenhuma"
            l_t = [status_d['av_t']] if status_d['av_t'] != "Nenhuma" else []
            if t_novas != "Nenhuma": l_t.append(t_novas)
            
            d_ch = {
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Ação": "CHEGADA", "Veículo": v_d, "Usuário": status_d["motorista"], "KM": km_d,
                "Avarias_Saida": status_d['av_t'], "Novas_Avarias_Chegada": t_novas,
                "Avarias_Totais": " | ".join(l_t) if l_t else "Nenhuma", "Observações": obs_d
            }
            df_at = pd.read_csv(arquivo_dados)
            df_fn = pd.concat([df_at, pd.DataFrame([d_ch])], ignore_index=True)
            df_fn.to_csv(arquivo_dados, index=False)
            st.success("Chegada registada!")
            st.rerun()

with tab3:
    st.header("Histórico")
    if os.path.exists(arquivo_dados):
        st.dataframe(pd.read_csv(arquivo_dados))
