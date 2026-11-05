# Hall × Magpylib: aproximação horizontal e virada do mesmo ímã

O [esquema dos eixos](esquema-montagem-horizontal.svg) é gerado **antes do ajuste**. Ele fixa Z como vertical da superfície, +X como eixo horizontal do Hall em direção ao ímã, e +Y como direção horizontal do comprimento. A seta de aproximação vai em −X quando a distância nominal cai de 50 a 0 mm.

## Observado e assumido

**Informado:** elemento Hall preto fixo na ponta do módulo, voltado para o ímã; aproximação horizontal; para o lado 2, a mesma peça foi virada para que a face antes apoiada ficasse para cima. Não há fotografia incorporada neste repositório; a geometria abaixo usa essa descrição. O experimentador identificou o sensor como Honeywell SS49E do kit Elegoo de 37 sensores. ‘Lado 1 = Sul; lado 2 = Norte’ é a atribuição adotada para esta análise segundo a convenção da ficha Honeywell, considerando a face sensível voltada para o ímã; não houve verificação independente dos polos.

**Hipóteses de cálculo:** comprimento local X → +Y global, largura local Y → −X global, espessura local Z → +Z global no lado 1. O lado 2 é uma rotação rígida de 180° em torno do comprimento local X (global Y): o vetor de polarização local `(0,0,+1)` T permanece o mesmo dentro da peça e passa de +Z para −Z global. É uma referência matemática para a hipótese de magnetização **através da espessura**, não uma medição. Nenhuma face é chamada de Norte ou Sul pelo modelo. A descrição textual não estabelece se o comprimento estava paralelo ou transversal à trajetória; este cenário escolhe comprimento transversal (+Y). Uma aproximação pela extremidade largura × espessura exigiria outra pose.

O Hall ideal está parado em `x=y=0`; seu plano frontal normal aponta para +X. O ímã se aproxima pela face lateral local +Y no lado 1 e local −Y no lado 2: ambas são faces comprimento × espessura, não a face maior horizontal. A face local −Z apoiada no lado 1 passa a +Z global (para cima) após a virada. Isto **não** implica que ela ficou voltada ao Hall, que está na direção horizontal da peça.

A altura do elemento Hall foi fixada provisoriamente em **2.240 mm** acima da superfície; a altura do centro do ímã é metade da espessura média, **2,240 mm**. O deslocamento entre a marca nominal e o elemento sensível foi fixado em **0.000 mm**. Esses valores não foram medidos. O alinhamento em Y também é assumido. A face próxima tem coordenada `x = d + deslocamento`; em 0 mm a superfície do cuboide alcança o plano x do Hall no modelo, sem afirmar contato físico no ensaio.

**Projeções candidatas do campo:** `normal_x` (+X global, normal da frente do módulo), `vertical_z` (+Z global) e `longitudinal_y` (+Y global). O eixo sensível e o sinal de resposta reais do SS49E não foram extraídos da montagem; cada projeção é uma hipótese separada.

Fonte: `data/experiments/hall-sensor/loopzero_hall_tensao_distancia.xlsx` (SHA-256 `d536ed2305b905a90187ce3de6868d18bbe4fc173b43d43379bd4288e16b4958`). As 904 leituras foram agregadas por lado e distância e conferidas contra a aba `Comparação`. Dimensões médias: 19,37 × 9,40 × 4,48 mm = `(0.01937, 0.00940, 0.00448)` m. Nenhum dos dez ímãs foi identificado como a peça do ensaio.

## Ajuste das 14 médias de 5 a 50 mm

Para cada projeção com campo não nulo, um único fator efetivo é ajustado aos dois lados por mínimos quadrados não ponderados, sem intercepto. O fator mistura polarização real, sensibilidade elétrica e geometria; não é magnetização medida nem calibração. Com template nulo, a escala é **não identificável**, e o resíduo exibido é o próprio ΔV observado.

| Projeção candidata | Escala efetiva (V/T de referência) | MAE (V) | RMSE (V) |
| --- | ---: | ---: | ---: |
| `normal_x` | não identificável | 0.184808 | 0.315405 |
| `vertical_z` | -12.320751 | 0.014489 | 0.016570 |
| `longitudinal_y` | não identificável | 0.184808 | 0.315405 |

O sinal da escala ajustada depende da escolha arbitrária de +Z local para a polarização de referência e do sentido positivo escolhido para a projeção. Escala negativa não identifica um polo magnético nem o sinal físico do SS49E.

## Observação, previsão e resíduo (V)

[Gráfico de 5–50 mm](comparacao-horizontal.png) · [CSV com todas as projeções](comparacao-horizontal.csv). Resíduo = ΔV observado − previsto. O CSV também traz campo estimado em mT por ΔV (mV)/14: **14 mV/mT é a sensibilidade típica do SS49E Honeywell identificado pelo experimentador, sem calibração individual da unidade**. Veja a [comparação condicional com a componente Magpylib](comparacao-campo-estimado-horizontal.md); os gráficos abaixo permanecem em volts.

| Lado | d (mm) | ΔV obs. | X previsto | X res. | Z previsto | Z res. | Y previsto | Y res. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Lado 1 | 5 | +0.774637 | +0.000000 | +0.774637 | +0.789761 | -0.015124 | +0.000000 | +0.774637 |
| Lado 1 | 10 | +0.263223 | +0.000000 | +0.263223 | +0.239178 | +0.024045 | +0.000000 | +0.263223 |
| Lado 1 | 15 | +0.121090 | +0.000000 | +0.121090 | +0.101648 | +0.019441 | +0.000000 | +0.121090 |
| Lado 1 | 20 | +0.083012 | +0.000000 | +0.083012 | +0.052127 | +0.030886 | +0.000000 | +0.083012 |
| Lado 1 | 30 | +0.024182 | +0.000000 | +0.024182 | +0.018972 | +0.005210 | +0.000000 | +0.024182 |
| Lado 1 | 40 | +0.014387 | +0.000000 | +0.014387 | +0.008907 | +0.005480 | +0.000000 | +0.014387 |
| Lado 1 | 50 | +0.008604 | +0.000000 | +0.008604 | +0.004869 | +0.003734 | +0.000000 | +0.008604 |
| Lado 2 | 5 | -0.781652 | +0.000000 | -0.781652 | -0.789761 | +0.008109 | +0.000000 | -0.781652 |
| Lado 2 | 10 | -0.263278 | +0.000000 | -0.263278 | -0.239178 | -0.024100 | +0.000000 | -0.263278 |
| Lado 2 | 15 | -0.118250 | +0.000000 | -0.118250 | -0.101648 | -0.016602 | +0.000000 | -0.118250 |
| Lado 2 | 20 | -0.072564 | +0.000000 | -0.072564 | -0.052127 | -0.020437 | +0.000000 | -0.072564 |
| Lado 2 | 30 | -0.029045 | +0.000000 | -0.029045 | -0.018972 | -0.010073 | +0.000000 | -0.029045 |
| Lado 2 | 40 | -0.019282 | +0.000000 | -0.019282 | -0.008907 | -0.010375 | +0.000000 | -0.019282 |
| Lado 2 | 50 | -0.014101 | +0.000000 | -0.014101 | -0.004869 | -0.009232 | +0.000000 | -0.014101 |

## 0 mm nominal: medição real e cálculo separado

As leituras Hall em 0 mm são **medições reais** transcritas na planilha. Somente os valores **calculados pelo modelo** nesse ponto são extrapolados a partir do ajuste de 5–50 mm; não foram fornecidos como previsões pelo experimentador. [Gráfico de 0 mm](comparacao-horizontal-zero.png). Valores em volts; cálculos sensíveis à altura e à definição do zero.

| Lado | ΔV obs. | X previsto | X res. | Z previsto | Z res. | Y previsto | Y res. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Lado 1 | +1.671804 | +0.000000 | +1.671804 | +4.886921 | -3.215117 | +0.000000 | +1.671804 |
| Lado 2 | -1.501611 | +0.000000 | -1.501611 | -4.886921 | +3.385310 | +0.000000 | -1.501611 |

## O que os resíduos permitem concluir

Os resíduos comparam formas de curva **dentro das hipóteses** de altura, alinhamento e projeção. Um erro menor não identifica o eixo sensível, a magnetização ou um polo real: outras alturas, orientações e deslocamentos podem alterar as curvas. A conversão adicional para mT usa somente a hipótese típica de 14 mV/mT; não é um campo calibrado. A direção/sinal de magnetização, o eixo e sinal de resposta do Hall, a altura do elemento sensível e o zero geométrico permanecem pendentes.

Os ajustes desta página usam exclusivamente a trajetória horizontal, com o Hall fixo e a mesma peça virada rigidamente. Não identificam a montagem completa nem um campo calibrado em mT.

Versões: Python 3.13.17, Magpylib 6.1.0, SciPy 1.18.1. Reproduza com `.\.venv\Scripts\python.exe simulation/magnetic-field/src/compare_hall_mountings.py`.
