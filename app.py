import streamlit as st
from datetime import datetime, timedelta
import uuid
import bd
import dashboard
import pytz

# =============================
# FUNÇÃO PARA SOMAR HORAS
# =============================
def somar_hora(hora_entrada, duracao):
    try:
        h1, m1 = map(int, hora_entrada.strip().split(":"))
        h2, m2 = map(int, duracao.strip().split(":"))
        entrada = datetime(2000, 1, 1, h1, m1)
        saida = entrada + timedelta(hours=h2, minutes=m2)
        return saida.strftime("%H:%M")
    except:
        return ""

# =============================
# VALIDAR FORMATO HH:MM
# =============================
def validar_hhmm(valor):
    try:
        if valor is None or valor.strip() == "":
            return True

        partes = valor.strip().split(":")
        if len(partes) != 2:
            return False

        h = int(partes[0])
        m = int(partes[1])

        if h < 0 or m < 0 or m > 59:
            return False

        return True
    except:
        return False


st.set_page_config(page_title="Sistema OS", layout="wide")
st.title("🚗 Sistema de Ordem de Serviço")

menu = st.sidebar.selectbox("Menu", ["Abrir OS", "OS em andamento", "Dashboard"])

# =============================
# ABRIR OS
# =============================
if menu == "Abrir OS":
    agora = datetime.now()
    data_entrada = agora.strftime("%d/%m/%Y")
    hora_entrada = agora.strftime("%H:%M")

    st.subheader("📥 Abrir Nova OS")
    with st.form("form_os", clear_on_submit=True):
        placa = st.text_input("Placa")

        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Data Entrada", value=data_entrada, disabled=True)
        with col2:
            st.text_input("Hora Entrada", value=hora_entrada, disabled=True)

        rampa = st.selectbox("Rampa", ["Rampa 1", "Rampa 2", "Rampa 3", "Chapeação", "Borracharia", "Externo"])
        tipo = st.selectbox("Tipo Serviço", ["Elétrica", "Mecânica", "Borracharia", "Chapeação", "Material", "Amarração"])
        obs = st.text_area("Observação")

        col3, col4 = st.columns(2)
        lista_executores = ["Selecione...", "Adilso", "Fabio", "Aleson", "Jesus", "Evandro", "Dionathan",
                            "Marcos", "Leandro", "Valdir", "Paulo", "Eduardo", "material"]

        with col3:
            executor1 = st.selectbox("Executor 1", lista_executores, index=0)
        with col4:
            executor2 = st.selectbox("Executor 2 (opcional)", [""] + lista_executores[1:], index=0)

        salvar = st.form_submit_button("🚀 Abrir OS")

    if salvar:
        if placa.strip() == "":
            st.error("Informe a placa!")
        elif executor1 == "Selecione...":
            st.error("Selecione o Executor 1!")
        else:
            dados = {
                "id": str(uuid.uuid4())[:8],
                "placa": placa.strip().upper(),
                "rampa": rampa,
                "tipo": tipo,
                "obs": obs,
                "data": data_entrada,
                "hora": hora_entrada,
                "executor1": executor1,
                "executor2": executor2
            }
            bd.abrir_os(dados)
            st.success("✅ OS criada com sucesso!")
            st.rerun()


# =============================
# OS EM ANDAMENTO
# =============================
elif menu == "OS em andamento":
    st.subheader("📋 OS em Manutenção")
    os_abertas = bd.listar_os()

    if len(os_abertas) == 0:
        st.info("Nenhuma OS em manutenção.")
    else:
        for i, row in enumerate(os_abertas):

            numero_os = row["NUMERO_OS"] if row["NUMERO_OS"] else "Abrindo..."
            titulo = f"🚗 {row['PLACA']} | 📍 {row['RAMPA']} | 🔧 {row['TIPO']} | 📄 OS: {numero_os}"

            with st.expander(titulo, expanded=False):

                st.write(f"👷 Executores: {row['EXECUTOR1']} / {row['EXECUTOR2']}")
                st.write(f"📝 Observação: {row['OBS']}")
                st.write(f"📅 Entrada: {row['DATA_ENTRADA']} {row['HORA_ENTRADA']}")

                st.divider()

                # =============================
                # EDITAR EXECUTORES
                # =============================
                st.markdown("### ✏️ Editar Executores")

                lista_executores = ["Selecione...", "Adilso", "Fabio", "Aleson", "Jesus", "Evandro", "Dionathan",
                                    "Marcos", "Leandro", "Valdir", "Paulo", "Eduardo", "material"]

                colA, colB = st.columns(2)

                with colA:
                    idx1 = lista_executores.index(row["EXECUTOR1"]) if row["EXECUTOR1"] in lista_executores else 0
                    novo_exec1 = st.selectbox("Executor 1", lista_executores, index=idx1, key=f"exec1_{i}")

                with colB:
                    lista_exec2 = [""] + lista_executores[1:]
                    idx2 = lista_exec2.index(row["EXECUTOR2"]) if row["EXECUTOR2"] in lista_exec2 else 0
                    novo_exec2 = st.selectbox("Executor 2", lista_exec2, index=idx2, key=f"exec2_{i}")

                if st.button("💾 Salvar Alterações", key=f"salvar_edit_{i}"):
                    if novo_exec1 == "Selecione...":
                        st.error("Selecione o Executor 1!")
                    else:
                        bd.editar_os(row["ID"], novo_exec1, novo_exec2)
                        st.success("Executores alterados com sucesso!")
                        st.rerun()

                st.divider()

                # =============================
                # FINALIZAR OS
                # =============================
                st.markdown("### ✅ Finalizar OS")

                data_saida_padrao = datetime.now().strftime("%d/%m/%Y")
                hora_saida_padrao = datetime.now().strftime("%H:%M")

                col1, col2 = st.columns(2)

                with col1:
                    data_saida = st.text_input("Data Saída", value=data_saida_padrao, key=f"data_saida_{i}")

                with col2:
                    hora_saida = st.text_input("Hora Saída", value=hora_saida_padrao, key=f"hora_saida_{i}")

                executor1_nome = row["EXECUTOR1"]
                executor2_nome = row["EXECUTOR2"]

                mao1 = st.text_input(f"Tempo Mão de Obra - {executor1_nome} (hh:mm)", key=f"mao1_{i}")
                mao2 = st.text_input(f"Tempo Mão de Obra - {executor2_nome} (hh:mm)", key=f"mao2_{i}")

                # =============================
                # BORRACHARIA (C e Q)
                # =============================
                valor_borracharia = ""
                qtd_movimento = ""

                if "BORR" in row["TIPO"].strip().upper():
                    st.divider()
                    st.markdown("### 🛞 Dados Borracharia")

                    colx1, colx2 = st.columns(2)

                    with colx1:
                        valor_borracharia = st.text_input("Valor (R$)", key=f"valor_borra_{i}")

                    with colx2:
                        qtd_movimento = st.text_input("Qtd Movimento de Pneus", key=f"qtd_mov_{i}")

                # =============================
                # BOTÃO FINALIZAR
                # =============================
                if st.button("🚀 Confirmar Finalização", key=f"confirmar_final_{i}"):

                    if not validar_hhmm(mao1):
                        st.error("Tempo Executor 1 inválido. Use formato HH:MM (ex: 01:20)")
                    elif mao2 and not validar_hhmm(mao2):
                        st.error("Tempo Executor 2 inválido. Use formato HH:MM (ex: 00:45)")
                    else:
                        total_exec1 = somar_hora(row["HORA_ENTRADA"], mao1) if mao1 else ""
                        total_exec2 = somar_hora(row["HORA_ENTRADA"], mao2) if mao2 else ""

                        # Salvar Borracharia antes de finalizar
                        if "BORR" in row["TIPO"].strip().upper():
                            bd.salvar_borracharia(row["ID"], qtd_movimento, valor_borracharia)

                        bd.finalizar_os(
                            row["ID"],
                            data_saida,
                            hora_saida,
                            mao1,
                            mao2,
                            total_exec1,
                            total_exec2
                        )

                        st.success("OS finalizada com sucesso!")
                        st.rerun()


# =============================
# DASHBOARD

elif menu == "Dashboard":
    dashboard.tela_dashboard()