# Relatório consolidado do experimento Hall

## Escopo e fontes

Este relatório reúne os dados e gráficos já produzidos no LoopZero. **Nenhum ajuste novo foi realizado.** A [planilha original](../../experiments/hall-sensor/loopzero_hall_tensao_distancia.xlsx) foi preservada (SHA-256 `d536ed2305b905a90187ce3de6868d18bbe4fc173b43d43379bd4288e16b4958`). Sua aba `Leituras` contém **904 observações**: 831 com ímã e 73 referências sem ímã. As 16 médias por lado e distância conferem com a aba `Comparação`.

O experimentador identificou o sensor como **Honeywell SS49E**, fornecido no kit Elegoo de 37 sensores. Essa identificação é informação do experimentador; este repositório não contém ensaio individual da sensibilidade da unidade. A [ficha técnica Honeywell, série SS39ET/SS49E/SS59ET, tabela 1 e figura 4](https://prod-edam.honeywell.com/content/dam/honeywell-edam/sps/siot/en-us/products/sensors/magnetic-sensors/linear-and-angle-sensor-ics/common/documents/sps-siot-ss39et-ss49e-ss59et-product-sheet-005850-3-en-ciid-50359.pdf) informa sensibilidade **típica de 1,4 mV/G a 25 °C** e mostra a convenção de polos na face sensível. Como `1 mT = 10 G`, a conversão adotada é **14 mV/mT**. Trata-se de conversão baseada na especificação do fabricante, **sem calibração individual**.

## Montagem e grandezas

O elemento Hall preto permaneceu fixo na ponta do módulo, voltado para o ímã. O **mesmo ímã** foi movido **horizontalmente** em direção ao sensor, de **50 a 0 mm nominais**. Para o lado 2, a peça foi virada rigidamente, de modo que a face antes apoiada na superfície ficou para cima; o Hall não se moveu. Virar a peça não significa que a face superior passou a apontar para o Hall. O [esquema da montagem e dos eixos](esquema-montagem-horizontal.svg) representa a trajetória: Z vertical, X horizontal na direção Hall–ímã e Y horizontal ao longo do comprimento assumido no modelo.

As dez peças da [planilha dimensional](../../magnets/dimensions.csv) têm média **19,37 × 9,40 × 4,48 mm** (comprimento × largura × espessura). O `magpylib.magnet.Cuboid` usa `(0.01937, 0.00940, 0.00448)` m. Não se sabe qual das dez peças foi usada na coleta.

Para cada lado, `ΔV = tensão média com ímã − referência sem ímã do mesmo lado`. As referências calculadas são **2,605196 V** (51 leituras, lado 1) e **2,614545 V** (22 leituras, lado 2). O campo é **estimado**, não medido diretamente: `B_estimado (mT) = ΔV (mV) / 14`. Seu sinal acompanha a variação de tensão na convenção de face sensível adotada. A [tabela integral das 16 médias](medias-por-distancia.csv) mantém as tensões em V, ΔV em mV e a coluna de campo estimado em mT.

| Lado | Distância nominal (mm) | Tensão média medida (V) | ΔV medido (V) | Campo estimado (mT; SS49E típico, sem calibração individual) |
| --- | ---: | ---: | ---: | ---: |
| 1 | 50 | 2,613800 | +0,008604 | +0,615 |
| 1 | 5 | 3,379833 | +0,774637 | +55,331 |
| 1 | **0** | **4,277000** | **+1,671804** | **+119,415** |
| 2 | 50 | 2,600444 | −0,014101 | −1,007 |
| 2 | 5 | 1,832894 | −0,781652 | −55,832 |
| 2 | **0** | **1,112934** | **−1,501611** | **−107,258** |

**As leituras em 0 mm nominal são medições reais.** A distância física entre a face próxima do ímã e o elemento sensível nessa marca não foi determinada. Os valores estimados de 119,4 e 107,3 mT em módulo ultrapassam a faixa magnética *típica* de ±100 mT citada para o SS49E na ficha Honeywell; a conversão linear nessa posição exige cautela.

## Resposta observada e atribuição de polos

Durante a aproximação, a tensão **aumentou no lado 1** e **diminuiu no lado 2**, em relação às respectivas referências sem ímã. Na convenção de polaridade indicada pela figura 4 da ficha Honeywell, **considerando a face sensível/face marcada do SS49E voltada para o ímã como assumido na interpretação da montagem**, o aumento corresponde à indicação de **Sul** e a diminuição à de **Norte**. Assim, **lado 1 = Sul; lado 2 = Norte é a atribuição adotada nesta análise**. Não houve verificação independente dos polos nem documentação que fixe com precisão o eixo sensível e a orientação da face marcada no instante da coleta. A atribuição se refere ao sinal visto pelo Hall nessa orientação, e não prova que a face lateral que se aproxima seja uma face polar do ímã.

As [curvas de tensão média](tensao-distancia.png) e de [ΔV](delta-v-distancia.png) mostram os resultados experimentais nas unidades originais. O [resumo das tensões](resumo.md) descreve a agregação e a proveniência.

## Comparação horizontal com Magpylib

A [comparação em volts](comparacao-horizontal.md), sua [tabela de previsões e resíduos](comparacao-horizontal.csv) e o [gráfico de 5–50 mm](comparacao-horizontal.png) usam o modelo horizontal: Hall fixo, ímã movendo-se em −X e virada rígida da mesma peça entre lados. A magnetização através da espessura, com vetor local preservado durante a virada, é **hipótese provisória**. Também são hipóteses o comprimento em Y, o alinhamento lateral e o eixo de leitura `vertical_z`. O modelo mantém outras projeções candidatas, pois o eixo sensível real não foi identificado geometricamente.

No cenário de referência, o Hall foi posto à altura do centro do ímã (**altura relativa 0 mm**) e o deslocamento entre lacuna física e distância nominal foi fixado em **0 mm**; nenhum desses valores foi medido. Uma escala efetiva comum aos dois lados foi ajustada somente às **14 médias de 5–50 mm**: para a projeção `vertical_z`, MAE **0,014489 V** e RMSE **0,016570 V**. A escala mistura magnetização, resposta elétrica e geometria; não mede magnetização.

A **atribuição Norte/Sul** acima pressupõe a orientação da face sensível em relação ao ímã. Ela não valida o eixo `vertical_z` usado na curva de melhor concordância deste cenário. Se o eixo sensível fosse normal à face do módulo voltada horizontalmente ao ímã, a projeção candidata seria `normal_x`; no cenário geométrico simétrico calculado, essa componente é nula no ponto do Hall. A orientação efetiva do chip no módulo e a geometria real precisam ser confirmadas antes de interpretar o ajuste `vertical_z` como a montagem física.

A [comparação em mT estimados](comparacao-campo-estimado-horizontal.md), com [tabela](comparacao-campo-estimado-horizontal.csv) e [gráfico](comparacao-campo-estimado-horizontal.png), confronta `ΔV/14` com a componente Bz calculada pelo mesmo modelo. Ela distingue o campo calculado com polarização **de referência** de 1 T da curva com escala efetiva. Na escala condicional de 14 mV/mT, o cenário de referência tem MAE **1,035 mT** e RMSE **1,184 mT** nos 14 pontos. A mudança de unidade não constitui evidência independente de concordância: esses erros são os resíduos em volts divididos pela sensibilidade assumida.

Os **dois pontos medidos em 0 mm** ficaram fora de todos esses ajustes. Para o cenário de referência, o cálculo extrapolado em 0 mm é **+4,886921 V** e **−4,886921 V** em ΔV, contra **+1,671804 V** e **−1,501611 V** medidos. A divergência é grande; o cálculo nesse ponto não foi uma previsão fornecida pelo experimentador. A [análise de sensibilidade geométrica já existente](sensibilidade-geometrica-horizontal.md) mostra que combinações distintas de altura relativa e deslocamento dão erros próximos entre 5 e 50 mm. Seu menor RMSE na grade é **0,006515 V** para altura relativa 0 mm e deslocamento 1,50 mm, ambos parâmetros exploratórios, não cotas identificadas.

## Alcance das conclusões

A inversão de sinal entre as duas posições da **mesma peça** e a queda do módulo de ΔV com a distância são fatos experimentais. O modelo horizontal reproduz qualitativamente essa inversão e aproxima as curvas de 5–50 mm sob as hipóteses declaradas. Os resíduos não identificam de forma única a magnetização, o eixo sensível, a altura do Hall, a lacuna física, a face polar do ímã nem a sensibilidade individual do sensor. A estimativa em mT usa a especificação típica Honeywell e não substitui uma calibração desta unidade.

## Nova coleta em grade

A [planilha adicional de 30 posições](../../experiments/hall-sensor/mapeamento_hall_grade.xlsx) e sua [comparação em mapas](mapeamento-hall-horizontal.md) foram incorporadas depois da primeira série. A grade cobre dois lados, X nominal de 5 a 50 mm e Y nominal de −10, 0 e +10 mm. Ela armazena **médias de blocos** (1.342 amostras com ímã resumidas e 126 referências resumidas), não as linhas seriais individuais. Seu relatório confere as fórmulas e confronta observado e calculado em volts reutilizando a escala anterior, **sem reajuste**. As definições físicas de X e Y no novo registro ainda precisam ser confirmadas.

Um [estudo exploratório posterior](mapeamento-hall-escala-exploratoria.md) analisa os resíduos por lado, X e Y e ajusta **somente uma escala comum** às 30 médias. Ele preserva a comparação anterior com escala fixa; a melhora de erro dentro dos pontos ajustados não identifica magnetização, geometria nem calibração do sensor.

**Atualização da grade:** os seis pontos de X=5 mm foram [retestados e substituídos](mapeamento-hall-x5-revisado.md). A grade anterior e o ajuste exploratório feito com ela agora são **históricos**. O relatório de reteste preserva os valores anteriores, confere a nova referência e compara mapas e resíduos com as escalas já publicadas, sem novo ajuste.

Uma [análise exploratória posterior da grade vigente](mapeamento-hall-x5-escala-exploratoria.md) ajusta um único fator elétrico comum aos dois lados nas 30 posições revisadas. Ela confronta resíduos e mapas com a escala fixa de −12,320751 V/T; os erros da escala ajustada são avaliados nos próprios pontos, sem validação independente nem interpretação como magnetização medida.
