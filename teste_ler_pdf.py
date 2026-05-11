from ler_pdf import ler_dados
import json

dados = ler_dados("formularios/formulario_exemplo.pdf")

for chave, valor in dados.items():
    if valor is not None:
        print(f"{chave}: {valor}")

print(f"\nCampos extraídos: {sum(1 for v in dados.values() if v is not None)}")
print(f"Campos vazios: {sum(1 for v in dados.values() if v is None)}")

import pdfplumber

with pdfplumber.open("formularios/formulario_exemplo.pdf") as pdf:
    tabelas = pdf.pages[0].extract_tables()
    print("=== TABELA 4 COMPLETA ===")
    for linha in tabelas[3]:
        print(linha)