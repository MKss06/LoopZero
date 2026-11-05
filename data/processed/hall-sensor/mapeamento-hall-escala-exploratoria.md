# Resíduos da grade Hall e escala comum exploratória

**Análise histórica:** os seis valores X=5 mm usados aqui foram substituídos pelo [reteste vigente](mapeamento-hall-x5-revisado.md). A escala ajustada nesta página é mantida como referência anterior; seu erro nesta mesma grade não representa os dados corrigidos.

Fonte preservada: [grade Hall original](../../experiments/hall-sensor/mapeamento_hall_grade.xlsx) (SHA-256 `9e319d3dd6cabaebb6a08f1ae7852fb8427609e24e9cdfd82415135228cfb83f`). Foram usadas as **30 médias** já conferidas em [mapeamento-hall-horizontal.md](mapeamento-hall-horizontal.md). Cada posição tem peso igual. As médias de blocos da planilha, referências sem ímã e conversão ADC–V não foram alteradas.

## Escalas comparadas

A escala fixa é **-12.320751 V/T de campo de referência**, publicada para as 14 médias de 5–50 mm da coleta anterior. O ajuste exploratório de **uma única escala para os dois lados** usa `s = Σ(Bz_ref × ΔV) / Σ(Bz_ref²)`, sem intercepto, nas 30 posições da nova grade: **-6.831328 V/T de referência**. Somente essa escala foi ajustada. A geometria, polarização local +Z de 1 T como referência matemática, eixo candidato `vertical_z`, altura relativa de 0 mm e deslocamento nominal–físico de 0 mm permaneceram os mesmos. A escala combina magnetização real, sensibilidade elétrica e erros geométricos; não é magnetização medida.

| Conjunto | Posições | Viés anterior (V) | MAE anterior (V) | RMSE anterior (V) | Viés exploratório (V) | MAE exploratório (V) | RMSE exploratório (V) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ambos os lados | 30 | -0.004140 | 0.074486 | 0.130403 | -0.004140 | 0.021621 | 0.040427 |
| Lado 1 | 15 | -0.078616 | 0.078616 | 0.136188 | -0.005004 | 0.023130 | 0.043918 |
| Lado 2 | 15 | +0.070336 | 0.070355 | 0.124349 | -0.003276 | 0.020111 | 0.036605 |

A redução do RMSE conjunto é **69.0%** dentro das mesmas posições usadas para o ajuste exploratório; não é validação em dados independentes. MAE, RMSE e viés continuam em volts medidos; nenhuma sensibilidade Hall individual foi inferida.

[Mapas de resíduos por lado](mapeamento-hall-escala-exploratoria.png) · [Tabela completa por lado, X e Y](mapeamento-hall-escala-exploratoria.csv). Resíduo = ΔV medido − ΔV calculado. Cada coluna do gráfico tem escala de cor própria para revelar a estrutura espacial; compare valores pela legenda, não apenas pela cor. Os valores de X são posições discretas, sem espaçamento gráfico proporcional aos milímetros.

## Resíduos por distância X

| Lado e X nominal | Posições | Viés anterior (V) | MAE anterior (V) | RMSE anterior (V) | Viés exploratório (V) | MAE exploratório (V) | RMSE exploratório (V) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Lado 1, X=5 mm | 3 | -0.286954 | 0.286954 | 0.290912 | -0.033668 | 0.081492 | 0.094615 |
| Lado 1, X=10 mm | 3 | -0.088410 | 0.088410 | 0.089216 | -0.004162 | 0.020815 | 0.023701 |
| Lado 1, X=20 mm | 3 | -0.010497 | 0.010497 | 0.010735 | +0.010052 | 0.010052 | 0.010846 |
| Lado 1, X=30 mm | 3 | -0.004931 | 0.004931 | 0.005157 | +0.002943 | 0.002943 | 0.003514 |
| Lado 1, X=50 mm | 3 | -0.002289 | 0.002289 | 0.002321 | -0.000186 | 0.000349 | 0.000458 |
| Lado 2, X=5 mm | 3 | +0.263036 | 0.263036 | 0.266374 | +0.009749 | 0.065082 | 0.078399 |
| Lado 2, X=10 mm | 3 | +0.079316 | 0.079316 | 0.079340 | -0.004933 | 0.014275 | 0.017668 |
| Lado 2, X=20 mm | 3 | +0.007091 | 0.007091 | 0.007509 | -0.013458 | 0.013458 | 0.014132 |
| Lado 2, X=30 mm | 3 | +0.002071 | 0.002168 | 0.002616 | -0.005802 | 0.005802 | 0.006138 |
| Lado 2, X=50 mm | 3 | +0.000165 | 0.000165 | 0.000196 | -0.001938 | 0.001938 | 0.001939 |

## Resíduos por posição lateral Y

| Lado e Y nominal | Posições | Viés anterior (V) | MAE anterior (V) | RMSE anterior (V) | Viés exploratório (V) | MAE exploratório (V) | RMSE exploratório (V) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Lado 1, Y=-10 mm | 5 | -0.094991 | 0.094991 | 0.162988 | -0.033801 | 0.036929 | 0.066324 |
| Lado 1, Y=+0 mm | 5 | -0.074793 | 0.074793 | 0.130537 | +0.023664 | 0.023664 | 0.034781 |
| Lado 1, Y=+10 mm | 5 | -0.066065 | 0.066065 | 0.109711 | -0.004875 | 0.008798 | 0.013331 |
| Lado 2, Y=-10 mm | 5 | +0.081359 | 0.081359 | 0.144077 | +0.020169 | 0.026382 | 0.048412 |
| Lado 2, Y=+0 mm | 5 | +0.070111 | 0.070169 | 0.125182 | -0.028345 | 0.028345 | 0.040436 |
| Lado 2, Y=+10 mm | 5 | +0.059537 | 0.059537 | 0.099798 | -0.001653 | 0.005607 | 0.006406 |

## Padrões e limites

Com a escala anterior, o modelo tende a superestimar o módulo de ΔV nos dois lados: viés negativo no lado 1 e positivo no lado 2. A tabela por X mostra em quais distâncias isso se concentra: em X=5 mm, o MAE anterior é 0,287 V no lado 1 e 0,263 V no lado 2. Com a escala exploratória, ainda é 0,081 V e 0,065 V, respectivamente. Em X=20 mm, o MAE do lado 2 sobe de 0,007 V para 0,013 V. Assim, a melhora global não elimina a estrutura por distância. A tabela por Y mostra a estrutura lateral, que uma escala uniforme não desloca nem torna assimétrica.

A maior diferença observada entre Y=+10 e Y=−10 mm ocorre em **Lado 1, X=5 mm**: **+0.116536 V** (modelo simétrico: +0.000000 V). A hipótese geométrica adotada produz a mesma previsão em ±10 mm. Essa assimetria observada não pode ser eliminada por um fator comum de escala; pode indicar deslocamento lateral, orientação ou diferença entre as condições de coleta, sem identificar qual delas.

A planilha não contém as leituras seriais individuais nem coordenadas físicas verificadas do elemento Hall. O eixo sensível e o sinal do chip na montagem, a altura relativa, o zero físico e a magnetização do ímã permanecem incertos. O campo em mT da grade usa **14 mV/mT típicos do SS49E Honeywell**, sem calibração individual; esta comparação de resíduos permanece em ΔV (V). Não se conclui que a escala exploratória seja propriedade física da peça ou do sensor.

Reproduza com `.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_grid_scale_exploration.py`.
