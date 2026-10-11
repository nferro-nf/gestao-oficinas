import streamlit as st
import json
import os
from pathlib import Path

# Cria pasta de fotos
Path("fotos").mkdir(exist_ok=True)

ARQUIVO = "equipamentos.json"


def carregar():
    if not os.path.exists(ARQUIVO):
        return []
    with open(ARQUIVO, "r") as f:
        return json.load(f)


def salvar(dados):
    with open(ARQUIVO, "w") as f:
        json.dump(dados, f, indent=4)


equipamentos = carregar()

st.set_page_config(page_title="Gestão Oficinas - FASE 6", layout="wide")
st.title("🛠️ Sistema Gestão Oficinas - FASE 6 COM FOTO")

# DASHBOARD
col1, col2, col3, col4 = st.columns(4)
total_custo = sum(sum(m.get('custo', 0) for m in eq.get('manutencoes', [])) for eq in equipamentos)
col1.metric("Equipamentos", len(equipamentos))
col2.metric("Manutenções", sum(len(eq.get('manutencoes', [])) for eq in equipamentos))
col3.metric("Custo Total", f"{total_custo:,.2f} MT")
col4.metric("Oficinas", len(set(eq.get('oficina', '') for eq in equipamentos)))

aba1, aba2, aba3 = st.tabs(["📊 Dashboard", "➕ Novo", "🔧 Manutenção"])

with aba1:
    # --- GRÁFICO VOLTOU ---
    import pandas as pd

    if equipamentos:
        dados_grafico = []
        for eq in equipamentos:
            custo_eq = sum(m.get('custo', 0) for m in eq.get('manutencoes', []))
            dados_grafico.append({"Oficina": eq.get('oficina', 'Maputo'), "Custo": custo_eq})

        if dados_grafico:
            df = pd.DataFrame(dados_grafico)
            df_agrupado = df.groupby("Oficina")["Custo"].sum().reset_index()
            st.bar_chart(df_agrupado, x="Oficina", y="Custo")
            st.divider()

        # --- LISTA COM FOTOS (teu código atual) ---
        for eq in equipamentos:
            with st.container(border=True):
                c1, c2 = st.columns([1, 3])
                with c1:
                    if eq.get('foto') and os.path.exists(eq['foto']):
                        st.image(eq['foto'], width=150)
                    else:
                        st.write("📷 Sem foto")
                with c2:
                    st.subheader(f"{eq.get('matricula', 'SEM MAT')} - {eq.get('modelo', 'Sem modelo')}")
                    st.write(f"**Oficina:** {eq.get('oficina', 'Maputo')} | **Status:** {eq.get('status', 'Ativo')}")
                    custo_eq = sum(m.get('custo', 0) for m in eq.get('manutencoes', []))
                    if custo_eq > 20000:
                        st.error(f"🚨 ATENÇÃO - CUSTO ALTO: {custo_eq:,.2f} MT")
                    else:
                        st.write(f"Custo: {custo_eq:,.2f} MT")
                        st.write("📷 Sem foto")
                with c2:
                    st.subheader(f"{eq.get('matricula', 'SEM MAT')} - {eq.get('modelo', 'Sem modelo')}")
                    st.write(f"**Oficina:** {eq.get('oficina', 'Maputo')} | **Status:** {eq.get('status', 'Ativo')}")
                    custo_eq = sum(m.get('custo', 0) for m in eq.get('manutencoes', []))
                    # ALERTA DE CUSTO ALTO - Já deixei pronto para o próximo desafio
                    if custo_eq > 20000:
                        st.error(f"🚨 ATENÇÃO - CUSTO ALTO: {custo_eq:,.2f} MT")
                    else:
                        st.write(f"Custo: {custo_eq:,.2f} MT")
    else:
        st.info("Nenhum equipamento ainda")

with aba2:
    st.subheader("Cadastrar novo equipamento")
    matricula = st.text_input("Matrícula (ex: EQ-004)")
    modelo = st.text_input("Modelo")
    oficina = st.selectbox("Oficina", ["Maputo", "Matola", "Beira", "Nampula"])
    foto_upload = st.file_uploader("Foto do equipamento", type=["jpg", "png", "jpeg"])

    if st.button("Salvar equipamento"):
        if matricula:
            caminho_foto = ""
            if foto_upload:
                caminho_foto = f"fotos/{matricula}.jpg"
                with open(caminho_foto, "wb") as f:
                    f.write(foto_upload.getbuffer())

            novo = {
                "matricula": matricula,
                "modelo": modelo,
                "oficina": oficina,
                "foto": caminho_foto,
                "status": "Ativo",
                "manutencoes": []
            }
            equipamentos.append(novo)
            salvar(equipamentos)
            st.success(f"Equipamento {matricula} salvo com foto!")
            st.rerun()
        else:
            st.error("Preencha a matrícula")

with aba3:
    st.subheader("Registrar manutenção")
    if equipamentos:
        lista_mat = [eq['matricula'] for eq in equipamentos]
        mat_sel = st.selectbox("Escolha o equipamento", lista_mat)
        desc = st.text_input("Descrição")
        custo = st.number_input("Custo MT", min_value=0.0)
        if st.button("Registrar"):
            for eq in equipamentos:
                if eq['matricula'] == mat_sel:
                    eq.setdefault('manutencoes', []).append({"descricao": desc, "custo": custo})
            salvar(equipamentos)
            st.success("Manutenção registrada!")
            st.rerun()