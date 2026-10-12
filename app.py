import streamlit as st, gspread, pandas as pd
from datetime import datetime
import uuid

st.set_page_config(page_title="Gestão Oficinas", layout="wide")

@st.cache_resource
def get_ws():
    creds = dict(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(creds)
    sh = client.open_by_url(st.secrets["spreadsheet"]["url"])
    try:
        ws = sh.worksheet("ordens")
    except:
        ws = sh.add_worksheet("ordens", 1000, 20)
    # garante header
    if not ws.row_values(1):
        ws.append_row(["id","nome","marca","modelo","ano","oficina","custo_total","status","data_entrada","telefone","servico"])
    return ws

st.title("🔧 Gestão Oficinas - Teste Sheets")
try:
    ws = get_ws()
    st.success("✅ CONECTADO ao Google Sheets! ID: 11lUj29...")
    
    with st.form("form"):
        nome=st.text_input("Cliente")
        marca=st.text_input("Marca")
        if st.form_submit_button("Salvar TESTE"):
            ws.append_row([str(uuid.uuid4())[:8], nome, marca, "teste","2024","teste",100,"Entrada",datetime.now().strftime("%d/%m/%Y"),"","teste"])
            st.success("Salvo! Vai ver na planilha agora.")
            st.balloons()
    
    df=pd.DataFrame(ws.get_all_records())
    st.dataframe(df)

except Exception as e:
    st.error(f"❌ ERRO DE CONEXÃO: {e}")
    st.info("Verifica Secrets e se requirements.txt tem gspread")
