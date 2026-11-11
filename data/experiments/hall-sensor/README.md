# Experimentos com sensor Hall Honeywell SS49E

O experimento inicial usa um sensor Hall 49E conectado ao Arduino UNO para observar a saída analógica em função da distância nominal em duas orientações do mesmo ímã de neodímio. As distâncias informadas são **0, 5, 10, 15, 20, 30, 40 e 50 mm**.

## Planilha recebida

[`loopzero_hall_tensao_distancia.xlsx`](loopzero_hall_tensao_distancia.xlsx) é uma cópia sem alterações do arquivo fornecido. SHA-256 do original e da cópia: `d536ed2305b905a90187ce3de6868d18bbe4fc173b43d43379bd4288e16b4958`. Preserve-a como fonte recebida; ela própria informa que as leituras foram **transcritas de mensagens ADC/Tensao**, que linhas incompletas sem ADC foram omitidas e que leituras anteriores à série final retomada no chat foram excluídas. Portanto, não equivale a um registro integral e direto da saída do instrumento.

A aba **Leituras** contém **904 linhas válidas**: 831 com ímã nas oito distâncias nominais, para os dois lados, e 73 referências sem ímã (51 do lado 1 e 22 do lado 2). Cada linha registra lado, distância nominal quando aplicável, número da amostra dentro do grupo, ADC, tensão Hall em volts e condição. A aba **Comparação** calcula média de tensão, diferença para a referência sem ímã do mesmo lado (`ΔV` em mV) e número de leituras. As referências médias exibidas são aproximadamente **2,605196 V** (lado 1) e **2,614545 V** (lado 2). Esses valores são saídas do sensor; `ΔV` não é campo magnético.

A [análise reproduzível](../../processed/hall-sensor/resumo.md) e suas curvas ficam em `data/processed/hall-sensor/`. O script lê esta planilha sem alterá-la e verifica todos os valores agregados contra `Comparação`.

## Grade de 30 posições

[`mapeamento_hall_grade.xlsx`](mapeamento_hall_grade.xlsx) é a cópia **sem alterações** da nova planilha fornecida (SHA-256 `9e319d3dd6cabaebb6a08f1ae7852fb8427609e24e9cdfd82415135228cfb83f`). Ela contém **30 posições**: dois lados, X nominal de 5, 10, 20, 30 e 50 mm, e Y nominal de −10, 0 e +10 mm. A aba `Médias por posição` registra contagem e média ADC de cada bloco serial, totalizando **1.342 amostras com ímã resumidas**, mais **126 amostras de referência resumidas** em blocos de início e fim. As leituras seriais individuais não estão na planilha; não é possível conferir cada média a partir delas.

A referência aplicada em cada lado é a média **não ponderada** das médias de início e fim. A tensão usa `ADC × 5/1023 V` com referência nominal de 5 V; ΔV usa a referência do lado, e a estimativa em mT usa 14 mV/mT típicos do SS49E, **sem calibração individual**. A [análise da grade](../../processed/hall-sensor/mapeamento-hall-horizontal.md) confere os valores das duas abas e compara os mapas com o cenário Magpylib horizontal anterior **sem novo ajuste**. X e Y são coordenadas nominais; a direção física e a origem de Y, a altura do Hall e o zero geométrico não foram verificados independentemente.

A [análise exploratória dos resíduos e de uma escala comum](../../processed/hall-sensor/mapeamento-hall-escala-exploratoria.md) usa as mesmas 30 posições, mantém os parâmetros geométricos e preserva o resultado com a escala anterior.

### Reteste de X=5 mm

[`mapeamento_hall_grade_revisado_x5.xlsx`](mapeamento_hall_grade_revisado_x5.xlsx) é a **nova fonte vigente** para a grade (SHA-256 `bfb6452d861a87b4c51acc3a07377e46d3301aa26b65477821cd8ae61045ed71`). Sua aba `Reteste X5` guarda os **seis blocos corrigidos**, as contagens e médias anteriores e as frequências dos códigos ADC do reteste. Esses seis blocos **substituem** os valores X=5 da primeira planilha; os outros 24 pontos e a primeira planilha permanecem preservados para histórico. Em X=5, ambos os lados usam a referência própria do reteste, média simples das referências inicial e final (534,344828 ADC); em X≥10 persistem as referências anteriores por lado.

O [relatório da revisão](../../processed/hall-sensor/mapeamento-hall-x5-revisado.md) apresenta os mapas vigentes, o histórico antes/depois e os resíduos com **escalas já publicadas, sem novo ajuste**. A grade vigente resume 1.313 amostras com ímã em 30 médias. As leituras seriais não têm ordem temporal na planilha.

Uma [análise exploratória posterior](../../processed/hall-sensor/mapeamento-hall-x5-escala-exploratoria.md) ajusta apenas uma escala elétrica comum aos dois lados nas 30 médias vigentes. As métricas desse ajuste são internas ao mesmo conjunto.

## Nova coleta: cinco ímãs lado a lado

[`mapeamento_cinco_imans.xlsx`](mapeamento_cinco_imans.xlsx) foi copiada sem alterações (SHA-256 `04b571c4addbc3dabd9efec2a6dfef5fb463fc77938764b68a3578bb001b1fea`). São **30 médias ADC** de blocos, em dois lados e posições X/Y, resumindo 1.331 leituras com ímãs; as leituras individuais não constam do arquivo. A referência sem ímã muda de 535,662921 ADC antes para 533 ADC depois. A nota da própria planilha informa que uma linha do bloco final foi inferida como ADC 533 a partir da tensão exibida. Sem tempo por posição, a [análise separada](../../processed/hall-sensor/mapeamento-cinco-imans-horizontal.md) compara ΔV com as duas referências, sem tratar a deriva como efeito magnético nem converter esta coleta para mT.

O experimentador confirmou que os cinco ímãs estavam encostados pelas faces, sem espaço entre eles, deitados pela espessura. A foto mostra a fileira em sequência no eixo de aproximação X, o módulo Hall fixo junto à marca X=0 e as posições Y como deslocamentos laterais. A grade contém X nominal = 5, 10, 20, 30 e 50 mm e Y = −10, 0 e +10 mm. O contato entre peças é confirmado; a largura individual das cinco peças, a distância ao elemento Hall interno, seu eixo sensível e a polaridade de cada ímã não foram medidos. O sensor foi identificado pelo experimentador como Honeywell SS49E; a tendência observada é aumento de tensão ao aproximar o lado 1 e diminuição no lado 2. A [ficha Honeywell](https://prod-edam.honeywell.com/content/dam/honeywell-edam/sps/siot/en-us/products/sensors/magnetic-sensors/linear-and-angle-sensor-ics/common/documents/sps-siot-ss39et-ss49e-ss59et-product-sheet-005850-3-en-ciid-50359.pdf) descreve resposta para os dois sentidos do campo; a correspondência física entre esses sinais e o eixo sensível da montagem permanece uma hipótese.

O [relatório consolidado](../../processed/hall-sensor/relatorio-consolidado.md) reúne a comparação horizontal com Magpylib em ΔV e a estimativa de campo por `ΔV (mV)/14`. As leituras em **0 mm nominal são medições reais**; somente os cálculos do modelo nesse ponto ficam fora do ajuste de 5–50 mm. O experimentador identificou o sensor como **Honeywell SS49E**, fornecido no kit Elegoo de 37 sensores. **14 mV/mT é a sensibilidade típica do fabricante; a unidade não foi calibrada individualmente.** O modelo não fornece magnetização medida nem campo calibrado.

As notas da planilha esclarecem que **0 mm é uma posição nominal**, sem distância confirmada até o elemento sensível do Hall, e que no **lado 2 o ímã foi virado**. A planilha não informa data da coleta, identificação do ímã entre os dez medidos, calibração tensão-campo nem a geometria completa do elemento sensível. Não atribua essas informações por inferência.

O esclarecimento posterior da montagem informa que o elemento Hall preto permaneceu fixo na ponta do módulo, voltado para o ímã; o ímã se moveu **horizontalmente** de 50 para 0 mm. No lado 2, a face antes apoiada na superfície ficou para cima. A face que ficou para cima não se tornou automaticamente a face de aproximação horizontal ao Hall. O [esquema e a comparação horizontal](../../processed/hall-sensor/comparacao-horizontal.md) usam essa descrição; a altura exata do elemento sensível e seu eixo de leitura permanecem pendentes. **Lado 1 = Sul; lado 2 = Norte** é a atribuição adotada nesta análise segundo a convenção da face sensível da ficha Honeywell, sem verificação independente dos polos.

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

A [comparação direta do mapa revisado do ímã único com a fileira](../../processed/hall-sensor/comparacao-grade-um-cinco-imans.md) usa as 30 coordenadas comuns e as referências próprias de cada coleta. Mantém a deriva da fileira explícita e compara tensão medida, ΔV e o campo de referência Magpylib sem tratar este último como campo calibrado.
