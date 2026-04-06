import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# Configuração da página
st.set_page_config(page_title="Frota Empresa", page_icon="🚗")
st.title("🚗 Gestão de Frota - Oficial")

# 1. Lista de Veículos
carros = {
    "Prisma": "FNZ6B39", "UP": "GCP3490", "Saveiro": "SUO3J14",
    "Strada": "TEQ3I82", "Onix": "FPQ7B62"
}
lista_v = [f"{n} ({p})" for n, p in carros.items()]

# 2. Mapa de Peças
pecas = [
    "1. Paralama dianteiro esquerdo", "2. Paralama dianteiro direito", "3. Párachoque dianteiro",
    "4. Capô", "5. Parabrisa", "6. Teto", "7. Porta dianteiro direito",
    "8. Porta traseira direito", "9. Porta dianteiro esquerdo", "10. Porta traseira esquerdo",
    "11. Paralama traseiro esquerdo", "12. Paralama traseiro direito", "13. Vidro traseiro",
    "14. Párachoque traseiro", "15. Pane mecânica / elétrica"
]

arq = "gestao_frota_oficial.csv"

if not os.path.exists(arq):
    cols = ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs"]
    pd.DataFrame(columns=cols).to_csv(arq, index=False)

def get_status(v_alvo):
    if os.path.exists(arq):
        try:
            df = pd.read_csv(arq)
            df_v = df[df['Veículo'] == v_alvo]
            if not df_v.empty:
                u = df_v.iloc[-1]
                return {"acao": u['Ação'], "user": u['Usuário'], "km": int(u['KM']), "av": str(u['Av_Totais'])}
        except: pass
    return {"acao": "CHEGADA", "user": "Ninguém", "km": 0, "av": "Nenhuma"}

t1, t2, t3 = st.tabs(["📤 Saída", "📥 Chegada", "📋 Histórico"])

with t1:
    st.header("Registar Saída")
    v_s = st.selectbox("Veículo", lista_v, key="vs")
    st_s = get_status(v_s)
    
    if st_s["acao"] == "SAÍDA":
        st.error("🚫 BLOQUEADO: O veículo está com " + st_s["user"])
    else:
        val_cnh = st.date_input("Validade da CNH", value=date.today(), key="cnh")
        
        if val_cnh < date.today():
            st.error("❌ MOTORISTA NÃO AUTORIZADO: CNH Vencida.")
        else:
            st.success("✅ Último KM registado: " + str(st_s["km"]))
            st.info("🔍 Avarias atuais: " + st_s["av"])
            
            n_s = st.text_input("Motorista", key="ns")
            km_s = st.number_input("KM Inicial", min_value=st_s['km'], value=st_s['km'], step=1, key="ks")
            
            default_av = []
            if st_s['av'] != "Nenhuma":
                itens_brutos = [x.strip() for x in st_s['av'].replace('|', ',').split(',')]
                default_av = [x for x in itens_brutos if x in pecas]

            av_s = st.multiselect("Confirme as avarias na saída:", pecas, default=default_av, key="as")
            ob_s = st.text_area("Observações:", key="os")
            
            if st.button("Confirmar Saída"):
                if n_s:
                    txt_av = ", ".join(av_s) if av_s else "Nenhuma"
                    nova_l = pd.DataFrame([{
                        "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "Ação": "SAÍDA", "Veículo": v_s, "Usuário": n_s, "KM": km_s,
                        "CNH": val_cnh.strftime("%d/%m/%Y"), "Av_Saida": txt_av,
                        "Av_Chegada": "Pendente", "Av_Totais": txt_av, "Obs": ob_s
                    }])
                    df_all = pd.concat([pd.read_csv(arq), nova_l], ignore_index=True)
                    df_all.to_csv(arq, index=False)
                    st.success("Saída registada!")
                    st.rerun()
                else:
                    st.error("Insira o nome do motorista.")

with t2:
    st.header("Registar Chegada")
    v_d = st.selectbox("Veículo", lista_v, key="vd")
    st_d = get_status(v_d)
    
    if st_d["acao"] == "CHEGADA":
        st.info("ℹ️ Veículo no pátio.")
    else:
        st.warning("👤 Motorista: " + st_d["user"] + " | KM Saída: " + str(st_d["km"]))
        km_d = st.number_input("KM Final", min_value=st_d['km'], value=st_d['km']+1, step=1, key="kd")
        
        st.write("**⚠️ Avarias registadas na saída:**")
        st.code(st_d["av"]) # Usando code block para evitar erros de markdown
        
        n_av = st.multiselect("Registrar NOVAS avarias:", pecas, key="ad")
        ob_d = st.text_area("Observações de Chegada:", key="od")
        
        if st.button("Confirmar Chegada"):
            txt_n = ", ".join(n_av) if n_av else "Nenhuma"
            l_t = [st_d['av']] if st_d['av'] != "Nenhuma" else []
            if txt_n != "Nenhuma": l_t.append(txt_n)
            
            nova_l = pd.DataFrame([{
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Ação": "CHEGADA", "Veículo": v_d, "Usuário": st_d['user'], "KM": km_d,
                "CNH": "N/A", "Av_Saida": st_d['av'], "Av_Chegada": txt_n,
                "Av_Totais": " | ".join(l_t) if l_t else "Nenhuma", "Obs": ob_d
            }])
            df_all = pd.concat([pd.read_csv(arq), nova_l], ignore_index=True)
            df_all.to_csv(arq, index=False)
            st.success("Chegada registada!")
            st.rerun()

with t3:
    st.header("Histórico")
    if os.path.exists(arq):
        st.dataframe(pd.read_csv(arq))
