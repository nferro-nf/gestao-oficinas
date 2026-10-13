import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, date
import uuid
import hashlib

st.set_page_config(page_title="Gestão Oficinas - Completo", layout="wide", page_icon="🔧")

# ========== FASE 8 - LOGIN MODULE ==========
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

@st.cache_resource
def get_client():
    creds = dict(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(creds)
    sh = client.open_by_url(st.secrets["spreadsheet"]["url"])
    return sh

def get_ws(nome, headers):
    sh = get_client()
    try:
        ws = sh.worksheet(nome)
    except:
        ws = sh.add_worksheet(nome, 2000, 30)
        ws.append_row(headers)
        return ws
    vals = ws.get_all_values()
    if not vals:
        ws.append_row(headers)
    elif vals[0]!= headers:
        # corrige header antigo - isso resolve seu KeyError
        ws.update('A1', [headers])
    return ws

def check_login(usuario, senha):
    ws_user = get_ws("usuarios", ["usuario","senha_hash","nome","perfil","ativo"])
    users = ws_user.get_all_records()
    df_u = pd.DataFrame(users)
    if df_u.empty:
        # cria admin padrão na primeira vez
        ws_user.append_row(["admin", hash_senha("admin123"), "Administrador", "admin", "SIM"])
        return usuario == "admin" and senha == "admin123", {"nome":"Administrador","perfil":"admin"}

    senha_h = hash_senha(senha)
    for u in users:
        if str(u['usuario']).lower() == usuario.lower() and str(u['senha_hash']) == senha_h and str(u['ativo']).upper() == "SIM":
            return True, u
    return False, None

# SESSION STATE LOGIN
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = None

def tela_login():
    st.title("🔐 Login - Gestão Oficinas")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/1995/1995458.png", width=100)
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", type="primary", use_container_width=True):
            ok, dados = check_login(usuario, senha)
            if ok:
                st.session_state.logado = True
                st.session_state.user = dados
                st.success(f"Bem-vindo {dados['nome']}!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")
        st.info("Primeiro acesso? Use admin / admin123 depois troque")

if not st.session_state.logado:
    tela_login()
    st.stop()

# ========== APP PRINCIPAL (só entra se logado) ==========
# HEADER LOGADO
c1, c2, c3 = st.columns([3,1,1])
c1.title(f"🔧 Gestão Oficinas - {st.session_state.user['nome']}")
c2.write(f"Perfil: **{st.session_state.user['perfil']}**")
if c3.button("Sair"):
    st.session_state.logado = False
    st.rerun()

#... SEU CÓDIGO DAS FASES 1-7 CONTINUA AQUI...
HEADERS_ORDENS = ["id","ordem","nome_oficina","cliente","tipo_equipamento","marca","modelo","ano","data_entrada","tempo_parado_dias","previsao_saida","sem_previsao","status","custo_total","telefone","servico"]

def load_df():
    ws = get_ws("ordens", HEADERS_ORDENS)
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    for col in HEADERS_ORDENS:
        if col not in df.columns:
            df[col] = ""
    return df, ws

def calc_tempo(data_str):
    try:
        dt = datetime.strptime(str(data_str), "%d/%m/%Y")
        return (datetime.now() - dt).days
    except:
        return 0

df, ws = load_df()

# DASHBOARD
c1,c2,c3,c4 = st.columns(4)
c1.metric("Total", len(df))
c2.metric("Sem Previsão", len(df[df['sem_previsao'].astype(str).str.upper()=="SIM"]) if not df.empty else 0)
c3.metric("Em Reparo", len(df[df['status'].str.contains('reparo', case=False, na=False)]) if not df.empty else 0)
c4.metric("Faturamento", f"{pd.to_numeric(df['custo_total'], errors='coerce').fillna(0).sum():,.0f} MT" if not df.empty else "0 MT")

tab1, tab2, tab3, tab4 = st.tabs(["📋 Ordens", "➕ Nova Ordem", "📊 Dashboard", "👥 Usuários"])

#... tab2 nova ordem igual ao código que te mandei antes...
with tab2:
    # só admin e recepcionista podem criar
    if st.session_state.user['perfil'] in ['admin','recepcao','mecanico']:
        with st.form("nova", clear_on_submit=True):
            col1,col2,col3 = st.columns(3)
            with col1:
                ordem = st.text_input("Nº Ordem *")
                cliente = st.text_input("Cliente *")
                nome_oficina = st.text_input("Oficina *", value="Oficina Central")
                tipo_equip = st.selectbox("Tipo *", ["Camião","Máquina Pesada","Empilhador Volvo","Gerador","Viatura","Outro"])
            with col2:
                marca = st.text_input("Marca", value="Volvo")
                modelo = st.text_input("Modelo")
                ano = st.text_input("Ano")
                telefone = st.text_input("Telefone")
            with col3:
                data_entrada = st.date_input("Entrada", value=date.today())
                status = st.selectbox("Status", ["Entrada","Em análise","Em reparo","Aguardando Peças","Pronto","Entregue"])
                sem_previsao = st.checkbox("Sem Previsão")
                previsao_saida = st.date_input("Previsão", value=date.today(), disabled=sem_previsao)
                custo = st.number_input("Custo MT", 0.0, step=100.0)
            servico = st.text_area("Serviço / Defeito *")
            if st.form_submit_button("💾 SALVAR", type="primary", use_container_width=True):
                if not ordem or not cliente:
                    st.warning("Preencha Ordem e Cliente")
                else:
                    linha = [str(uuid.uuid4())[:8], ordem, nome_oficina, cliente, tipo_equip, marca, modelo, ano, data_entrada.strftime("%d/%m/%Y"), (date.today()-data_entrada).days, "" if sem_previsao else previsao_saida.strftime("%d/%m/%Y"), "SIM" if sem_previsao else "NÃO", status, custo, telefone, servico]
                    ws.append_row(linha)
                    st.success(f"Ordem {ordem} salva!"); st.balloons()
                    st.cache_resource.clear()

with tab1:
    if df.empty:
        st.info("Nenhuma ordem")
    else:
        busca = st.text_input("Buscar")
        df_view = df.copy()
        if busca:
            df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(busca, case=False, na=False)).any(axis=1)]
        st.dataframe(df_view, use_container_width=True)

with tab4:
    if st.session_state.user['perfil'] == 'admin':
        st.subheader("Gestão de Usuários")
        with st.form("novo_user"):
            u = st.text_input("Usuário novo")
            n = st.text_input("Nome")
            s = st.text_input("Senha", type="password")
            p = st.selectbox("Perfil", ["admin","recepcao","mecanico","consulta"])
            if st.form_submit_button("Criar Usuário"):
                ws_u = get_ws("usuarios", ["usuario","senha_hash","nome","perfil","ativo"])
                ws_u.append_row([u, hash_senha(s), n, p, "SIM"])
                st.success(f"Usuário {u} criado")
    else:
        st.warning("Só admin pode gerenciar usuários")
