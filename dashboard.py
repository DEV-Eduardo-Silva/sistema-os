import streamlit as st
from datetime import datetime
import bd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
import pytz

# =========================
# TEMPO (COM FUSO CORRETO)
# =========================
def calcular_tempo(data_str, hora_str):
    try:
        fuso = pytz.timezone("America/Sao_Paulo")

        dt = datetime.strptime(
            f"{data_str} {hora_str}",
            "%d/%m/%Y %H:%M"
        )

        dt = fuso.localize(dt)
        agora = datetime.now(fuso)

        diff = agora - dt

        total_min = int(diff.total_seconds() / 60)
        horas = total_min // 60
        minutos = total_min % 60

        return f"{horas:02d}:{minutos:02d}"
    except:
        return "--:--"


# =========================
# CARD
# =========================
def card_setor(titulo, lista_os=None):

    if not lista_os:
        st.markdown(f"""
        <div style="background:#16a34a;padding:20px;border-radius:15px;color:white;">
            <b>{titulo} - 🟢 LIVRE</b>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"""
    <div style="background:#dc2626;padding:20px;border-radius:15px;color:white;">
        <b>{titulo} - 🔴 OCUPADO</b><br><br>
    """, unsafe_allow_html=True)

    for os in lista_os:
        tempo = calcular_tempo(
            os.get("DATA_ENTRADA", ""),
            os.get("HORA_ENTRADA", "")
        )

        st.markdown(f"""
        🚗 <b>Placa:</b> {os.get('PLACA','')}<br>
        🔧 <b>Tipo:</b> {os.get('TIPO','')}<br>
        👷 <b>Executores:</b> {os.get('EXECUTORES','')}<br>
        📝 <b>Obs:</b> {os.get('OBS','-')}<br>
        📄 <b>OS:</b> {os.get('NUMERO_OS','')}<br>
        ⏱️ <b>Tempo:</b> {tempo}<br>
        <hr style="border:1px solid rgba(255,255,255,0.3);">
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# DASHBOARD
# =========================
def tela_dashboard():

    st.subheader("📊 CONTROLE OFICINA")
    st_autorefresh(interval=30000, key="dash_refresh")

    # =========================
    # FILTRO DATA
    # =========================
    colf1, colf2 = st.columns(2)

    with colf1:
        data_inicio = st.date_input(
            "Data início",
            datetime.today()
        )

    with colf2:
        data_fim = st.date_input(
            "Data fim",
            datetime.today()
        )

    # =========================
    # KPI
    # =========================
    total, manut, final = bd.contar_por_periodo(
        data_inicio,
        data_fim
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("TOTAL PLACAS NO PERÍODO", total)
    c2.metric("PLACAS EM MANUTENÇÃO", manut)
    c3.metric("PLACAS FINALIZADAS", final)

    st.divider()

    # =========================
    # GRÁFICO EXECUTORES
    # =========================
    with st.expander(
        "📊 OS por Executor (clique para abrir)",
        expanded=False
    ):

        contagem = bd.os_por_executor_periodo(
            data_inicio,
            data_fim
        )

        contagem = {
            k: v for k, v in contagem.items()
            if k.strip().upper() != "MATERIAL"
        }

        if len(contagem) == 0:
            st.info("Nenhuma OS encontrada no período.")

        else:
            contagem_ordenada = dict(
                sorted(
                    contagem.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            )

            executores = list(contagem_ordenada.keys())
            valores = list(contagem_ordenada.values())

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.bar(executores, valores)

            ax.set_ylabel("Quantidade de OS")
            ax.set_xlabel("Executor")
            ax.set_title("Total de OS por Executor")

            plt.xticks(rotation=0)

            for i, v in enumerate(valores):
                ax.text(
                    i,
                    v + 0.1,
                    str(v),
                    ha='center',
                    fontweight='bold'
                )

            st.pyplot(fig)

    # =========================
    # OS AGRUPADAS
    # =========================
    os_agrupadas = bd.listar_os_agrupadas()
    os_filtradas = []

    for os in os_agrupadas:
        data_str = os.get("DATA_ENTRADA", "").strip()

        if data_str == "":
            continue

        try:
            data_os = datetime.strptime(
                data_str,
                "%d/%m/%Y"
            ).date()
        except:
            continue

        if data_os < data_inicio or data_os > data_fim:
            continue

        os_filtradas.append(os)

    # =========================
    # SETORES
    # =========================
    setores = {
        "RAMPA 1": [],
        "RAMPA 2": [],
        "RAMPA 3": [],
        "CHAPEAÇÃO": [],
        "BORRACHARIA": []
    }

    for os in os_filtradas:

        rampa = os.get("RAMPA", "").upper()
        tipo = os.get("TIPO", "").upper()

        if "RAMPA 1" in rampa:
            setores["RAMPA 1"].append(os)

        if "RAMPA 2" in rampa:
            setores["RAMPA 2"].append(os)

        if "RAMPA 3" in rampa:
            setores["RAMPA 3"].append(os)

        if "CHAP" in tipo:
            setores["CHAPEAÇÃO"].append(os)

        if "BORR" in tipo:
            setores["BORRACHARIA"].append(os)

    # =========================
    # LAYOUT
    # =========================
    col1, col2, col3 = st.columns(3)

    with col1:
        card_setor("RAMPA 1", setores["RAMPA 1"])

    with col2:
        card_setor("RAMPA 2", setores["RAMPA 2"])

    with col3:
        card_setor("RAMPA 3", setores["RAMPA 3"])

    st.divider()

    col4, col5 = st.columns(2)

    with col4:
        card_setor("CHAPEAÇÃO", setores["CHAPEAÇÃO"])

    with col5:
        card_setor("BORRACHARIA", setores["BORRACHARIA"])