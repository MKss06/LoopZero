# Estimativa condicional de campo × Magpylib horizontal

O experimentador identificou o sensor como Honeywell SS49E do kit Elegoo de 37 sensores. **14 mV/mT é a sensibilidade típica adotada da ficha Honeywell; esta unidade não foi calibrada individualmente.** A ficha técnica indica 1,4 mV/G a 25 °C, que equivale a 14 mV/mT: [fonte](https://prod-edam.honeywell.com/content/dam/honeywell-edam/sps/siot/en-us/products/sensors/magnetic-sensors/linear-and-angle-sensor-ics/common/documents/sps-siot-ss39et-ss49e-ss59et-product-sheet-005850-3-en-ciid-50359.pdf). O campo abaixo é **estimado a partir de tensões**, não medido por um instrumento calibrado. Sinais em mT seguem a convenção de ΔV; o sentido físico depende do eixo sensível e da resposta elétrica reais.

Fonte experimental preservada: `data/experiments/hall-sensor/loopzero_hall_tensao_distancia.xlsx` (SHA-256 `d536ed2305b905a90187ce3de6868d18bbe4fc173b43d43379bd4288e16b4958`). As 904 leituras e as referências sem ímã por lado foram conferidas contra a aba `Comparação`. `B_estimado = ΔV (mV) / 14`. As [tensões e curvas originais](resumo.md) continuam em V/mV.

## Hipóteses do cálculo

O [modelo horizontal](comparacao-horizontal.md) mantém o Hall fixo, o ímã em movimento em −X e a virada rígida entre lados. O comprimento está em +Y, a espessura em Z e a magnetização atravessando a espessura é hipótese provisória. A polarização local de +1 T é somente a referência numérica usada pelo Magpylib, não uma medida.

A componente escolhida é **Bz global**, candidato para o eixo sensível do Hall, que permanece desconhecido. O Hall é colocado na mesma altura do centro do ímã (altura relativa 0 mm) e o deslocamento físico − nominal é 0 mm. Assim, a lacuna física no cenário é `distância nominal + 0 mm`. Altura e deslocamento são hipóteses, não cotas medidas. A [análise de sensibilidade geométrica](sensibilidade-geometrica-horizontal.md) mostra outras combinações.

Nas 14 médias de 5–50 mm foi ajustada apenas uma escala elétrica comum aos lados, sem intercepto. Dividi-la pelos 14 V/T assumidos resulta em um fator efetivo assinado de **-0.880054** para a componente de referência de 1 T. Esse fator mistura magnetização, sensibilidade real, orientação e geometria. Não é magnetização medida nem calibração do sensor. MAE = **1.035 mT** e RMSE = **1.184 mT** apenas na escala condicional de 14 mV/mT, para os pontos de ajuste.

[Gráfico](comparacao-campo-estimado-horizontal.png) · [Tabela CSV completa](comparacao-campo-estimado-horizontal.csv). A componente bruta Magpylib é mostrada separadamente da versão com escala efetiva; nenhuma das duas é campo medido. Resíduo = estimativa de ΔV − modelo escalado.

| Lado | d nominal (mm) | ΔV medido (V) | Campo estimado (mT; SS49E típico, não calibrado) | Bz Magpylib, 1 T ref. (mT; não medido) | Bz escalado (mT; não calibrado) | Resíduo (mT) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Lado 1 | 5 | +0.774637 | +55.331 | -64.100 | +56.412 | -1.080 |
| Lado 1 | 10 | +0.263223 | +18.802 | -19.413 | +17.084 | +1.717 |
| Lado 1 | 15 | +0.121090 | +8.649 | -8.250 | +7.261 | +1.389 |
| Lado 1 | 20 | +0.083012 | +5.929 | -4.231 | +3.723 | +2.206 |
| Lado 1 | 30 | +0.024182 | +1.727 | -1.540 | +1.355 | +0.372 |
| Lado 1 | 40 | +0.014387 | +1.028 | -0.723 | +0.636 | +0.391 |
| Lado 1 | 50 | +0.008604 | +0.615 | -0.395 | +0.348 | +0.267 |
| Lado 2 | 5 | -0.781652 | -55.832 | +64.100 | -56.412 | +0.579 |
| Lado 2 | 10 | -0.263278 | -18.806 | +19.413 | -17.084 | -1.721 |
| Lado 2 | 15 | -0.118250 | -8.446 | +8.250 | -7.261 | -1.186 |
| Lado 2 | 20 | -0.072564 | -5.183 | +4.231 | -3.723 | -1.460 |
| Lado 2 | 30 | -0.029045 | -2.075 | +1.540 | -1.355 | -0.720 |
| Lado 2 | 40 | -0.019282 | -1.377 | +0.723 | -0.636 | -0.741 |
| Lado 2 | 50 | -0.014101 | -1.007 | +0.395 | -0.348 | -0.659 |

## 0 mm nominal: medição real e cálculo separado

As tensões em 0 mm são medições reais da planilha. O campo estimado vem dessas medições e da sensibilidade típica assumida; o valor Magpylib nesse ponto é extrapolação **calculada**, fora do ajuste de 5–50 mm. Não foi uma previsão fornecida pelo experimentador. Os módulos estimados de 119,4 e 107,3 mT ultrapassam a faixa magnética típica de ±100 mT indicada na ficha do SS49E Honeywell; a extrapolação linear do chip do kit nessa posição não está validada.

| Lado | ΔV medido (V) | Campo estimado (mT; SS49E típico, não calibrado) | Bz Magpylib, 1 T ref. (mT; não medido) | Bz escalado extrapolado (mT; não calibrado) |
| --- | ---: | ---: | ---: | ---: |
| Lado 1 | +1.671804 | +119.415 | -396.642 | +349.066 |
| Lado 2 | -1.501611 | -107.258 | +396.642 | -349.066 |

A concordância em 5–50 mm caracteriza somente a forma das curvas sob este cenário. A divergência em 0 mm indica que a extrapolação geométrica e a resposta elétrica não estão resolvidas. A conversão por 14 não acrescenta uma medição independente: os resíduos em mT são os resíduos em mV divididos por 14. Eixo sensível e sinal do Hall, magnetização, altura relativa e deslocamento do zero ainda precisam ser determinados.

Reproduza com `.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_field_estimate.py`.
