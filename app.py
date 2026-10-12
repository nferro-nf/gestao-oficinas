import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, date
import uuid

st.set_page_config(page_title="Gestão Oficinas - Completo", layout="wide", page_icon="🔧")

@st.cache_resource
def get_ws():
    creds = dict(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(creds)
    sh = client.open_by_url(st.secrets["spreadsheet"]["url"])
    try:
        ws = sh.worksheet("ordens")
    except:
        ws = sh.add_worksheet("ordens", 2000, 30)
    headers = ["id","ordem","nome_oficina","cliente","tipo_equipamento","marca","modelo","ano","data_entrada","tempo_parado_dias","previsao_saida","sem_previsao","status","custo_total","telefone","servico"]
    if not ws.row_values(1):
        ws.append_row(headers)
    return ws

def load_df():
    ws = get_ws()
    df = pd.DataFrame(ws.get_all_records())
    return df, ws

def calc_tempo(data_str):
    try:
        dt = datetime.strptime(data_str, "%d/%m/%Y")
        return (datetime.now() - dt).days
    except:
        return 0

st.title("🔧 Gestão de Oficinas - Sistema Completo")

try:
    df, ws = load_df()
    st.success(f"✅ Conectado - {len(df)} ordens na nuvem")
except Exception as e:
    st.error(f"Erro: {e}"); st.stop()

# METRICAS
c1,c2,c3,c4 = st.columns(4)
c1.metric("Total Ordens", len(df))
c2.metric("Sem Previsão", len(df[df['sem_previsao'].astype(str).str.contains('SIM', na=False)]) if not df.empty else 0)
c3.metric("Em Reparo", len(df[df['status'].astype(str).str.contains('reparo', case=False, na=False)]) if not df.empty else 0)
if not df.empty:
    try:
        c4.metric("Faturamento", f"{pd.to_numeric(df['custo_total'], errors='coerce').sum():,.0f} MT")
    except: pass

tab1, tab2, tab3 = st.tabs(["📋 Ordens", "➕ Nova Ordem", "📊 Dashboard"])

with tab2:
    with st.form("nova", clear_on_submit=True):
        col1,col2,col3 = st.columns(3)
        with col1:
            ordem = st.text_input("Nº Ordem *", placeholder="2026-001")
            cliente = st.text_input("Cliente *", placeholder="TCM")
            nome_oficina = st.text_input("Nome da Oficina *", placeholder="Oficina Central Matola")
            tipo_equip = st.selectbox("Tipo Equipamento *", ["Camião","Máquina Pesada","Empilhador Volvo","Gerador","Viatura Ligeira","Outro"])
        with col2:
            marca = st.text_input("Marca", value="Volvo")
            modelo = st.text_input("Modelo")
            ano = st.text_input("Ano")
            telefone = st.text_input("Telefone")
        with col3:
            data_entrada = st.date_input("Data Entrada", value=date.today())
            status = st.selectbox("Status", ["Entrada","Em análise","Em reparo","Aguardando Peças","Pronto","Entregue"])
            sem_previsao = st.checkbox("Sem Previsão de Saída")
            previsao_saida = st.date_input("Previsão Saída", value=date.today(), disabled=sem_previsao)
            custo = st.number_input("Custo MT", 0.0, step=100.0)
        servico = st.text_area("Serviço / Defeito *")
        if st.form_submit_button("💾 SALVAR NO SHEETS", use_container_width=True, type="primary"):
            linha = [str(uuid.uuid4())[:8], ordem, nome_oficina, cliente, tipo_equip, marca, modelo, ano, data_entrada.strftime("%d/%m/%Y"), (date.today()-data_entrada).days, "" if sem_previsao else previsao_saida.strftime("%d/%m/%Y"), "SIM" if sem_previsao else "NÃO", status, custo, telefone, servico]
            ws.append_row(linha)
            st.success(f"Ordem {ordem} salva!"); st.balloons()
            st.cache_resource.clear()

with tab1:
    if df.empty:
        st.info("Nenhuma ordem")
    else:
        f1,f2 = st.columns(2)
        filtro_oficina = f1.selectbox("Filtrar Oficina", ["Todas"] + sorted(df['nome_oficina'].dropna().astype(str).unique().tolist()) if 'nome_oficina' in df.columns else ["Todas"])
        filtro_status = f2.selectbox("Filtrar Status", ["Todos"] + sorted(df['status'].dropna().astype(str).unique().tolist()) if 'status' in df.columns else ["Todos"])
        busca = st.text_input("Buscar")
        df_view = df.copy()
        if filtro_oficina != "Todas": df_view = df_view[df_view['nome_oficina'].astype(str)==filtro_oficina]
        if filtro_status != "Todos": df_view = df_view[df_view['status'].astype(str)==filtro_status]
        if busca: df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(busca, case=False, na=False)).any(axis=1)]
        df_view['tempo_parado_atual'] = df_view['data_entrada'].apply(calc_tempo)
        st.dataframe(df_view, use_container_width=True, height=500)
        st.download_button("📥 Baixar CSV", df_view.to_csv(index=False).encode('utf-8'), "ordens.csv", "text/csv")

with tab3:
    if not df.empty:
        c1,c2 = st.columns(2)
        if 'tipo_equipamento' in df.columns: c1.bar_chart(df['tipo_equipamento'].value_counts())
        if 'nome_oficina' in df.columns: c2.bar_chart(df['nome_oficina'].value_counts())
