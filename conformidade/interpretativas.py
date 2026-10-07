# conformidade/interpretativas.py
# Normas do CCP e legislação conexa que requerem interpretação jurídica casuística.
# Não são verificáveis automaticamente.
# A flag requer_analise_juridica=True é o ponto de ligação ao agente jurídico.
#
# Versão 2 — Maio 2026
# Estado: Por validar
#
# Normas registadas por módulo de origem:
#   limiares.py                              — art. 17º, 22º, 46º-A
#   ajustes_diretos_e_consultas_previas.py   — art. 113º, 114º, 116º, 117º
#   juri.py                                  — art. 67º, 68º
#   caucao.py                                — art. 88º, 89º
#   duracao_contrato.py                      — art. 63º, 440º


NORMAS_INTERPRETATIVAS = [

    # -----------------------------------------------------------------------
    # Art. 17º CCP — Valor do contrato
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 17º/6 CCP",
        "titulo":    "Acumulados em entidades com unidades orgânicas",
        "descricao": "Quando a entidade adjudicante é organizada por unidades orgânicas, "
                     "o valor do contrato deve considerar o total de todas elas, salvo se "
                     "forem independentemente responsáveis pelas suas aquisições. Na "
                     "preparação do procedimento, devem ser consideradas as aquisições "
                     "das unidades orgânicas na análise de acumulados.",
        "motivo":    "A determinação do grau de autonomia de cada unidade orgânica e a "
                     "agregação dos acumulados requerem análise casuística da estrutura "
                     "da entidade adjudicante.",
        "condicao_alerta": lambda dados: True,
        "mensagem":  "Na análise de acumulados, verificar se foram consideradas as "
                     "aquisições de todas as unidades orgânicas da entidade adjudicante, "
                     "salvo se cada unidade for independentemente responsável pelas suas "
                     "aquisições (art. 17º/6 CCP).",
        "nivel":     "aviso",
        "momento":   "lancamento",
    },
    {
        "artigo":    "art. 17º/7 CCP",
        "titulo":    "Fundamentação do valor do contrato",
        "descricao": "O valor do contrato deve ser fundamentado com base em critérios "
                     "objectivos, usando como referência os custos médios unitários de "
                     "prestações do mesmo tipo em anteriores procedimentos.",
        "motivo":    "A adequação da fundamentação é casuística e requer análise do "
                     "histórico de contratação e dos critérios utilizados.",
        "condicao_alerta": lambda dados: True,
        "mensagem":  "Confirmar que o valor do contrato está fundamentado com base em "
                     "critérios objectivos, preferencialmente por referência a custos "
                     "médios unitários de prestações similares em anteriores procedimentos "
                     "(art. 17º/7 CCP).",
        "nivel":     "info",
        "momento":   "lancamento",
    },
    {
        "artigo":    "art. 17º/8 CCP",
        "titulo":    "Proibição de fraccionamento artificial do valor do contrato",
        "descricao": "O valor do contrato não pode ser fraccionado com o intuito de "
                     "contornar exigências legais, designadamente os limiares de escolha "
                     "do procedimento.",
        "motivo":    "A intenção de fraccionar é um elemento subjectivo não verificável "
                     "automaticamente. A verificação objectiva dos acumulados é feita "
                     "nos módulos limiares.py e ajustes_diretos_e_consultas_previas.py.",
        "condicao_alerta": lambda dados: True,
        "mensagem":  "Verificar se o procedimento em curso, considerado no contexto dos "
                     "contratos similares celebrados, não configura fraccionamento "
                     "artificial do valor do contrato para efeitos de escolha de "
                     "procedimento menos exigente (art. 17º/8 CCP).",
        "nivel":     "aviso",
        "momento":   "lancamento",
    },

    # -----------------------------------------------------------------------
    # Art. 22º/1/b) CCP — Previsibilidade dos procedimentos subsequentes
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 22º/1/b) CCP",
        "titulo":    "Previsibilidade de procedimentos subsequentes",
        "descricao": "Quando a formação de contratos do mesmo tipo ocorre ao longo de "
                     "um ano, o somatório deve ser considerado se a entidade adjudicante, "
                     "aquando do lançamento do primeiro procedimento, devesse ter previsto "
                     "a necessidade dos subsequentes.",
        "motivo":    "O critério da previsibilidade é subjectivo e requer análise "
                     "casuística do contexto em que o primeiro procedimento foi lançado.",
        "condicao_alerta": lambda dados: bool(dados.get("ACUM_OBJETO")),
        "mensagem":  "Foram identificados contratos similares nos últimos 12 meses. "
                     "Avaliar se, aquando do lançamento do primeiro procedimento, a "
                     "entidade adjudicante devesse ter previsto a necessidade dos "
                     "procedimentos subsequentes, com impacto na escolha do procedimento "
                     "aplicável (art. 22º/1/b) CCP).",
        "nivel":     "aviso",
        "momento":   "lancamento",
    },

    # -----------------------------------------------------------------------
    # Art. 46º-A CCP — Adjudicação por lotes
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 46º-A/2/a) e b) CCP",
        "titulo":    "Fundamentos para não divisão em lotes",
        "descricao": "A decisão de não contratar por lotes deve ser fundamentada. "
                     "Constituem fundamento a incindibilidade técnica ou funcional das "
                     "prestações, ou a maior eficiência da gestão de um único contrato.",
        "motivo":    "A adequação dos fundamentos é casuística — requer análise da "
                     "natureza das prestações e das condições de execução.",
        "condicao_alerta": lambda dados: (
            not dados.get("TEM_LOTES")
            and (dados.get("PRECO_BASE") or 0) > 135_000
        ),
        "mensagem":  "O contrato não está dividido em lotes e o valor supera o limiar "
                     "do art. 46º-A/2 CCP. A decisão de não dividir em lotes deve ser "
                     "expressamente fundamentada, designadamente com base na "
                     "incindibilidade técnica ou funcional das prestações ou na maior "
                     "eficiência da gestão de um único contrato (art. 46º-A/2/a) e b) CCP).",
        "nivel":     "aviso",
        "momento":   "lancamento",
    },

    # -----------------------------------------------------------------------
    # Art. 113º CCP — Escolha das entidades convidadas
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 113º/5 CCP",
        "titulo":    "Proibição de convite a entidades que prestaram serviços gratuitos",
        "descricao": "Não podem ser convidadas entidades que tenham executado obras, "
                     "fornecido bens ou prestado serviços a título gratuito no ano "
                     "económico em curso ou nos dois anos anteriores, excepto ao abrigo "
                     "do Estatuto do Mecenato.",
        "motivo":    "Não existe campo no formulário para identificar prestações gratuitas "
                     "anteriores. A verificação depende de informação não estruturada.",
        "condicao_alerta": lambda dados: bool(dados.get("EMPRESAS_CONVIDADAS")),
        "mensagem":  "Verificar se alguma das entidades convidadas prestou serviços, "
                     "forneceu bens ou executou obras a título gratuito à entidade "
                     "adjudicante no ano económico em curso ou nos dois anos anteriores, "
                     "fora do âmbito do Estatuto do Mecenato (art. 113º/5 CCP).",
        "nivel":     "aviso",
        "momento":   "lancamento",
    },

    # -----------------------------------------------------------------------
    # Art. 114º/2 CCP — Relação entre entidades convidadas
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 114º/2 CCP",
        "titulo":    "Entidades convidadas especialmente relacionadas entre si",
        "descricao": "As entidades convidadas não podem ser especialmente relacionadas "
                     "entre si — nomeadamente por partilharem representantes legais, "
                     "sócios, ou por se encontrarem em relação de participação ou grupo.",
        "motivo":    "A verificação automática por NIF e sócios é feita em "
                     "ajustes_diretos_e_consultas_previas.py. Situações de proximidade "
                     "não estruturada (ex: relações pessoais, acordos informais) "
                     "requerem análise casuística.",
        "condicao_alerta": lambda dados: (
            len(dados.get("EMPRESAS_CONVIDADAS") or []) > 1
        ),
        "mensagem":  "Confirmar que as entidades convidadas não são especialmente "
                     "relacionadas entre si por factores não capturados pela verificação "
                     "automática de estruturas, como acordos informais ou relações "
                     "pessoais entre titulares (art. 114º/2 CCP).",
        "nivel":     "aviso",
        "momento":   "lancamento",
    },

    # -----------------------------------------------------------------------
    # Art. 116º CCP — Prazo de esclarecimentos
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 116º CCP",
        "titulo":    "Prazo de esclarecimentos em procedimentos com prazo curto",
        "descricao": "Quando o prazo para apresentação de proposta for inferior a nove "
                     "dias, os esclarecimentos podem ser prestados até ao dia anterior "
                     "ao termo desse prazo.",
        "motivo":    "O prazo é indicativo e depende do que a unidade definir nas peças "
                     "do procedimento — a adequação é casuística.",
        "condicao_alerta": lambda dados: bool(dados.get("PRAZO_ENTREGA")),
        "mensagem":  "Verificar se o prazo fixado para apresentação de proposta respeita "
                     "os requisitos do art. 116º CCP, em particular no que respeita ao "
                     "prazo para prestação de esclarecimentos.",
        "nivel":     "info",
        "momento":   "lancamento",
    },

    # -----------------------------------------------------------------------
    # Art. 117º CCP — Agrupamentos
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 117º CCP",
        "titulo":    "Regras sobre agrupamentos de concorrentes",
        "descricao": "Pode apresentar proposta um agrupamento desde que um dos seus "
                     "membros seja a entidade convidada. A entidade convidada não pode "
                     "integrar agrupamento em procedimentos ao abrigo das alíneas c) e "
                     "d) do art. 19º e 20º ou para contratos ao abrigo de acordo-quadro.",
        "motivo":    "A verificação depende da composição das propostas recebidas, "
                     "informação não disponível antes da abertura das propostas.",
        "condicao_alerta": lambda dados: (
            (dados.get("TIPO_PROCEDIMENTO") or "") in ("Ajuste Directo", "Consulta Prévia")
        ),
        "mensagem":  "Confirmar, após abertura das propostas, se alguma proposta foi "
                     "apresentada por agrupamento e, em caso afirmativo, verificar o "
                     "cumprimento das regras do art. 117º CCP, nomeadamente que a "
                     "entidade convidada integra o agrupamento e que não se trata de "
                     "procedimento em que tal seja proibido.",
        "nivel":     "info",
        "momento":   "pos_abertura",
    },

    # -----------------------------------------------------------------------
    # Art. 67º CCP — Júri
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 67º/2 CCP",
        "titulo":    "Designação de titulares do órgão como membros do júri",
        "descricao": "Os titulares do órgão competente para a decisão de contratar "
                     "podem ser designados membros do júri.",
        "motivo":    "A adequação desta designação é casuística e pode levantar "
                     "questões de conflito de interesses ou segregação de funções.",
        "condicao_alerta": lambda dados: (
            (dados.get("TIPO_PROCEDIMENTO") or "") != "Ajuste Directo"
        ),
        "mensagem":  "Verificar se algum membro do júri é titular do órgão competente "
                     "para a decisão de contratar e, em caso afirmativo, avaliar se "
                     "essa designação é adequada face às regras de segregação de funções "
                     "e inexistência de conflitos de interesses (art. 67º/2 CCP).",
        "nivel":     "info",
        "momento":   "lancamento",
    },
    {
        "artigo":    "art. 67º/3 CCP",
        "titulo":    "Dispensa de júri em concurso público urgente",
        "descricao": "No concurso público urgente, o órgão competente pode decidir que "
                     "o procedimento seja conduzido pelos serviços da entidade adjudicante, "
                     "dispensando o júri formal.",
        "motivo":    "O formulário não distingue procedimentos urgentes — a dispensa "
                     "não é verificável automaticamente.",
        "condicao_alerta": lambda dados: (
            (dados.get("TIPO_PROCEDIMENTO") or "") == "Concurso Público"
        ),
        "mensagem":  "Se o presente concurso público for urgente, o órgão competente "
                     "pode dispensar o júri e determinar que o procedimento seja "
                     "conduzido pelos serviços (art. 67º/3 CCP). Confirmar se esta "
                     "dispensa foi ou não exercida.",
        "nivel":     "info",
        "momento":   "lancamento",
    },
    {
        "artigo":    "art. 67º/4 CCP",
        "titulo":    "Dispensa de júri quando apresentada uma única proposta",
        "descricao": "O júri pode ser dispensado nos procedimentos em que seja "
                     "apresentada apenas uma proposta.",
        "motivo":    "Só é verificável após abertura das propostas.",
        "condicao_alerta": lambda dados: (
            (dados.get("TIPO_PROCEDIMENTO") or "") != "Ajuste Directo"
        ),
        "mensagem":  "Após abertura das propostas, verificar se foi apresentada apenas "
                     "uma proposta — nesse caso, o júri pode ser dispensado "
                     "(art. 67º/4 CCP).",
        "nivel":     "info",
        "momento":   "pos_abertura",
    },
    {
        "artigo":    "art. 67º/5 CCP",
        "titulo":    "Declaração de inexistência de conflitos de interesses",
        "descricao": "Antes do início de funções, os membros do júri e demais "
                     "intervenientes devem subscrever declaração de inexistência de "
                     "conflitos de interesses (modelo do anexo XIII ao CCP).",
        "motivo":    "Não existe campo no formulário para confirmar a subscrição "
                     "das declarações.",
        "condicao_alerta": lambda dados: (
            (dados.get("TIPO_PROCEDIMENTO") or "") != "Ajuste Directo"
        ),
        "mensagem":  "Confirmar que todos os membros do júri e demais intervenientes "
                     "no processo de avaliação de propostas subscreveram a declaração "
                     "de inexistência de conflitos de interesses, nos termos do "
                     "art. 67º/5 CCP e do modelo constante do anexo XIII ao CCP.",
        "nivel":     "aviso",
        "momento":   "lancamento",
    },

    # -----------------------------------------------------------------------
    # Art. 68º CCP — Funcionamento do júri
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 68º CCP",
        "titulo":    "Regras de funcionamento do júri",
        "descricao": "O júri só pode funcionar com todos os membros efetivos presentes. "
                     "As deliberações são tomadas por maioria, sem abstenção, e devem "
                     "ser sempre fundamentadas.",
        "motivo":    "As regras de funcionamento decorrem do procedimento em si e não "
                     "são verificáveis a partir do formulário.",
        "condicao_alerta": lambda dados: (
            (dados.get("TIPO_PROCEDIMENTO") or "") != "Ajuste Directo"
        ),
        "mensagem":  "Verificar o cumprimento das regras de funcionamento do júri: "
                     "presença de todos os membros efetivos nas reuniões, deliberações "
                     "fundamentadas por maioria sem abstenção, e registo em acta dos "
                     "votos de vencido (art. 68º CCP).",
        "nivel":     "info",
        "momento":   "pos_abertura",
    },

    # -----------------------------------------------------------------------
    # Art. 88º/89º CCP — Caução
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 88º/2/b) e c) CCP",
        "titulo":    "Isenção de caução por tipo de entidade ou contrato",
        "descricao": "Pode não ser exigida caução quando o adjudicatário seja entidade "
                     "prevista nos art. 2º ou 7º CCP, ou quando se trate dos contratos "
                     "previstos na alínea c) do n.º 1 do art. 95º.",
        "motivo":    "A qualificação da entidade adjudicatária ou do contrato requer "
                     "análise jurídica casuística.",
        "condicao_alerta": lambda dados: (
            (dados.get("CAUCAO") or "").strip().lower() in ("não", "nao")
            and (dados.get("PRECO_BASE") or 0) >= 500_000
        ),
        "mensagem":  "A caução não foi exigida num contrato de valor igual ou superior "
                     "a 500 000 €. Verificar se existe fundamento legal para a dispensa "
                     "ao abrigo do art. 88º/2/b) (adjudicatário é entidade do art. 2º "
                     "ou 7º CCP) ou art. 88º/2/c) (contrato ao abrigo do art. 95º/1/c) "
                     "CCP).",
        "nivel":     "aviso",
        "momento":   "lancamento",
    },
    {
        "artigo":    "art. 89º/3 CCP",
        "titulo":    "Valor da caução em contratos sem pagamento de preço",
        "descricao": "Quando for exigida caução em contratos que não impliquem o "
                     "pagamento de preço, o valor não pode ser superior a 2% do "
                     "montante da utilidade económica imediata do contrato.",
        "motivo":    "A determinação da utilidade económica imediata requer análise "
                     "casuística.",
        "condicao_alerta": lambda dados: False,
        "mensagem":  "Em contratos sem pagamento de preço, o valor da caução não pode "
                     "exceder 2% da utilidade económica imediata do contrato "
                     "(art. 89º/3 CCP).",
        "nivel":     "info",
        "momento":   "lancamento",
    },
    {
        "artigo":    "art. 89º/4 CCP",
        "titulo":    "Caução em contratos com renovações",
        "descricao": "Quando o contrato previr renovações, o valor da caução tem por "
                     "referência o preço do período de vigência inicial, devendo ser "
                     "prestada nova caução a cada renovação.",
        "motivo":    "Depende das condições de renovação definidas no contrato.",
        "condicao_alerta": lambda dados: (
            (dados.get("CAUCAO") or "").strip().lower() == "sim"
            and bool(dados.get("GARANTIA_ANOS"))
        ),
        "mensagem":  "Se o contrato previr renovações, verificar que o valor da caução "
                     "tem por referência o preço do período de vigência inicial e que "
                     "cada renovação está condicionada à prestação de nova caução "
                     "(art. 89º/4 CCP).",
        "nivel":     "info",
        "momento":   "lancamento",
    },

    # -----------------------------------------------------------------------
    # Art. 63º CCP — Adequação do prazo de apresentação de propostas
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 63º/2 CCP",
        "titulo":    "Adequação do prazo de apresentação de propostas",
        "descricao": "Na fixação do prazo para apresentação de propostas, deve ser "
                     "tido em conta o tempo necessário à sua elaboração, em função da "
                     "natureza, características, volume e complexidade das prestações.",
        "motivo":    "A adequação do prazo à complexidade do contrato é casuística.",
        "condicao_alerta": lambda dados: (
            (dados.get("TIPO_PROCEDIMENTO") or "") != "Ajuste Directo"
        ),
        "mensagem":  "Verificar se o prazo fixado para apresentação de propostas é "
                     "adequado à natureza, complexidade e volume das prestações objecto "
                     "do contrato, garantindo condições de efectiva concorrência "
                     "(art. 63º/2 CCP).",
        "nivel":     "info",
        "momento":   "lancamento",
    },

    # -----------------------------------------------------------------------
    # Art. 440º/1 CCP — Fundamentação do prazo superior a 3 anos
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 440º/1 CCP",
        "titulo":    "Fundamentação do prazo de vigência superior a 3 anos",
        "descricao": "O prazo de vigência pode exceder 3 anos se tal se revelar "
                     "necessário ou conveniente em função da natureza das prestações "
                     "ou das condições de execução.",
        "motivo":    "A adequação da fundamentação é casuística.",
        "condicao_alerta": lambda dados: (
            bool(dados.get("PRAZO_ENTREGA"))
            and float(dados.get("PRAZO_ENTREGA") or 0) > 1095
        ),
        "mensagem":  "O prazo de vigência do contrato é superior a 3 anos. Confirmar "
                     "que a fundamentação apresentada é adequada e suficiente face à "
                     "natureza das prestações ou às condições de execução "
                     "(art. 440º/1 CCP).",
        "nivel":     "aviso",
        "momento":   "lancamento",
    },

    # -----------------------------------------------------------------------
    # Art. 290º-A CCP — Gestor do contrato
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 290º-A/3 CCP",
        "titulo":    "Indicadores de execução em contratos complexos ou de longa duração",
        "descricao": "Em contratos com especiais características de complexidade técnica "
                     "ou financeira, ou de duração superior a três anos, o gestor deve "
                     "elaborar indicadores de execução quantitativos e qualitativos.",
        "motivo":    "A definição dos indicadores adequados é casuística e depende da "
                     "natureza do contrato.",
        "condicao_alerta": lambda dados: (
            bool(dados.get("GESTOR_CONTRATO"))
            and (dados.get("PRAZO_ENTREGA") or 0)
            and float(dados.get("PRAZO_ENTREGA") or 0) > 1095
        ),
        "mensagem":  "O contrato tem duração superior a três anos. O gestor do contrato "
                     "deve elaborar indicadores de execução quantitativos e qualitativos "
                     "adequados ao tipo de contrato, nos termos do art. 290º-A/3 CCP.",
        "nivel":     "aviso",
        "momento":   "execucao",
    },
    {
        "artigo":    "art. 290º-A/7 CCP",
        "titulo":    "Declaração de inexistência de conflitos de interesses do gestor",
        "descricao": "Antes do início de funções, o gestor do contrato deve subscrever "
                     "declaração de inexistência de conflitos de interesses.",
        "motivo":    "Não existe campo no formulário para confirmar a subscrição.",
        "condicao_alerta": lambda dados: bool(dados.get("GESTOR_CONTRATO")),
        "mensagem":  "Confirmar que o gestor do contrato subscreveu a declaração de "
                     "inexistência de conflitos de interesses antes do início de funções, "
                     "nos termos do art. 290º-A/7 CCP e do modelo do anexo XIII ao CCP.",
        "nivel":     "aviso",
        "momento":   "pos_abertura",
    },

    # -----------------------------------------------------------------------
    # Art. 292º CCP — Adiantamentos de preço
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 292º CCP",
        "titulo":    "Adiantamentos de preço",
        "descricao": "O contraente público pode efectuar adiantamentos de preço até 30% "
                     "do preço contratual, desde que seja prestada caução de valor igual "
                     "ou superior aos adiantamentos, e esteja previsto no CE",
        "motivo":    "Os adiantamentos dependem de decisão da entidade adjudicante e "
                     "das condições do contrato — não são verificáveis a priori.",
        "condicao_alerta": lambda dados: False,
        "mensagem":  "Se forem previstos adiantamentos de preço, verificar que o valor "
                     "não excede 30% do preço contratual e que é prestada caução de "
                     "valor igual ou superior (art. 292º/1 CCP).",
        "nivel":     "info",
        "momento":   ["lancamento", "execucao"],
    },

    # -----------------------------------------------------------------------
    # Art. 311º-313º CCP — Modificação do contrato
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 312º CCP",
        "titulo":    "Fundamentos de modificação do contrato",
        "descricao": "O contrato pode ser modificado com base em cláusulas que o prevejam, "
                     "por alteração anormal e imprevisível das circunstâncias, ou por "
                     "razões de interesse público.",
        "motivo":    "Os fundamentos de modificação são casuísticos e requerem análise "
                     "jurídica das circunstâncias concretas.",
        "condicao_alerta": lambda dados: False,
        "mensagem":  "Qualquer modificação do contrato deve ser fundamentada nos termos "
                     "do art. 312º CCP e respeitar os limites do art. 313º CCP.",
        "nivel":     "info",
        "momento":   "execucao",
    },
    {
        "artigo":    "art. 313º CCP",
        "titulo":    "Limites à modificação do contrato",
        "descricao": "A modificação não pode alterar a natureza global do contrato. "
                     "Modificações por razões de interesse público não podem ser "
                     "substanciais nem falsear a concorrência.",
        "motivo":    "A avaliação da substancialidade da modificação é casuística.",
        "condicao_alerta": lambda dados: False,
        "mensagem":  "Verificar que qualquer modificação do contrato respeita os limites "
                     "do art. 313º CCP, designadamente que não altera a natureza global "
                     "do contrato nem falseia a concorrência.",
        "nivel":     "info",
        "momento":   "execucao",
    },
    {
        "artigo":    "art. 315º CCP",
        "titulo":    "Publicidade das modificações do contrato",
        "descricao": "As modificações do contrato devem ser publicitadas no portal dos "
                     "contratos públicos até cinco dias após a sua concretização, sendo "
                     "a publicitação condição de eficácia.",
        "motivo":    "Ocorre durante a execução do contrato — não verificável a priori.",
        "condicao_alerta": lambda dados: False,
        "mensagem":  "Todas as modificações do contrato devem ser publicitadas no portal "
                     "dos contratos públicos até cinco dias após a sua concretização, "
                     "sendo a publicitação condição de eficácia (art. 315º CCP).",
        "nivel":     "info",
        "momento":   "execucao",
    },

    # -----------------------------------------------------------------------
    # Art. 343º-406º CCP — Empreitadas de obras públicas
    # -----------------------------------------------------------------------
    {
        "artigo":    "art. 344º/2 CCP",
        "titulo":    "Director de fiscalização e gestor do contrato em empreitadas",
        "descricao": "Em empreitadas, o dono da obra é representado pelo director de "
                     "fiscalização em todos os aspectos relacionados com a obra, e pelo "
                     "gestor do contrato nos demais aspectos.",
        "motivo":    "O director de fiscalização é designado numa fase posterior à do "
                     "formulário de lançamento do procedimento.",
        "condicao_alerta": lambda dados: (
            "empreitada" in (dados.get("TIPO_OBJETO") or "").lower()
            or "obras" in (dados.get("TIPO_OBJETO") or "").lower()
        ),
        "mensagem":  "Em empreitadas de obras públicas, deve ser designado director de "
                     "fiscalização da obra para representar o dono da obra em todos os "
                     "aspectos relacionados com a obra (art. 344º/2 CCP). Confirmar a "
                     "designação antes do início dos trabalhos.",
        "nivel":     "aviso",
        "momento":   ["lancamento", "execucao"],
    },
    {
        "artigo":    "art. 352º CCP",
        "titulo":    "Posse administrativa dos terrenos antes da celebração do contrato",
        "descricao": "Antes da celebração do contrato, o dono da obra deve estar na "
                     "posse administrativa da totalidade dos terrenos a expropriar, "
                     "salvo quando o número de prédios e o prazo tornem esta obrigação "
                     "desproporcionada.",
        "motivo":    "Depende da situação fundiária específica da obra — casuístico.",
        "condicao_alerta": lambda dados: (
            "empreitada" in (dados.get("TIPO_OBJETO") or "").lower()
            or "obras" in (dados.get("TIPO_OBJETO") or "").lower()
        ),
        "mensagem":  "Em empreitadas de obras públicas, verificar se o dono da obra "
                     "está na posse administrativa dos terrenos necessários antes da "
                     "celebração do contrato, nos termos do art. 352º CCP.",
        "nivel":     "aviso",
        "momento":   "lancamento",
    },
    {
        "artigo":    "art. 370º/4 CCP",
        "titulo":    "Limite de trabalhos complementares",
        "descricao": "O valor acumulado dos trabalhos complementares não pode exceder "
                     "50% do preço contratual inicial.",
        "motivo":    "Só verificável durante a execução do contrato — não disponível "
                     "no formulário de lançamento.",
        "condicao_alerta": lambda dados: (
            "empreitada" in (dados.get("TIPO_OBJETO") or "").lower()
            or "obras" in (dados.get("TIPO_OBJETO") or "").lower()
        ),
        "mensagem":  "O valor acumulado dos trabalhos complementares não pode exceder "
                     "50% do preço contratual inicial (art. 370º/4 CCP). Monitorizar "
                     "durante a execução do contrato.",
        "nivel":     "info",
        "momento":   "execucao",
    },
    {
        "artigo":    "art. 397º/2 CCP",
        "titulo":    "Prazos de garantia da obra",
        "descricao": "Os prazos de garantia são: 10 anos para elementos estruturais, "
                     "5 anos para elementos não estruturais e instalações técnicas, "
                     "3 anos para equipamentos.",
        "motivo":    "Os prazos decorrem directamente da lei — a sua aplicação é "
                     "automática mas a verificação do cumprimento ocorre durante a "
                     "execução e após a recepção provisória.",
        "condicao_alerta": lambda dados: (
            "empreitada" in (dados.get("TIPO_OBJETO") or "").lower()
            or "obras" in (dados.get("TIPO_OBJETO") or "").lower()
        ),
        "mensagem":  "Confirmar que o caderno de encargos prevê os prazos de garantia "
                     "legais: 10 anos (elementos estruturais), 5 anos (elementos não "
                     "estruturais e instalações técnicas) e 3 anos (equipamentos), "
                     "nos termos do art. 397º/2 CCP.",
        "nivel":     "info",
        "momento":   "lancamento",
    },
    {
        "artigo":    "art. 403º/1 CCP",
        "titulo":    "Sanção por atraso na execução da obra",
        "descricao": "Em caso de atraso imputável ao empreiteiro, o dono da obra pode "
                     "aplicar sanção de 1‰/dia do preço contratual inicial, até ao dobro "
                     "desse valor.",
        "motivo":    "A sanção é fixada nas peças do procedimento e aplicada durante a "
                     "execução — não verificável no formulário de lançamento.",
        "condicao_alerta": lambda dados: (
            "empreitada" in (dados.get("TIPO_OBJETO") or "").lower()
            or "obras" in (dados.get("TIPO_OBJETO") or "").lower()
        ),
        "mensagem":  "Confirmar que o caderno de encargos prevê a sanção por atraso "
                     "nos termos do art. 403º/1 CCP: 1‰ por dia de atraso do preço "
                     "contratual inicial, podendo o contrato prever valor superior "
                     "até ao dobro desse limite.",
        "nivel":     "info",
        "momento":   "execucao",
    },
]


def verificar_interpretativas(dados, momento="lancamento"):
    """
    Verifica quais normas interpretativas são relevantes para este procedimento
    e emite alertas para análise jurídica pelo técnico ou agente jurídico.

    O parâmetro `momento` filtra as normas por fase do procedimento:
        "lancamento"   — momento de lançar o procedimento (default)
        "pos_abertura" — após abertura de propostas
        "execucao"     — durante ou após execução contratual
    """
    alertas = []
    for norma in NORMAS_INTERPRETATIVAS:
        # Filtra por momento
        momento_norma = norma.get("momento", "lancamento")
        if isinstance(momento_norma, list):
            if momento not in momento_norma:
                continue
        elif momento_norma != momento:
            continue

        try:
            if norma["condicao_alerta"](dados):
                alertas.append({
                    "nivel":                   norma["nivel"],
                    "artigo":                  norma["artigo"],
                    "campo":                   None,
                    "mensagem":                norma["mensagem"],
                    "requer_analise_juridica": True,
                    "momento":                 momento_norma,
                })
        except Exception:
            pass
    return alertas