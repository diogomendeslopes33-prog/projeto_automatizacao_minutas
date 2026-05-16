# conformidade/caucao.py
# Verificação de regras de caução
# Art. 88º, 89º e 90º CCP
#
# Versão 1 — Maio 2026
# Estado: Por validar

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

LIMIAR_CAUCAO_OBRIGATORIA = 500_000   # art. 88º/2/a) CCP
PERCENTAGEM_CAUCAO_NORMAL = 0.05      # art. 89º/1 CCP — máximo 5%
DIAS_5_ANOS               = 1_825     # 5 anos em dias corridos — art. 89º/5 CCP
FATOR_DIAS_UTEIS          = 1.4       # aproximação conservadora dias úteis → corridos


# ---------------------------------------------------------------------------
# Utilitário — converter prazo para dias corridos
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
    else:
        # Dias corridos, semanas, meses — tenta converter
        if "semana" in unidade:
            return prazo * 7, True
        elif "m" in unidade:  # meses
            return prazo * 30.44, False
        else:
            return prazo, True  # assume dias corridos


# ---------------------------------------------------------------------------
# Art. 88º/1 e 88º/2/a) CCP
# Obrigatoriedade de caução face ao valor do contrato
# ---------------------------------------------------------------------------

def verificar_obrigatoriedade_caucao(dados):
    # Art. 88º/1 CCP
    # Em contratos que impliquem o pagamento de um preço pela entidade
    # adjudicante, deve ser exigida caução ao adjudicatário.
    # Art. 88º/2/a) CCP
    # Pode não ser exigida quando o preço contratual for inferior a € 500 000.
    # Art. 88º/3 CCP
    # Quando não seja exigida caução, a entidade adjudicante pode prever a
    # retenção de até 10% do valor dos pagamentos — deve ser previsto no
    # caderno de encargos.

    alertas = []

    preco_base = dados.get("PRECO_BASE")
    caucao     = (dados.get("CAUCAO") or "").strip().lower()

    if preco_base is None:
        alertas.append({
            "nivel":    "erro",
            "artigo":   "art. 88º CCP",
            "campo":    "PRECO_BASE",
            "mensagem": "Não foi possível determinar o preço base. "
                        "A verificação da obrigatoriedade de caução não pode ser efectuada.",
        })
        return alertas

    if preco_base >= LIMIAR_CAUCAO_OBRIGATORIA:
        # Caução obrigatória — art. 88º/1
        if caucao == "não" or caucao == "nao":
            alertas.append({
                "nivel":    "erro",
                "artigo":   "art. 88º/1 CCP",
                "campo":    "CAUCAO",
                "mensagem": (
                    f"O valor do contrato ({preco_base:,.2f} €) é igual ou superior a "
                    f"{LIMIAR_CAUCAO_OBRIGATORIA:,.2f} €. A prestação de caução é obrigatória "
                    f"e não pode ser dispensada com base no critério do valor "
                    f"(art. 88º/2/a) CCP). Verificar se existe outro fundamento legal "
                    f"para a dispensa."
                ),
            })
    else:
        # Caução facultativa — art. 88º/2/a)
        if caucao == "não" or caucao == "nao":
            alertas.append({
                "nivel":    "aviso",
                "artigo":   "art. 88º/2/a) e 88º/3 CCP",
                "campo":    "CAUCAO",
                "mensagem": (
                    f"O valor do contrato ({preco_base:,.2f} €) é inferior a "
                    f"{LIMIAR_CAUCAO_OBRIGATORIA:,.2f} €, pelo que a caução pode não ser "
                    f"exigida. Quando não seja exigida caução, a entidade adjudicante pode "
                    f"prever a retenção de até 10% do valor dos pagamentos a efectuar — "
                    f"verificar se esta faculdade está expressamente prevista no caderno "
                    f"de encargos (art. 88º/3 CCP)."
                ),
            })

    return alertas


# ---------------------------------------------------------------------------
# Art. 89º/1, 89º/5 e 89º/6 CCP
# Valor da caução — máximo de 5% do preço contratual
# Contratos com duração superior a 5 anos: base limitada ao primeiro terço
# ---------------------------------------------------------------------------

def verificar_valor_caucao(dados):
    # Art. 89º/1 CCP
    # O valor da caução é, no máximo, de 5% do preço contratual.
    # Art. 89º/5 CCP
    # Em contratos de execução duradoura superior a cinco anos, o valor de
    # referência para o cálculo limita-se ao primeiro terço da duração.
    # Art. 89º/6 CCP
    # Na falta de fixação, o valor da caução é de 5% do preço contratual.

    alertas = []

    preco_base   = dados.get("PRECO_BASE")
    caucao       = (dados.get("CAUCAO") or "").strip().lower()
    valor_caucao = dados.get("VALOR_CAUCAO")  # valor declarado no procedimento

    if caucao == "não" or caucao == "nao":
        return alertas

    if preco_base is None:
        return alertas

    # Verificar duração — art. 89º/5
    prazo        = dados.get("PRAZO_ENTREGA")
    prazo_unid   = dados.get("PRAZO_ENTREGA_UNIDADE")
    dias, exacto = _prazo_para_dias_corridos(prazo, prazo_unid)

    base_calculo   = preco_base
    nota_terco     = ""
    duracao_longa  = False

    if dias is not None and dias > DIAS_5_ANOS:
        duracao_longa = True
        # Base de cálculo limitada ao primeiro terço da duração — art. 89º/5
        # O preço é distribuído proporcionalmente: base = preço × (1/3)
        base_calculo = preco_base / 3
        nota_terco = (
            f" O contrato tem duração superior a 5 anos"
            f"{'(conversão aproximada)' if not exacto else ''}, "
            f"pelo que a base de cálculo da caução se limita ao primeiro terço "
            f"do preço contratual ({base_calculo:,.2f} €), nos termos do art. 89º/5 CCP."
        )

    caucao_maxima = base_calculo * PERCENTAGEM_CAUCAO_NORMAL

    if valor_caucao is None:
        # Sem valor declarado — aplicar padrão de 5% e emitir info
        alertas.append({
            "nivel":    "info",
            "artigo":   "art. 89º/1 e 89º/6 CCP",
            "campo":    "VALOR_CAUCAO",
            "mensagem": (
                f"O valor da caução não foi declarado. Por aplicação do art. 89º/6 CCP, "
                f"o valor padrão é de 5% do preço contratual"
                f"{'(base: primeiro terço)' if duracao_longa else ''}: "
                f"{caucao_maxima:,.2f} €.{nota_terco}"
            ),
        })
    else:
        try:
            valor_caucao = float(valor_caucao)
        except (TypeError, ValueError):
            alertas.append({
                "nivel":    "erro",
                "artigo":   "art. 89º/1 CCP",
                "campo":    "VALOR_CAUCAO",
                "mensagem": "O valor da caução declarado não é um número válido.",
            })
            return alertas

        if valor_caucao > caucao_maxima:
            alertas.append({
                "nivel":    "erro",
                "artigo":   "art. 89º/1 CCP",
                "campo":    "VALOR_CAUCAO",
                "mensagem": (
                    f"O valor da caução declarado ({valor_caucao:,.2f} €) excede o máximo "
                    f"legalmente admissível de 5% do preço contratual"
                    f"{'(base: primeiro terço)' if duracao_longa else ''} "
                    f"({caucao_maxima:,.2f} €), nos termos do art. 89º/1 CCP.{nota_terco}"
                ),
            })
        else:
            alertas.append({
                "nivel":    "info",
                "artigo":   "art. 89º/1 CCP",
                "campo":    "VALOR_CAUCAO",
                "mensagem": (
                    f"Valor da caução declarado: {valor_caucao:,.2f} € "
                    f"({valor_caucao / base_calculo * 100:.2f}% do preço contratual"
                    f"{'(base: primeiro terço)' if duracao_longa else ''}). "
                    f"Dentro do limite legal de 5% ({caucao_maxima:,.2f} €).{nota_terco}"
                ),
            })

    return alertas


# ---------------------------------------------------------------------------
# Art. 353º/1 CCP — Reforço de caução em empreitadas
# Dedução de 5% em cada pagamento parcial, salvo dispensa ou percentagem
# inferior fixada no contrato
# ---------------------------------------------------------------------------

def verificar_reforco_caucao_empreitada(dados):
    # Art. 353º/1 CCP
    # Nas empreitadas de obras públicas, às importâncias a receber em cada
    # pagamento parcial é deduzido o montante correspondente a 5% desse
    # pagamento, para reforço da caução, salvo se o contrato fixar
    # percentagem inferior ou dispensar tal dedução.

    alertas = []

    tipo_objeto = (dados.get("TIPO_OBJETO") or "").strip().lower()
    if "empreitada" not in tipo_objeto and "obras" not in tipo_objeto:
        return alertas

    caucao = (dados.get("CAUCAO") or "").strip().lower()
    if caucao in ("não", "nao"):
        return alertas

    reforco_caucao = dados.get("REFORCO_CAUCAO")  # percentagem ou "dispensado"

    if reforco_caucao is None:
        alertas.append({
            "nivel":    "aviso",
            "artigo":   "art. 353º/1 CCP",
            "campo":    "REFORCO_CAUCAO",
            "mensagem": (
                "Em empreitadas de obras públicas, deve ser deduzido 5% de cada "
                "pagamento parcial para reforço da caução, salvo se o contrato "
                "fixar percentagem inferior ou dispensar tal dedução "
                "(art. 353º/1 CCP). Verificar se o caderno de encargos prevê "
                "esta dedução ou a sua dispensa."
            ),
        })
    else:
        reforco_str = str(reforco_caucao).strip().lower()
        if reforco_str in ("dispensado", "dispensada", "não", "nao"):
            alertas.append({
                "nivel":    "info",
                "artigo":   "art. 353º/1 CCP",
                "campo":    "REFORCO_CAUCAO",
                "mensagem": (
                    "A dedução para reforço de caução foi dispensada no contrato. "
                    "Confirmar que esta dispensa está expressamente prevista no "
                    "caderno de encargos (art. 353º/1 CCP)."
                ),
            })
        else:
            try:
                pct = float(reforco_caucao)
                if pct > 5:
                    alertas.append({
                        "nivel":    "erro",
                        "artigo":   "art. 353º/1 CCP",
                        "campo":    "REFORCO_CAUCAO",
                        "mensagem": (
                            f"A percentagem de reforço de caução fixada ({pct}%) excede "
                            f"o limite legal de 5% por pagamento parcial "
                            f"(art. 353º/1 CCP)."
                        ),
                    })
                else:
                    alertas.append({
                        "nivel":    "info",
                        "artigo":   "art. 353º/1 CCP",
                        "campo":    "REFORCO_CAUCAO",
                        "mensagem": (
                            f"Reforço de caução fixado em {pct}% por pagamento parcial "
                            f"(limite legal: 5%) — dentro do admissível "
                            f"(art. 353º/1 CCP)."
                        ),
                    })
            except (TypeError, ValueError):
                alertas.append({
                    "nivel":    "aviso",
                    "artigo":   "art. 353º/1 CCP",
                    "campo":    "REFORCO_CAUCAO",
                    "mensagem": (
                        "O valor do reforço de caução declarado não é reconhecível. "
                        "Verificar se o caderno de encargos prevê a dedução de 5% "
                        "por pagamento parcial ou a sua dispensa (art. 353º/1 CCP)."
                    ),
                })

    return alertas


# ---------------------------------------------------------------------------
# Função agregadora
# ---------------------------------------------------------------------------

def verificar_caucao(dados):
    """
    Agrega todas as verificações de caução.
    Cobre os art. 88º, 89º, 90º e 353º CCP.
    Devolve lista consolidada de alertas.
    """
    alertas = []
    alertas.extend(verificar_obrigatoriedade_caucao(dados))
    alertas.extend(verificar_valor_caucao(dados))
    alertas.extend(verificar_reforco_caucao_empreitada(dados))
    return alertas