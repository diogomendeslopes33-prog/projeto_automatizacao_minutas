# utils.py
# Funções de formatação e limpeza de valores.
# Sem efeitos secundários — recebem um valor, devolvem um valor transformado.
# Usadas pelo ler_pdf.py (limpeza) e pelo preencher_word.py (formatação).

import re
from datetime import datetime


# --- Limpeza de valores extraídos do PDF ---

def limpar_texto(texto):
    """
    Remove espaços extra, quebras de linha e caracteres estranhos.
    Usado para normalizar texto extraído do PDF.
    """
    if not texto:
        return ""
    texto = texto.strip()
    texto = re.sub(r'\s+', ' ', texto)  # múltiplos espaços → um espaço
    return texto


def limpar_valor_monetario(texto):
    """
    Extrai valor numérico de string monetária do PDF.
    "30 312,21 €" → 30312.21

    Devolve float ou None se não conseguir extrair.
    """
    if not texto:
        return None
    # Remove tudo excepto dígitos, vírgula e ponto
    texto = re.sub(r'[^\d,.]', '', texto.strip())
    # Formato português: ponto como separador de milhar, vírgula como decimal
    texto = texto.replace('.', '').replace(',', '.')
    try:
        return float(texto)
    except ValueError:
        return None


def limpar_email(texto):
    """
    Extrai endereço de email de uma string.
    "Técnico superior Rui Ruiu ruiruiu@ua.pt" → "ruiruiu@ua.pt"
    """
    if not texto:
        return ""
    match = re.search(r'[\w.\-+]+@[\w.\-]+\.[a-zA-Z]{2,}', texto)
    return match.group(0) if match else ""


# --- Formatação para as minutas Word ---

def formatar_valor_euros(valor):
    """
    Formata float como string monetária portuguesa.
    30312.21 → "30.312,21 €"
    """
    if valor is None:
        return "[a preencher]"
    try:
        valor = float(valor)
        # Formata com separadores portugueses
        inteiro = int(valor)
        decimais = round((valor - inteiro) * 100)
        inteiro_fmt = f"{inteiro:,}".replace(",", ".")
        return f"{inteiro_fmt},{decimais:02d} €"
    except (ValueError, TypeError):
        return "[a preencher]"


def valor_por_extenso(valor):
    """
    Converte valor numérico para texto por extenso em português.
    Inclui cêntimos. Suporta até 999.999.999 euros.
    Exemplos:
        30312.21 → trinta mil trezentos e doze euros e vinte e um cêntimos
        50000.00 → cinquenta mil euros
        1500.50  → mil e quinhentos euros e cinquenta cêntimos
        1000000  → um milhão de euros
    """
    if valor is None:
        return "[a preencher]"

    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return "[a preencher]"

    if valor < 0:
        return "[a preencher]"

    euros = int(valor)
    centimos = round((valor - euros) * 100)

    unidades_lst = [
        "", "um", "dois", "três", "quatro", "cinco",
        "seis", "sete", "oito", "nove", "dez",
        "onze", "doze", "treze", "catorze", "quinze",
        "dezasseis", "dezassete", "dezoito", "dezanove"
    ]
    dezenas_lst = [
        "", "", "vinte", "trinta", "quarenta", "cinquenta",
        "sessenta", "setenta", "oitenta", "noventa"
    ]
    centenas_lst = [
        "", "cem", "duzentos", "trezentos", "quatrocentos",
        "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"
    ]

    def converter_centenas(n):
        """Converte número de 1 a 999 para extenso."""
        if n == 0:
            return ""
        if n == 100:
            return "cem"
        c = n // 100
        resto = n % 100
        if resto == 0:
            return centenas_lst[c]
        if resto < 20:
            u = unidades_lst[resto]
        else:
            d = dezenas_lst[resto // 10]
            u_idx = resto % 10
            u = d + (" e " + unidades_lst[u_idx] if u_idx else "")
        return (centenas_lst[c] + " e " + u) if c else u

    def converter_inteiro(n):
        """Converte inteiro para extenso, sem unidade monetária."""
        if n == 0:
            return "zero"

        milhoes = n // 1000000
        resto_m = n % 1000000
        milhares = resto_m // 1000
        resto = resto_m % 1000

        partes = []

        if milhoes:
            if milhoes == 1:
                partes.append("um milhão")
            else:
                partes.append(converter_centenas(milhoes) + " milhões")

        if milhares:
            if milhares == 1:
                partes.append("mil")
            else:
                partes.append(converter_centenas(milhares) + " mil")

        if resto:
            partes.append(converter_centenas(resto))

        if not partes:
            return "zero"

        # Regra do "e":
        # — entre milhares e resto quando resto < 100
        # — sempre entre milhões/mil e resto quando só há duas partes simples
        if len(partes) == 1:
            return partes[0]

        # Regra do "e":
        # 1. Último bloco < 100 → sempre "e"
        # 2. Exactamente dois blocos e o segundo é centena redonda → "e"
        #    ex: "mil e quinhentos", "dois mil e trezentos"
        # 3. Resto contrário → sem "e"

        ultimo_numero = resto if resto > 0 else (milhares if milhoes > 0 and milhares > 0 and resto == 0 else 0)

        if resto > 0 and resto < 100:
            # "trinta mil e doze", "mil e dois"
            usa_e = True
        elif len(partes) == 2 and resto == 0 and milhoes == 0 and milhares > 0:
            # "mil e quinhentos", "dois mil e trezentos"
            usa_e = True
        elif len(partes) == 2 and milhoes > 0 and milhares == 0 and resto == 0:
            # "um milhão e quinhentos" — nunca acontece com estrutura actual
            usa_e = True
        else:
            usa_e = False

        if usa_e:
            return " ".join(partes[:-1]) + " e " + partes[-1]
        else:
            return " ".join(partes)

    # Constrói resultado final
    if euros == 0 and centimos == 0:
        return "zero euros"

    partes_resultado = []

    if euros > 0:
        texto_euros = converter_inteiro(euros)
        # "de" após milhão/milhões
        if euros >= 1000000 and euros % 1000000 == 0:
            partes_resultado.append(texto_euros + " de euros")
        else:
            unidade = "euro" if euros == 1 else "euros"
            partes_resultado.append(texto_euros + " " + unidade)

    if centimos > 0:
        texto_centimos = converter_inteiro(centimos)
        unidade = "cêntimo" if centimos == 1 else "cêntimos"
        partes_resultado.append(texto_centimos + " " + unidade)

    return " e ".join(partes_resultado)


def formatar_data(texto):
    """
    Normaliza data para formato longo português.
    "2025-04-02" ou "2 de abril de 2025" → "2 de abril de 2025"
    Devolve o texto original se não conseguir converter.
    """
    if not texto:
        return "[a preencher]"

    meses = {
        "01": "janeiro", "02": "fevereiro", "03": "março",
        "04": "abril", "05": "maio", "06": "junho",
        "07": "julho", "08": "agosto", "09": "setembro",
        "10": "outubro", "11": "novembro", "12": "dezembro"
    }

    # Tenta formato ISO: 2025-04-02
    match = re.match(r'(\d{4})-(\d{2})-(\d{2})', texto.strip())
    if match:
        ano, mes, dia = match.groups()
        return f"{int(dia)} de {meses.get(mes, mes)} de {ano}"

    # Se já estiver em formato longo, devolve limpo
    return limpar_texto(texto)


def juntar_campos(lista, separador="\n"):
    """
    Junta lista de strings num único campo para marcadores compostos.
    Usado para vogais, empresas, etc.
    ["Ara Arara — araarara@ua.pt", "Lia Lia — lialia@ua.pt"]
    → "Ara Arara — araarara@ua.pt\nLia Lia — lialia@ua.pt"
    """
    if not lista:
        return "[a preencher]"
    return separador.join(str(item) for item in lista if item)