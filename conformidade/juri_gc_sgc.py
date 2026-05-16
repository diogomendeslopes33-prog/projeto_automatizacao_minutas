# conformidade/juri_gc_sgc.py
# Verificação de regras de composição do júri, gestor do contrato
# e substituto do gestor do contrato
# Art. 67º, 68º e 69º CCP (júri)
# Art. 290º-A CCP (gestor do contrato)
#
# Versão 2 — Maio 2026
# Estado: Por validar

# ---------------------------------------------------------------------------
# Campos de membros do júri esperados no formulário
# ---------------------------------------------------------------------------

CAMPOS_EFETIVOS = [
    "PRESIDENTE_JURI_NOME",
    "VOGAL_EFETIVO_1_NOME",
    "VOGAL_EFETIVO_2_NOME",
]

CAMPOS_SUPLENTES = [
    "VOGAL_SUPLENTE_1_NOME",
    "VOGAL_SUPLENTE_2_NOME",
]


# ---------------------------------------------------------------------------
# Art. 67º/1 e 67º/3 CCP
# Obrigatoriedade e composição do júri
# ---------------------------------------------------------------------------

def verificar_composicao_juri(dados):
    # Art. 67º/1 CCP
    # Com excepção do ajuste directo, os procedimentos são conduzidos por um
    # júri composto, em número ímpar, por um mínimo de três membros efetivos
    # (um dos quais preside) e dois suplentes.
    # Art. 67º/3 CCP
    # O concurso público urgente pode ser conduzido pelos serviços da entidade
    # adjudicante, dispensando o júri — distinção que o formulário não prevê,
    # tratada nas normas interpretativas.

    alertas = []

    tipo_procedimento = (dados.get("TIPO_PROCEDIMENTO") or "").strip()

    # Ajuste directo — sem júri obrigatório
    if tipo_procedimento == "Ajuste Directo":
        return alertas

    efetivos_em_falta = [
        campo for campo in CAMPOS_EFETIVOS
        if not (dados.get(campo) or "").strip()
    ]

    suplentes_em_falta = [
        campo for campo in CAMPOS_SUPLENTES
        if not (dados.get(campo) or "").strip()
    ]

    if efetivos_em_falta:
        campos_str = ", ".join(efetivos_em_falta)
        alertas.append({
            "nivel":    "erro",
            "artigo":   "art. 67º/1 CCP",
            "campo":    campos_str,
            "mensagem": (
                f"O júri do procedimento não está completamente designado. "
                f"Faltam os seguintes membros efetivos: {campos_str}. "
                f"O júri deve ser composto por um mínimo de três membros efetivos "
                f"em número ímpar, um dos quais preside, nos termos do art. 67º/1 CCP."
            ),
        })

    if suplentes_em_falta:
        campos_str = ", ".join(suplentes_em_falta)
        alertas.append({
            "nivel":    "erro",
            "artigo":   "art. 67º/1 CCP",
            "campo":    campos_str,
            "mensagem": (
                f"O júri do procedimento não está completamente designado. "
                f"Faltam os seguintes membros suplentes: {campos_str}. "
                f"O júri deve incluir dois suplentes, nos termos do art. 67º/1 CCP."
            ),
        })

    return alertas


# ---------------------------------------------------------------------------
# Art. 67º/1 CCP — verificar duplicação de membros no júri
# O mesmo técnico não pode acumular mais do que um lugar no júri
# ---------------------------------------------------------------------------

def verificar_duplicacao_juri(dados):
    # Art. 67º/1 CCP
    # O júri é composto por membros distintos. A designação do mesmo técnico
    # para mais do que um lugar no júri é inadmissível.

    alertas = []

    tipo_procedimento = (dados.get("TIPO_PROCEDIMENTO") or "").strip()
    if tipo_procedimento == "Ajuste Directo":
        return alertas

    todos_campos = CAMPOS_EFETIVOS + CAMPOS_SUPLENTES
    nomes = [
        (campo, (dados.get(campo) or "").strip().lower())
        for campo in todos_campos
        if (dados.get(campo) or "").strip()
    ]

    vistos = {}
    for campo, nome in nomes:
        if nome in vistos:
            alertas.append({
                "nivel":    "erro",
                "artigo":   "art. 67º/1 CCP",
                "campo":    campo,
                "mensagem": (
                    f"O membro '{dados.get(campo)}' está designado para mais do que "
                    f"um lugar no júri ('{vistos[nome]}' e '{campo}'). "
                    f"Cada membro do júri deve ocupar um único lugar."
                ),
            })
        else:
            vistos[nome] = campo

    return alertas


# ---------------------------------------------------------------------------
# Art. 290º-A CCP — Gestor do contrato e substituto
# Obrigatoriedade de designação antes do início de funções
# ---------------------------------------------------------------------------

def verificar_gestor_contrato(dados):
    # Art. 290º-A/1 CCP
    # O contraente público deve designar um ou mais gestores do contrato,
    # com a função de acompanhar permanentemente a execução do contrato.
    # Por extensão da mesma lógica, deve também ser designado um substituto
    # para assegurar continuidade em caso de ausência ou impedimento.

    alertas = []

    gestor    = (dados.get("GESTOR_CONTRATO") or "").strip()
    substituto = (dados.get("SUBSTITUTO_GESTOR_CONTRATO") or "").strip()

    if not gestor:
        alertas.append({
            "nivel":    "erro",
            "artigo":   "art. 290º-A/1 CCP",
            "campo":    "GESTOR_CONTRATO",
            "mensagem": "O gestor do contrato não foi designado. O contraente público "
                        "deve designar um gestor do contrato com a função de acompanhar "
                        "permanentemente a sua execução, nos termos do art. 290º-A/1 CCP.",
        })

    if not substituto:
        alertas.append({
            "nivel":    "aviso",
            "artigo":   "art. 290º-A/1 CCP",
            "campo":    "SUBSTITUTO_GESTOR_CONTRATO",
            "mensagem": "O substituto do gestor do contrato não foi designado. "
                        "A designação de substituto assegura a continuidade do "
                        "acompanhamento da execução do contrato em caso de ausência "
                        "ou impedimento do gestor principal.",
        })

    # Verificar se gestor e substituto são a mesma pessoa
    if gestor and substituto and gestor.lower() == substituto.lower():
        alertas.append({
            "nivel":    "erro",
            "artigo":   "art. 290º-A/1 CCP",
            "campo":    "SUBSTITUTO_GESTOR_CONTRATO",
            "mensagem": (
                f"O gestor do contrato e o substituto são a mesma pessoa ('{gestor}'). "
                f"O substituto deve ser uma pessoa distinta do gestor principal, "
                f"para assegurar efectiva continuidade do acompanhamento da execução."
            ),
        })

    return alertas


# ---------------------------------------------------------------------------
# Função agregadora
# ---------------------------------------------------------------------------

def verificar_juri(dados):
    """
    Agrega todas as verificações de júri, gestor do contrato e substituto.
    Cobre os art. 67º, 68º, 69º e 290º-A CCP.
    Devolve lista consolidada de alertas.
    """
    alertas = []
    alertas.extend(verificar_composicao_juri(dados))
    alertas.extend(verificar_duplicacao_juri(dados))
    alertas.extend(verificar_gestor_contrato(dados))
    return alertas