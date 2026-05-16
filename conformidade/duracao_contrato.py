# conformidade/duracao_contrato.py
# Verificação de regras de duração e prazos do contrato
# Art. 48º, 63º, 65º e 440º CCP
#
# Versão 1 — Maio 2026
# Estado: Por validar

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

LIMITE_VIGENCIA_ANOS  = 3       # art. 48º e 440º/1 CCP — prazo máximo em anos
DIAS_3_ANOS           = 1_095   # 3 anos em dias corridos
PRAZO_MINIMO_PROPOSTAS = 66     # art. 65º CCP — prazo mínimo de manutenção de propostas
FATOR_DIAS_UTEIS      = 1.4     # aproximação conservadora dias úteis → corridos


# ---------------------------------------------------------------------------
# Utilitário — converter prazo para dias corridos
# (partilha lógica com caucao.py — considerar extrair para utils.py no futuro)
# ---------------------------------------------------------------------------

def _prazo_para_dias_corridos(prazo, unidade):
    """
    Converte o prazo de execução para dias corridos.
    Devolve (dias, exacto) onde exacto=False indica conversão aproximada.
    """
    try:
        prazo = float(prazo)
    except (TypeError, ValueError):
        return None, False

    unidade = (unidade or "").strip().lower()

    if "úteis" in unidade or "uteis" in unidade:
        return prazo * FATOR_DIAS_UTEIS, False
    elif "semana" in unidade:
        return prazo * 7, True
    elif "m" in unidade:  # meses
        return prazo * 30.44, False
    else:
        return prazo, True  # assume dias corridos


# ---------------------------------------------------------------------------
# Art. 48º e 440º/1 CCP
# Prazo de vigência superior a 3 anos obriga a fundamentação
# ---------------------------------------------------------------------------

def verificar_prazo_vigencia(dados):
    # Art. 48º CCP
    # Em contratos de locação ou aquisição de bens móveis ou serviços,
    # a fixação de prazo de vigência superior a três anos deve ser fundamentada.
    # Art. 440º/1 CCP
    # O prazo de vigência do contrato não pode ser superior a três anos,
    # incluindo quaisquer prorrogações, salvo se tal se revelar necessário
    # ou conveniente em função da natureza das prestações ou das condições
    # de execução — nesse caso, deve ser fundamentado.
    # O campo PRAZO_ENTREGA representa o prazo de vigência do contrato,
    # conforme definido no formulário.

    alertas = []

    prazo      = dados.get("PRAZO_ENTREGA")
    unidade    = dados.get("PRAZO_ENTREGA_UNIDADE")
    tipo_objeto = (dados.get("TIPO_OBJETO") or "").strip()

    if prazo is None:
        alertas.append({
            "nivel":    "aviso",
            "artigo":   "art. 48º e art. 440º/1 CCP",
            "campo":    "PRAZO_ENTREGA",
            "mensagem": "O prazo de vigência do contrato não foi declarado. "
                        "Não é possível verificar o cumprimento do limite de três anos.",
        })
        return alertas

    dias, exacto = _prazo_para_dias_corridos(prazo, unidade)

    if dias is None:
        alertas.append({
            "nivel":    "aviso",
            "artigo":   "art. 48º e art. 440º/1 CCP",
            "campo":    "PRAZO_ENTREGA",
            "mensagem": "O prazo de vigência do contrato não foi possível converter "
                        "para dias corridos. Verificar manualmente se o prazo supera "
                        "os três anos e, em caso afirmativo, fundamentar.",
        })
        return alertas

    nota_aproximacao = " (valor calculado por aproximação — confirmar)" if not exacto else ""

    if dias > DIAS_3_ANOS:
        alertas.append({
            "nivel":    "aviso",
            "artigo":   "art. 48º e art. 440º/1 CCP",
            "campo":    "PRAZO_ENTREGA",
            "mensagem": (
                f"O prazo de vigência do contrato ({prazo} {unidade}{nota_aproximacao}) "
                f"é superior a três anos. Nos termos do art. 48º e 440º/1 CCP, "
                f"esta fixação deve ser expressamente fundamentada no processo, "
                f"com base na natureza das prestações ou nas condições de execução."
            ),
        })

    return alertas


# ---------------------------------------------------------------------------
# Art. 65º CCP
# Prazo mínimo de manutenção das propostas — 66 dias
# ---------------------------------------------------------------------------

def verificar_prazo_manutencao_propostas(dados):
    # Art. 65º CCP
    # Os concorrentes são obrigados a manter as propostas pelo prazo de 66 dias
    # contados da data do termo do prazo fixado para a apresentação das propostas,
    # salvo se o programa do procedimento ou convite fixar prazo superior.
    # Este alerta é informativo — lembra que o prazo mínimo deve constar das peças.

    alertas = []

    tipo_procedimento = (dados.get("TIPO_PROCEDIMENTO") or "").strip()

    # Não aplicável a ajuste directo — não há propostas em sentido formal
    if tipo_procedimento == "Ajuste Directo":
        return alertas

    alertas.append({
        "nivel":    "info",
        "artigo":   "art. 65º CCP",
        "campo":    None,
        "mensagem": (
            f"O prazo mínimo de manutenção das propostas é de {PRAZO_MINIMO_PROPOSTAS} dias, "
            f"contados da data do termo do prazo de apresentação das propostas "
            f"(art. 65º CCP). Confirmar que este prazo consta expressamente das "
            f"peças do procedimento, podendo ser fixado prazo superior."
        ),
    })

    return alertas


# ---------------------------------------------------------------------------
# Função agregadora
# ---------------------------------------------------------------------------

def verificar_duracao_contrato(dados):
    """
    Agrega todas as verificações de duração e prazos do contrato.
    Cobre os art. 48º, 65º e 440º CCP.
    Devolve lista consolidada de alertas.
    """
    alertas = []
    alertas.extend(verificar_prazo_vigencia(dados))
    alertas.extend(verificar_prazo_manutencao_propostas(dados))
    return alertas