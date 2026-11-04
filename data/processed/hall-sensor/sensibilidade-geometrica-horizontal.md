# Sensibilidade geométrica do modelo Hall horizontal

Fonte: `data/experiments/hall-sensor/loopzero_hall_tensao_distancia.xlsx` (SHA-256 `d536ed2305b905a90187ce3de6868d18bbe4fc173b43d43379bd4288e16b4958`). As **904 leituras** foram reagregadas e conferidas com a aba `Comparação`. A planilha e os resultados anteriores não foram alterados. A [montagem horizontal](comparacao-horizontal.md) define a peça, a virada rígida e a projeção candidata **vertical_z** usada aqui; o eixo sensível real não foi medido.

## Parâmetros e convenções

- `altura_relativa_mm = z_Hall − z_centro_ímã`. Valores positivos colocam o elemento acima do centro; negativos, abaixo. O centro do ímã fica a 2,24 mm da superfície neste modelo apoiado, mas **a entrada da grade é relativa**; não se presume altura medida do Hall.
- `deslocamento_mm = lacuna_física − distância_nominal`. Assim, `lacuna_física = d_nominal + deslocamento`, medida horizontalmente da face próxima do ímã ao elemento Hall. Deslocamento positivo põe o elemento mais longe; zero põe o ponto no plano da face em 0 mm. Somente deslocamentos não negativos são aceitos, e o código também verifica que o ponto não fica **dentro** do cuboide.
- Grade exploratória: altura relativa de **-2.00 a +2.00 mm**, passo **0.25 mm**; deslocamento de **0.00 a 6.00 mm**, passo **0.25 mm**. São limites escolhidos para exploração, **não limites medidos**.

Em cada uma das combinações da grade, ajusta-se **apenas uma escala elétrica comum aos dois lados**, por mínimos quadrados sem intercepto, nas mesmas 14 médias de 5–50 mm. O erro mostrado é calculado nessas 14 médias. O ponto de 0 mm nunca entra no ajuste nem na escolha do menor erro. As tensões em 0 mm da planilha são **medições reais**; as tensões obtidas pelo modelo nesse ponto são cálculos de extrapolação.

[Mapa de RMSE](sensibilidade-geometrica-horizontal-mapa.png) · [Grade completa](sensibilidade-geometrica-horizontal-grade.csv) · [Curvas representativas](sensibilidade-geometrica-horizontal-curvas.png) · [Resíduos de cada cenário mostrado](sensibilidade-geometrica-horizontal-residuos.csv).

## Melhores resultados da grade

| Ordem | Altura relativa (mm) | Deslocamento (mm) | Escala efetiva (V/T ref.) | MAE (V) | RMSE (V) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | +0.00 | 1.50 | -18.290096 | 0.004938 | 0.006515 |
| 2 | -0.25 | 1.50 | -18.332132 | 0.004988 | 0.006516 |
| 3 | +0.25 | 1.50 | -18.332132 | 0.004988 | 0.006516 |
| 4 | +0.50 | 1.50 | -18.458757 | 0.005137 | 0.006543 |
| 5 | -0.50 | 1.50 | -18.458757 | 0.005137 | 0.006543 |
| 6 | +0.75 | 1.50 | -18.671535 | 0.005386 | 0.006665 |
| 7 | -0.75 | 1.50 | -18.671535 | 0.005386 | 0.006665 |
| 8 | -1.00 | 1.25 | -17.870487 | 0.005126 | 0.006673 |
| 9 | +1.00 | 1.25 | -17.870487 | 0.005126 | 0.006673 |
| 10 | -0.75 | 1.25 | -17.571339 | 0.004878 | 0.006725 |

**33 de 425 combinações** têm RMSE até 10% acima do mínimo. Nessa faixa, a altura relativa vai de -1.50 a +1.50 mm e o deslocamento de 0.75 a 1.75 mm. Pares de alturas com sinais opostos e mesmo valor absoluto produzem curvas idênticas no modelo simétrico. Esses parâmetros não são identificados como medidas pela grade.

O contorno laranja do mapa separa cenários que extrapolam 0 mm dentro ou fora da faixa nominal ADC de 0–5 V; não participou do ajuste das curvas.

## Cenários mostrados nas curvas e resíduos

| Cenário | Altura relativa (mm) | Deslocamento (mm) | RMSE 5–50 mm (V) |
| --- | ---: | ---: | ---: |
| melhor na grade | +0.00 | 1.50 | 0.006515 |
| alternativa próxima | -1.50 | 0.75 | 0.007035 |
| cenário anterior | +0.00 | 0.00 | 0.016570 |
| melhor com 0–5 V | +2.00 | 3.50 | 0.025813 |

A tabela abaixo traz **observado, previsto e resíduo por lado e distância** para o menor RMSE. A tabela CSV de resíduos contém os mesmos valores para todos os cenários representativos. Resíduo = observado − previsto, em volts.

| Lado | d (mm) | ΔV observado (V) | ΔV previsto (V) | Resíduo (V) |
| --- | ---: | ---: | ---: | ---: |
| Lado 1 | 5 | +0.774637 | +0.777585 | -0.002948 |
| Lado 1 | 10 | +0.263223 | +0.267626 | -0.004403 |
| Lado 1 | 15 | +0.121090 | +0.121567 | -0.000477 |
| Lado 1 | 20 | +0.083012 | +0.064972 | +0.018040 |
| Lado 1 | 30 | +0.024182 | +0.024824 | -0.000642 |
| Lado 1 | 40 | +0.014387 | +0.011980 | +0.002407 |
| Lado 1 | 50 | +0.008604 | +0.006666 | +0.001937 |
| Lado 2 | 5 | -0.781652 | -0.777585 | -0.004067 |
| Lado 2 | 10 | -0.263278 | -0.267626 | +0.004348 |
| Lado 2 | 15 | -0.118250 | -0.121567 | +0.003317 |
| Lado 2 | 20 | -0.072564 | -0.064972 | -0.007592 |
| Lado 2 | 30 | -0.029045 | -0.024824 | -0.004221 |
| Lado 2 | 40 | -0.019282 | -0.011980 | -0.007302 |
| Lado 2 | 50 | -0.014101 | -0.006666 | -0.007435 |

## 0 mm nominal: tensão medida e extrapolação calculada

Os valores de ΔV observado em 0 mm são **medições reais** da planilha; não são previsões fornecidas pelo experimentador. Somente os valores calculados pelo modelo nesse ponto são extrapolações fora do ajuste. O cálculo soma o ΔV do modelo à **referência sem ímã do mesmo lado** para obter a tensão total prevista. A faixa **0–5 V** é o limite nominal de leitura ADC inferido da conversão das leituras (aproximadamente `ADC × 5/1023`), **não** uma especificação confirmada de saída linear do AH49E. A alimentação e a faixa válida do sensor ainda precisam ser verificadas.

| Cenário | Lado | ΔV medido (V) | ΔV calculado (V) | Saída calculada (V) | Dentro de 0–5 V? |
| --- | --- | ---: | ---: | ---: | --- |
| melhor na grade | Lado 1 | +1.671804 | +4.043316 | 6.648512 | não |
| melhor na grade | Lado 2 | -1.501611 | -4.043316 | -1.428770 | não |
| alternativa próxima | Lado 1 | +1.671804 | +4.130223 | 6.735419 | não |
| alternativa próxima | Lado 2 | -1.501611 | -4.130223 | -1.515678 | não |
| cenário anterior | Lado 1 | +1.671804 | +4.886921 | 7.492117 | não |
| cenário anterior | Lado 2 | -1.501611 | -4.886921 | -2.272376 | não |
| melhor com 0–5 V | Lado 1 | +1.671804 | +2.390405 | 4.995601 | sim |
| melhor com 0–5 V | Lado 2 | -1.501611 | -2.390405 | 0.224140 | sim |

Em toda a grade, **102/425 cenários** preveem, em 0 mm, tensão dentro de 0–5 V nos dois lados. Entre os 33 cenários até 10% do menor RMSE, **0** passam nessa checagem. O menor RMSE entre os cenários que passam é **0.025813 V**. Esse teste de plausibilidade elétrica não usa 0 mm para ajustar parâmetros e não calibra o sensor. O 0 nominal não é a distância confirmada até o elemento sensível. O cenário de menor RMSE nas 14 médias extrapola para fora de 0–5 V nos dois lados; portanto, seu bom ajuste naquela faixa não valida a resposta elétrica em 0 mm.

## Conclusões sob variação geométrica

A aproximação horizontal, o Hall fixo e a inversão de sinal entre lados continuam representados em toda a grade. A forma da curva em ΔV pode ser semelhante para várias combinações de altura relativa e deslocamento; o fator efetivo também muda. Assim, um menor RMSE de grade **não mede** altura, zero, magnetização ou sensibilidade elétrica. O eixo vertical de leitura e a magnetização pela espessura permanecem hipóteses. ΔV não foi convertido para mT. A identidade dos polos e do ímã ensaiado permanece desconhecida.

Versões: Python 3.13.17, Magpylib 6.1.0, SciPy 1.18.1. Da raiz do repositório: `.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_geometry_sensitivity.py`.
