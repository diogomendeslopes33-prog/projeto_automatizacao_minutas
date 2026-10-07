# acumulados_erp.py
# Camada C — carregador partilhado do export bruto de contratos do ERP
# ("Procura de Contratos - COMPRA - Todos os Anos", folha "consulta").
#
# Usado por acumulados_cpv.py (acumulado por CPV, filtro feito na pesquisa
# ao ERP) e acumulados_objeto.py (acumulado por objecto, pesquisa mais
# larga + curadoria manual do técnico antes de exportar).
#
# Não faz nenhuma agregação — só lê, valida e filtra contratos anulados.
# A soma por janela temporal e a comparação semântica ficam nos módulos
# específicos, que reutilizam esta função.

import openpyxl
from logger import log_tecnico


def carregar_contratos_erp(caminho_excel):
    """
    Lê o export bruto de contratos do ERP e devolve uma lista de dicts,
    um por contrato, já filtrada de registos anulados.

    Cada dict tem:
        {
            "id_contrato":      int,   # ID_CONTRATO — identificador único
            "valor":            float, # VALOR_TOTALSEMIVA_CONTRATO
            "data_adjudicacao": date,  # DATA_DECISAO_ADJUDICACAO
            "objeto":           str,   # OBJETO_CONTRATO
            "adjudicatario":    str,   # ADJUDICATARIO
            "nif":              str,   # NIF_ADJUDICATARIO
        }

    Devolve None se o ficheiro não puder ser lido ou não tiver a folha
    'consulta' — o chamador deve tratar isso como "acumulado não
    verificado", nunca assumir 0 (mesmo princípio já aplicado a CAUCAO
    em ler_pdf.py e a acum_fornecedor em limiares.py).

    Contratos com MOTIVOANULACAO preenchido são excluídos — não contam
    para nenhum acumulado, independentemente do valor de
    NOME_ESTADOCONTRATO (que pode variar sem incluir necessariamente a
    palavra "Anulado").
    """
    try:
        wb = openpyxl.load_workbook(caminho_excel, data_only=True)
    except Exception as e:
        log_tecnico("erro", {"modulo": "acumulados_erp", "erro": str(e), "ficheiro": caminho_excel})
        return None

    if "consulta" not in wb.sheetnames:
        log_tecnico("aviso", {
            "modulo": "acumulados_erp",
            "mensagem": "Folha 'consulta' não encontrada",
            "ficheiro": caminho_excel,
        })
        return None

    ws = wb["consulta"]
    linhas = list(ws.iter_rows(values_only=True))
    if not linhas:
        return []

    cabecalhos = list(linhas[0])

    def _idx(nome_coluna):
        try:
            return cabecalhos.index(nome_coluna)
        except ValueError:
            return None

    idx_id          = _idx("ID_CONTRATO")
    idx_valor       = _idx("VALOR_TOTALSEMIVA_CONTRATO")
    idx_data        = _idx("DATA_DECISAO_ADJUDICACAO")
    idx_objeto      = _idx("OBJETO_CONTRATO")
    idx_adjudic     = _idx("ADJUDICATARIO")
    idx_nif         = _idx("NIF_ADJUDICATARIO")
    idx_motivo_anul = _idx("MOTIVOANULACAO")

    if idx_valor is None or idx_data is None:
        log_tecnico("aviso", {
            "modulo": "acumulados_erp",
            "mensagem": "Colunas essenciais (VALOR_TOTALSEMIVA_CONTRATO / DATA_DECISAO_ADJUDICACAO) não encontradas",
            "ficheiro": caminho_excel,
        })
        return None

    contratos = []
    for linha in linhas[1:]:
        if linha[idx_valor] is None or linha[idx_data] is None:
            continue

        # Exclui contratos anulados
        if idx_motivo_anul is not None and linha[idx_motivo_anul]:
            continue

        contratos.append({
            "id_contrato":      linha[idx_id] if idx_id is not None else None,
            "valor":            float(linha[idx_valor]),
            "data_adjudicacao": linha[idx_data],
            "objeto":           linha[idx_objeto] if idx_objeto is not None else None,
            "adjudicatario":    linha[idx_adjudic] if idx_adjudic is not None else None,
            "nif":              linha[idx_nif] if idx_nif is not None else None,
        })

    return contratos


def carregar_contratos_pasta(caminho_pasta):
    """
    Lê TODOS os ficheiros .xlsx dentro de uma pasta (cada um resultado de
    uma pesquisa por termo diferente ao ERP — ver Decisão sobre pesquisa
    multi-termo para acumulados_objeto.py) e junta-os numa única lista de
    contratos, deduplicada por ID_CONTRATO.

    Usado quando a pesquisa de "objecto" é feita por vários termos
    separados (ex: "mobiliário", "cadeiras", "equipamento tecnológico"),
    cada um exportado para um ficheiro próprio dentro da mesma pasta —
    em vez de obrigar o técnico a fundir manualmente os resultados antes
    de exportar.

    Devolve None se a pasta não existir ou não tiver nenhum .xlsx válido
    — o chamador deve tratar como "acumulado não verificado".
    """
    import os

    if not os.path.isdir(caminho_pasta):
        log_tecnico("aviso", {
            "modulo": "acumulados_erp",
            "mensagem": "Pasta não encontrada",
            "pasta": caminho_pasta,
        })
        return None

    ficheiros_xlsx = [
        os.path.join(caminho_pasta, f)
        for f in os.listdir(caminho_pasta)
        if f.lower().endswith(".xlsx")
    ]

    if not ficheiros_xlsx:
        log_tecnico("aviso", {
            "modulo": "acumulados_erp",
            "mensagem": "Nenhum ficheiro .xlsx encontrado na pasta",
            "pasta": caminho_pasta,
        })
        return None

    vistos = {}
    for caminho in ficheiros_xlsx:
        contratos_ficheiro = carregar_contratos_erp(caminho)
        if contratos_ficheiro is None:
            continue
        for contrato in contratos_ficheiro:
            chave = contrato.get("id_contrato")
            if chave is None:
                # Sem ID_CONTRATO (raro) — usa o próprio dict como chave
                # de último recurso, aceitando risco mínimo de duplicação
                chave = (contrato["valor"], contrato["data_adjudicacao"], contrato["objeto"])
            if chave not in vistos:
                vistos[chave] = contrato

    return list(vistos.values())


def filtrar_ultimos_12_meses(contratos, data_referencia):
    """
    Filtra a lista de contratos (já carregada por carregar_contratos_erp)
    para os que têm data_adjudicacao dentro dos últimos 12 meses corridos
    a contar de data_referencia (inclusive).
    """
    from datetime import timedelta
    limite_inferior = data_referencia - timedelta(days=365)
    return [
        c for c in contratos
        if limite_inferior <= c["data_adjudicacao"].date() <= data_referencia
    ]