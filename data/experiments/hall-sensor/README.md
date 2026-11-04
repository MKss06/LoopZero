# Experimento com sensor Hall 49E

O experimento inicial usa um sensor Hall 49E conectado ao Arduino UNO para observar a saída analógica em função da distância nominal em duas orientações do mesmo ímã de neodímio. As distâncias informadas são **0, 5, 10, 15, 20, 30, 40 e 50 mm**.

## Planilha recebida

[`loopzero_hall_tensao_distancia.xlsx`](loopzero_hall_tensao_distancia.xlsx) é uma cópia sem alterações do arquivo fornecido. SHA-256 do original e da cópia: `d536ed2305b905a90187ce3de6868d18bbe4fc173b43d43379bd4288e16b4958`. Preserve-a como fonte recebida; ela própria informa que as leituras foram **transcritas de mensagens ADC/Tensao**, que linhas incompletas sem ADC foram omitidas e que leituras anteriores à série final retomada no chat foram excluídas. Portanto, não equivale a um registro integral e direto da saída do instrumento.

A aba **Leituras** contém **904 linhas válidas**: 831 com ímã nas oito distâncias nominais, para os dois lados, e 73 referências sem ímã (51 do lado 1 e 22 do lado 2). Cada linha registra lado, distância nominal quando aplicável, número da amostra dentro do grupo, ADC, tensão Hall em volts e condição. A aba **Comparação** calcula média de tensão, diferença para a referência sem ímã do mesmo lado (`ΔV` em mV) e número de leituras. As referências médias exibidas são aproximadamente **2,605196 V** (lado 1) e **2,614545 V** (lado 2). Esses valores são saídas do sensor; `ΔV` não é campo magnético.

A [análise reproduzível](../../processed/hall-sensor/resumo.md) e suas curvas ficam em `data/processed/hall-sensor/`. O script lê esta planilha sem alterá-la e verifica todos os valores agregados contra `Comparação`.

Uma [comparação horizontal com Magpylib](../../processed/hall-sensor/comparacao-horizontal.md) usa ΔV em volts. As leituras em **0 mm nominal são medições reais**; somente as tensões calculadas pelo modelo nesse ponto ficam fora do ajuste de 5–50 mm. O modelo não fornece magnetização medida nem campo calibrado em mT.

As notas da planilha esclarecem que **0 mm é uma posição nominal**, sem distância confirmada até o elemento sensível do Hall, e que no **lado 2 o ímã foi virado**. A planilha não informa data da coleta, identificação do ímã entre os dez medidos, calibração tensão-campo nem a geometria completa do elemento sensível. Não atribua essas informações por inferência.

O esclarecimento posterior da montagem informa que o elemento Hall preto permaneceu fixo na ponta do módulo, voltado para o ímã; o ímã se moveu **horizontalmente** de 50 para 0 mm. No lado 2, a face antes apoiada na superfície ficou para cima. A face que ficou para cima não se tornou automaticamente a face de aproximação horizontal ao Hall. O [esquema e a comparação horizontal](../../processed/hall-sensor/comparacao-horizontal.md) usam essa descrição; a altura exata do elemento sensível e seu eixo de leitura permanecem pendentes. A associação “lado 1 = Sul; lado 2 = Norte” depende da resposta do AH49E e da orientação da face marcada e não constitui medição confirmada dos polos.

Conforme o **esquema B** descrito para a montagem, o lado maior do ímã estava deitado e o movimento de aproximação era perpendicular ao sensor. Isso define uma relação de orientação e trajetória, não qual dimensão do cuboide coincide com a direção de aproximação. A identidade do ímã usado entre os dez da tabela é desconhecida. Também faltam a posição do elemento sensível, a distância geométrica correspondente a cada marca de medição e a magnetização do ímã.

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
