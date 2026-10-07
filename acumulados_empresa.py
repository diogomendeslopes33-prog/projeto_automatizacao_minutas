# acumulados_empresa.py
# Camada C — acumulado por fornecedor, extraído do relatório PDF do ERP
# "Documentos de um Fornecedor no âmbito do CCP" (ano económico e 2 anos
# anteriores) — cobre art. 113º/2, 113º/6 e 114º/2 CCP.
#
# O relatório é gerado pelo próprio ERP já com os limiares e valores
# disponíveis calculados por categoria (Limite a verificar × Forma de
# Adjudicação) — não recalculamos a soma, extraímos os valores já prontos,
# tal como apresentados ao técnico. As categorias usadas pelo ERP
# ("Bens ou Serviços", "Empreitadas de obras públicas") são mantidas tal
# qual, sem reconverter para a nomenclatura de TIPO_OBJETO — é a função
# de conformidade (verificar_acumulado_fornecedor, em limiares.py) que faz
# essa correspondência ao consumir estes dados.

import re
import pdfplumber
from logger import log_tecnico


def carregar_acumulado_fornecedor(caminho_pdf):
    """
    Extrai o NIF do fornecedor e o acumulado por categoria
    (Limite a verificar × Forma de Adjudicação) do relatório PDF do ERP.

    Devolve dict:
        {
            "nif": "500000000",
            "categorias": {
                "Bens ou Serviços": {
                    "Ajuste Direto": {"total": 19929.29, "limite": 19999.99, "disponivel": 70.70},
                },
                "Empreitadas de obras públicas": {
                    "Ajuste Direto": {"total": 9940.00, "limite": 29999.99, "disponivel": 20059.99},
                    "Consulta Prévia": {"total": 18768.58, "limite": 149999.99, "disponivel": 131231.41},
                },
            },
        }

    Devolve None se o PDF não puder ser lido ou não tiver a estrutura
    esperada — nesse caso, o chamador deve tratar como "acumulado não
    verificado", nunca assumir 0 silenciosamente (mesmo princípio já
    aplicado ao campo CAUCAO em ler_pdf.py).
    """
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            texto = "\n".join(p.extract_text() or "" for p in pdf.pages)
    except Exception as e:
        log_tecnico("erro", {"modulo": "acumulados_empresa", "erro": str(e), "pdf": caminho_pdf})
        return None

    nif_match = re.search(r'NIF:\s*(\d+)', texto)
    nif = nif_match.group(1) if nif_match else None

    categorias = {}

    # Cada bloco começa com "Limite a verificar: <categoria> Forma de
    # Adjudicação: <forma>" e termina nos três totais que lhe seguem —
    # o conteúdo entre eles (tabela de documentos) é ignorado, só
    # interessam os totais já calculados pelo ERP.
    padrao_bloco = re.compile(
        r'Limite a verificar:\s*(.+?)\s+Forma de Adjudicação:\s*(.+?)\n'
        r'.*?'
        r'Total do Valor Sem IVA \(1\):\s*([\d\s.,]+)\n'
        r'Limite \(2\):\s*([\d\s.,]+)\n'
        r'Valor Dispon[íi]vel \(2-1\):\s*([\d\s.,\-]+)',
        re.DOTALL
    )

    for m in padrao_bloco.finditer(texto):
        categoria  = m.group(1).strip()
        forma      = m.group(2).strip()
        total      = _valor_pt(m.group(3))
        limite     = _valor_pt(m.group(4))
        disponivel = _valor_pt(m.group(5))

        categorias.setdefault(categoria, {})[forma] = {
            "total": total,
            "limite": limite,
            "disponivel": disponivel,
        }

    if not categorias:
        log_tecnico("aviso", {
            "modulo": "acumulados_empresa",
            "mensagem": "Estrutura de blocos não reconhecida no PDF",
            "pdf": caminho_pdf,
        })
        return None

    return {"nif": nif, "categorias": categorias}


def _valor_pt(texto):
    """
    Converte um valor no formato português ('19 929,29', espaço como
    separador de milhar e vírgula como decimal) para float.
    """
    limpo = texto.strip().replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None