# Camada B — Enriquecimento empresarial via Informa D&B.
# Modo actual: leitura de PDF exportado manualmente do site Informa D&B.
# Modo futuro: chamada à API Informa D&B (alterar MODO_EMPRESAS=api no .env).
# A interface de saída é idêntica nos dois modos — o resto do sistema não muda.
#
# NOTA DE ARQUITECTURA: a extracção da rede de administradores usa coordenadas
# (x, y) das palavras no PDF, não a ordem sequencial do texto extraído. Isto
# é necessário porque o relatório Informa D&B usa um layout em duas colunas
# (cargo/nome à esquerda, lista de ligações à direita) que pode quebrar mal
# quando lido como texto linear — sobretudo em mudanças de página, onde uma
# lista de ligações longa do último administrador de uma página pode aparecer
# no topo da página seguinte, antes do nome do próximo administrador.

import os
import re
import pdfplumber
import config
from logger import log_tecnico


# ---------------------------------------------------------------------------
# Interface pública
# ---------------------------------------------------------------------------

def obter_empresas(nif_empresa):
    """Wrapper principal — decide o modo com base em MODO_EMPRESAS no .env."""
    if config.MODO_EMPRESAS == "api":
        return _obter_empresas_api(nif_empresa)
    else:
        return _obter_empresas_pdf(nif_empresa)


def enriquecer_empresas_convidadas(empresas_convidadas):
    """
    Para cada empresa convidada, descobre as suas relacionadas (via participações
    societárias e via rede de administradores) e os seus sócios/administradores.
    """
    resultado = []
    for empresa in empresas_convidadas:
        nif = empresa.get("nif", "")
        log_tecnico("camada_b_inicio", {"empresa": empresa.get("nome"), "nif": nif})

        caminho_pdf = _encontrar_pdf_empresa(nif, empresa.get("nome", ""))

        if caminho_pdf:
            dados_informa = _obter_empresas_pdf(caminho_pdf)
            empresa_enriquecida = dict(empresa)
            empresa_enriquecida["relacionadas"] = dados_informa.get("relacionadas", [])
            empresa_enriquecida["socios"]       = dados_informa.get("socios", [])
            log_tecnico("camada_b_concluida", {
                "empresa": empresa.get("nome"),
                "relacionadas": len(empresa_enriquecida["relacionadas"]),
                "socios": len(empresa_enriquecida["socios"]),
            })
        else:
            empresa_enriquecida = dict(empresa)
            empresa_enriquecida["relacionadas"] = []
            empresa_enriquecida["socios"]       = []
            log_tecnico("camada_b_sem_pdf", {
                "empresa": empresa.get("nome"), "nif": nif
            })

        resultado.append(empresa_enriquecida)

    return resultado


# ---------------------------------------------------------------------------
# Modo PDF — leitura do relatório estrutural Informa D&B
# ---------------------------------------------------------------------------

def _encontrar_pdf_empresa(nif, nome):
    """Procura o PDF Informa D&B correspondente a uma empresa."""
    pasta = config.PASTA_PDFS_EMPRESAS
    if not os.path.isdir(pasta):
        return None

    ficheiros = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]

    if nif:
        for f in ficheiros:
            if nif in f:
                return os.path.join(pasta, f)

    if nome:
        palavras = nome.split()[:3]
        for f in ficheiros:
            if any(p.lower() in f.lower() for p in palavras if len(p) > 3):
                return os.path.join(pasta, f)

    return None


def _obter_empresas_pdf(caminho_pdf):
    """
    Extrai dados de relacionadas e sócios do relatório estrutural Informa D&B.
    Devolve dict com 'relacionadas' (deduplicada) e 'socios'.
    """
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            texto_completo = "\n".join(
                pagina.extract_text() or "" for pagina in pdf.pages
            )
            relacionadas_admin, admins = _extrair_rede_administradores_por_posicao(pdf)
    except Exception as e:
        log_tecnico("erro", {"modulo": "apinforma", "erro": str(e), "pdf": caminho_pdf})
        return {"relacionadas": [], "socios": []}

    nome_propria_empresa = _extrair_nome_propria_empresa(texto_completo)

    relacionadas_participacao = _extrair_relacionadas_participacao(
        texto_completo, nome_propria_empresa
    )
    relacionadas_socios = _extrair_socios_com_ligacoes(texto_completo)
    socios_acionistas    = _extrair_socios_acionistas(texto_completo)

    todas_relacionadas = _juntar_e_deduplicar(
        relacionadas_participacao,
        _juntar_e_deduplicar(relacionadas_admin, relacionadas_socios),
    )

    todos_socios = list(socios_acionistas)
    socios_vistos = {s.strip().upper() for s in socios_acionistas}
    for admin in admins:
        if admin.strip().upper() not in socios_vistos:
            todos_socios.append(admin)
            socios_vistos.add(admin.strip().upper())

    return {
        "relacionadas": todas_relacionadas,
        "socios":       todos_socios,
    }


def _extrair_nome_propria_empresa(texto):
    """
    Extrai o nome da própria empresa do cabeçalho do relatório Informa D&B —
    a linha imediatamente antes de "NIF ... | DUNS® ...". Usado para
    auto-filtro: excluir a própria empresa de aparecer na sua lista de
    relacionadas (ver _extrair_relacionadas_participacao).
    """
    match = re.search(r'^(.+?)\nNIF\s+\d', texto, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


# ---------------------------------------------------------------------------
# Extracção de relacionadas via participação societária directa
# ---------------------------------------------------------------------------

def _extrair_relacionadas_participacao(texto, nome_propria_empresa=None):
    """
    Extrai empresas relacionadas por participação societária directa:
    empresa-mãe, participações maioritárias e minoritárias.

    CORRECÇÃO: o relatório Informa D&B pode listar, na secção de
    "Participações minoritárias / igualitárias", uma referência de volta
    à própria empresa de origem (ex: o relatório da XX, S.A. lista
    "4.62% XX, S.A." — a participação que a própria XX detém
    nela própria através da estrutura societária, não uma relacionada
    real). Sem filtrar isto, a empresa aparecia como sua própria
    relacionada na minuta. nome_propria_empresa, quando fornecido, exclui
    qualquer correspondência exacta (normalizada) com o nome de origem.
    """
    relacionadas = []
    nomes_vistos = set()
    linhas = [l.strip() for l in texto.split("\n")]

    nome_proprio_normalizado = (
        _normalizar_nome_empresa(nome_propria_empresa)
        if nome_propria_empresa else None
    )

    for i, linha in enumerate(linhas):
        if re.match(r'^Empresa-m[aã]e$', linha, re.IGNORECASE):
            if i + 1 < len(linhas):
                nome = linhas[i + 1].strip()
                if (nome and "CONSULTAR" not in nome and "DUNS" not in nome
                        and len(nome) > 3
                        and _normalizar_nome_empresa(nome) != nome_proprio_normalizado):
                    relacionadas.append({
                        "nome": nome, "nif": None,
                        "tipo": "empresa_mae", "participacao": None,
                        "origem": "participacao",
                    })
                    nomes_vistos.add(nome)
            break

    for i, linha in enumerate(linhas):
        match_pct_isolada = re.match(r'^(\d{1,3}(?:[,.]\d{1,2})?)%$', linha)
        match_pct_inline   = re.match(r'^(\d{1,3}(?:[,.]\d{1,2})?)%\s+(.{5,100})$', linha)

        nome_candidato = None
        pct = None

        if match_pct_isolada:
            pct = float(match_pct_isolada.group(1).replace(",", "."))
            if i + 1 < len(linhas):
                nome_candidato = linhas[i + 1].strip()
        elif match_pct_inline:
            pct = float(match_pct_inline.group(1).replace(",", "."))
            nome_candidato = match_pct_inline.group(2).strip()

        if nome_candidato is None or pct is None or pct > 100:
            continue
        if len(nome_candidato) <= 4:
            continue
        if re.match(r'^[\d\s,.€%]+$', nome_candidato):
            continue
        if any(x in nome_candidato.upper() for x in ["DUNS", "CONSULTAR"]):
            continue
        if nome_candidato in nomes_vistos:
            continue
        if not re.match(r'^[A-ZÁÀÂÃÉÊÍÓÔÕÚÇÜ0-9]', nome_candidato):
            continue
        # CORRECÇÃO: exclui auto-referência à própria empresa de origem
        if (nome_proprio_normalizado is not None
                and _normalizar_nome_empresa(nome_candidato) == nome_proprio_normalizado):
            continue

        tipo = "maioritaria" if pct >= 50 else "minoritaria"
        relacionadas.append({
            "nome": nome_candidato, "nif": None,
            "tipo": tipo, "participacao": pct,
            "origem": "participacao",
        })
        nomes_vistos.add(nome_candidato)

    return relacionadas


def _normalizar_nome_empresa(nome):
    """
    Normaliza um nome de empresa para comparação de auto-referência:
    maiúsculas, sem espaços extra, sem pontuação de pontuação societária
    comum (vírgulas, pontos). "XX, S.A." e "XX, S.A" devem
    normalizar para o mesmo valor.
    """
    if not nome:
        return None
    limpo = re.sub(r'[.,]', '', nome.upper())
    limpo = re.sub(r'\s+', ' ', limpo).strip()
    return limpo


# ---------------------------------------------------------------------------
# Extracção de sócios/acionistas nominais
# ---------------------------------------------------------------------------

def _extrair_socios_acionistas(texto):
    """
    Extrai nomes da secção 'Sócios / Acionistas'.
    A secção termina no primeiro marcador de secção seguinte — que pode ser
    'Empresa-mãe' (quando existe) ou, na ausência desta, 'Poderes de decisão'
    ou 'Órgãos de gestão e administração' (relatórios de empresas mais
    pequenas, sem participações noutras sociedades).
    """
    socios = []
    nomes_vistos = set()
    linhas = [l.strip() for l in texto.split("\n")]

    _MARCADORES_FIM = (
        r'^Empresa-m[aã]e$',
        r'^Poderes de decis[aã]o$',
        r'^[Óo]rg[aã]os de gest[aã]o e administra[cç][aã]o',
        r'^Informa[cç][aã]o de distribui[cç][aã]o de capital',
    )

    inicio_idx = fim_idx = None
    for i, linha in enumerate(linhas):
        if re.match(r'^Sócios\s*/\s*Acionistas$', linha, re.IGNORECASE):
            inicio_idx = i + 1
        elif inicio_idx is not None and any(
            re.match(padrao, linha, re.IGNORECASE) for padrao in _MARCADORES_FIM
        ):
            fim_idx = i
            break

    if inicio_idx is None:
        return socios

    # Limite de segurança — nunca processa mais de 40 linhas mesmo sem
    # marcador de fim encontrado, para não invadir secções não relacionadas
    fim_idx = fim_idx or min(inicio_idx + 40, len(linhas))

    for linha in linhas[inicio_idx:fim_idx]:
        linha = linha.strip()
        if not linha or len(linha) < 5:
            continue
        if linha.lower() in _PALAVRAS_IGNORAR():
            continue
        if re.match(r'^(valor|percentagem)', linha.lower()):
            continue
        if re.match(r'^[\d\s,.€%]+$', linha):
            continue
        if any(x in linha for x in ["DUNS", "CONSULTAR", "Informação de distribuição"]):
            continue
        if not re.match(r'^[A-ZÁÀÂÃÉÊÍÓÔÕÚÇÜ0-9]', linha):
            continue

        nome_limpo = re.sub(r'\s+[\d.,]+\s*€?\s*[\d.,]*\s*%?\s*$', '', linha).strip()
        nome_limpo = re.sub(r'\s+\d[\d.,]*$', '', nome_limpo).strip()

        if nome_limpo and len(nome_limpo.split()) >= 2 and nome_limpo not in nomes_vistos:
            socios.append(nome_limpo)
            nomes_vistos.add(nome_limpo)

    return socios


def _PALAVRAS_IGNORAR():
    return {
        "nome", "valor (€)", "percentagem (%)", "participação",
        "valor", "percentagem", "entidade(s)", "país", "portugal",
    }


# ---------------------------------------------------------------------------
# Extracção da rede de administradores POR POSIÇÃO (x, y) — robusta a quebras
# de página e a colunas duplas mal ordenadas pelo extract_text().
#
# Estratégia:
#   1. Para cada página, separa palavras em coluna esquerda (cargo/nome,
#      x0 pequeno) e coluna direita (ligações, x0 grande).
#   2. Agrupa palavras da coluna esquerda em blocos "Cargo + Nome" por
#      proximidade vertical (y0).
#   3. Para cada bloco, recolhe todas as palavras da coluna direita cujo y0
#      esteja entre o y0 deste bloco e o y0 do bloco seguinte (na mesma
#      página ou na página seguinte, se o bloco for o último da página).
#   4. Reconstrói as linhas de ligação ("EMPRESA como Cargo") a partir das
#      palavras recolhidas, agrupando por proximidade vertical.
# ---------------------------------------------------------------------------

_CARGOS_ADMIN = (
    "Presidente do Conselho de Administração",
    "Vice-Presidente do Conselho de Administração",
    "Vogal do Conselho de Administração",
)

# CORRECÇÃO: cargos típicos de Sociedade por Quotas (Lda.) — distintos dos
# cargos de Sociedade Anónima acima. Ao contrário destes, não aparecem
# fragmentados em várias linhas no relatório Informa D&B (são sempre uma
# única linha na coluna esquerda), por isso não precisam da lógica de
# _PREFIXOS_CARGO/junção de linhas — são reconhecidos directamente.
#
# Sem este reconhecimento, _extrair_rede_administradores_por_posicao nunca
# identificava um bloco de administrador para empresas Lda. (a maioria dos
# casos reais), e por isso nunca recolhia as suas ligações — mesmo quando
# essas ligações estavam claramente listadas no PDF ("Entidade(s) a que
# também está ligado/a"). Isto fazia com que só a participação societária
# directa (_extrair_relacionadas_participacao) aparecesse como relacionada,
# perdendo todas as ligações via rede de administradores.
_CARGOS_QUOTAS = (
    "Sócio-Gerente",
    "Gerente",
    "Administrador Único",
)

_PALAVRAS_CARGO = {
    "Presidente", "Vice-Presidente", "Vogal", "do", "Conselho",
    "de", "Administração", "Sócio-Gerente", "Gerente", "Administrador",
    "Único",
}

_LIMITE_COLUNA_X = 150  # abaixo disto é coluna esquerda (cargo/nome)


def _extrair_rede_administradores_por_posicao(pdf):
    """
    Percorre todas as páginas do PDF reconstruindo blocos de administrador
    (cargo + nome) e as respectivas ligações, usando coordenadas (x, y)
    em vez da ordem linear do texto extraído.
    Devolve (relacionadas, socios).
    """
    blocos = []  # cada bloco: {"nome": str, "y_inicio": float, "y_fim": float, "pagina": int}

    # --- Passo 1: identificar blocos de cargo+nome em todas as páginas ---
    for num_pagina, pagina in enumerate(pdf.pages):
        palavras = pagina.extract_words()
        esquerda = sorted(
            (w for w in palavras if w['x0'] < _LIMITE_COLUNA_X),
            key=lambda w: w['top']
        )
        direita = sorted(
            (w for w in palavras if w['x0'] >= _LIMITE_COLUNA_X),
            key=lambda w: w['top']
        )

        # Agrupa palavras da coluna esquerda em linhas por proximidade vertical
        linhas_esq = _agrupar_por_linha(esquerda)

        # Funde linhas consecutivas que formam um cargo conhecido
        # (cargos podem estar partidos em 1, 2 ou 3 linhas)
        i = 0
        while i < len(linhas_esq):
            texto_linha = " ".join(w['text'] for w in linhas_esq[i]).strip()
            cargo_completo = None
            linhas_consumidas = 1

            primeira_palavra = texto_linha.split()[0] if texto_linha else ""

            # CORRECÇÃO: cargos de Sociedade por Quotas — reconhecimento
            # directo, sem necessidade de juntar linhas seguintes (são
            # sempre uma única linha no relatório, ao contrário dos cargos
            # de S.A. que podem vir fragmentados).
            if texto_linha in _CARGOS_QUOTAS:
                cargo_completo = texto_linha

            # Cargos de Sociedade Anónima — lógica original, só tentada se
            # ainda não tiver casado com um cargo de Quotas acima.
            comeca_com_cargo = primeira_palavra in (
                "Presidente", "Vice-Presidente", "Vogal"
            ) if texto_linha else False

            if not cargo_completo and comeca_com_cargo:
                # Os cargos no relatório Informa D&B aparecem frequentemente
                # com a última palavra ("Administração") em falta na coluna
                # esquerda — essa palavra está sempre na coluna direita,
                # imediatamente antes do nome do administrador. Por isso
                # aceitam-se também os prefixos dos cargos conhecidos.
                _PREFIXOS_CARGO = {
                    "Presidente do Conselho de Administração": [
                        "Presidente do Conselho de Administração",
                        "Presidente do Conselho",
                        "Presidente do Conselho de",
                    ],
                    "Vice-Presidente do Conselho de Administração": [
                        "Vice-Presidente do Conselho de Administração",
                        "Vice-Presidente do Conselho",
                        "Vice-Presidente do Conselho de",
                    ],
                    "Vogal do Conselho de Administração": [
                        "Vogal do Conselho de Administração",
                        "Vogal do Conselho",
                        "Vogal do Conselho de",
                    ],
                }
                for cargo, prefixos in _PREFIXOS_CARGO.items():
                    if texto_linha in prefixos:
                        cargo_completo = cargo
                        break

                # Se não casou directamente, tenta juntar com 1-2 linhas seguintes
                if not cargo_completo:
                    for cargo in _CARGOS_ADMIN:
                        for n_juntar in (1, 2):
                            if i + n_juntar >= len(linhas_esq):
                                continue
                            fragmentos = [texto_linha]
                            for k in range(1, n_juntar + 1):
                                frag = " ".join(w['text'] for w in linhas_esq[i + k]).strip()
                                fragmentos.append(frag)
                            junta = re.sub(r'\s+', ' ', " ".join(fragmentos)).strip()
                            if junta == cargo:
                                cargo_completo = cargo
                                linhas_consumidas = n_juntar + 1
                                break
                            junta_sem_de = re.sub(r'\s+', ' ', re.sub(r'\bde\b', '', junta)).strip()
                            cargo_sem_de = re.sub(r'\s+', ' ', re.sub(r'\bde\b', '', cargo)).strip()
                            if junta_sem_de == cargo_sem_de:
                                cargo_completo = cargo
                                linhas_consumidas = n_juntar + 1
                                break
                        if cargo_completo:
                            break

            if cargo_completo:
                y_cargo = linhas_esq[i][0]['top']
                # O nome está na coluna DIREITA, à mesma altura vertical do
                # cargo. Pode vir precedido de um fragmento residual do
                # cargo partido (ex: "Administração Cláudio Jorge...") —
                # remove-se esse fragmento antes de aceitar o nome.
                linhas_dir_pagina = _agrupar_por_linha(direita)
                nome = None
                y_nome = y_cargo
                for linha_dir in linhas_dir_pagina:
                    y_linha = linha_dir[0]['top']
                    if abs(y_linha - y_cargo) <= 8:
                        candidato = " ".join(w['text'] for w in linha_dir).strip()
                        # Remove fragmento residual do cargo no início da linha
                        candidato_limpo = re.sub(
                            r'^(Administração|de Administração|do Conselho de Administração)\s+',
                            '', candidato
                        ).strip()
                        if (len(candidato_limpo) > 3
                                and candidato_limpo.lower() not in ("de", "do", "e")
                                and re.match(r'^[A-ZÁÀÂÃÉÊÍÓÔÕÚÇÜ]', candidato_limpo)):
                            nome = candidato_limpo
                            y_nome = y_linha
                            break

                if nome:
                    blocos.append({
                        "nome": nome,
                        "cargo": cargo_completo,
                        "pagina": num_pagina,
                        "y": y_nome,
                    })

            i += linhas_consumidas if cargo_completo else 1

        # Guarda as palavras da coluna direita desta página para o passo 2
        blocos_pagina = [b for b in blocos if b["pagina"] == num_pagina]
        for b in blocos_pagina:
            b["_palavras_direita_pagina"] = direita

    # --- Passo 2: para cada bloco, recolher ligações até ao bloco seguinte ---
    relacionadas = []
    pares_vistos = set()  # (administrador, empresa) — evita repetir a MESMA
                           # ligação do MESMO administrador (ex: por OCR duplo),
                           # mas permite que empresas diferentes administradores
                           # estejam ligados à mesma empresa.
    socios = []
    socios_vistos = set()

    for idx, bloco in enumerate(blocos):
        nome_admin = bloco["nome"]
        if nome_admin.strip().upper() not in socios_vistos:
            socios.append(nome_admin)
            socios_vistos.add(nome_admin.strip().upper())

        # Define o intervalo (página, y) onde procurar ligações:
        # começa no y deste bloco, termina no y do próximo bloco (ou fim do PDF)
        pagina_inicio = bloco["pagina"]
        y_inicio = bloco["y"]

        if idx + 1 < len(blocos):
            pagina_fim = blocos[idx + 1]["pagina"]
            y_fim = blocos[idx + 1]["y"]
        else:
            pagina_fim = pagina_inicio + 999  # até ao fim do documento
            y_fim = None

        texto_ligacoes = _recolher_texto_direita(
            pdf, pagina_inicio, y_inicio, pagina_fim, y_fim
        )

        for match_ent in re.finditer(
            r'([A-ZÁÀÂÃÉÊÍÓÔÕÚÇÜ0-9][^\n]{4,100}?)\s+como\s+([^\n]{3,60})',
            texto_ligacoes
        ):
            nome_emp = match_ent.group(1).strip()
            cargo_emp = match_ent.group(2).strip()

            eh_propria_pessoa = nome_emp.strip().upper() == nome_admin.strip().upper()
            tem_forma_juridica = bool(re.search(
                r'\b(LDA|S\.?A\.?|UNIPESSOAL|SGPS)\b', nome_emp, re.IGNORECASE
            ))
            parece_empresa = tem_forma_juridica or nome_emp.isupper()
            eh_frase_longa = len(nome_emp.split()) > 12

            par = (nome_admin.strip().upper(), nome_emp.strip().upper())

            if (not eh_frase_longa
                    and not eh_propria_pessoa
                    and parece_empresa
                    and par not in pares_vistos
                    and len(nome_emp) > 4):
                relacionadas.append({
                    "nome": nome_emp, "nif": None,
                    "tipo": "ligacao_administrador",
                    "participacao": None,
                    "origem": "administrador",
                    "via": nome_admin,
                    "cargo": cargo_emp,
                })
                pares_vistos.add(par)

    return relacionadas, socios


def _agrupar_por_linha(palavras_ordenadas, tolerancia=3):
    """Agrupa palavras em linhas por proximidade vertical (top)."""
    if not palavras_ordenadas:
        return []
    linhas = []
    linha_actual = [palavras_ordenadas[0]]
    for w in palavras_ordenadas[1:]:
        if abs(w['top'] - linha_actual[-1]['top']) <= tolerancia:
            linha_actual.append(w)
        else:
            linhas.append(sorted(linha_actual, key=lambda x: x['x0']))
            linha_actual = [w]
    linhas.append(sorted(linha_actual, key=lambda x: x['x0']))
    return linhas


def _recolher_texto_direita(pdf, pagina_inicio, y_inicio, pagina_fim, y_fim):
    """
    Recolhe o texto da coluna direita entre (pagina_inicio, y_inicio) e
    (pagina_fim, y_fim), reconstruindo linhas por proximidade vertical.
    Processa página a página, na ordem correcta, para nunca misturar
    posições verticais de páginas diferentes na mesma ordenação.
    Quando y_fim é None (último administrador do PDF), a recolha pára no
    primeiro marcador de fim de secção ("Página X de Y", "Outros órgãos")
    para não invadir secções não relacionadas com órgãos de gestão.
    """
    pagina_fim_real = min(pagina_fim, len(pdf.pages) - 1)
    todas_linhas = []

    for num_pagina in range(pagina_inicio, pagina_fim_real + 1):
        pagina = pdf.pages[num_pagina]
        palavras = pagina.extract_words()
        direita = [w for w in palavras if w['x0'] >= _LIMITE_COLUNA_X]

        palavras_pagina = []
        for w in direita:
            if num_pagina == pagina_inicio and w['top'] < y_inicio - 2:
                continue
            if num_pagina == pagina_fim and y_fim is not None and w['top'] >= y_fim - 2:
                continue
            palavras_pagina.append(w)

        # Ordena e agrupa SÓ dentro desta página, antes de passar à seguinte
        palavras_pagina.sort(key=lambda w: w['top'])
        linhas_pagina = _agrupar_por_linha(palavras_pagina)

        for linha in linhas_pagina:
            texto_linha = " ".join(w['text'] for w in linha)
            # Pára ao encontrar marcador de fim de secção, mesmo quando
            # y_fim ainda não foi definido (último bloco) — EXCEPTO se o
            # marcador for o rodapé "Página X de Y" da PRÓPRIA página de
            # início (num_pagina == pagina_inicio), onde aparece sempre
            # no fim da página, ABAIXO do bloco do administrador, sem
            # significar fim da secção — só faria sentido como travão se
            # já estivéssemos a percorrer texto de uma página seguinte.
            #
            # CORRECÇÃO: sem esta exceção, um administrador cujo cargo
            # ficasse no fim de uma página, com as suas ligações listadas
            # já na página seguinte, nunca chegava a ler essas ligações —
            # a recolha parava logo no rodapé da própria página inicial.
            eh_rodape_pagina = re.match(r'^Página\s+\d+\s+de\s+\d+', texto_linha.strip())
            if y_fim is None and eh_rodape_pagina and num_pagina != pagina_inicio:
                return "\n".join(todas_linhas)
            if y_fim is None and not eh_rodape_pagina and texto_linha.strip() in ("Outros órgãos", "ATIVIDADE"):
                return "\n".join(todas_linhas)
            if eh_rodape_pagina:
                continue
            todas_linhas.append(texto_linha)

    return "\n".join(todas_linhas)


def _chave_dedup_nome(nome):
    """
    Normaliza um nome de empresa para efeitos de deduplicação — remove
    sufixos descritivos entre parênteses (ex: "(SEM ATIVIDADE COMERCIAL)")
    que o relatório Informa D&B por vezes acrescenta ao nome em apenas
    uma das ocorrências da mesma empresa, fazendo com que duas referências
    à mesma entidade pareçam nomes diferentes.

    CORRECÇÃO: sem isto, "EQUIPAMARAVILHA..., LDA" e "EQUIPAMARAVILHA...,
    LDA (SEM ATIVIDADE COMERCIAL)" eram tratadas como duas relacionadas
    distintas, duplicando a mesma empresa na minuta.
    """
    sem_parenteses = re.sub(r'\s*\([^)]*\)\s*$', '', nome).strip()
    return sem_parenteses.upper()


def _extrair_socios_com_ligacoes(texto):
    """
    Extrai relacionadas a partir da secção 'Sócios / Acionistas com
    ligações a outras entidades' — formato:

        Nome do Sócio Entidade(s) a que também está ligado/a:
        EMPRESA A, LDA como Cargo
        EMPRESA B, LDA como Cargo
        Outro Nome Entidade(s) a que também está ligado/a:
        EMPRESA C, LDA como Cargo

    CORRECÇÃO: secção distinta da rede de administradores por posição —
    aqui o nome do sócio e a frase "Entidade(s) a que também está
    ligado/a:" estão na MESMA linha de texto linear (sem necessidade de
    coordenadas x/y, ao contrário do bloco de administradores). Antes
    desta função, estas ligações nunca eram capturadas — esta secção só
    aparece em relatórios cujos sócios (não administradores) têm ligações
    societárias próprias, e tinha passado despercebida nos PDFs testados
    anteriormente.
    """
    relacionadas = []
    linhas = [l.strip() for l in texto.split("\n")]

    inicio_idx = None
    for i, linha in enumerate(linhas):
        if re.match(
            r'^Sócios\s*/\s*Acionistas\s+com\s+liga[cç][oõ]es\s+a\s+outras\s+entidades$',
            linha, re.IGNORECASE
        ):
            inicio_idx = i + 1
            break

    if inicio_idx is None:
        return relacionadas

    _MARCADORES_FIM = (
        r'^Poderes de decis[aã]o$',
        r'^[Óo]rg[aã]os de gest[aã]o e administra[cç][aã]o',
    )

    padrao_nome_e_ligado = re.compile(
        r'^(.+?)\s+Entidade\(s\)\s+a\s+que\s+também\s+está\s+ligado/a:\s*$',
        re.IGNORECASE
    )
    padrao_ligacao = re.compile(r'^(.+?)\s+como\s+(.+)$')

    socio_actual = None
    for linha in linhas[inicio_idx:inicio_idx + 60]:
        if any(re.match(p, linha, re.IGNORECASE) for p in _MARCADORES_FIM):
            break

        m_nome = padrao_nome_e_ligado.match(linha)
        if m_nome:
            socio_actual = m_nome.group(1).strip()
            continue

        if socio_actual is None:
            continue

        m_ligacao = padrao_ligacao.match(linha)
        if m_ligacao:
            nome_empresa = m_ligacao.group(1).strip()
            cargo = m_ligacao.group(2).strip()
            if len(nome_empresa) > 4 and not nome_empresa.upper().startswith(socio_actual.upper()):
                relacionadas.append({
                    "nome": nome_empresa, "nif": None,
                    "tipo": "ligacao_socio", "participacao": None,
                    "origem": "administrador",
                    "via": socio_actual, "cargo": cargo,
                })

    return relacionadas


def _juntar_e_deduplicar(lista_a, lista_b):
    """
    Junta duas listas de relacionadas, deduplicando por nome normalizado
    (case-insensitive, sem sufixos descritivos entre parênteses — ver
    _chave_dedup_nome).

    Quando duas ocorrências da mesma empresa diferem só no sufixo
    descritivo, mantém-se a versão SEM sufixo (mais limpa para a minuta),
    a menos que só exista a versão com sufixo.
    """
    vistos = {}
    for item in lista_a + lista_b:
        chave = _chave_dedup_nome(item["nome"])
        if chave not in vistos:
            vistos[chave] = item
        else:
            existente = vistos[chave]
            # Prioridade 1: origem "participacao" é mais fiável que "administrador"
            # Prioridade 2 (entre duas do mesmo tipo de origem): preferir o
            # nome sem sufixo descritivo entre parênteses (mais limpo)
            existente_tem_sufixo = bool(re.search(r'\([^)]*\)\s*$', existente["nome"]))
            item_tem_sufixo = bool(re.search(r'\([^)]*\)\s*$', item["nome"]))

            if existente.get("origem") == "administrador" and item.get("origem") == "participacao":
                vistos[chave] = item
            elif existente_tem_sufixo and not item_tem_sufixo:
                vistos[chave] = item
    return list(vistos.values())


# ---------------------------------------------------------------------------
# Modo API — implementação futura
# ---------------------------------------------------------------------------

def _obter_empresas_api(nif_empresa):
    """
    Chama a API Informa D&B para obter dados de empresas relacionadas.
    Implementação futura — requer APINFORMA_API_KEY no .env.
    """
    raise NotImplementedError(
        "Modo API não implementado. "
        "Configure MODO_EMPRESAS=pdf no .env para usar o modo PDF."
    )