# Experimento com sensor Hall 49E

O experimento inicial usa um sensor Hall 49E conectado ao Arduino UNO para observar a saída analógica em função da distância até faces opostas de um ímã de neodímio. As distâncias informadas são **0, 5, 10, 15, 20, 30, 40 e 50 mm**. Este diretório está preparado para os arquivos originais; nenhum valor de medição é presumido aqui.

Para cada coleta, registre em um arquivo de metadados associado:

- ID do experimento, data da coleta e responsável ou equipe;
- ID do ímã e identificação inequívoca da face medida;
- distância em milímetros e como ela foi medida, incluindo a referência do zero;
- leituras ADC originais e o modo de aquisição, incluindo quantidade de amostras;
- tensão em volts, método de conversão e tensão de referência do ADC;
- tensão de referência medida sem ímã, com condições dessa medição;
- placa, circuito, alimentação, orientação e demais condições de montagem;
- observações, fontes de incerteza, resolução e eventuais calibrações.

Prefira CSV em UTF-8 com cabeçalhos e unidades explícitas, por exemplo `distancia_mm`, `adc_contagem`, `tensao_v`. Se o equipamento fornecer outro formato, preserve-o. Não preencha campos com valores estimados como se fossem observados. Guarde análises e transformações em `../../processed/`, identificando os arquivos de origem e o procedimento de processamento.
