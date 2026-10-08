Automatizador de Minutas — Contratação Pública UA

Sistema de automação de procedimentos de contratação pública, desenvolvido para a Universidade de Aveiro. Lê formulários PDF, verifica conformidade com o Código dos Contratos Públicos, consulta acumulados no ERP e preenche automaticamente minutas Word — gerando um registo auditável de cada procedimento.

O problema

Cada procedimento de contratação pública na UA implica hoje trabalho manual e repetitivo: transcrever dados de um formulário SharePoint para uma minuta Word, verificar manualmente uma dúzia de regras do CCP, consultar acumulados no ERP, e identificar empresas relacionadas com as convidadas — tarefa praticamente impraticável com rigor para redes extensas de administradores.

Com 400-500 procedimentos por ano, o risco de erro é real. E o erro em contratação pública tem consequências legais.

O que o sistema faz
Formulário PDF (SharePoint)
        │
        ▼
  Extracção de dados ──────────────────────────────────────────────┐
  (53 campos: intervenientes,                                       │
   júri, CPV, preço base,                                          │
   lotes, caução, datas...)                                        │
        │                                                          │
        ├──► Camada B: Empresas ◄── PDFs Informa D&B               │
        │    (relacionadas, sócios,                                 │
        │     rede de administradores)                              │
        │                                                          │
        ├──► Camada C: Acumulados ERP ◄── exports ERP              │
        │    (por fornecedor, CPV,                                  │
        │     e objecto de contrato)                                │
        │                                                          │
        ▼                                                          │
  Verificação de Conformidade CCP ◄─────────────────────────────── ┘
  (17 regras, 28 normas interpretativas)
        │
        ├──► Minuta Word preenchida
        └──► Relatório de conformidade

  Verificação 2 (após edição manual)
  → confirma erros resolvidos, detecta novos

O técnico recebe dois documentos: a minuta pronta a rever e um relatório de conformidade com erros, avisos e informações. A decisão de aprovação é sempre sua.

Princípios de design

Sem LLM no núcleo de conformidade. Toda a lógica jurídica é determinística — regras explícitas do CCP em Python. O único componente de IA é sentence-transformers para comparação semântica de objectos de contrato, sem GPU, sem chamadas externas.

Nunca assume valor por omissão. Campo em falta gera alerta explícito, nunca 0 ou "Não" silencioso. Aplica-se a campos do formulário, acumulados ERP e PDFs Informa D&B.

O técnico decide sempre. O sistema detecta e reporta; não aprova nem rejeita procedimentos. A assinatura é sempre humana.

Registo auditável. Todos os eventos ficam registados no sequencia/ com timestamp, programa e operador — reconstituindo a linha do tempo completa de cada procedimento.

Conformidade verificada
Norma	O que verifica
Art. 17º, 19º-22º CCP	Limiares por tipo de procedimento e objecto
Art. 46º-A/2 CCP	Obrigação de fundamentar não divisão em lotes
Art. 67º-69º CCP	Composição e impedimentos do júri
Art. 88º-90º, 353º CCP	Caução obrigatória e valor
Art. 112º-114º CCP	Condições de recurso a ajuste directo e consulta prévia
Art. 113º/2, 113º/6, 114º/2 CCP	Acumulados por fornecedor e por CPV
Art. 290º-A CCP	Gestor de contrato e substituto obrigatórios
Art. 48º, 63º, 65º, 440º CCP	Duração e prorrogação do contrato
DL 127/2008, DL 13-A/2025	Execução orçamental e registo de compromissos
Limiares LOPTC	€750k por contrato, €950k acumulado
Camada B — Empresas relacionadas

O relatório Informa D&B tem uma estrutura em duas colunas (cargo/nome à esquerda, ligações à direita) que a leitura linear do PDF confunde, sobretudo em quebras de página. A extracção usa coordenadas (x, y) em vez de ordem linear de texto.

Três fontes de relacionadas, deduplicadas:

Participação societária directa (empresa-mãe, maioritárias, minoritárias)
Sócios/Acionistas nominais com ligações externas
Rede de ligações de cada administrador ("Entidade(s) a que também está ligado/a")

Validado com 8 PDFs reais — S.A. e Lda., incluindo redes de até 48 relacionadas.

Verificação 2

Após o técnico editar a minuta manualmente, o comando --verificar relê a minuta, compara com os alertas da Verificação 1 e produz um segundo relatório com três secções: erros resolvidos, erros persistentes e erros novos introduzidos na edição.

bash
python main.py --verificar UA-2026-0042
Instalação
1. Clonar e criar ambiente virtual
bash
git clone https://github.com/[utilizador]/automatizador-minutas.git
cd automatizador-minutas
python -m venv .venv
.venv\Scripts\activate        # Windows
2. Instalar dependências
bash
python -m pip install -r requirements.txt

Nota (rede com VPN): se a instalação falhar por erro SSL, instalar por cabo/docking station. O modelo sentence-transformers (~470 MB) é descarregado do HuggingFace na primeira execução — também requer acesso directo à internet.

3. Configurar variáveis de ambiente
bash
cp .env.example .env
# editar .env com os caminhos locais
4. Estrutura de pastas esperada
Z:\01_python_contratacao\
├── sequencia\              ← programa autónomo partilhado
│   └── sequencia.py
└── automatizador_minutas\
    ├── main.py
    ├── formularios\
    │   ├── {formulario}.pdf
    │   ├── empresas\{NIF}.PDF              ← Informa D&B
    │   ├── acumulados_empresa\{NIF}.PDF    ← ERP por fornecedor
    │   ├── acumulados_cpv\{CPV}.xlsx       ← ERP por CPV
    │   └── acumulados_objetos\{REF}\       ← ERP por objecto
    └── minutas\
        └── [minutas Word com marcadores]
Utilização
bash
# Fluxo principal — processa todos os formulários em formularios/
python main.py

# Verificação 2 — após edição manual da minuta
python main.py --verificar UA-2026-0042

Os ficheiros da Camada B e Camada C são recomendados mas não bloqueantes — quando ausentes, o sistema gera avisos explícitos em vez de parar.

Minutas suportadas
Tipo de procedimento	Tipo de objecto	Estado
Consulta Prévia	Aquisição de bens	✅ Construída e validada
Ajuste Directo	Serviços	🔄 Em desenvolvimento
Restantes 7 combinações	—	⬜ Por construir

A arquitectura suporta todas as 9 combinações — cada nova minuta é adicionada em mapeamento.py sem alterações ao núcleo.

Estrutura do código
main.py                     # orquestrador
config.py                   # configuração e variáveis de ambiente
ler_pdf.py                  # extracção de 53 campos do formulário
mapeamento.py               # tipo-procedimento × tipo-objecto → minuta
preencher_word.py           # preenchimento de marcadores, blocos e tabelas
apinforma.py                # Camada B: empresas relacionadas
relatorio.py                # relatório de conformidade Word
analisar_minuta.py          # Verificação 2
acumulados_erp.py           # Camada C: carregador ERP partilhado
acumulados_empresa.py       # Camada C: acumulado por fornecedor
acumulados_cpv.py           # Camada C: acumulado por CPV
acumulados_objeto.py        # Camada C: acumulado por objecto (semântico)
conformidade/               # 17 funções + 28 normas interpretativas
logger.py                   # logs técnico, utilização e supervisão
utils.py                    # formatação de euros, extenso, datas
Notas legais

Os limiares legais estão sujeitos a revisão periódica. Verificar antes de cada ciclo de aprovação:

Limiares JOUE — revisão bianual (próxima: Janeiro 2028)
Limiares LOPTC — proposta de alteração legislativa pendente
Limiar extensão de encargos — revisto anualmente pela LOE

Este sistema classifica-se como risco reduzido nos termos do EU AI Act — não toma decisões autónomas com efeitos jurídicos.