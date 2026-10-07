# preencher_word.py
# Preenche uma minuta Word com os dados extraídos do formulário.
# Processa por esta ordem:
#   1. Blocos condicionais (SE_X/FIM_X)
#   2. Blocos de repetição em tabelas (INICIO_X/FIM_X)
#   3. Substituição simples de marcadores

import os
import copy
from docx import Document
from utils import formatar_valor_euros, valor_por_extenso, formatar_data, juntar_campos
from mapeamento import CAMPOS_CONDICIONAIS, BLOCOS_REPETICAO, CAMPOS_SEM_FORMULARIO
from logger import log_tecnico

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


# ---------------------------------------------------------------------------
# FUNÇÃO PRINCIPAL
# ---------------------------------------------------------------------------

def preencher_minuta(caminho_minuta, dados, caminho_output, procedimento_id=None):
    """
    Preenche a minuta Word com os dados fornecidos e guarda em caminho_output.
    Devolve caminho_output se bem sucedido.
    """
    log_tecnico("minuta_inicio", {"minuta": caminho_minuta}, procedimento_id)

    doc = Document(caminho_minuta)

    # Prepara dicionário de substituição simples
    substituicoes = _preparar_substituicoes(dados)

    # 1. Blocos condicionais
    _processar_condicionais(doc, dados)

    # 2. Blocos de repetição em tabelas
    _processar_blocos_tabela(doc, dados, substituicoes)

    # 3. Substituição simples — parágrafos e células de tabela
    _substituir_marcadores(doc, substituicoes)

    # Guarda o documento
    os.makedirs(os.path.dirname(caminho_output), exist_ok=True)
    doc.save(caminho_output)

    log_tecnico("minuta_gerada", {"output": caminho_output}, procedimento_id)
    return caminho_output


# ---------------------------------------------------------------------------
# PREPARAÇÃO DAS SUBSTITUIÇÕES SIMPLES
# ---------------------------------------------------------------------------

def _preparar_substituicoes(dados):
    """
    Constrói dicionário {marcador: valor} para substituição simples.
    Campos None ou ausentes → [a preencher].
    """
    subs = {}

    for chave, valor in dados.items():
        marcador = f"{{{{{chave}}}}}"

        if chave in CAMPOS_SEM_FORMULARIO or valor is None:
            subs[marcador] = "[a preencher]"
        elif isinstance(valor, float):
            subs[marcador] = formatar_valor_euros(valor)
        elif isinstance(valor, list):
            continue
        elif isinstance(valor, bool):
            subs[marcador] = "Sim" if valor else "Não"
        else:
            subs[marcador] = str(valor)

    # Campos calculados
    preco = dados.get("PRECO_BASE")
    subs["{{PRECO_BASE_EXTENSO}}"] = valor_por_extenso(preco) if preco else "[a preencher]"

    # CPV_COMPLETO — sem lotes
    cpv = dados.get("CPV", "")
    cpv_desc = dados.get("CPV_DESC", "")
    if cpv and cpv_desc:
        subs["{{CPV_COMPLETO}}"] = f"{cpv} — {cpv_desc}"
    else:
        subs["{{CPV_COMPLETO}}"] = "[a preencher]"

    # Cargos do júri — não vêm do formulário
    for campo_cargo in [
        "PRESIDENTE_JURI_CARGO",
        "VOGAL_EFETIVO_1_CARGO", "VOGAL_EFETIVO_2_CARGO",
        "VOGAL_SUPLENTE_1_CARGO", "VOGAL_SUPLENTE_2_CARGO"
    ]:
        subs[f"{{{{{campo_cargo}}}}}"] = "[a preencher]"

    # Versão com plicas — para marcadores envolvidos em aspas na minuta
    for marcador, valor in list(subs.items()):
        subs[f"'{marcador}'"] = valor

    return subs


# ---------------------------------------------------------------------------
# BLOCOS CONDICIONAIS
# ---------------------------------------------------------------------------

def _processar_condicionais(doc, dados):
    """
    Para cada campo condicional, activa o bloco correcto e remove o outro.
    """
    for campo, (se_sim, fim_sim, se_nao, fim_nao) in CAMPOS_CONDICIONAIS.items():
        valor = dados.get(campo)
        verdadeiro = valor in ("Sim", True, "sim", "SIM")

        if verdadeiro:
            _remover_bloco(doc, f"{{{{{se_nao}}}}}", f"{{{{{fim_nao}}}}}")
            _remover_marcadores_controlo(doc, f"{{{{{se_sim}}}}}", f"{{{{{fim_sim}}}}}")
        else:
            _remover_bloco(doc, f"{{{{{se_sim}}}}}", f"{{{{{fim_sim}}}}}")
            _remover_marcadores_controlo(doc, f"{{{{{se_nao}}}}}", f"{{{{{fim_nao}}}}}")


def _remover_bloco(doc, marcador_inicio, marcador_fim):
    """Remove todos os parágrafos entre marcador_inicio e marcador_fim (inclusive)."""
    dentro = False
    a_remover = []

    for p in list(doc.paragraphs):
        texto = _texto_paragrafo(p)
        if marcador_inicio in texto:
            dentro = True
        if dentro:
            a_remover.append(p)
        if dentro and marcador_fim in texto:
            dentro = False

    for p in a_remover:
        _remover_paragrafo(p)

    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                _remover_bloco_celula(celula, marcador_inicio, marcador_fim)


def _remover_bloco_celula(celula, marcador_inicio, marcador_fim):
    """Remove parágrafos dentro de uma célula entre os marcadores."""
    dentro = False
    a_remover = []

    for p in list(celula.paragraphs):
        texto = _texto_paragrafo(p)
        if marcador_inicio in texto:
            dentro = True
        if dentro:
            a_remover.append(p)
        if dentro and marcador_fim in texto:
            dentro = False

    for p in a_remover:
        _remover_paragrafo(p)


def _remover_marcadores_controlo(doc, marcador_inicio, marcador_fim):
    """Remove só os parágrafos que contêm os marcadores de controlo."""
    for p in list(doc.paragraphs):
        texto = _texto_paragrafo(p)
        if marcador_inicio in texto or marcador_fim in texto:
            _remover_paragrafo(p)

    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                for p in list(celula.paragraphs):
                    texto = _texto_paragrafo(p)
                    if marcador_inicio in texto or marcador_fim in texto:
                        _remover_paragrafo(p)


# ---------------------------------------------------------------------------
# BLOCOS DE REPETIÇÃO EM TABELAS
# ---------------------------------------------------------------------------

def _processar_blocos_tabela(doc, dados, substituicoes):
    """
    Processa todos os blocos de repetição em tabelas e parágrafos.
    """
    # Blocos em tabelas
    for tabela in doc.tables:
        for nome_bloco in ["LOTES_CPV", "LOTES_CAB", "EMPRESAS", "EMP_ACUM"]:
            _processar_bloco(tabela, nome_bloco, dados, substituicoes)

    # Blocos em parágrafos
    _processar_bloco_paragrafos(doc, "LOTES_VALOR", dados, substituicoes)


def _processar_bloco(tabela, nome_bloco, dados, substituicoes):
    """
    Detecta e processa um bloco de repetição numa tabela.

    Para o bloco EMP_ACUM (empresas com acumulados), cada item replicado
    contém um bloco aninhado de relacionadas (EMP_REL_ACUM). Esse bloco
    aninhado existe APENAS UMA VEZ no modelo original da tabela — por isso
    é capturado e guardado em memória (como cópias XML independentes) ANTES
    de o ciclo de empresas começar a inserir e remover linhas. Sem isto, a
    segunda iteração do ciclo já não encontra o bloco aninhado (foi consumido
    pela primeira), o que produzia relacionadas trocadas, vazias ou da
    empresa errada.
    """
    cfg = BLOCOS_REPETICAO.get(nome_bloco)
    if not cfg:
        return

    m_inicio = f"{{{{{cfg['inicio']}}}}}"
    m_fim    = f"{{{{{cfg['fim']}}}}}"

    # Encontra linhas de início e fim
    idx_inicio = idx_fim = None
    for i, linha in enumerate(tabela.rows):
        texto = _texto_linha(linha)
        if m_inicio in texto and idx_inicio is None:
            idx_inicio = i
        if m_fim in texto and idx_inicio is not None:
            idx_fim = i
            break

    if idx_inicio is None or idx_fim is None:
        return

    # Guarda referências aos TRs antes de qualquer modificação
    tr_inicio  = tabela.rows[idx_inicio]._tr
    tr_fim     = tabela.rows[idx_fim]._tr
    trs_modelo = [tabela.rows[i]._tr for i in range(idx_inicio + 1, idx_fim)]

    if not trs_modelo:
        return

    # --- Captura do molde do bloco aninhado de relacionadas (só para EMP_ACUM) ---
    # Guardamos CÓPIAS XML independentes (deepcopy) dos TRs do bloco aninhado,
    # extraídas dos trs_modelo ANTES de qualquer linha ser inserida ou removida.
    # Cada empresa, no ciclo abaixo, recebe uma cópia fresca deste molde.
    #
    # CORRECÇÃO (Decisão 38): trs_modelo continha TODAS as linhas entre
    # INICIO_EMP_ACUM e FIM_EMP_ACUM — incluindo as linhas que pertencem ao
    # bloco aninhado EMP_REL_ACUM (controlo + linha de dados + aviso sem_rel).
    # O ciclo de empresas copiava e inserrnia ESSAS linhas também, como se
    # fossem parte fixa da empresa — daí marcadores {{EMP_REL_NOME}} a sobrar
    # no documento final e o aviso "sem relacionadas" duplicado/mal colocado.
    #
    # Agora trs_modelo é dividido em duas partes ANTES do ciclo de empresas:
    #   - trs_modelo_empresa  → só as linhas próprias da empresa (replicadas
    #                            tal como antes, uma vez por empresa)
    #   - (o bloco aninhado nunca é replicado directamente — só entra via
    #      cópias frescas do molde, inseridas no ponto exacto)
    molde_rel = None
    trs_modelo_empresa = trs_modelo
    if nome_bloco == "EMP_ACUM":
        molde_rel = _capturar_molde_relacionadas(trs_modelo)
        if molde_rel is not None:
            # Remove do conjunto "linhas da empresa" tudo o que pertence ao
            # bloco aninhado (do INICIO_EMP_REL_ACUM ao FIM_SEM_REL, inclusive,
            # consoante o que existir). Usa os índices já calculados no molde.
            idx_remover = set(
                range(molde_rel["idx_inicio_bloco"], molde_rel["idx_fim_bloco"] + 1)
            )
            trs_modelo_empresa = [
                tr for i, tr in enumerate(trs_modelo) if i not in idx_remover
            ]

    # Dados a iterar
    lista = dados.get(cfg["chave_dados"]) or []

    # CORRECÇÃO: quando não há lotes (procedimento com CPV isolado, não
    # dividido em lotes), dados["LOTES"] fica vazio/None por design — é o
    # comportamento correcto de ler_pdf.py (ver correcção de TEM_LOTES).
    # Mas os blocos LOTES_CPV/LOTES_CAB/LOTES_VALOR são blocos de
    # repetição que, sem nenhum item na lista, simplesmente não inserem
    # nenhuma linha — fazendo a tabela do CPV desaparecer da minuta por
    # completo (só ficava o cabeçalho), em vez de mostrar a linha única
    # do CPV isolado que já existia antes desta tabela ser tratada como
    # bloco de repetição. Constrói-se aqui um item sintético "lote único"
    # a partir dos campos CPV/CPV_DESC/TIPO_OBJETO já disponíveis em
    # dados, para que esta tabela continue a mostrar uma linha mesmo sem
    # lotes reais — replicando o mesmo padrão de "sem dados → linha
    # única" já usado para EMP_ACUM acima.
    if nome_bloco in ("LOTES_CPV", "LOTES_CAB", "LOTES_VALOR") and not lista:
        if dados.get("CPV"):
            lista = [{
                "NR": 1,
                "NOME": dados.get("CPV_DESC") or "",
                "VALOR": dados.get("PRECO_BASE"),
                "CABIMENTO": dados.get("CENTRO_CUSTOS") or "",
                "CPV": dados.get("CPV"),
                "CPV_DESC": dados.get("CPV_DESC") or "",
            }]

    # Para EMP_ACUM sem dados — coloca [em desenvolvimento]
    if nome_bloco == "EMP_ACUM" and not lista:
        novo_tr = copy.deepcopy(trs_modelo_empresa[0])
        _substituir_xml(novo_tr, {"{{EMP_NOME}}": "[em desenvolvimento]"})
        tr_fim.addprevious(novo_tr)
        tr_inicio.getparent().remove(tr_inicio)
        for tr in trs_modelo:
            tr.getparent().remove(tr)
        tr_fim.getparent().remove(tr_fim)
        return

    # Replica linhas para cada item
    for item in lista:
        subs_item = _preparar_subs_item(item, nome_bloco, dados, substituicoes)

        # TRs desta empresa — APENAS as linhas próprias (já sem o bloco
        # aninhado, removido acima). O ponto de inserção do bloco de
        # relacionadas é onde a linha de dados da empresa ficar, sempre
        # antes de tr_fim (fim do EMP_ACUM).
        trs_desta_empresa = []
        for tr_modelo in trs_modelo_empresa:
            novo_tr = copy.deepcopy(tr_modelo)
            _substituir_xml(novo_tr, subs_item)
            trs_desta_empresa.append(novo_tr)
            tr_fim.addprevious(novo_tr)

        # Bloco aninhado de relacionadas — insere sempre cópias frescas do
        # molde capturado no início da função, directamente antes de tr_fim
        # (ou seja, depois das linhas próprias desta empresa que já foram
        # inseridas, e antes da próxima empresa / fim do bloco EMP_ACUM)
        if nome_bloco == "EMP_ACUM" and molde_rel is not None:
            _inserir_bloco_relacionadas(molde_rel, item, tr_fim)

    # Remove linhas de controlo e modelo usando referências directas
    for tr in [tr_inicio] + trs_modelo + [tr_fim]:
        try:
            parent = tr.getparent()
            if parent is not None:
                parent.remove(tr)
        except Exception:
            pass


def _capturar_molde_relacionadas(trs_modelo):
    """
    Procura, dentro dos TRs modelo de EMP_ACUM, os marcadores do bloco
    aninhado EMP_REL_ACUM e do bloco SE_SEM_REL, e devolve um "molde" —
    dict com cópias XML profundas (deepcopy) de cada secção.

    CORRECÇÃO (Decisão 38): além das cópias do molde, devolve também
    idx_inicio_bloco / idx_fim_bloco — o intervalo COMPLETO (controlo +
    dados + aviso) que pertence ao bloco aninhado dentro de trs_modelo.
    Este intervalo é usado por _processar_bloco para EXCLUIR essas linhas
    das "linhas próprias da empresa" — nunca devem ser inseridas como TR
    autónomo; só entram via cópias frescas do molde, por relacionada.

    Devolve None se os marcadores não forem encontrados (minuta sem
    bloco de relacionadas dentro de EMP_ACUM).
    """
    cfg = BLOCOS_REPETICAO.get("EMP_REL_ACUM")
    if not cfg:
        return None

    m_inicio_rel = f"{{{{{cfg['inicio']}}}}}"
    m_fim_rel    = f"{{{{{cfg['fim']}}}}}"
    m_sem_rel_ini = "{{SE_SEM_REL}}"
    m_sem_rel_fim = "{{FIM_SEM_REL}}"

    def _texto_tr(tr):
        return "".join(t.text or "" for t in tr.iter(f"{{{W_NS}}}t"))

    idx_inicio_rel = idx_fim_rel = None
    idx_sem_rel_ini = idx_sem_rel_fim = None

    for i, tr in enumerate(trs_modelo):
        texto = _texto_tr(tr)
        if m_inicio_rel in texto and idx_inicio_rel is None:
            idx_inicio_rel = i
        if m_fim_rel in texto and idx_inicio_rel is not None and idx_fim_rel is None:
            idx_fim_rel = i
        if m_sem_rel_ini in texto and idx_sem_rel_ini is None:
            idx_sem_rel_ini = i
        if m_sem_rel_fim in texto and idx_sem_rel_fim is None:
            idx_sem_rel_fim = i

    if idx_inicio_rel is None or idx_fim_rel is None:
        return None

    # TRs modelo da relacionada (entre início e fim do bloco aninhado).
    #
    # CORRECÇÃO (2ª parte da Decisão 38): este intervalo, na estrutura
    # real, inclui também o bloco SE_SEM_REL/aviso/FIM_SEM_REL — porque
    # esse bloco vive DENTRO de INICIO_EMP_REL_ACUM...FIM_EMP_REL_ACUM,
    # não fora dele como a versão de teste inicial assumia. Sem esta
    # exclusão, cada relacionada inserida arrastava consigo uma cópia
    # extra do aviso "sem relacionadas".
    #
    # Por isso: ao construir trs_linha_rel, excluímos também o intervalo
    # idx_sem_rel_ini..idx_sem_rel_fim, se estiver contido aqui dentro.
    indices_excluir_do_molde_linha = set()
    if idx_sem_rel_ini is not None and idx_sem_rel_fim is not None:
        if idx_inicio_rel < idx_sem_rel_ini and idx_sem_rel_fim < idx_fim_rel:
            indices_excluir_do_molde_linha = set(
                range(idx_sem_rel_ini, idx_sem_rel_fim + 1)
            )

    trs_linha_rel = [
        copy.deepcopy(trs_modelo[i])
        for i in range(idx_inicio_rel + 1, idx_fim_rel)
        if i not in indices_excluir_do_molde_linha
    ]

    # TRs do bloco "sem relacionadas" (se existir)
    trs_sem_rel_modelo = []
    if idx_sem_rel_ini is not None and idx_sem_rel_fim is not None:
        trs_sem_rel_modelo = [
            copy.deepcopy(trs_modelo[i])
            for i in range(idx_sem_rel_ini, idx_sem_rel_fim + 1)
        ]

    # Intervalo COMPLETO a excluir das "linhas próprias da empresa":
    # do início do que aparecer primeiro (INICIO_EMP_REL_ACUM ou SE_SEM_REL)
    # até ao fim do que aparecer depois (FIM_EMP_REL_ACUM ou FIM_SEM_REL).
    candidatos_inicio = [idx_inicio_rel]
    candidatos_fim = [idx_fim_rel]
    if idx_sem_rel_ini is not None:
        candidatos_inicio.append(idx_sem_rel_ini)
    if idx_sem_rel_fim is not None:
        candidatos_fim.append(idx_sem_rel_fim)

    idx_inicio_bloco = min(candidatos_inicio)
    idx_fim_bloco = max(candidatos_fim)

    return {
        "idx_inicio_rel":    idx_inicio_rel,
        "idx_fim_rel":       idx_fim_rel,
        "idx_inicio_bloco":  idx_inicio_bloco,  # ← novo: limite a excluir
        "idx_fim_bloco":     idx_fim_bloco,      # ← novo: limite a excluir
        "trs_linha_rel":     trs_linha_rel,       # molde da(s) linha(s) por relacionada
        "trs_sem_rel":       trs_sem_rel_modelo,  # molde do aviso "sem relacionadas"
    }


def _inserir_bloco_relacionadas(molde_rel, empresa, tr_fim):
    """
    Insere o bloco de relacionadas desta empresa, directamente antes de
    tr_fim (fim do bloco EMP_ACUM) — ou seja, logo depois das linhas
    próprias da empresa que _processar_bloco já inseriu.

    CORRECÇÃO (Decisão 38): já não recebe trs_desta_empresa nem procura
    marcadores de controlo "sobreviventes" — essa abordagem falhava porque
    as linhas do bloco aninhado deixaram de ser inseridas como TR autónomo
    (são excluídas em _processar_bloco antes do ciclo de empresas). Esta
    função insere sempre cópias frescas do molde, no ponto exacto.
    """
    relacionadas = empresa.get("relacionadas") or []

    if not relacionadas:
        # Sem relacionadas: insere o aviso "sem relacionadas". O molde
        # trs_sem_rel inclui as próprias linhas de controlo SE_SEM_REL/
        # FIM_SEM_REL (que na minuta são TRs autónomos, não texto dentro
        # da linha de aviso) — essas ficam vazias depois de limpar o
        # marcador e não devem ser inseridas, ou sobram linhas em branco.
        # Filtra-as: só insere TRs cujo texto, depois de limpar os
        # marcadores de controlo, ainda tem conteúdo real.
        for tr_modelo_sem_rel in molde_rel["trs_sem_rel"]:
            novo_tr = copy.deepcopy(tr_modelo_sem_rel)
            for t_elem in novo_tr.iter(f"{{{W_NS}}}t"):
                if t_elem.text:
                    t_elem.text = (
                        t_elem.text.replace("{{SE_SEM_REL}}", "")
                                    .replace("{{FIM_SEM_REL}}", "")
                    )
            texto_restante = "".join(
                t.text or "" for t in novo_tr.iter(f"{{{W_NS}}}t")
            ).strip()
            if texto_restante:
                tr_fim.addprevious(novo_tr)
        return

    # Com relacionadas: insere uma cópia fresca do molde de linha por cada
    # relacionada, antes de tr_fim
    for rel in relacionadas:
        subs_rel = {
            "{{EMP_REL_NOME}}":           rel.get("nome", "[a preencher]"),
            "{{EMP_REL_NIF}}":            rel.get("nif", "[a preencher]"),
            "{{ACUM_EMP_REL_ANO_ATUAL}}": "[em desenvolvimento]",
            "{{ACUM_EMP_REL_ANO_1}}":     "[em desenvolvimento]",
            "{{ACUM_EMP_REL_ANO_2}}":     "[em desenvolvimento]",
            "{{ACUM_EMP_REL_TOTAL}}":     "[em desenvolvimento]",
        }
        for tr_modelo_rel in molde_rel["trs_linha_rel"]:
            novo_tr = copy.deepcopy(tr_modelo_rel)
            _substituir_xml(novo_tr, subs_rel)
            tr_fim.addprevious(novo_tr)


def _processar_bloco_paragrafos(doc, nome_bloco, dados, substituicoes):
    """
    Processa blocos de repetição em parágrafos normais (não tabelas).
    Replica o parágrafo modelo para cada item da lista.
    """
    cfg = BLOCOS_REPETICAO.get(nome_bloco)
    if not cfg:
        return

    m_inicio = f"{{{{{cfg['inicio']}}}}}"
    m_fim    = f"{{{{{cfg['fim']}}}}}"

    paragrafos = list(doc.paragraphs)
    idx_inicio = idx_fim = None

    for i, p in enumerate(paragrafos):
        texto = _texto_paragrafo(p)
        if m_inicio in texto and idx_inicio is None:
            idx_inicio = i
        if m_fim in texto and idx_inicio is not None:
            idx_fim = i
            break

    if idx_inicio is None or idx_fim is None:
        return

    # Parágrafos modelo
    ps_modelo = paragrafos[idx_inicio + 1:idx_fim]
    if not ps_modelo:
        return

    # Dados a iterar
    lista = dados.get(cfg["chave_dados"]) or []

    # Referência de inserção — parágrafo FIM
    p_fim = paragrafos[idx_fim]

    # Replica parágrafos para cada item
    for item in lista:
        subs_item = _preparar_subs_item(item, nome_bloco, dados, substituicoes)
        for p_modelo in ps_modelo:
            # Copia o parágrafo modelo
            novo_p = copy.deepcopy(p_modelo._element)
            # Substitui marcadores no XML
            for t_elem in novo_p.iter(f"{{{W_NS}}}t"):
                if t_elem.text:
                    texto_novo = t_elem.text
                    for marcador, valor in subs_item.items():
                        texto_novo = texto_novo.replace(marcador, str(valor))
                    t_elem.text = texto_novo
            # Insere antes do parágrafo FIM
            p_fim._element.addprevious(novo_p)

    # Remove parágrafos de controlo e modelo
    for p in [paragrafos[idx_inicio]] + ps_modelo + [p_fim]:
        try:
            parent = p._element.getparent()
            if parent is not None:
                parent.remove(p._element)
        except Exception:
            pass


def _substituir_bloco_vazio(tabela, idx_inicio, idx_fim, texto_substituto):
    """Substitui bloco inteiro por uma única linha com texto."""
    tr_fim = tabela.rows[idx_fim]._tr
    tr_modelo = tabela.rows[idx_inicio + 1]._tr
    novo_tr = copy.deepcopy(tr_modelo)
    _substituir_xml(novo_tr, {"{{EMP_NOME}}": texto_substituto})
    tr_fim.addprevious(novo_tr)
    _remover_trs(tabela, list(range(idx_inicio, idx_fim + 1)))


def _substituir_xml(tr, substituicoes):
    """
    Substitui marcadores directamente nos nós de texto de um TR.
    Consolida runs partidos antes de substituir.
    """
    from lxml import etree

    # Consolida texto de cada parágrafo (w:p) dentro do TR
    W_P = f"{{{W_NS}}}p"
    W_R = f"{{{W_NS}}}r"
    W_T = f"{{{W_NS}}}t"
    W_RPR = f"{{{W_NS}}}rPr"

    for p_elem in tr.iter(W_P):
        # Recolhe todos os runs do parágrafo
        runs = p_elem.findall(f".//{W_R}")
        if not runs:
            continue

        # Constrói texto completo do parágrafo
        texto_completo = "".join(
            t.text or "" for r in runs for t in r.findall(W_T)
        )

        # Verifica se há marcadores
        if "{{" not in texto_completo:
            continue

        # Aplica substituições
        texto_novo = texto_completo
        for marcador, valor in substituicoes.items():
            texto_novo = texto_novo.replace(marcador, str(valor))

        if texto_novo == texto_completo:
            continue

        # Guarda formatação do primeiro run
        primeiro_run = runs[0]
        rpr = primeiro_run.find(W_RPR)

        # Remove todos os runs
        for r in runs:
            p_elem.remove(r)

        # Cria novo run com texto substituído
        novo_r = etree.SubElement(p_elem, W_R)
        if rpr is not None:
            novo_r.insert(0, copy.deepcopy(rpr))
        novo_t = etree.SubElement(novo_r, W_T)
        novo_t.text = texto_novo
        if " " in texto_novo:
            novo_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def _remover_trs(tabela, indices):
    """Remove linhas por índice — do fim para o início."""
    for idx in sorted(set(indices), reverse=True):
        try:
            tr = tabela.rows[idx]._tr
            tr.getparent().remove(tr)
        except (IndexError, AttributeError):
            pass


def _remover_linhas_entre(tabela, m_inicio, m_fim):
    """Remove todas as linhas entre dois marcadores (inclusive)."""
    dentro = False
    a_remover = []
    for i, linha in enumerate(tabela.rows):
        texto = _texto_linha(linha)
        if m_inicio in texto:
            dentro = True
        if dentro:
            a_remover.append(i)
        if dentro and m_fim in texto:
            dentro = False
    _remover_trs(tabela, a_remover)


def _limpar_marcadores_linha(tabela, marcador):
    """Remove o marcador do texto de uma linha sem apagar a linha."""
    for linha in tabela.rows:
        texto = _texto_linha(linha)
        if marcador in texto:
            for celula in linha.cells:
                for p in celula.paragraphs:
                    _substituir_paragrafo(p, {marcador: ""})


# ---------------------------------------------------------------------------
# SUBSTITUIÇÃO SIMPLES
# ---------------------------------------------------------------------------

def _substituir_marcadores(doc, substituicoes):
    """
    Substitui todos os marcadores simples em parágrafos e células de tabela.
    """
    for p in doc.paragraphs:
        _substituir_paragrafo(p, substituicoes)

    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                for p in celula.paragraphs:
                    _substituir_paragrafo(p, substituicoes)


def _substituir_paragrafo(paragrafo, substituicoes):
    """
    Substitui marcadores num parágrafo preservando a formatação.
    Reconstrói os runs para garantir substituição mesmo quando
    o marcador está partido entre vários runs.
    """
    texto_completo = _texto_paragrafo(paragrafo)

    if "{{" not in texto_completo:
        return

    texto_novo = texto_completo
    for marcador, valor in substituicoes.items():
        texto_novo = texto_novo.replace(marcador, valor)

    if texto_novo != texto_completo:
        if paragrafo.runs:
            run0 = paragrafo.runs[0]
            font_name = run0.font.name
            font_size = run0.font.size
            bold      = run0.bold
            italic    = run0.italic
            try:
                color = run0.font.color.rgb if run0.font.color and run0.font.color.type else None
            except Exception:
                color = None

            for run in paragrafo.runs:
                run._r.getparent().remove(run._r)

            novo_run = paragrafo.add_run(texto_novo)
            novo_run.font.name = font_name
            novo_run.font.size = font_size
            novo_run.bold      = bold
            novo_run.italic    = italic
            if color:
                novo_run.font.color.rgb = color


# ---------------------------------------------------------------------------
# AUXILIARES
# ---------------------------------------------------------------------------

def _preparar_subs_item(item, nome_bloco, dados, substituicoes):
    """Prepara substituições específicas para um item de uma lista."""
    subs = dict(substituicoes)

    if nome_bloco in ("LOTES_CPV", "LOTES_CAB", "LOTES_VALOR"):
        subs.update({
            "{{LOTE_NR}}":           str(item.get("NR", "")),
            "{{LOTE_NOME}}":         item.get("NOME", "[a preencher]"),
            "{{LOTE_VALOR}}":        formatar_valor_euros(item.get("VALOR")),
            "{{LOTE_CABIMENTO}}":    item.get("CABIMENTO") or "[a preencher]",
            "{{LOTE_CPV}}":          item.get("CPV", "[a preencher]"),
            "{{LOTE_CPV_DESC}}":     item.get("CPV_DESC", "[a preencher]"),
            "{{LOTE_CPV_COMPLETO}}": f"{item.get('CPV', '')} — {item.get('CPV_DESC', '')}",
            "{{LOTE_ACUM_CPV}}":     "[em desenvolvimento]",
            # CORRECÇÃO: a minuta real usa o marcador {{ACUM_CPV}} (sem o
            # prefixo LOTE_) para o acumulado por CPV — discrepância de
            # nomenclatura entre mapeamento.py e a minuta Word, do mesmo
            # tipo já resolvido no main.py para outros campos (Decisão 36).
            # Mantém-se como alias aqui em vez de alterar a minuta, já que
            # ambos os campos pertencem à Camada C (ainda não construída).
            "{{ACUM_CPV}}":          "[em desenvolvimento]",
            "{{LOTE_TIPO_OBJETO}}":  dados.get("TIPO_OBJETO", "[a preencher]"),
            # CORRECÇÃO: a minuta real usa {{TIPO_OBJETO}} (sem o prefixo
            # LOTE_) na coluna "Tipo de despesa" desta tabela — confirmado
            # por inspecção directa da estrutura real (mesmo padrão de
            # discrepância de nomenclatura já visto em ACUM_CPV).
            "{{TIPO_OBJETO}}":       dados.get("TIPO_OBJETO", "[a preencher]"),
        })

    elif nome_bloco in ("EMPRESAS", "EMP_ACUM"):
        subs.update({
            "{{EMP_NOME}}":           item.get("nome", "[a preencher]"),
            "{{EMP_NIF}}":            item.get("nif", "[a preencher]"),
            "{{EMP_EMAIL}}":          item.get("email", "[a preencher]"),
            "{{ACUM_EMP_ANO_ATUAL}}": "[em desenvolvimento]",
            "{{ACUM_EMP_ANO_1}}":     "[em desenvolvimento]",
            "{{ACUM_EMP_ANO_2}}":     "[em desenvolvimento]",
            "{{ACUM_EMP_TOTAL}}":     "[em desenvolvimento]",
        })

    return subs


def _texto_paragrafo(paragrafo):
    """Devolve o texto completo de um parágrafo."""
    return "".join(run.text for run in paragrafo.runs)


def _texto_linha(linha):
    """Devolve o texto completo de uma linha de tabela."""
    partes = []
    for celula in linha.cells:
        texto_celula = " ".join(
            "".join(run.text for run in p.runs)
            for p in celula.paragraphs
        )
        partes.append(texto_celula)
    return " ".join(partes)


def _remover_paragrafo(paragrafo):
    """Remove um parágrafo do documento."""
    p = paragrafo._element
    p.getparent().remove(p)