import os
import json

# Estrutura unificada dos dados consolidando os arquivos e os PDFs anexados
frota_veiculos = [
    {
        "id": 1,
        "veiculo": "GM/ZAFIRA",
        "placa": "DTP9H76",
        "renavam": "00917609069",
        "local": "Primavera do leste",
        "contato": "(75) 992887893",
        "responsavel": "Luciano",
        "proprietario_crlv": "Jane Kelly Goncalves de Amorim",
        "status_vistoria": "OK",
        "documento_anexo": {
            "nome_arquivo": "CRLV-e_DTP9H76_2024.pdf",
            "exercicio_crlv": 2024,
            "caminho": "/documentos/veiculos/DTP9H76.pdf"
        },
        "ipva": {
            "valor": 824.53,
            "vencimento": "2026-01-19",
            "status": "PAGO"
        },
        "licenciamento": {
            "valor": None,
            "vencimento": None,
            "status": "PENDENTE"
        },
        "multas": [
            {"valor": 215.67, "data_referencia": "01/25", "status": "EM ABERTO"}
        ]
    },
    {
        "id": 2,
        "veiculo": "HILUX TIO VERO",
        "placa": "HKN5321",
        "renavam": "00214279804",
        "local": "Primavera do leste",
        "contato": "(16) 988577836",
        "responsavel": "Tio Vero",
        "proprietario_crlv": "Trailba Anacleto Oliveira",
        "status_vistoria": "OK",
        "documento_anexo": {
            "nome_arquivo": "CRLV-e_HKN5321_2025.pdf",
            "exercicio_crlv": 2025,
            "caminho": "/documentos/veiculos/HKN5321.pdf"
        },
        "ipva": {
            "valor": 4170.55,
            "vencimento": "2026-02-12",
            "status": "PAGO"
        },
        "licenciamento": {
            "valor": 174.08,
            "vencimento": "2026-07-31",
            "status": "PAGO"
        },
        "multas": []
    },
    {
        "id": 3,
        "veiculo": "JEEP/RENEGADE",
        "placa": "RNS5J76",
        "renavam": "01274088523",
        "local": "Campo Grande",
        "contato": "(67) 998472299",
        "responsavel": "Jaqueline",
        "proprietario_crlv": "Jose Valfrido Alves Ximenes",
        "status_vistoria": "OK",
        "documento_anexo": {
            "nome_arquivo": "CRLV-e_RNS5J76_2024.pdf",
            "exercicio_crlv": 2024,
            "caminho": "/documentos/veiculos/RNS5J76.pdf"
        },
        "ipva": {
            "valor": 0.0,
            "vencimento": None,
            "status": "PAGO"
        },
        "licenciamento": {
            "valor": 239.99,
            "vencimento": "2026-07-31",
            "status": "PAGO"
        },
        "multas": []
    },
    {
        "id": 4,
        "veiculo": "VW/GOL 1.0 Cinza",
        "placa": "DNK3F42",
        "renavam": "00844244449",
        "local": "Primavera do leste",
        "contato": "(16) 991681514",
        "responsavel": "Xauli",
        "proprietario_crlv": "Jane Kelly Goncalves de Amorim",
        "status_vistoria": "OK",
        "documento_anexo": {
            "nome_arquivo": "CRLV-e_DNK3F42_2025.pdf",
            "exercicio_crlv": 2025,
            "caminho": "/documentos/veiculos/DNK3F42.pdf"
        },
        "ipva": {
            "valor": 0.0,
            "vencimento": None,
            "status": "ISENTO"
        },
        "licenciamento": {
            "valor": None,
            "vencimento": None,
            "status": "PENDENTE"
        },
        "multas": [
            {"valor": 270.47, "data_referencia": None, "status": "EM ABERTO"}
        ]
    },
    {
        "id": 5,
        "veiculo": "VW/GOL 1.0 Preto",
        "placa": "EDY9I72",
        "renavam": "00156878364",
        "local": "Cuiabá",
        "contato": "(77) 991799067",
        "responsavel": "Júnior",
        "proprietario_crlv": "Jane Kelly Goncalves de Amorim",
        "status_vistoria": "OK",
        "documento_anexo": {
            "nome_arquivo": "CRLV-e_EDY9I72_2026.pdf",
            "exercicio_crlv": 2026,
            "caminho": "/documentos/veiculos/EDY9I72.pdf"
        },
        "ipva": {
            "valor": 0.0,
            "vencimento": None,
            "status": "ISENTO"
        },
        "licenciamento": {
            "valor": 181.13,
            "vencimento": "2026-07-31",
            "status": "PAGO"
        },
        "multas": [
            {"valor": 2017.39, "data_referencia": "12/25 e 01/26", "status": "EM ABERTO"}
        ]
    },
    {
        "id": 6,
        "veiculo": "VW/KOMBI",
        "placa": "HEL7F13",
        "renavam": "00904876683",
        "local": "Pato Branco",
        "contato": "(16) 981078251",
        "responsavel": "Delmiro",
        "proprietario_crlv": "Jane Kelly Goncalves de Amorim",
        "status_vistoria": "OK",
        "documento_anexo": {
            "nome_arquivo": "CRLV-e_HEL7F13_2025.pdf",
            "exercicio_crlv": 2025,
            "caminho": "/documentos/veiculos/HEL7F13.pdf"
        },
        "ipva": {
            "valor": 308.39,
            "vencimento": "2026-02-19",
            "status": "PAGO"
        },
        "licenciamento": {
            "valor": 174.08,
            "vencimento": "2026-08-31",
            "status": "EM ABERTO"
        },
        "multas": [
            {"valor": 1348.43, "data_referencia": "01/25,02/25,03/25 e 05/25", "status": "EM ABERTO"}
        ]
    },
    {
        "id": 7,
        "veiculo": "HILLUX JOÃO",
        "placa": "UDE4B85",
        "renavam": "01467335476",
        "local": "Em Viagem",
        "contato": "(16) 981895558",
        "responsavel": "João Frutuoso",
        "proprietario_crlv": "Jane Kelly Goncalves de Amorim",
        "status_vistoria": "OK",
        "documento_anexo": {
            "nome_arquivo": "CRLV-e_UDE4B85_2025.pdf",
            "exercicio_crlv": 2025,
            "caminho": "/documentos/veiculos/UDE4B85.pdf"
        },
        "ipva": {
            "valor": 12305.59,
            "vencimento": "2026-01-16",
            "status": "PAGO"
        },
        "licenciamento": {
            "valor": 174.08,
            "vencimento": "2026-09-30",
            "status": "EM ABERTO"
        },
        "multas": []
    },
    {
        "id": 8,
        "veiculo": "HILLUX MARKUS VINICIUS",
        "placa": "ETY3733",
        "renavam": "00377362689",
        "local": "Jaboticabal",
        "contato": None,
        "responsavel": "Markus Vinicius",
        "proprietario_crlv": "Markus Vinicius da Silva",
        "status_vistoria": "OK",
        "documento_anexo": {
            "nome_arquivo": "CRLV-e_ETY3733_2025.pdf",
            "exercicio_crlv": 2025,
            "caminho": "/documentos/veiculos/ETY3733.pdf"
        },
        "ipva": {
            "valor": 4378.59,
            "vencimento": "2026-02-19",
            "status": "PAGO"
        },
        "licenciamento": {
            "valor": 174.08,
            "vencimento": "2026-08-31",
            "status": "EM ABERTO"
        },
        "multas": [
            {"valor": 405.69, "data_referencia": "08/25 e 07/25", "status": "PAGO"}
        ]
    }
]

def buscar_ficha_veiculo(placa):
    """Retorna os dados completos do veiculo com o PDF anexado pela placa"""
    for veiculo in frota_veiculos:
        if veiculo["placa"].upper() == placa.upper():
            return veiculo
    return None

# Exemplo de teste de consulta da ficha
placa_busca = "EDY9I72"
ficha = buscar_ficha_veiculo(placa_busca)
print(json.dumps(ficha, indent=4, ensure_ascii=False))