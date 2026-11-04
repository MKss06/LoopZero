# Análise de tensão do sensor Hall

Fonte preservada: `data/experiments/hall-sensor/loopzero_hall_tensao_distancia.xlsx` (SHA-256 `d536ed2305b905a90187ce3de6868d18bbe4fc173b43d43379bd4288e16b4958`).
Reproduzida com Python 3.13.17 e Matplotlib 3.11.2.

Foram analisadas **904 leituras**: 831 com ímã e 73 referências sem ímã. As médias, contagens e ΔV conferem com a aba `Comparação`.

| Lado | Referência sem ímã (V) | n referência | ΔV em 0 mm (mV) | ΔV em 50 mm (mV) |
| --- | ---: | ---: | ---: | ---: |
| Lado 1 | 2.605196 | 51 | +1671.804 | +8.604 |
| Lado 2 | 2.614545 | 22 | -1501.611 | -14.101 |

As curvas mostram **tensões medidas**, inclusive em 0 mm nominal; 0 mm não é uma distância confirmada até o elemento sensível. Para o lado 2, o mesmo ímã foi virado: a face antes apoiada ficou para cima, enquanto o Hall permaneceu fixo e a aproximação foi horizontal. Essa face superior não é automaticamente a face voltada ao Hall. A planilha foi transcrita de mensagens, com linhas incompletas e leituras anteriores omitidas conforme suas notas; portanto, não representa o fluxo integral do instrumento.

ΔV = média de tensão com ímã − referência sem ímã do mesmo lado. Sem sensibilidade e eixo sensível calibrados, ΔV não é convertido em mT. Nenhuma magnetização foi ajustada a estes dados.

Os 16 grupos e todas as contagens, médias e diferenças estão na [tabela de médias](medias-por-distancia.csv). Veja as curvas de [tensão](tensao-distancia.png) e [ΔV](delta-v-distancia.png).

Para reproduzir, na raiz do repositório, execute `.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_analysis.py` no PowerShell, ou `python simulation/magnetic-field/src/hall_analysis.py` com o ambiente ativado.
