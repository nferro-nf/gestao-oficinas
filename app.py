import streamlit as st, gspread, pandas as pd
from datetime import datetime
import uuid

st.set_page_config(page_title="Gestão Oficinas", layout="wide", page_icon="🔧")

@st.cache_resource
def get_ws():
    creds = dict(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(creds)
    sh = client.open_by_url(st.secrets["spreadsheet"]["url"])
    try:
        ws = sh.worksheet("ordens")
    except:
        ws = sh.add_worksheet("ordens", 1000, 20)
    if not ws.row_values(1):
        ws.append_row(["id","nome","marca","modelo","ano","oficina","custo_total","status","data_entrada","telefone","servico"])
    return ws

# ... aqui cola o resto do teu código original de gestão ...
# Mas onde tinha db.execute("INSERT") troca por ws.append_row([...])
