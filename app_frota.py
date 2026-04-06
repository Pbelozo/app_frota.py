import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os

st.set_page_config(page_title="Frota Empresa", page_icon="🚗", layout="wide")
st.title("🚗 Gestão de Frota - Oficial V28")

# --- CONFIGURAÇÃO DA FROTA E REVISÕES ---
# Definimos a quilometragem da última revisão e a periodicidade
carros_config = {
    "Prisma": {"placa": "FNZ6B39", "revisao_km": 50000, "revisao_data": date(2024, 12, 20), "intervalo_km": 10000},
    "UP": {"placa": "GCP3490", "revisao_km": 30000, "revisao_data": date(2025, 1, 15), "intervalo_km": 10000},
    "Saveiro": {"placa": "SUO3J14", "revisao_km": 45000, "revisao_data": date(2024, 11, 10), "intervalo_km": 10000},
    "Strada": {"placa": "TEQ3I82", "revisao_km": 15000, "revisao_data": date(2025, 5, 20), "intervalo_km": 10000},
    "Onix": {"placa": "FPQ7B62", "revisao_km": 20000, "revisao_data": date(2025, 3, 1), "intervalo_km": 10000}
}
lista_v = [n + " (" + c["placa"] + ")" for n, c in carros_config.items()]

pecas = ["1. Paralama dianteiro esquerdo", "2. Paralama dianteiro direito", "3. Párachoque dianteiro", "4. Capô", "5. Parabrisa", "6. Teto", "7. Porta dianteiro direito", "8. Porta traseira direito", "9. Porta dianteiro esquerdo", "10. Porta traseira esquerdo", "11. Paralama traseiro esquerdo", "12. Paralama traseiro direito", "13. Vidro traseiro", "14. Párachoque traseiro", "15. Pane mecânica / elétrica"]

arq = "gestao_frota_oficial.csv"

if not os.path.exists(arq):
    cols = ["Data", "Ação", "Veículo", "Usuário", "KM", "CNH", "Av_Saida", "Av_Chegada", "Av_Totais", "Obs", "Foto"]
    pd.DataFrame(columns=cols).to_csv(arq, index=False)

def get_status(v_alvo):
    nome_carro = v_alvo.split(" ")[0]
    if os.path.exists(arq):
        try:
            df = pd.read_csv(arq)
            df_v = df[df['Veículo'] == v_alvo]
            if not df_v.empty:
                ult = df_v.iloc[-1]
                return {"acao": ult['Ação'], "user": ult['Usuário'], "km": int(ult['KM']), "av": str(ult['Av_Totais']) if pd.notna(ult['Av_Totais']) else "Nenhuma"}
        except: pass
    return {"acao": "CHEGADA", "user": "Ninguém", "km": carros_config[nome_carro]["revisao_km"], "av": "Nenhuma"}

t1, t2, t3, t4 = st.tabs(["📤 Saída", "📥 Chegada", "🔧 Manutenção", "📋 Histórico"])

# --- ABA 1: SAÍDA COM ALERTAS DE REVISÃO E FOTO ---
with t1:
    st.header("Registar Saída")
    v_s = st.selectbox("Selecione o Veículo", lista_v, key="vs")
    st_s = get_status(v_s)
    
    # Lógica de Alerta de Revisão
    nome_c = v_s.split(" ")[0]
    conf = carros_config[nome_c]
    prox_km = conf["revisao_km"] + conf["intervalo_km"]
    prox_data = conf["revisao_data"] + timedelta(days=365)
    
    km_restante = prox_km - st_s["km"]
    dias_restante = (prox_data - date.today()).days

    if km_restante <= 500 or dias_restante <= 30:
        st.warning(f"⚠️ PROXIMA REVISÃO: {prox_km} KM ou em {prox_data.strftime('%d/%m/%Y')}")
        if km_restante <= 0 or dias_restante <= 0:
            st.error("🚨 ATENÇÃO: PRAZO DE REVISÃO VENCIDO!")

    if st_s["acao"] == "SAÍDA":
        st.error(f"🚫 BLOQUEADO: Veículo com {st_s['user']}")
    else:
        val_cnh = st.date_input("Validade CNH", value=date.today(), key="cnh")
        if val_cnh < date.today():
            st.error("❌ CNH Vencida.")
        else:
            n_s = st.text_input("Motorista", key="ns")
            km_s = st.number_input("KM Inicial", min_value=st_s['km'], value=st_s['km'], step=1)
            
            limpo = st_s['av'].replace(' | ', ',').replace('|', ',')
            d_av = [x.strip() for x in limpo.split(',')] if st_s['av'] != "Nenhuma" else []
            av_s = st.multiselect("Checklist Saída:", pecas, default=[x for x in d_av if x in pecas])
            
            foto_s = st.file_uploader("Foto do Veículo (Saída)", type=["jpg", "png", "jpeg"], key="f_sai")
            if foto_s: st.image(foto_s, caption="Preview Saída", width=300)
            
            ob_s = st.text_area("Observações:", key="os")
            
            if st.button("Confirmar Saída"):
                if n_s:
                    txt_av = ", ".join(av_s) if av_s else "Nenhuma"
                    tem_foto = "Sim" if foto_s else "Não"
                    nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "SAÍDA", "Veículo": v_s, "Usuário": n_s, "KM": km_s, "CNH": val_cnh.strftime("%d/%m/%Y"), "Av_Saida": txt_av, "Av_Chegada": "Pendente", "Av_Totais": txt_av, "Obs": ob_s, "Foto": tem_foto}])
                    pd.concat([pd.read_csv(arq), nova], ignore_index=True).to_csv(arq, index=False)
                    st.success("Saída Registada!"); st.rerun()

# --- ABA 2: CHEGADA COM FOTO ---
with t2:
    st.header("Registar Chegada")
    v_d = st.selectbox("Veículo", lista_v, key="vd")
    st_d = get_status(v_d)
    if st_d["acao"] != "SAÍDA": st.info("ℹ️ No pátio.")
    else:
        km_d = st.number_input("KM Final", min_value=st_d['km'], value=st_d['km'], step=1)
        n_av = st.multiselect("Novas avarias:", pecas)
        
        foto_d = st.file_uploader("Foto do Veículo (Chegada)", type=["jpg", "png", "jpeg"], key="f_che")
        if foto_d: st.image(foto_d, caption="Preview Chegada", width=300)
        
        if st.button("Confirmar Chegada"):
            txt_n = ", ".join(n_av) if n_av else "Nenhuma"
            l_b = [st_d['av']] if st_d['av'] != "Nenhuma" else []
            if txt_n != "Nenhuma": l_b.append(txt_n)
            tem_foto = "Sim" if foto_d else "Não"
            nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "CHEGADA", "Veículo": v_d, "Usuário": st_d['user'], "KM": km_d, "CNH": "", "Av_Saida": st_d['av'], "Av_Chegada": txt_n, "Av_Totais": " | ".join(l_b) if l_b else "Nenhuma", "Obs": "Retorno", "Foto": tem_foto}])
            pd.concat([pd.read_csv(arq), nova], ignore_index=True).to_csv(arq, index=False)
            st.success("Chegada Registada!"); st.rerun()

# --- ABA 3: REPAROS ---
with t3:
    st.header("🔧 Reparos")
    v_m = st.selectbox("Veículo", lista_v, key="vm")
    st_m = get_status(v_m)
    if st_m["av"] == "Nenhuma": st.success("✅ Sem avarias.")
    else:
        lista_at = [x.strip() for x in st_m['av'].replace('|', ',').split(',')]
        reparados = st.multiselect("Itens consertados:", lista_at)
        mec = st.text_input("Responsável", key="mec")
        if st.button("Registar Reparo"):
            if reparados and mec:
                rest = [i for i in lista_at if i not in reparados]
                nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ação": "REPARO", "Veículo": v_m, "Usuário": mec, "KM": st_m["km"], "CNH": "", "Av_Saida": "Conserto: "+", ".join(reparados), "Av_Chegada": "", "Av_Totais": " | ".join(rest) if rest else "Nenhuma", "Obs": "Manutenção", "Foto": "N/A"}])
                pd.concat([pd.read_csv(arq), nova], ignore_index=True).to_csv(arq, index=False)
                st.success("Atualizado!"); st.rerun()

# --- ABA 4: HISTÓRICO ---
with t4:
    st.header("📋 Histórico")
    if os.path.exists(arq):
        dfv = pd.read_csv(arq).fillna("").replace(["None", "nan"], "")
        st.dataframe(dfv, use_container_width=True)
