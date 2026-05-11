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
    "Técnico superior Sofia Portugal sofiaportugal@ua.pt" → "sofiaportugal@ua.pt"
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
    50000 → "cinquenta mil euros"
    Suporta valores até 999.999 euros.
    """
    if valor is None:
        return "[a preencher]"

    try:
        valor = int(float(valor))
    except (ValueError, TypeError):
        return "[a preencher]"

    unidades = ["", "um", "dois", "três", "quatro", "cinco",
                "seis", "sete", "oito", "nove", "dez",
                "onze", "doze", "treze", "catorze", "quinze",
                "dezasseis", "dezassete", "dezoito", "dezanove"]
    dezenas = ["", "", "vinte", "trinta", "quarenta", "cinquenta",
               "sessenta", "setenta", "oitenta", "noventa"]
    centenas = ["", "cem", "duzentos", "trezentos", "quatrocentos",
                "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"]

    def converter_centenas(n):
        if n == 0:
            return ""
        if n == 100:
            return "cem"
        c = n // 100
        resto = n % 100
        if resto == 0:
            return centenas[c]
        if resto < 20:
            u = unidades[resto]
        else:
            d = dezenas[resto // 10]
            u_idx = resto % 10
            u = d + (" e " + unidades[u_idx] if u_idx else "")
        return (centenas[c] + " e " + u) if c else u

    if valor == 0:
        return "zero euros"
    if valor < 0:
        return "[a preencher]"

    milhares = valor // 1000
    resto = valor % 1000

    partes = []
    if milhares:
        if milhares == 1:
            partes.append("mil")
        else:
            partes.append(converter_centenas(milhares) + " mil")
    if resto:
        partes.append(converter_centenas(resto))

    return " e ".join(partes) + " euros"


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
    ["Ana Braga — anabraga@ua.pt", "Liliana Afonso — liliana.afonso@ua.pt"]
    → "Ana Braga — anabraga@ua.pt\nLiliana Afonso — liliana.afonso@ua.pt"
    """
    if not lista:
        return "[a preencher]"
    return separador.join(str(item) for item in lista if item)