# Comparação direta das grades Hall: um e cinco ímãs

## Fontes vigentes e método

Ímã único: [planilha revisada](../../experiments/hall-sensor/mapeamento_hall_grade_revisado_x5.xlsx) (SHA-256 `bfb6452d861a87b4c51acc3a07377e46d3301aa26b65477821cd8ae61045ed71`). Os seis pontos X=5 mm vêm do reteste válido; os outros 24 são da coleta anterior [preservada](../../experiments/hall-sensor/mapeamento_hall_grade.xlsx). Fileira: [planilha original](../../experiments/hall-sensor/mapeamento_cinco_imans.xlsx) (SHA-256 `04b571c4addbc3dabd9efec2a6dfef5fb463fc77938764b68a3578bb001b1fea`). São 30 posições por configuração, cruzadas exatamente por lado, X e Y. As planilhas e os resultados anteriores permanecem intactos.

As coordenadas são **nominais**: X = 5, 10, 20, 30, 50 mm; Y = −10, 0, +10 mm. A correspondência de `lado 1` e `lado 2` entre coletas é assumida pela identificação registrada; não há verificação independente das polaridades dos cinco ímãs. Em um ímã, a referência aplicada é a média dos blocos inicial e final do lado, exceto X=5, que usa a referência própria do reteste. Em cinco ímãs, mostram-se separadamente as referências inicial e final. A média dos extremos é usada **apenas como cenário ilustrativo** para os mapas e métricas; não representa a referência verdadeira em cada instante. A faixa entre extremos não é intervalo de confiança.

`ΔV = tensão média medida − referência sem ímã` (conversão ADC × 5/1023 V, nominal). Diferença observada = ΔV de cinco − ΔV de um. O Magpylib usa o mesmo Hall fixo, X horizontal, Y lateral, componente candidata `vertical_z` (+Z global), polarização de referência local +Z e escala elétrica fixa **-12.320751 V/T**. Um cuboide médio é comparado com cinco cuboides médios encostados em X; a soma dos campos é calculada sem novo ajuste. Os campos em T são campos de **referência matemática para polarização de 1 T**, não medições absolutas calibradas. Não se aplica conversão em mT aos dados Hall nesta comparação.

[Tabela dos 30 pares com tensões, referências, ΔV, campos de referência, previsões, resíduos e razões](comparacao-grade-um-cinco-imans.csv) · [mapas medidos](comparacao-grade-um-cinco-imans-medido.png) · [mapas calculados](comparacao-grade-um-cinco-imans-modelo.png) · [mapas de resíduos](comparacao-grade-um-cinco-imans-residuos.png).

## Métricas (volts)

| Configuração | MAE | RMSE |
| --- | ---: | ---: |
| Um ímã | 0.048615 | 0.081033 |
| Cinco · referência inicial | 0.136766 | 0.214953 |
| Cinco · referência final | 0.135345 | 0.214252 |
| Cinco · média ilustrativa | 0.135510 | 0.214504 |
| Diferença 5 − 1 · média ilustrativa | 0.086932 | 0.141016 |

## Diferenças observadas e razão

A referência dos cinco caiu **-0.013015 V** entre início e fim; portanto, o ΔV calculado com a referência final é algebricamente maior em 0,013015 V para cada posição, e a diferença 5 − 1 também muda por esse valor. A tabela mostra ambos os extremos. A deriva da referência do ímã único varia por lado e pelo reteste e consta por linha. Em X=5, Y=0 mm, o lado 1 tem ΔV de **+0,7784 V** com um ímã e **+0,6001 V** com cinco (referência média ilustrativa); o lado 2 tem **−0,6482 V** e **−0,6247 V**. Em Y=±10 mm e X=5, o módulo da resposta de cinco também é menor. Em X=50 mm, as respostas são pequenas e a deriva de 0,013015 V da fileira pode mudar sua interpretação de sinal. Nas seis coordenadas de X=5 mm, o módulo de ΔV da fileira é menor que o do ímã único sob a referência média ilustrativa; a tendência não é uniforme nas distâncias maiores. Essas diferenças são observações em volts sob as referências indicadas, não uma estimativa calibrada de campo.

A razão `ΔV_cinco_intermediário / ΔV_um` foi calculada em **18/30** posições. Critério conservador: `|ΔV_um| > 2 × max(|deriva da referência de um|, |deriva da referência de cinco|)`. O fator 2 é uma regra exploratória para afastar denominadores pequenos, não um limite estatístico. Nas demais posições, a razão aparece como inconclusiva; nesta grade, são os 12 pontos em X=30 e 50 mm. Mesmo onde calculada, a razão não mede quantas vezes o campo físico aumentou.

## Limitações

A fileira tem faces encostadas, mas as larguras individuais e a magnetização/polaridade de cada peça não foram medidas. O eixo sensível real do SS49E, a distância entre a marca X=0 e seu elemento interno, a altura e a orientação exata entre coletas permanecem hipóteses. As 30 médias da fileira resumem leituras individuais indisponíveis; não permitem estimar variância ponto a ponto. A deriva observada não determina a referência de cada instante. As escalas e geometrias foram herdadas para comparação exploratória, sem calibração ou validação independente.
