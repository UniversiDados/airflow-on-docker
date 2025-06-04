# scripts/01_extract_api_data.py
import requests
import json
import argparse
import os

def extract_data(api_url, output_path):
    """
    Extrai dados da API REST Countries e salva em um arquivo JSON.
    """
    print(f"Iniciando extração da API: {api_url}")
    countries_data = None
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Levanta um erro para status HTTP ruins (4xx ou 5xx)
        countries_data = response.json()
        print(f"Sucesso! Obtidos dados de {len(countries_data)} países.")

        # Garante que o diretório de saída exista
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(countries_data, f, ensure_ascii=False, indent=4)
        print(f"Dados brutos salvos em: {output_path}")

    except requests.exceptions.RequestException as e:
        print(f"Erro ao chamar a API: {e}")
        raise
    except Exception as e_gen:
        print(f"Um erro geral ocorreu: {e_gen}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrai dados da API REST Countries.")
    parser.add_argument("--output_path", required=True, help="Caminho para salvar o arquivo JSON de saída.")
    
    args = parser.parse_args()
    
    api_url = "https://restcountries.com/v3.1/all"
    extract_data(api_url, args.output_path)