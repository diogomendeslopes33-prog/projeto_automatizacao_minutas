Automatizador de Minutas — Contratação Pública UA

Sistema de automação de minutas e verificação de conformidade para procedimentos de contratação pública, desenvolvido para a Universidade de Aveiro.

Lê o formulário de lançamento exportado do SharePoint em PDF, verifica a conformidade com o Código dos Contratos Públicos, consulta acumulados no ERP, preenche automaticamente a minuta Word e gera um relatório de conformidade.

O que o sistema faz
formulário PDF  →  extracção de dados  →  verificação CCP  →  minuta Word + relatório
                        ↑                       ↑
                  Informa D&B (empresas)    acumulados ERP
Lê o formulário — extrai 53 campos (intervenientes, júri, CPV, preço base, lotes, caução, datas, despesa plurianual)
Camada B — Empresas — para cada empresa convidada, lê o relatório Informa D&B e identifica empresas relacionadas e sócios com ligações externas
Camada C — Acumulados ERP — verifica acumulados por fornecedor (PDF ERP), por CPV (Excel) e por objecto de contrato (similaridade semântica)
Verifica conformidade — 17 regras do CCP (art. 17º, 19º-22º, 46º-A, 67º-69º, 88º-90º, 112º-114º, 290º-A, entre outros)
Preenche a minuta — substitui marcadores, preenche blocos condicionais e tabelas de repetição
Gera relatório — documento Word com erros, avisos e informações, organizado por gravidade
Verificação 2 — após edição manual da minuta, confirma se os erros foram corrigidos e detecta novos
Estrutura do projecto
automatizador_minutas/
│
├── main.py                         # orquestrador principal
├── config.py                       # configuração (pastas, variáveis de ambiente)
├── logger.py                       # logs técnico, utilização e supervisão
├── utils.py                        # formatação de euros, extenso, datas
│
├── ler_pdf.py                      # extracção de 53 campos do formulário PDF
├── mapeamento.py                   # mapeamento tipo-procedimento × tipo-objecto → minuta
├── preencher_word.py               # preenchimento da minuta Word
├── apinforma.py                    # Camada B: empresas relacionadas via Informa D&B
├── relatorio.py                    # geração do relatório de conformidade Word
├── analisar_minuta.py              # Verificação 2: double-check sobre a minuta final
│
├── acumulados_erp.py               # Camada C: carregador partilhado do export ERP
├── acumulados_empresa.py           # Camada C: acumulado por fornecedor (PDF ERP)
├── acumulados_cpv.py               # Camada C: acumulado por CPV (Excel ERP)
├── acumulados_objeto.py            # Camada C: acumulado por objecto (semântico)
│
├── conformidade/                   # verificação de conformidade CCP
│   ├── limiares.py                 # art. 17º, 19º-22º, 46º-A, LOPTC
│   ├── ajuste_diretos_e_consultas_previas.py  # art. 112º-114º
│   ├── juri_gc_sgc.py              # art. 67º-69º, 290º-A
│   ├── caucao.py                   # art. 88º-90º, 353º
│   ├── duracao_contrato.py         # art. 48º, 63º, 65º, 440º
│   ├── execucao_orcamental.py      # DL 127/2008, DL 13-A/2025
│   └── interpretativas.py         # 28 normas interpretativas
│
├── minutas/                        # minutas Word com marcadores {{CAMPO}}
│   └── Minutas Iniciais Cpr_bens_teste.docx
│
├── formularios/                    # formulários PDF + ficheiros ERP e Informa D&B
│   ├── {formulario}.pdf
│   ├── empresas/{NIF}.PDF          # relatórios Informa D&B
│   ├── acumulados_empresa/{NIF}.PDF   # relatórios ERP por fornecedor
│   ├── acumulados_cpv/{CPV}.xlsx      # exports ERP por código CPV
│   └── acumulados_objetos/{REF}/      # exports ERP por objecto (pasta multi-termo)
│
├── output/                         # minutas e relatórios gerados (no .gitignore)
├── logs/                           # logs de utilização e supervisão (no .gitignore)
│
├── .env.example
├── requirements.txt
└── README.md

sequencia/                          # programa autónomo partilhado (fora desta pasta)
├── sequencia.py
└── sequencia.db
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

Nota (rede institucional com VPN): se a instalação falhar por erro SSL, ligar por cabo/docking station ou desligar temporariamente a VPN. O modelo sentence-transformers (~470 MB) é descarregado do HuggingFace na primeira execução — também requer acesso directo à internet.

3. Configurar variáveis de ambiente
bash
cp .env.example .env

Editar .env:

env
PASTA_FORMULARIOS=formularios
PASTA_MINUTAS=minutas
PASTA_OUTPUT=output
PASTA_PDFS_EMPRESAS=formularios/empresas
PASTA_ACUMULADOS_EMPRESA=formularios/acumulados_empresa
PASTA_ACUMULADOS_CPV=formularios/acumulados_cpv
PASTA_ACUMULADOS_OBJETOS=formularios/acumulados_objetos
PASTA_SEQUENCIA=../sequencia
4. Instalar e inicializar o sequencia/

O sequencia/ é um programa autónomo partilhado por todos os programas do sistema. Deve existir ao mesmo nível desta pasta:

Z:\01_python_contratacao\
├── sequencia\
│   └── sequencia.py
└── automatizador_minutas\
    └── main.py
Utilização
Fluxo principal
bash
python main.py

O programa lista os formulários PDF disponíveis em formularios/ e processa cada um:

gera um ID de procedimento (UA-AAAA-NNNN)
preenche a minuta Word correspondente ao tipo de procedimento e tipo de objecto
gera o relatório de conformidade
Verificação 2 (após edição manual da minuta)
bash
python main.py --verificar UA-2026-0042

Relê a minuta gerada, compara com os alertas da Verificação 1 e produz um relatório com erros resolvidos, persistentes e novos.

Ficheiros necessários por procedimento
Ficheiro	Onde colocar	Obrigatório
Formulário PDF (SharePoint)	formularios/	✅
Relatório Informa D&B por empresa convidada	formularios/empresas/{NIF}.PDF	Recomendado
Relatório ERP por fornecedor	formularios/acumulados_empresa/{NIF}.PDF	Recomendado
Export ERP por CPV	formularios/acumulados_cpv/{CPV}.xlsx	Recomendado
Export(s) ERP por objecto	formularios/acumulados_objetos/{REF}/	Recomendado

Os ficheiros da Camada B (Informa D&B) e Camada C (ERP) são recomendados mas não bloqueantes — quando ausentes, o sistema gera avisos explícitos em vez de assumir valores por omissão.

Minutas suportadas
Tipo de procedimento	Tipo de objecto	Estado
Consulta Prévia	Aquisição de bens	✅
Ajuste Directo	Serviços	🔄 Em desenvolvimento
Ajuste Directo	Aquisição de bens	⬜
Ajuste Directo	Empreitada	⬜
Consulta Prévia	Serviços	⬜
Consulta Prévia	Empreitada	⬜
Concurso Público	Aquisição de bens	⬜
Concurso Público	Serviços	⬜
Concurso Público	Empreitada	⬜
Arquitectura técnica
Camadas
Camada	Módulo(s)	Descrição
A — Formulário	ler_pdf.py, preencher_word.py	Extracção de dados e preenchimento da minuta
B — Empresas	apinforma.py	Relacionadas e sócios via Informa D&B
C — Acumulados	acumulados_*.py	Acumulados ERP por fornecedor, CPV e objecto
D — Conformidade	conformidade/	17 regras CCP, 28 normas interpretativas
Princípios de design
Sem LLM no núcleo de conformidade — toda a lógica jurídica é determinística; sentence-transformers é usado apenas para similaridade semântica de objectos de contrato
Nunca assume valor por omissão — campo em falta gera alerta explícito, nunca 0 ou "Não" silencioso
O técnico decide sempre — o sistema detecta e reporta; não aprova nem rejeita procedimentos
Registo auditável — todos os eventos ficam registados no sequencia/ com timestamp, programa e operador
Extracção de empresas relacionadas

O relatório Informa D&B tem duas colunas (cargo/nome à esquerda, ligações à direita) que a leitura linear do PDF confunde. A extracção usa coordenadas (x, y) em vez de ordem linear de texto. Três fontes de relacionadas, deduplicadas:

Participação societária directa
Sócios/Acionistas nominais
Rede de ligações de cada administrador

Validado com 8 PDFs reais (Julcar, MOBAPEC, Tripolo, Nautilus, Euroshelves, Nacionalgest, Segurajuda, Sosel).

Conformidade verificada
Norma	O que verifica
Art. 17º, 19º-22º CCP	Limiares por tipo de procedimento e objecto
Art. 46º-A/2 CCP	Obrigação de fundamentar não divisão em lotes
Art. 67º-69º CCP	Composição do júri
Art. 88º-90º, 353º CCP	Caução obrigatória e valor
Art. 112º-114º CCP	Ajuste directo e consulta prévia — condições de recurso
Art. 113º/2, 113º/6, 114º/2 CCP	Acumulados por fornecedor e por CPV
Art. 290º-A CCP	Gestor de contrato e substituto
Art. 48º, 63º, 65º, 440º CCP	Duração do contrato
DL 127/2008, DL 13-A/2025	Execução orçamental e compromissos
Limiares LOPTC	€750k por contrato, €950k acumulado
Notas legais

Os limiares legais estão sujeitos a revisão periódica:

Limiares JOUE (€216k bens/serviços, €5.404M empreitadas) — revisão bianual, próxima Janeiro 2028
Limiares LOPTC — proposta de alteração legislativa pendente
Limiar extensão de encargos (€500k) — revisto anualmente pela LOE

Verificar actualizações antes de cada ciclo de aprovação orçamental.

Enquadramento (EU AI Act)

Este sistema classifica-se como risco reduzido nos termos do EU AI Act — não toma decisões autónomas com efeitos jurídicos; as decisões de aprovação, adjudicação e assinatura são sempre do técnico e dos órgãos competentes. Ver memória descritiva Parte 3 para análise completa.

Estado do projecto

Versão: 9 — Outubro 2026 Fluxo principal: funcional e validado com dados reais (Consulta Prévia + Bens) Verificação 2: construída e testada Pendente: teste de ponta a ponta com procedimento real (Camada C incluída), 8 minutas restantes, revisão jurídica/DPO