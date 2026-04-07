import streamlit as st
from datetime import datetime
import uuid
import bd
import dashboard
import pytz


# =============================
# SOMAR HORAS
# =============================
def somar_hora(hora_entrada, duracao):
    try:
        if not hora_entrada or not duracao:
            return ""

        hora_entrada = hora_entrada.strip()[:5]
        duracao = duracao.strip()[:5]

        h1, m1 = map(int, hora_entrada.split(":"))
        h2, m2 = map(int, duracao.split(":"))

        total = (h1 * 60 + m1) + (h2 * 60 + m2)

        horas = total // 60
        minutos = total % 60

        return f"{horas:02d}:{minutos:02d}"

    except:
        return ""


# =============================
# VALIDAR HH:MM
# =============================
def validar_hhmm(valor):
    try:
        if valor is None or valor.strip() == "":
            return True

        h, m = map(int, valor.strip().split(":"))

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

    tz = pytz.timezone("America/Sao_Paulo")
    agora = datetime.now(tz)

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

        rampa = st.selectbox(
            "Rampa",
            ["Rampa 1", "Rampa 2", "Rampa 3", "Chapeação", "Borracharia", "Externo"]
        )

        tipo = st.selectbox(
            "Tipo Serviço",
            ["Elétrica", "Mecânica", "Borracharia", "Chapeação", "Material", "Amarração"]
        )

        obs = st.text_area("Observação")

        lista_executores = [
            "Selecione...",
            "Adilso","Fabio","Aleson","Jesus","Evandro",
            "Dionathan","Marcos","Leandro","Valdir",
            "Paulo","Eduardo","material"
        ]

        col3, col4 = st.columns(2)

        with col3:
            executor1 = st.selectbox("Executor 1", lista_executores)

        with col4:
            executor2 = st.selectbox(
                "Executor 2 (opcional)",
                [""] + lista_executores[1:]
            )

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
            st.success("OS criada!")
            st.rerun()


# =============================
# OS EM ANDAMENTO
# =============================
elif menu == "OS em andamento":

    st.subheader("📋 OS em Manutenção")

    os_abertas = bd.listar_os()

    if len(os_abertas) == 0:
        st.info("Nenhuma OS em manutenção.")

    for i, row in enumerate(os_abertas):

        numero_os = row["NUMERO_OS"] if row["NUMERO_OS"] else "Abrindo..."

        titulo = f"🚗 {row['PLACA']} | 📍 {row['RAMPA']} | 🔧 {row['TIPO']} | 📄 OS: {numero_os}"

        with st.expander(titulo):

            st.write(f"👷 Executores: {row['EXECUTOR1']} / {row['EXECUTOR2']}")
            st.write(f"📝 Observação: {row['OBS']}")
            st.write(f"📅 Entrada: {row['DATA_ENTRADA']} {row['HORA_ENTRADA']}")

            st.divider()

            # =============================
            # EDITAR EXECUTOR
            # =============================
            st.markdown("### ✏️ Editar Executores")

            lista_executores = [
                "Selecione...",
                "Adilso","Fabio","Aleson","Jesus","Evandro",
                "Dionathan","Marcos","Leandro","Valdir",
                "Paulo","Eduardo","material"
            ]

            colA, colB = st.columns(2)

            with colA:
                novo_exec1 = st.selectbox(
                    "Executor 1",
                    lista_executores,
                    index=lista_executores.index(row["EXECUTOR1"])
                    if row["EXECUTOR1"] in lista_executores else 0,
                    key=f"exec1_{i}"
                )

            with colB:
                lista2 = [""] + lista_executores[1:]
                novo_exec2 = st.selectbox(
                    "Executor 2",
                    lista2,
                    index=lista2.index(row["EXECUTOR2"])
                    if row["EXECUTOR2"] in lista2 else 0,
                    key=f"exec2_{i}"
                )

            if st.button("💾 Salvar executores", key=f"save_exec_{i}"):

                bd.editar_os(row["ID"], novo_exec1, novo_exec2)
                st.success("Executores atualizados")
                st.rerun()

            st.divider()

            # =============================
            # FINALIZAR
            # =============================
            st.markdown("### ✅ Finalizar OS")

            tz = pytz.timezone("America/Sao_Paulo")
            agora = datetime.now(tz)

            data_saida = st.text_input(
                "Data Saída",
                agora.strftime("%d/%m/%Y"),
                key=f"data_{i}"
            )

            hora_saida = st.text_input(
                "Hora Saída",
                agora.strftime("%H:%M"),
                key=f"hora_{i}"
            )

            mao1 = st.text_input(
                f"Tempo {row['EXECUTOR1']} (HH:MM)",
                value="",
                key=f"mao1_{i}"
            )

            mao2 = st.text_input(
                f"Tempo {row['EXECUTOR2']} (HH:MM)",
                value="",
                key=f"mao2_{i}"
            )

            # BORRACHARIA
            valor_borracharia = ""
            qtd_movimento = ""

            if "BORR" in row["TIPO"].strip().upper():

                st.divider()
                st.markdown("### 🛞 Borracharia")

                valor_borracharia = st.text_input(
                    "Valor",
                    key=f"valor_{i}"
                )

                qtd_movimento = st.text_input(
                    "Qtd Movimento",
                    key=f"qtd_{i}"
                )

            # BOTÃO FINALIZAR
            if st.button("🚀 Finalizar", key=f"final_{i}"):

                if not validar_hhmm(mao1):
                    st.error("Tempo executor 1 inválido")
                    st.stop()

                if mao2 and not validar_hhmm(mao2):
                    st.error("Tempo executor 2 inválido")
                    st.stop()

                total_exec1 = somar_hora(row["HORA_ENTRADA"], mao1)
                total_exec2 = somar_hora(row["HORA_ENTRADA"], mao2)

                # SALVAR BORRACHARIA
                if "BORR" in row["TIPO"].strip().upper():
                    bd.salvar_borracharia(
                        row["ID"],
                        qtd_movimento,
                        valor_borracharia
                    )

                bd.finalizar_os(
                    row["ID"],
                    data_saida,
                    hora_saida,
                    mao1,
                    mao2,
                    total_exec1,
                    total_exec2
                )

                st.success("OS Finalizada!")
                st.rerun()


# =============================
# DASHBOARD
# =============================
elif menu == "Dashboard":
    dashboard.tela_dashboard()