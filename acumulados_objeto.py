# acumulados_objeto.py
# Camada C — acumulado por objecto, últimos 12 meses corridos (Decisão 8).
# Alimenta dados["ACUM_OBJETO"] em limiares.py (lista de dicts com "valor"),
# usado por verificar_fracionamento_art22 (art. 22º/1/b) e
# verificar_visto_tribunal_contas.
#
# Sem LLM (Decisão 17) — usa sentence-transformers, embeddings locais,
# para comparação semântica. O ficheiro Excel de entrada já vem de uma
# pesquisa mais larga (palavra-chave) e curadoria manual do técnico — a
# similaridade semântica aqui serve para RANQUEAR e confirmar o grau de
# semelhança real dentro desse conjunto já seleccionado, apoiando a
# decisão do art. 22º/1/b) sobre se as prestações são efectivamente do
# mesmo tipo — não para pesquisar candidatos (isso já é feito no ERP).

from datetime import date
from acumulados_erp import carregar_contratos_pasta, filtrar_ultimos_12_meses

_MODELO_EMBEDDINGS = "paraphrase-multilingual-MiniLM-L12-v2"
_LIMIAR_SIMILARIDADE_OMISSAO = 0.60

_modelo_carregado = None


def _obter_modelo():
    """Carrega o modelo de embeddings uma única vez (custo de arranque alto)."""
    global _modelo_carregado
    if _modelo_carregado is None:
        from sentence_transformers import SentenceTransformer
        _modelo_carregado = SentenceTransformer(_MODELO_EMBEDDINGS)
    return _modelo_carregado


def calcular_acumulado_objeto(caminho_pasta, objeto_atual, data_referencia=None,
                                limiar_similaridade=_LIMIAR_SIMILARIDADE_OMISSAO):
    """
    Calcula a lista de contratos semanticamente semelhantes a
    objeto_atual, dentro dos últimos 12 meses corridos a contar de
    data_referencia (por omissão, hoje).

    CORRECÇÃO DE DESENHO: caminho_pasta é uma PASTA, não um ficheiro
    único — a pesquisa por "objecto" ao ERP faz-se tipicamente por
    vários termos separados (ex: "mobiliário", "cadeiras", "equipamento
    tecnológico"), cada um exportado para o seu próprio .xlsx dentro
    desta pasta. carregar_contratos_pasta junta e deduplica todos os
    ficheiros por ID_CONTRATO, para que o mesmo contrato encontrado por
    dois termos diferentes não seja contado em duplicado.

    Devolve:
        list[dict] — cada item: {"valor": float, "nif": str,
                     "objeto": str, "similaridade": float}, ordenada por
                     similaridade decrescente. Pode ser [] se a pasta foi
                     lida com sucesso mas nada ficou dentro da janela ou
                     acima do limiar — "verificado, sem resultados".
        None       — se a pasta não existir/não tiver ficheiros válidos
                     — o chamador deve tratar como "acumulado não
                     verificado", nunca assumir lista vazia silenciosamente.
    """
    if data_referencia is None:
        data_referencia = date.today()

    contratos = carregar_contratos_pasta(caminho_pasta)
    if contratos is None:
        return None

    contratos_periodo = filtrar_ultimos_12_meses(contratos, data_referencia)
    contratos_com_objeto = [c for c in contratos_periodo if c.get("objeto")]

    if not contratos_com_objeto:
        return []

    modelo = _obter_modelo()

    textos = [objeto_atual] + [c["objeto"] for c in contratos_com_objeto]
    embeddings = modelo.encode(textos, normalize_embeddings=True)

    embedding_atual = embeddings[0]
    embeddings_contratos = embeddings[1:]

    resultado = []
    for contrato, emb in zip(contratos_com_objeto, embeddings_contratos):
        similaridade = float(embedding_atual @ emb)  # cosine, já normalizado
        if similaridade >= limiar_similaridade:
            resultado.append({
                "valor":        contrato["valor"],
                "nif":          contrato.get("nif"),
                "objeto":       contrato["objeto"],
                "similaridade": round(similaridade, 3),
            })

    resultado.sort(key=lambda x: x["similaridade"], reverse=True)
    return resultado