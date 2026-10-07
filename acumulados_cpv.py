# acumulados_cpv.py
# Camada C — acumulado por CPV, últimos 12 meses corridos (Decisão 8).
# Alimenta directamente dados["ACUM_CPV"] em limiares.py, para
# verificar_fracionamento_art22 e verificar_visto_tribunal_contas.
#
# O ficheiro Excel de entrada já vem filtrado pelo CPV pretendido — o
# filtro é feito na pesquisa ao ERP, não neste código (ver acumulados_erp.py).

from datetime import date
from acumulados_erp import carregar_contratos_erp, filtrar_ultimos_12_meses


def calcular_acumulado_cpv(caminho_excel, data_referencia=None):
    """
    Calcula o valor acumulado (soma de VALOR_TOTALSEMIVA_CONTRATO) dos
    contratos do export de um CPV específico, nos últimos 12 meses
    corridos a contar de data_referencia (por omissão, hoje).

    Devolve:
        float — valor acumulado (pode ser 0.0, se o ficheiro foi lido
                com sucesso mas não há contratos dentro da janela —
                isto é um "0 verificado", diferente de "não verificado")
        None  — se o ficheiro não puder ser lido — o chamador deve
                tratar como "acumulado não verificado", nunca assumir 0
    """
    if data_referencia is None:
        data_referencia = date.today()

    contratos = carregar_contratos_erp(caminho_excel)
    if contratos is None:
        return None

    contratos_periodo = filtrar_ultimos_12_meses(contratos, data_referencia)
    return sum(c["valor"] for c in contratos_periodo)