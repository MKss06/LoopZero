# Grade Hall revisada: reteste de X=5 mm

Fonte vigente preservada: [mapeamento_hall_grade_revisado_x5.xlsx](../../experiments/hall-sensor/mapeamento_hall_grade_revisado_x5.xlsx) (SHA-256 `bfb6452d861a87b4c51acc3a07377e46d3301aa26b65477821cd8ae61045ed71`). A [planilha anterior](../../experiments/hall-sensor/mapeamento_hall_grade.xlsx) e seus [mapas históricos](mapeamento-hall-horizontal.md) também permanecem preservados. **As seis posições X=5 mm anteriores foram substituídas pelo reteste; as outras 24 posições não mudaram.** A grade vigente resume **1313 amostras com ímã** em 30 médias de blocos. A planilha não contém a ordem temporal das leituras seriais.

## Conferência e referência do reteste

A aba `Reteste X5` contém a distribuição de códigos ADC do novo bloco, as médias e contagens anteriores, e a referência específica do reteste. As frequências dos códigos reproduzem as seis contagens e médias novas. Foram conferidos também ΔV, `ADC × 5/1023 V`, a conversão por 14 mV/mT e as seis células X=5 da aba `Mapa`. A referência reteste usa **29** leituras iniciais (média **533,689655 ADC**) e **25** finais (média **535,000000 ADC**); a média simples aplicada aos dois lados em X=5 é **534,344828 ADC**. Para X≥10 mm permanecem as referências antigas próprias de cada lado. As planilhas não foram editadas.

[CSV vigente de 30 posições](mapeamento-hall-x5-revisado.csv) · [Histórico dos seis pontos, com estado substituído/vigente](mapeamento-hall-x5-revisado-historico.csv) · [Mapas vigentes](mapeamento-hall-x5-revisado.png) · [Gráfico antes/depois em X=5](mapeamento-hall-x5-revisado-historico.png). O campo em mT segue **14 mV/mT típicos do SS49E Honeywell**, sem calibração individual; os resíduos são analisados em volts.

## Comparação com escalas já publicadas

**Primeira comparação, sem reajuste:** a escala fixa do modelo horizontal, **-12.320751 V/T de referência**, ajustada à primeira coleta de 14 médias, é aplicada à grade revisada. Para rastrear a análise anterior da grade, também mostramos a escala **-6.831328 V/T**, exploratoriamente ajustada às 30 posições **anteriores**, sem novo ajuste ao reteste. A geometria horizontal, a virada rígida, a polarização local +Z de referência, a componente candidata `vertical_z`, a altura relativa de 0 mm e o deslocamento nominal de 0 mm foram mantidos. Nenhuma geometria ou orientação foi ajustada.

| Escala e conjunto | Posições | MAE antes (V) | MAE revisado (V) | RMSE antes (V) | RMSE revisado (V) |
| --- | ---: | ---: | ---: | ---: | ---: |
| fixa −12,320751, ambos | 30 | 0.074486 | 0.048615 | 0.130403 | 0.081033 |
| fixa −12,320751, Lado 1 | 15 | 0.078616 | 0.042080 | 0.136188 | 0.068255 |
| fixa −12,320751, Lado 2 | 15 | 0.070355 | 0.055151 | 0.124349 | 0.092054 |
| fixa −12,320751, só X=5 | 6 | 0.274995 | 0.145644 | 0.278913 | 0.159998 |
| exploratória histórica −6,831328, ambos | 30 | 0.021621 | 0.029261 | 0.040427 | 0.075203 |
| exploratória histórica −6,831328, Lado 1 | 15 | 0.023130 | 0.036634 | 0.043918 | 0.090805 |
| exploratória histórica −6,831328, Lado 2 | 15 | 0.020111 | 0.021887 | 0.036605 | 0.055367 |
| exploratória histórica −6,831328, só X=5 | 6 | 0.073287 | 0.111488 | 0.086886 | 0.166297 |

Com o reteste, o RMSE da escala fixa de −12,320751 V/T passa de **0.130403** para **0.081033 V**. A escala exploratória histórica de −6,831328 V/T passa de **0.040427** para **0.075203 V**. A vantagem numérica da escala exploratória anterior diminui muito após a troca dos seis pontos; ela ainda tem RMSE ligeiramente menor na grade revisada, sem ter sido ajustada a ela. Essas métricas não identificam a montagem física nem autorizam escolher magnetização.

## Seis posições substituídas

ΔV é a tensão medida menos a referência aplicada da respectiva série. O resíduo usa a escala fixa de −12,320751 V/T em ambas as versões; portanto, a mudança de erro reflete somente os dados substituídos e a nova referência do reteste.

| Lado | Y (mm) | ΔV anterior (V; substituído) | ΔV reteste (V; vigente) | Modelo sem reajuste (V) | Resíduo anterior (V) | Resíduo reteste (V) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Lado 1 | -10 | +0.109223 | +0.306915 | +0.457855 | -0.348632 | -0.150941 |
| Lado 1 | +0 | +0.509625 | +0.778373 | +0.789761 | -0.280136 | -0.011388 |
| Lado 1 | +10 | +0.225759 | +0.307360 | +0.457855 | -0.232096 | -0.150495 |
| Lado 2 | -10 | -0.146499 | -0.249877 | -0.457855 | +0.311356 | +0.207978 |
| Lado 2 | +0 | -0.520888 | -0.648243 | -0.789761 | +0.268873 | +0.141518 |
| Lado 2 | +10 | -0.248976 | -0.246309 | -0.457855 | +0.208880 | +0.211546 |

## Limites

O reteste corrige as coordenadas declaradas de X=5 mm, mas a planilha não fornece posição física do elemento Hall, orientação sensível confirmada, magnetização medida ou distâncias físicas verificadas. A comparação mantém a hipótese de Y lateral ao comprimento; seu sinal e origem físicos não foram confirmados. As escalas elétricas não são magnetizações medidas. Os dados anteriores continuam úteis para histórico, mas **não entram na grade vigente**. Nenhuma nova escala foi ajustada **neste relatório**. Uma [análise exploratória posterior](mapeamento-hall-x5-escala-exploratoria.md) ajusta uma escala comum à grade revisada e identifica separadamente os erros avaliados nos próprios pontos.

Reproduza com `.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_grid_x5_revision.py`.
