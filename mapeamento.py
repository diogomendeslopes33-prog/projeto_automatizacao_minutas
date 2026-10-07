# mapeamento.py
# Dicionário de minutas e configuração de marcadores.
# Para adicionar uma nova minuta: acrescentar entrada em MINUTAS
# e confirmar que os marcadores estão na lista CAMPOS_CONDICIONAIS.

import os
import config

# ---------------------------------------------------------------------------
# MINUTAS — tipo de procedimento + tipo de contrato → ficheiro Word
# ---------------------------------------------------------------------------

MINUTAS = {
    ("Consulta Prévia", "Bens"): os.path.join(
        config.PASTA_MINUTAS, "Minutas Iniciais Cpr_bens_teste.docx"
    ),
    ("Ajuste Directo", "Serviços"): os.path.join(
        config.PASTA_MINUTAS, "Minutas Iniciais AD_Serviços.docx"
    ),

    # Adicionar novas minutas aqui:
    # ("Ajuste Directo", "Bens"):       os.path.join(config.PASTA_MINUTAS, "...docx"),
    # ("Consulta Prévia", "Serviços"):  os.path.join(config.PASTA_MINUTAS, "...docx"),
}

# ---------------------------------------------------------------------------
# BLOCOS CONDICIONAIS — campo de dados → marcadores SE/FIM
# Formato: "CAMPO": ("SE_X", "FIM_X", "SE_Y", "FIM_Y")
#   SE_X/FIM_X → bloco activo quando campo == valor_verdadeiro
#   SE_Y/FIM_Y → bloco activo quando campo != valor_verdadeiro
# ---------------------------------------------------------------------------

CAMPOS_CONDICIONAIS = {
    "CAUCAO": (
        "SE_CAUCAO_SIM", "FIM_CAUCAO_SIM",
        "SE_CAUCAO_NAO", "FIM_CAUCAO_NAO"
    ),
    "PRR": (
        "SE_PRR_SIM", "FIM_PRR_SIM",
        "SE_PRR_NAO", "FIM_PRR_NAO"
    ),
    "DESPESA_PLURIANUAL": (
        "SE_DESPESA_PLURIANUAL_SIM", "FIM_DESPESA_PLURIANUAL_SIM",
        "SE_DESPESA_PLURIANUAL_NAO", "FIM_DESPESA_PLURIANUAL_NAO"
    ),
    "FINANCIAMENTO": (
        "SE_FINANCIAMENTO_SIM", "FIM_FINANCIAMENTO_SIM",
        "SE_FINANCIAMENTO_NAO", "FIM_FINANCIAMENTO_NAO"
    ),
    "TEM_LOTES": (
        "SE_COM_LOTES", "FIM_COM_LOTES",
        "SE_SEM_LOTES", "FIM_SEM_LOTES"
    ),
}

# ---------------------------------------------------------------------------
# BLOCOS DE REPETIÇÃO — configuração de cada bloco
# Formato: nome → dict com tipo, marcadores de início/fim, campos internos
# ---------------------------------------------------------------------------

BLOCOS_REPETICAO = {
    "LOTES_CPV": {
        "tipo":         "tabela",
        "inicio":       "INICIO_LOTES_CPV",
        "fim":          "FIM_LOTES_CPV",
        "chave_dados":  "LOTES",
        "campos": [
            "TIPO_OBJETO", "LOTE_NR", "LOTE_NOME",
            "LOTE_CPV", "LOTE_CPV_DESC", "LOTE_CPV_COMPLETO",
            "LOTE_ACUM_CPV",
        ],
    },
    "LOTES_CAB": {
        "tipo":         "tabela",
        "inicio":       "INICIO_LOTES_CAB",
        "fim":          "FIM_LOTES_CAB",
        "chave_dados":  "LOTES",
        "campos": [
            "LOTE_NR", "LOTE_NOME", "LOTE_CABIMENTO",
            "CENTRO_CUSTOS", "CLASS_ECONOMICA",
        ],
    },
    "LOTES_VALOR": {
        "tipo":        "paragrafo",
        "inicio":      "INICIO_LOTES_VALOR",
        "fim":         "FIM_LOTES_VALOR",
        "chave_dados": "LOTES",
        "campos": [
            "LOTE_NR", "LOTE_NOME", "LOTE_VALOR",
        ],
    },
    "EMPRESAS": {
        "tipo":         "tabela",
        "inicio":       "INICIO_EMPRESAS",
        "fim":          "FIM_EMPRESAS",
        "chave_dados":  "EMPRESAS_CONVIDADAS",
        "campos": [
            "EMP_NOME", "EMP_NIF", "EMP_EMAIL",
        ],
    },
    "EMP_ACUM": {
        "tipo":            "tabela",
        "inicio":          "INICIO_EMP_ACUM",
        "fim":             "FIM_EMP_ACUM",
        "chave_dados":     "EMPRESAS_CONVIDADAS",
        "campos": [
            "EMP_NOME", "EMP_NIF",
            "ACUM_EMP_ANO_ATUAL", "ACUM_EMP_ANO_1",
            "ACUM_EMP_ANO_2", "ACUM_EMP_TOTAL",
        ],
        "bloco_aninhado": "EMP_REL_ACUM",
    },
    "EMP_REL_ACUM": {
        "tipo":         "tabela",
        "inicio":       "INICIO_EMP_REL_ACUM",
        "fim":          "FIM_EMP_REL_ACUM",
        "chave_dados":  "relacionadas",
        "campos": [
            "EMP_REL_NOME", "EMP_REL_NIF",
            "ACUM_EMP_REL_ANO_ATUAL", "ACUM_EMP_REL_ANO_1",
            "ACUM_EMP_REL_ANO_2", "ACUM_EMP_REL_TOTAL",
        ],
        "bloco_vazio": ("SE_SEM_REL", "FIM_SEM_REL"),
    },
}

# ---------------------------------------------------------------------------
# CAMPOS SEM CORRESPONDÊNCIA NO FORMULÁRIO → [a preencher]
# ---------------------------------------------------------------------------

CAMPOS_SEM_FORMULARIO = {
    "NR_PROCEDIMENTO",
    "NR_COMPROMISSO",
    "CLASS_ECONOMICA",
}

# ---------------------------------------------------------------------------
# FUNÇÕES
# ---------------------------------------------------------------------------

def seleccionar_minuta(tipo_procedimento, tipo_contrato):
    """
    Devolve o caminho da minuta para a combinação indicada.
    Lança ValueError se a combinação não existir.
    """
    chave = (tipo_procedimento, tipo_contrato)
    if chave not in MINUTAS:
        disponiveis = ", ".join(
            f"{p} + {c}" for p, c in MINUTAS.keys()
        )
        raise ValueError(
            f"Minuta não encontrada para '{tipo_procedimento}' + '{tipo_contrato}'. "
            f"Disponíveis: {disponiveis}"
        )
    caminho = MINUTAS[chave]
    if not os.path.isfile(caminho):
        raise FileNotFoundError(
            f"Ficheiro de minuta não encontrado: '{caminho}'"
        )
    return caminho


def listar_minutas():
    """
    Devolve lista de tuplos (tipo_procedimento, tipo_contrato)
    das minutas disponíveis.
    """
    return list(MINUTAS.keys())