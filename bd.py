import gspread
import streamlit as st
from datetime import datetime
import os

# =============================
# CONFIG GOOGLE SHEETS
# =============================
PLANILHA_ID = "1uLXKsjRVk_2QqV3couSAnLvmiYq4uI1DKwEqxn_8bqo"

def conectar_google():
    # Se estiver no Streamlit Cloud (secrets)
    try:
        if "gcp_service_account" in st.secrets:
            return gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    except:
        pass

    # rodando local com credenciais.json
    if os.path.exists("credenciais.json"):
        return gspread.service_account(filename="credenciais.json")

    raise Exception("Nenhuma credencial encontrada: configure secrets.toml ou credenciais.json")

gc = conectar_google()
sh = gc.open_by_key(PLANILHA_ID)
ws = sh.sheet1
# =============================
# FUNÇÕES AUXILIARES  
# # =============================
def proxima_linha_vazia():
    valores = ws.col_values(2)  # coluna B (PLACA)
    return len(valores) + 1


def ler_tabela():
    dados = ws.get_all_values()
    if len(dados) <= 1:
        return []
    return dados[1:]


def buscar_linha_por_id(id_os):
    dados = ws.get_all_values()
    for i, row in enumerate(dados, start=1):
        if len(row) > 0 and row[0].strip() == id_os.strip():
            return i
    return None


def parse_data_hora(data_str, hora_str):
    try:
        return datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M")
    except:
        return None


# =============================
# ABRIR OS
# =============================
def abrir_os(dados):
    linha = proxima_linha_vazia()

    ws.update_cell(linha, 1, dados["id"])                 # A ID
    ws.update_cell(linha, 2, dados["placa"])              # B PLACA
    ws.update_cell(linha, 4, dados["rampa"])              # D RAMPA
    ws.update_cell(linha, 5, dados["tipo"])               # E TIPO SERVIÇO
    ws.update_cell(linha, 6, "SIM")                       # F EXECUTAR
    ws.update_cell(linha, 7, dados["obs"])                # G OBS
    ws.update_cell(linha, 8, dados["data"])               # H DATA ENTRADA
    ws.update_cell(linha, 9, dados["hora"])               # I HORA ENTRADA
    ws.update_cell(linha, 12, "EM MANUTENCAO")            # L STATUS
    ws.update_cell(linha, 16, dados["executor1"])         # P EXECUTOR 1
    ws.update_cell(linha, 19, dados["executor2"])         # S EXECUTOR 2


# =============================
# LISTAR OS EM MANUTENÇÃO (NORMAL)
# =============================
def listar_os():
    linhas = ler_tabela()
    os_abertas = []

    for row in linhas:
        try:
            # garantir até coluna U (21)
            while len(row) < 21:
                row.append("")

            id_os = row[0]         # A
            placa = row[1]         # B
            rampa = row[3]         # D
            tipo = row[4]          # E
            obs = row[6]           # G
            data_ent = row[7]      # H
            hora_ent = row[8]      # I
            status = row[11]       # L
            numero_os = row[14]    # O
            executor1 = row[15]    # P
            executor2 = row[18]    # S

            if status.strip().upper() == "EM MANUTENCAO":
                os_abertas.append({
                    "ID": id_os,
                    "PLACA": placa,
                    "RAMPA": rampa,
                    "TIPO": tipo,
                    "OBS": obs,
                    "DATA_ENTRADA": data_ent,
                    "HORA_ENTRADA": hora_ent,
                    "STATUS": status,
                    "NUMERO_OS": numero_os,
                    "EXECUTOR1": executor1,
                    "EXECUTOR2": executor2
                })

        except:
            continue

    return os_abertas


# =============================
# AGRUPAR OS POR PLACA + RAMPA
# =============================
def listar_os_agrupadas():
    os_abertas = listar_os()
    agrupado = {}

    for os in os_abertas:
        placa = os.get("PLACA", "").strip().upper()
        rampa = os.get("RAMPA", "").strip().upper()

        chave = f"{placa}_{rampa}"

        if chave not in agrupado:
            agrupado[chave] = {
                "PLACA": placa,
                "RAMPA": rampa,
                "TIPOS": set(),
                "EXECUTORES": set(),
                "OBS": [],
                "NUMEROS_OS": set(),
                "DATA_ENTRADA": os.get("DATA_ENTRADA", ""),
                "HORA_ENTRADA": os.get("HORA_ENTRADA", "")
            }

        tipo = os.get("TIPO", "").strip()
        if tipo:
            agrupado[chave]["TIPOS"].add(tipo)

        ex1 = os.get("EXECUTOR1", "").strip()
        ex2 = os.get("EXECUTOR2", "").strip()

        if ex1:
            agrupado[chave]["EXECUTORES"].add(ex1)
        if ex2:
            agrupado[chave]["EXECUTORES"].add(ex2)

        obs = os.get("OBS", "").strip()
        if obs:
            agrupado[chave]["OBS"].append(obs)

        num_os = os.get("NUMERO_OS", "").strip()
        if num_os:
            agrupado[chave]["NUMEROS_OS"].add(num_os)

        # manter a data/hora mais antiga como entrada (para tempo correto)
        dt_atual = parse_data_hora(os.get("DATA_ENTRADA", ""), os.get("HORA_ENTRADA", ""))
        dt_salva = parse_data_hora(agrupado[chave]["DATA_ENTRADA"], agrupado[chave]["HORA_ENTRADA"])

        if dt_atual and dt_salva:
            if dt_atual < dt_salva:
                agrupado[chave]["DATA_ENTRADA"] = os.get("DATA_ENTRADA", "")
                agrupado[chave]["HORA_ENTRADA"] = os.get("HORA_ENTRADA", "")

    resultado = []
    for chave, item in agrupado.items():
        resultado.append({
            "PLACA": item["PLACA"],
            "RAMPA": item["RAMPA"],
            "TIPO": " / ".join(sorted(item["TIPOS"])) if item["TIPOS"] else "",
            "EXECUTORES": " / ".join(sorted(item["EXECUTORES"])) if item["EXECUTORES"] else "",
            "OBS": " | ".join(item["OBS"][-2:]) if item["OBS"] else "-",
            "NUMERO_OS": " / ".join(sorted(item["NUMEROS_OS"])) if item["NUMEROS_OS"] else "Abrindo...",
            "DATA_ENTRADA": item["DATA_ENTRADA"],
            "HORA_ENTRADA": item["HORA_ENTRADA"]
        })

    return resultado


# =============================
# EDITAR OS (EXECUTORES)
# =============================
def editar_os(id_os, executor1, executor2):
    linha = buscar_linha_por_id(id_os)

    if linha is None:
        print("ERRO: ID não encontrado:", id_os)
        return

    ws.update_cell(linha, 16, executor1)  # P EXECUTOR 1
    ws.update_cell(linha, 19, executor2)  # S EXECUTOR 2


# =============================
# FINALIZAR OS
# =============================
def finalizar_os(id_os, data_saida, hora_saida, mao1, mao2, total_exec1, total_exec2):
    linha = buscar_linha_por_id(id_os)

    if linha is None:
        print("ERRO: ID não encontrado:", id_os)
        return

    # STATUS FINALIZADA (L = 12)
    ws.update_cell(linha, 12, "FINALIZADO")

    # DATA SAÍDA (J = 10)
    ws.update_cell(linha, 10, data_saida)

    # HORA SAÍDA (K = 11)
    ws.update_cell(linha, 11, hora_saida)

    # EXECUTOR 1
    ws.update_cell(linha, 13, mao1)         # M = Tempo mão de obra
    ws.update_cell(linha, 18, total_exec1)  # R = Hora final (entrada + mao1)

    # EXECUTOR 2
    ws.update_cell(linha, 20, mao2)         # T = Tempo mão de obra 2
    ws.update_cell(linha, 21, total_exec2)  # U = Hora final (entrada + mao2)


# =============================
# KPI POR PLACA (GERAL)
# =============================
def contar_os_por_placa():
    linhas = ler_tabela()

    placas_total = set()
    placas_manut = set()
    placas_final = set()

    for row in linhas:
        try:
            while len(row) < 12:
                row.append("")

            placa = row[1].strip().upper()
            status = row[11].strip().upper()

            if placa:
                placas_total.add(placa)

            if status == "EM MANUTENCAO":
                placas_manut.add(placa)

            if status in ["OK", "FINALIZADO"]:
                placas_final.add(placa)

        except:
            continue

    return len(placas_total), len(placas_manut), len(placas_final)


# =============================
# KPI POR PERÍODO (DATA ENTRADA - COLUNA H)
# =============================
def contar_por_periodo(data_inicio, data_fim):
    linhas = ler_tabela()

    placas_total = set()
    placas_manut = set()
    placas_final = set()

    for row in linhas:
        try:
            while len(row) < 12:
                row.append("")

            placa = row[1].strip().upper()
            data_entrada = row[7].strip()      # H DATA ENTRADA
            status = row[11].strip().upper()   # L STATUS

            if placa == "" or data_entrada == "":
                continue

            try:
                data_os = datetime.strptime(data_entrada, "%d/%m/%Y").date()
            except:
                continue

            if data_os < data_inicio or data_os > data_fim:
                continue

            placas_total.add(placa)

            if status == "EM MANUTENCAO":
                placas_manut.add(placa)

            if status in ["OK", "FINALIZADO"]:
                placas_final.add(placa)

        except:
            continue

    return len(placas_total), len(placas_manut), len(placas_final)
def os_por_executor_periodo(data_inicio, data_fim):
    linhas = ler_tabela()

    contagem = {}

    for row in linhas:
        try:
            while len(row) < 19:
                row.append("")

            data_entrada = row[7].strip()  # H
            status = row[11].strip().upper()
            exec1 = row[15].strip()        # P
            exec2 = row[18].strip()        # S

            if data_entrada == "":
                continue

            try:
                data_os = datetime.strptime(data_entrada, "%d/%m/%Y").date()
            except:
                continue

            if data_os < data_inicio or data_os > data_fim:
                continue

            if status not in ["EM MANUTENCAO", "OK", "FINALIZADO"]:
                continue

            if exec1 != "":
                contagem[exec1] = contagem.get(exec1, 0) + 1

            if exec2 != "":
                contagem[exec2] = contagem.get(exec2, 0) + 1

        except:
            continue

    return contagem
def salvar_borracharia(id_os, qtd_movimento, valor):
    linha = buscar_linha_por_id(id_os)

    if linha is None:
        print("ERRO: ID não encontrado:", id_os)
        return

    # Coluna C = 3 (Qtd Movimento Pneus)
    ws.update_cell(linha, 3, qtd_movimento)

    # Coluna Q = 17 (Valor)
    ws.update_cell(linha, 17, valor)
    