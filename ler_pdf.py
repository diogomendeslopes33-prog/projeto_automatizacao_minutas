# ler_pdf.py
# Extrai campos do formulário PDF e devolve dicionário normalizado.
# Ponto de substituição futuro: quando vier integração SharePoint,
# este módulo é substituído por ler_sharepoint.py com a mesma interface.

import pdfplumber
import re
from utils import limpar_texto, limpar_valor_monetario, limpar_email
from logger import log_tecnico


def ler_dados(caminho_pdf):
    """
    Extrai todos os campos do formulário PDF.
    Devolve dicionário com chaves normalizadas.
    Campos não encontrados ficam com valor None.
    """
    log_tecnico("ficheiro_lido", {"caminho": caminho_pdf})

    dados = _inicializar_dados()

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            paginas = pdf.pages

            if len(paginas) >= 1:
                _extrair_pagina1(paginas[0], dados)
            if len(paginas) >= 2:
                _extrair_pagina2(paginas[1], dados)
            if len(paginas) >= 3:
                _extrair_pagina3(paginas[2], dados)
            if len(paginas) >= 4:
                _extrair_pagina4(paginas[3], dados)

    except Exception as e:
        log_tecnico("erro", {"modulo": "ler_pdf", "erro": str(e)})
        raise

    log_tecnico("extracao_concluida", {
        "campos_extraidos": sum(1 for v in dados.values() if v is not None),
        "campos_vazios": sum(1 for v in dados.values() if v is None)
    })

    return dados


def _inicializar_dados():
    """
    Dicionário com todas as chaves possíveis inicializadas a None.
    Garante estrutura consistente independentemente do conteúdo do PDF.
    """
    return {
        # Identificação
        "REFERENCIA": None,
        "UNIDADE": None,
        "OBJETO": None,
        "TIPO_OBJETO": None,
        "TIPO_PROCEDIMENTO": None,
        "DESIGNACAO_PROJETO": None,
        "NECESSIDADE_RECORRENTE": None,
        "FUNDAMENTACAO": None,

        # Intervenientes
        "PROPONENTE_CARGO": None,
        "PROPONENTE_NOME": None,
        "PROPONENTE_EMAIL": None,
        "GESTOR_CARGO": None,
        "GESTOR_NOME": None,
        "GESTOR_EMAIL": None,
        "SUBSTITUTO_CARGO": None,
        "SUBSTITUTO_NOME": None,
        "SUBSTITUTO_EMAIL": None,
        "ORGAO_COMPETENTE": None,

        # Júri
        "PRESIDENTE_JURI_NOME": None,
        "PRESIDENTE_JURI_EMAIL": None,
        "VOGAL_EFETIVO_1_NOME": None,
        "VOGAL_EFETIVO_1_EMAIL": None,
        "VOGAL_EFETIVO_2_NOME": None,
        "VOGAL_EFETIVO_2_EMAIL": None,
        "VOGAL_SUPLENTE_1_NOME": None,
        "VOGAL_SUPLENTE_1_EMAIL": None,
        "VOGAL_SUPLENTE_2_NOME": None,
        "VOGAL_SUPLENTE_2_EMAIL": None,

        # Empresas convidadas
        "EMPRESAS_CONVIDADAS": None,  # lista de dicts

        # Financeiro
        "PRECO_BASE": None,
        "JUSTIFICATIVO_PRECO": None,
        "IVA_TAXA": None,
        "VALOR_IVA": None,
        "VALOR_FINAL": None,
        "CENTRO_CUSTOS": None,
        "PRR": None,

        # Lotes
        "TEM_LOTES": None,
        "LOTES": None,  # lista de dicts

        # Condições
        "DESPESA_PLURIANUAL": None,
        "CRITERIO_ADJUDICACAO": None,
        "CAUCAO": None,
        "RETENCAO_CAUCAO": None,
        "CONDICOES_PAGAMENTO": None,
        "FINANCIAMENTO": None,
        "GARANTIA_ANOS": None,
        "PRAZO_ENTREGA": None,
        "PRAZO_ENTREGA_UNIDADE": None,
        "LOCAL_ENTREGA": None,

        # Técnico AAC
        "TECNICO_AAC_NOME": None,
        "TECNICO_AAC_EMAIL": None,

        # Datas e número
        "DATA_APROVACAO": None,
        "DATA_PUBLICACAO": None,
        "DATA_LIMITE_PROPOSTAS": None,
        "DATA_LIMITE_PRONUNCIA": None,
        "DATA_LIMITE_HABILITACAO": None,
        "ANO": None,

        # Campos sem correspondência no formulário
        "NR_PROCEDIMENTO": None,   # gerado posteriormente
        "NR_COMPROMISSO": None,    # gerado posteriormente
        "CLASS_ECONOMICA": None,   # requer leitura do cabimento
    }


def _extrair_pagina1(pagina, dados):
    """Página 1 — identificação, intervenientes e júri."""
    tabelas = pagina.extract_tables()

    # Tabela 3 — campos chave/valor linha a linha
    if len(tabelas) >= 3:
        tab = tabelas[2]
        chaves = [
            "UNIDADE", "OBJETO", "TIPO_OBJETO",
            "TIPO_PROCEDIMENTO", "DESIGNACAO_PROJETO", "NECESSIDADE_RECORRENTE"
        ]
        for i, chave in enumerate(chaves):
            if i < len(tab) and tab[i] and tab[i][0]:
                dados[chave] = limpar_texto(tab[i][0])

    # Tabela 2 — referência do formulário
    if len(tabelas) >= 2:
        tab = tabelas[1]
        if len(tab) >= 2 and tab[1] and len(tab[1]) >= 2:
            dados["REFERENCIA"] = limpar_texto(tab[1][1])

    # Tabela 4 — intervenientes (cargo | nome | email)
    if len(tabelas) >= 4:
        tab = tabelas[3]
        if len(tab) >= 1 and tab[0]:
            dados["PROPONENTE_CARGO"] = limpar_texto(tab[0][0])
            dados["PROPONENTE_NOME"]  = limpar_texto(tab[0][1]) if len(tab[0]) > 1 else None
            dados["PROPONENTE_EMAIL"] = limpar_texto(tab[0][2]) if len(tab[0]) > 2 else None
        if len(tab) >= 2 and tab[1]:
            dados["GESTOR_CARGO"] = limpar_texto(tab[1][0])
            dados["GESTOR_NOME"]  = limpar_texto(tab[1][1]) if len(tab[1]) > 1 else None
            dados["GESTOR_EMAIL"] = limpar_texto(tab[1][2]) if len(tab[1]) > 2 else None
        if len(tab) >= 3 and tab[2]:
            dados["SUBSTITUTO_CARGO"] = limpar_texto(tab[2][0])
            dados["SUBSTITUTO_NOME"]  = limpar_texto(tab[2][1]) if len(tab[2]) > 1 else None
            dados["SUBSTITUTO_EMAIL"] = limpar_texto(tab[2][2]) if len(tab[2]) > 2 else None
        if len(tab) >= 4 and tab[3] and tab[3][0]:
            dados["ORGAO_COMPETENTE"] = limpar_texto(tab[3][0])

    # Tabela 5 — júri (nome | email)
    if len(tabelas) >= 5:
        tab = tabelas[4]
        campos_juri = [
            ("PRESIDENTE_JURI_NOME", "PRESIDENTE_JURI_EMAIL"),
            ("VOGAL_EFETIVO_1_NOME", "VOGAL_EFETIVO_1_EMAIL"),
            ("VOGAL_EFETIVO_2_NOME", "VOGAL_EFETIVO_2_EMAIL"),
            ("VOGAL_SUPLENTE_1_NOME", "VOGAL_SUPLENTE_1_EMAIL"),
            ("VOGAL_SUPLENTE_2_NOME", "VOGAL_SUPLENTE_2_EMAIL"),
        ]
        for i, (nome_campo, email_campo) in enumerate(campos_juri):
            if i < len(tab) and tab[i]:
                dados[nome_campo] = limpar_texto(tab[i][0]) if tab[i][0] else None
                dados[email_campo] = limpar_texto(tab[i][1]) if len(tab[i]) > 1 else None

    # Fundamentação — texto corrido da página
    texto = pagina.extract_text() or ""
    match = re.search(r'Fundamentação da aquisição\s*(.+?)(?:Pedidos associados|Proponente)', texto, re.DOTALL)
    if match:
        dados["FUNDAMENTACAO"] = limpar_texto(match.group(1))


def _extrair_pagina2(pagina, dados):
    """Página 2 — empresas, financeiro, lotes."""
    tabelas = pagina.extract_tables()
    texto = pagina.extract_text() or ""

    # Tabela 2 — empresas convidadas (nome | NIF | email)
    if len(tabelas) >= 2:
        tab = tabelas[1]
        empresas = []
        for linha in tab:
            if not linha or not linha[0]:
                continue
            # Ignora cabeçalho
            if limpar_texto(linha[0]).lower() in ("nome", ""):
                continue
            empresas.append({
                "nome": limpar_texto(linha[0]),
                "nif": limpar_texto(linha[1]) if len(linha) > 1 else "",
                "email": limpar_texto(linha[2]) if len(linha) > 2 else "",
            })
        if empresas:
            dados["EMPRESAS_CONVIDADAS"] = empresas

    # Tabela 3 — preço base e justificativo
    if len(tabelas) >= 3:
        tab = tabelas[2]
        if tab and tab[0]:
            dados["PRECO_BASE"] = limpar_valor_monetario(tab[0][0])
            dados["JUSTIFICATIVO_PRECO"] = limpar_texto(tab[0][1]) if len(tab[0]) > 1 else None

    # Tabela 4 — IVA taxa, valor IVA, valor final
    if len(tabelas) >= 4:
        tab = tabelas[3]
        if len(tab) >= 1 and tab[0] and tab[0][0]:
            dados["VALOR_IVA"] = limpar_valor_monetario(tab[0][0])
        if len(tab) >= 2 and tab[1] and tab[1][0]:
            dados["VALOR_FINAL"] = limpar_valor_monetario(tab[1][0])

    # Tabela 5 — lotes
    if len(tabelas) >= 5:
        tab = tabelas[4]
        lotes = []
        for linha in tab:
            if not linha or not linha[0]:
                continue
            try:
                nr = int(limpar_texto(linha[0]))
            except ValueError:
                continue
            lotes.append({
                "NR": nr,
                "NOME": limpar_texto(linha[1]) if len(linha) > 1 else "",
                "VALOR": limpar_valor_monetario(linha[2]) if len(linha) > 2 else None,
                "CABIMENTO": limpar_texto(linha[3]) if len(linha) > 3 else "",
                "CPV": limpar_texto(linha[5]) if len(linha) > 5 else "",
                "CPV_DESC": limpar_texto(linha[6]) if len(linha) > 6 else "",
            })
        if lotes:
            dados["LOTES"] = lotes
            dados["TEM_LOTES"] = True

    # Texto corrido — campos dispersos
    _extrair_campo_texto(texto, r'Centro de custo\s*\n([\d.]+)', "CENTRO_CUSTOS", dados)
    _extrair_campo_texto(texto, r'PRR\?\s*\n(\w+)', "PRR", dados)
    _extrair_campo_texto(texto, r'Lotes\?(\w+)', "TEM_LOTES", dados, transformar=lambda x: x.lower() == "sim")
    _extrair_campo_texto(texto, r'Despesa plurianual\?\s*(\w+)', "DESPESA_PLURIANUAL", dados)
    _extrair_campo_texto(texto, r'Critério de adjudicação\s*(.+?)(?:\n|$)', "CRITERIO_ADJUDICACAO", dados)
    _extrair_campo_texto(texto, r'IVA Taxa[^\n]*\n[^\n]*\n(\d+)', "IVA_TAXA", dados)


def _extrair_pagina3(pagina, dados):
    """Página 3 — condições, prazos, local, técnico."""
    tabelas = pagina.extract_tables()
    texto = pagina.extract_text() or ""

    # Tabela 2 — prazo de entrega
    if len(tabelas) >= 2:
        tab = tabelas[1]
        if tab and tab[0]:
            dados["PRAZO_ENTREGA"] = limpar_texto(tab[0][0])
            dados["PRAZO_ENTREGA_UNIDADE"] = limpar_texto(tab[0][1]) if len(tab[0]) > 1 else None

    # Tabela 3 — local de entrega
    if len(tabelas) >= 3:
        tab = tabelas[2]
        if tab and tab[0] and len(tab[0]) > 1:
            dados["LOCAL_ENTREGA"] = limpar_texto(tab[0][1])

    # Tabela 4 — técnico AAC
    if len(tabelas) >= 4:
        tab = tabelas[3]
        if tab and tab[0]:
            dados["TECNICO_AAC_NOME"] = limpar_texto(tab[0][0])
            dados["TECNICO_AAC_EMAIL"] = limpar_texto(tab[0][1]) if len(tab[0]) > 1 else None

    # Texto corrido
    _extrair_campo_texto(texto, r'Caução\?\s*(\w+)', "CAUCAO", dados)
    _extrair_campo_texto(texto, r'Retenção nas faturas para reforço de caução\?\s*(\w+)', "RETENCAO_CAUCAO", dados)
    _extrair_campo_texto(texto, r'Condições de pagamento\s*\n(.+?)(?:\n|Financiamento)', "CONDICOES_PAGAMENTO", dados, re.DOTALL)
    _extrair_campo_texto(texto, r'Financiamento\?\s*(\w+)', "FINANCIAMENTO", dados)
    _extrair_campo_texto(texto, r'Garantia \(Anos\)\s*(\d+)', "GARANTIA_ANOS", dados)


def _extrair_pagina4(pagina, dados):
    """Página 4 — datas e número do procedimento."""
    texto = pagina.extract_text() or ""

    _extrair_campo_texto(texto, r'Data de aprovação\s+([\d]+ de \w+ de \d{4})', "DATA_APROVACAO", dados)
    _extrair_campo_texto(texto, r'Data de publicação BaseGov\s+([\d]+ de \w+ de \d{4})', "DATA_PUBLICACAO", dados)
    _extrair_campo_texto(texto, r'Data limite de apresentação de propostas\s+([\d]+ de \w+ de \d{4})', "DATA_LIMITE_PROPOSTAS", dados)
    _extrair_campo_texto(texto, r'Data limite da pronuncia\s+([\d]+ de \w+ de \d{4})', "DATA_LIMITE_PRONUNCIA", dados)
    _extrair_campo_texto(texto, r'Data limite para apresentação de documentos de habilitação\s+([\d]+ de \w+ de \d{4})', "DATA_LIMITE_HABILITACAO", dados)
    _extrair_campo_texto(texto, r'Ano\s+Número do contrato\s+\S+\s+(\d{4})', "ANO", dados)


def _extrair_campo_texto(texto, padrao, chave, dados, flags=0, transformar=None):
    """
    Auxiliar — extrai um campo do texto corrido via regex.
    Se encontrar, guarda em dados[chave].
    Se transformar for fornecido, aplica a função ao valor extraído.
    """
    match = re.search(padrao, texto, flags)
    if match:
        valor = limpar_texto(match.group(1))
        dados[chave] = transformar(valor) if transformar else valor