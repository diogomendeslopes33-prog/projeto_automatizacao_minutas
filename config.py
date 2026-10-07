# config.py
# Único ficheiro que lê o .env — todos os outros módulos importam daqui.
# Regra de volumes externos: as pastas de dados (logs, output, formularios)
# são configuradas via .env para suportar mapeamento Docker sem alterar código.
# Regra de abstracção de fonte: listar_formularios() devolve sempre uma lista
# de caminhos — hoje PDFs, amanhã referências SharePoint sem alterar o resto.

from dotenv import load_dotenv
import os

load_dotenv()

# --- Identificação do utilizador ---
UTILIZADOR = os.getenv("UTILIZADOR", "")

# --- Pastas do sistema ---
PASTA_MINUTAS     = os.getenv("PASTA_MINUTAS", "minutas")
PASTA_FORMULARIOS = os.getenv("PASTA_FORMULARIOS", "formularios")
PASTA_OUTPUT      = os.getenv("PASTA_OUTPUT", "output")
PASTA_LOGS        = os.getenv("PASTA_LOGS", "logs")

# --- Camada B — Enriquecimento empresarial ---
MODO_EMPRESAS       = os.getenv("MODO_EMPRESAS", "pdf")
PASTA_PDFS_EMPRESAS = os.getenv("PASTA_PDFS_EMPRESAS", "formularios/empresas")
APINFORMA_API_KEY   = os.getenv("APINFORMA_API_KEY")

# --- Camada C — Acumulados ERP ---
PASTA_ACUMULADOS_EMPRESA = os.getenv("PASTA_ACUMULADOS_EMPRESA", "formularios/acumulados_empresa")
PASTA_ACUMULADOS_CPV     = os.getenv("PASTA_ACUMULADOS_CPV", "formularios/acumulados_cpv")
PASTA_ACUMULADOS_OBJETOS = os.getenv("PASTA_ACUMULADOS_OBJETOS", "formularios/acumulados_objetos")


def listar_formularios():
    """
    Devolve lista de caminhos completos dos PDFs em PASTA_FORMULARIOS.
    Ponto de substituição futuro: quando vier integração SharePoint,
    esta função passa a devolver referências remotas — o resto não muda.
    """
    if not os.path.isdir(PASTA_FORMULARIOS):
        return []

    ficheiros = [
        os.path.join(PASTA_FORMULARIOS, f)
        for f in sorted(os.listdir(PASTA_FORMULARIOS))
        if f.lower().endswith(".pdf")
    ]
    return ficheiros


def validar_configuracao():
    """
    Verifica se o ambiente está pronto para executar.
    Erros bloqueiam o programa. Avisos informam mas não bloqueiam.
    Devolve True se não houver erros, False caso contrário.
    """
    erros = []
    avisos = []

    # Pastas obrigatórias — devem existir antes de arrancar
    for pasta in [PASTA_MINUTAS, PASTA_FORMULARIOS, PASTA_OUTPUT, PASTA_LOGS]:
        if not os.path.isdir(pasta):
            erros.append(f"Pasta não encontrada: '{pasta}'")

    # Formulários — tem de haver pelo menos um PDF na pasta
    formularios = listar_formularios()
    if not formularios:
        erros.append(f"Nenhum PDF encontrado em '{PASTA_FORMULARIOS}'")

    # Modo de empresas — só aceita dois valores válidos
    if MODO_EMPRESAS not in ("pdf", "api"):
        erros.append(f"MODO_EMPRESAS inválido: '{MODO_EMPRESAS}' — use 'pdf' ou 'api'")

    # Modo API sem chave — erro, não aviso
    if MODO_EMPRESAS == "api" and not APINFORMA_API_KEY:
        erros.append("MODO_EMPRESAS='api' mas APINFORMA_API_KEY não configurada")

    # Avisos — funcionalidades limitadas mas o núcleo funciona
    if not UTILIZADOR:
        avisos.append("UTILIZADOR não definido — logs sem identificação")
    if MODO_EMPRESAS == "pdf":
        avisos.append("APINFORMA_API_KEY não configurada — Camada B em modo PDF")
    if not PASTA_ACUMULADOS_EMPRESA:
        avisos.append("PASTA_ACUMULADOS_EMPRESA não encontrada — Camada C inactiva")

    # Apresentar resultados
    if avisos:
        print("\n  Avisos:")
        for aviso in avisos:
            print(f"   • {aviso}")

    if erros:
        print("\n Erros de configuração:")
        for erro in erros:
            print(f"   • {erro}")
        print("\nCorrige o .env antes de continuar.\n")
        return False

    print("\n Configuração validada com sucesso.\n")
    return True