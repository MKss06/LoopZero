# Mapeamento Hall em 30 posições × modelo horizontal

**Histórico substituído em X=5 mm:** os seis valores desta primeira grade foram substituídos pelo [reteste vigente](mapeamento-hall-x5-revisado.md). Este relatório e seus mapas permanecem para rastreabilidade; não representam a grade vigente completa.

Fonte original preservada: [mapeamento_hall_grade.xlsx](../../experiments/hall-sensor/mapeamento_hall_grade.xlsx) (SHA-256 `9e319d3dd6cabaebb6a08f1ae7852fb8427609e24e9cdfd82415135228cfb83f`). A aba `Médias por posição` contém **30 médias de blocos seriais**, não as linhas individuais da porta serial: 1342 amostras com ímã resumidas. Há ainda 126 amostras de referência resumidas. Não é possível recalcular cada média ADC a partir de leituras individuais ausentes; foram conferidas as fórmulas, os valores em cache e as 30 células do mapa. A observação da posição lado 1, X=10, Y=−10 mm diz que a média usa a repetição estável após um primeiro bloco com troca de patamar; essa escolha da fonte foi preservada, sem reconstruir o bloco omitido.

## Cálculos conferidos

Para cada lado, a referência aplicada é a **média simples** das médias ADC do começo e do fim, sem ponderação pelos tamanhos dos blocos. A planilha não tem tempo por posição, então não permite interpolar deriva temporal. A conversão inscrita é `tensão = média ADC × 5/1023 V`, com 5 V nominais, não aferidos. `ΔV = (média ADC − referência aplicada) × 5/1023 × 1000 mV` e `campo estimado = ΔV/14 mT`.

O experimentador identificou o sensor como **Honeywell SS49E** do kit Elegoo de 37 sensores. Os **14 mV/mT** são a sensibilidade típica da [ficha Honeywell](https://prod-edam.honeywell.com/content/dam/honeywell-edam/sps/siot/en-us/products/sensors/magnetic-sensors/linear-and-angle-sensor-ics/common/documents/sps-siot-ss39et-ss49e-ss59et-product-sheet-005850-3-en-ciid-50359.pdf) (1,4 mV/G × 10 G/mT), não uma calibração individual. O campo em mT é estimado a partir de tensão; não é medição de campo calibrada.

| Lado | n início | Referência início (ADC) | n fim | Referência fim (ADC) | Referência aplicada (ADC) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lado 1 | 24 | 533.541667 | 40 | 534.025000 | 533.783333 |
| Lado 2 | 28 | 534.035714 | 34 | 533.911765 | 533.973739 |

## Comparação sem ajuste novo

[Mapa observado, mapa calculado e resíduos em volts](mapeamento-hall-horizontal.png) · [Tabela completa de 30 posições](mapeamento-hall-horizontal.csv). A posição X é tratada como a distância horizontal nominal da face próxima ao Hall; Y é tratado **provisoriamente** como deslocamento lateral ao longo do comprimento do ímã. O Hall fica fixo e o centro do ímã é deslocado para `Y_global = −Y_grade`. O sinal e a origem física de Y não foram documentados independentemente. X=0 não aparece nesta grade. O gráfico organiza as posições X como categorias; o espaçamento vertical das células não é proporcional aos milímetros.

Foi reutilizado o cenário de [comparação horizontal anterior](comparacao-horizontal.md): comprimento em +Y, polarização local +Z de **1 T apenas como referência matemática**, virada rígida entre os lados, projeção candidata `vertical_z`, Hall na altura do centro do ímã e deslocamento do zero igual a 0 mm. A escala elétrica **-12.320751 V/T** é a já publicada para as 14 médias de 5–50 mm da outra coleta. **Nenhuma escala, altura ou deslocamento foi ajustado à grade.** As alturas, o eixo sensível, a magnetização real e a distância física permanecem desconhecidos. A média dimensional do cuboide é 19,37 × 9,40 × 4,48 mm.

| Conjunto | MAE entre ΔV medido e modelo (V) |
| --- | ---: |
| Lado 1 (15 posições) | 0.078616 |
| Lado 2 (15 posições) | 0.070355 |
| Ambos (30 posições) | 0.074486 |

RMSE conjunto: **0.130403 V**. Esses números medem a transferência do cenário anterior a esta grade; não validam a orientação sensível do Hall. A componente de referência Magpylib e a versão com escala efetiva são cálculos, não campo medido. Um [estudo exploratório separado de uma escala comum](mapeamento-hall-escala-exploratoria.md) examina os resíduos sem substituir esta comparação fixa.

## Leitura dos mapas

A grade registra sinal positivo para o lado 1 e negativo para o lado 2 em todas as posições. O maior módulo em cada lado ocorre em X=5 mm, Y=0 mm. A concentração central e a inversão de sinal podem ser comparadas visualmente com o cenário horizontal, mas a concordância quantitativa deve ser julgada pelos resíduos da tabela e do gráfico. Assimetria entre Y=−10 e Y=+10 mm pode refletir alinhamento ou outra característica da montagem; esta planilha não identifica sua causa.

A resposta estimada em mT apenas reescala ΔV. A curva `vertical_z` não demonstra que esse seja o eixo sensível real. Se a face marcada do SS49E estivesse apontada horizontalmente para o ímã, a projeção normal candidata seria X, cuja escala elétrica não foi identificada no ajuste anterior simétrico. São necessários a orientação do chip, a definição física de X/Y, a altura relativa e o zero físico antes de atribuir significado físico aos resíduos.

Reproduza a conferência e os mapas com `.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_grid_analysis.py`.
