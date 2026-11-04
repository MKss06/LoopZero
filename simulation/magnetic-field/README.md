# Simulação de campo magnético

Área para modelar os campos estáticos dos ímãs permanentes e comparar previsões com dados experimentais. `src/` receberá código Python, `tests/` verificações de comportamento e `notebooks/` estudos exploratórios. Ainda não há implementação ou resultado validado.

## Ambiente

Use Python 3.12 a 3.14. A partir da raiz do repositório:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r simulation/magnetic-field/requirements.txt
```

Em Linux/macOS: `python3 -m venv .venv`, `source .venv/bin/activate` e o mesmo comando `pip`. As faixas de dependências iniciam uma série compatível para desenvolvimento; registre versões exatas no relatório de cada estudo reproduzível. O Magpylib 6 introduziu mudanças incompatíveis com exemplos da versão 5; consulte a documentação da versão instalada antes de adaptar código antigo.

## Convenções futuras

Documente a geometria, orientação e magnetização dos ímãs, sistema de coordenadas, unidades, hipóteses e versão das bibliotecas. Identifique claramente saídas de simulação e medições. Salve dados derivados em `data/processed/`, com referência aos dados brutos e ao script que os produziu.
