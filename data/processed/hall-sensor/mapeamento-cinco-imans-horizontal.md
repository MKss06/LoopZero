# Nova coleta Hall: fileira de cinco ímãs

Fonte preservada: [mapeamento_cinco_imans.xlsx](../../experiments/hall-sensor/mapeamento_cinco_imans.xlsx), SHA-256 `04b571c4addbc3dabd9efec2a6dfef5fb463fc77938764b68a3578bb001b1fea`. São **30 médias ADC** de blocos que resumem **1331 leituras com ímãs**. A planilha não contém essas leituras individuais. Todos os 30 valores de `tensão média = média ADC × 5/1023 V`, suas fórmulas e caches, consistência interna das contagens, referências e variação final–inicial foram conferidas. Sem as leituras individuais, não é possível auditar as médias nem as contagens de cada bloco. A tensão de 5 V é nominal, conforme a própria planilha.

## Referência sem ímã e deriva

Referência inicial escolhida: **535.662921 ADC** (89 leituras; 2.618098 V). Referência final: **533.000000 ADC** (42 leituras; 2.605083 V). Mudança final–inicial: **-2.662921 ADC** ou **-0.013015 V**. A nota da planilha diz que a primeira linha do bloco final estava cortada e foi **inferida como ADC 533** a partir da tensão exibida de cerca de 2,605 V; assim, a referência final e a deriva não são inteiramente observações diretas.

Como não há horário por posição, calculamos ΔV com **ambas as referências**, sem atribuir uma evolução temporal a cada média. A faixa entre elas é um cenário de deriva entre os dois valores registrados, não um intervalo de confiança nem garantia de que a referência sempre ficou dentro dela. A referência intermediária é a média aritmética dos extremos, usada somente para mapas e métricas descritivas. Nenhum campo em mT é inferido dos dados Hall.

## Modelo Magpylib sem novo ajuste

[Esquema dos eixos e da fileira assumida](mapeamento-cinco-imans-horizontal-esquema.svg). É uma vista de cálculo; não representa distâncias físicas medidas.

**Disposição informada pelo experimentador:** cinco ímãs lado a lado pelos comprimentos, deitados pela espessura. Para representá-la, usamos cinco cuboides idênticos com as dimensões médias dos dez ímãs (19,37 × 9,40 × 4,48 mm), comprimentos paralelos a +Y global, espessuras verticais, bordas longas contíguas **sem espaço entre as faces, conforme confirmado pelo experimentador**, centros separados pela largura média de **9,40 mm** ao longo de +X global. A **foto da montagem** mostra o Hall fixo junto à marca X=0 e a fileira seguindo o eixo de aproximação X; as marcas Y indicam deslocamentos laterais. O código coloca os cinco centros em +X e move a fileira em −X quando X nominal diminui. Como **convenção não medida**, X nominal é a lacuna entre o ponto sensível modelado e a borda da peça mais próxima; não se conhece a distância real até o elemento interno. A separação entre faces é zero, mas as larguras individuais das cinco peças não foram identificadas. Y nominal desloca a fileira lateralmente. Foram registradas as posições nominais X = 5, 10, 20, 30 e 50 mm e Y = −10, 0 e +10 mm. Isso não identifica quais peças foram usadas. Para o lado 2, as cinco peças giram rigidamente com seu vetor local de polarização +Z. Todos os vetores locais +Z iguais são hipótese provisória de magnetização através da espessura; não conhecemos a direção nem a intensidade reais, nem se os cinco ímãs tinham polos alinhados.

Reutilizamos o cenário anterior: centro do ímã a 2,24 mm da superfície como convenção geométrica, Hall na mesma altura relativa, deslocamento nominal–físico de 0 mm, projeção candidata `vertical_z` e escala elétrica fixa **-12.320751 V/T** de campo de referência para polarização matemática de 1 T. Essa escala efetiva veio do ensaio anterior com um único ímã; sua transferência para cinco peças pressupõe resposta elétrica comparável e magnetizações semelhantes, sem confirmação. Esses valores não foram reajustados à nova coleta nem são medidas de altura, zero físico, sensibilidade ou magnetização. O campo calculado do modelo é mostrado em T de referência, não como mT medidos pelo Hall.

### Auditoria da geometria implementada

| Aspecto | Código atual | Registro experimental |
| --- | --- | --- |
| Dimensões | Cinco cuboides iguais de 19,37 × 9,40 × 4,48 mm, média de dez peças dimensionadas | Não há identificação dimensional individual das cinco peças usadas |
| Centros e espaçamento | `x = X_nominal + 4,70 + (0, 9,40, 18,80, 28,20, 37,60) mm`; `y = −Y_nominal`; `z = 2,24 mm`; separação entre faces = 0 | Foto mostra a sequência em X, Hall junto a X=0 e Y lateral; contato entre faces confirmado pelo experimentador; distância ao elemento interno desconhecida |
| Lado 1 | Comprimento local X → +Y global; largura local Y → −X; espessura local Z → +Z | Eixos longos transversais à sequência de aproximação X na foto; face de apoio visível |
| Lado 2 | Giro rígido de 180° em torno do comprimento de cada peça: X local → +Y, Y local → +X, Z local → −Z; Hall fixo | A descrição do ensaio anterior com um ímã diz que a face apoiada ficou para cima; a nova planilha não registra como as cinco peças foram viradas nem sua ordem depois do giro |
| Magnetização | Cada cuboide tem `polarization=(0,0,+1)` T **local** como referência; o giro leva o vetor junto; as cinco contribuições são somadas | Polaridade, intensidade e uniformidade de cada peça não foram medidas |
| Leitura | Componente candidata vertical global `vertical_z`; escala elétrica −12,320751 V/T herdada do ensaio de um ímã | Eixo sensível, altura e distância física do elemento Hall não foram medidos nesta coleta |

O código mantém os cinco centros em +X ao gerar cada lado. Uma virada física da fileira como conjunto inverteria a ordem das peças; como os cinco cuboides do cenário são idênticos, essa permutação não altera o campo calculado, mas pode importar para cinco ímãs reais distintos. A **foto enviada pelo experimentador nesta conversa** mostra cinco barras com eixos longos paralelos e faces maiores voltadas para cima, em sequência na direção X. O módulo Hall está parado próximo à marca X=0; as marcas Y são laterais. Assim, a disposição geral implementada coincide com a foto, e **nenhuma posição de cuboide foi alterada** nesta revisão. A imagem não mede altura, posição interna do Hall ou polaridade das peças; também não estabelece a correspondência entre a face fotografada e os lados da planilha. A convenção de sinal `y = −Y_nominal` e a projeção `vertical_z` continuam hipóteses, não orientações sensíveis comprovadas. Esta foto não foi arquivada no repositório.

### Sinal elétrico e eixo candidato

O sensor foi identificado pelo experimentador como **Honeywell SS49E**. A [ficha técnica Honeywell](https://prod-edam.honeywell.com/content/dam/honeywell-edam/sps/siot/en-us/products/sensors/magnetic-sensors/linear-and-angle-sensor-ics/common/documents/sps-siot-ss39et-ss49e-ss59et-product-sheet-005850-3-en-ciid-50359.pdf) (tabela 1, figura 2 e desenho de polaridade) descreve resposta linear bipolar: o campo em um sentido aumenta a tensão em relação ao nulo; no sentido oposto a diminui. Na aproximação observada, a tensão **sobe no lado 1 e desce no lado 2**. Com a referência intermediária apenas ilustrativa, os três pontos de X=50 mm do lado 1 ainda ficam ligeiramente abaixo dela; o aumento descreve a tendência ao aproximar, não o sinal de cada ΔV contra toda referência. No cenário calculado, `vertical_z` é a componente **+Z global** (vertical à superfície), não o eixo X da trajetória. A polarização local +Z de referência produz componente modelada negativa no lado 1 e positiva no lado 2; a escala efetiva **-12.320751 V/T** inverte esses sinais e resulta em ΔV calculado positivo no lado 1 e negativo no lado 2 nas 30 posições. O sinal dessa escala depende do referencial e da polarização de referência escolhidos; não é uma medição do sinal físico da sensibilidade do SS49E. A foto mostra o encapsulamento junto a X=0, mas não fixa o eixo sensível do chip em relação a +Z, nem os polos dos cinco ímãs.

## Comparação em volts

[Tabela ponto a ponto com as duas referências](mapeamento-cinco-imans-horizontal-ponto-a-ponto.csv) · [Tabela de ΔV e campo de referência do modelo](mapeamento-cinco-imans-horizontal.csv) · [Mapas](mapeamento-cinco-imans-horizontal-mapas.png) · [Curvas com faixa de referência](mapeamento-cinco-imans-horizontal-curvas.png). Resíduo = ΔV observado sob cada referência − ΔV calculado pelo modelo. `Distância modelo–faixa` vale zero se o modelo cair entre os dois ΔV extremos; caso contrário, é a distância até o extremo mais próximo. A série intermediária não corrige a deriva.

| Referência aplicada | Posições | MAE (V) | RMSE (V) |
| --- | ---: | ---: | ---: |
| Inicial | 30 | 0.136766 | 0.214953 |
| Final | 30 | 0.135345 | 0.214252 |
| Intermediária ilustrativa | 30 | 0.135510 | 0.214504 |

| Lado, referência intermediária | Posições | MAE (V) | RMSE (V) |
| --- | ---: | ---: | ---: |
| Lado 1 | 15 | 0.146902 | 0.218069 |
| Lado 2 | 15 | 0.124118 | 0.210879 |

Mesmo escolhendo, para cada posição, o extremo de referência mais favorável ao modelo, a distância à faixa tem MAE **0.129548 V** e RMSE **0.210446 V**. O modelo cai na faixa das duas referências em **3/30** posições. Isso descreve apenas este cenário geométrico e de deriva; não identifica a montagem real.

- Lado 1, X=5 mm: no centro Y=0, ΔV intermediário +0.600052 V versus modelo +0.957279 V; em Y=+10 mm, +0.108211 V versus +0.592109 V.
- Lado 2, X=5 mm: no centro Y=0, ΔV intermediário -0.624708 V versus modelo -0.957279 V; em Y=+10 mm, -0.099100 V versus -0.592109 V.

### Tensão medida, tensão prevista e referência por posição

`V_prevista = V_referência_sem_ímã + ΔV_modelo`; `resíduo = V_medida − V_prevista`. As letras `i` e `f` indicam as referências inicial e final. Trocar somente a referência de **2.618098** para **2.605083 V** diminui a tensão total prevista e aumenta **cada** resíduo em **0.013015 V**. Isso é uma análise dos dois cenários de referência, não uma correção temporal conhecida.

| Lado | X | Y | V medida | V ref. i | V prevista i | Resíduo i | V ref. f | V prevista f | Resíduo f |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Lado 1 | 50 | +0 | 2.603421 | 2.618098 | 2.630425 | -0.027003 | 2.605083 | 2.617409 | -0.013988 |
| Lado 1 | 50 | +10 | 2.603590 | 2.618098 | 2.629995 | -0.026406 | 2.605083 | 2.616980 | -0.013390 |
| Lado 1 | 50 | -10 | 2.603617 | 2.618098 | 2.629995 | -0.026378 | 2.605083 | 2.616980 | -0.013363 |
| Lado 1 | 30 | +0 | 2.618642 | 2.618098 | 2.656866 | -0.038224 | 2.605083 | 2.643851 | -0.025209 |
| Lado 1 | 30 | +10 | 2.616969 | 2.618098 | 2.653861 | -0.036892 | 2.605083 | 2.640846 | -0.023877 |
| Lado 1 | 30 | -10 | 2.615708 | 2.618098 | 2.653861 | -0.038153 | 2.605083 | 2.640846 | -0.025138 |
| Lado 1 | 20 | +0 | 2.646628 | 2.618098 | 2.708553 | -0.061925 | 2.605083 | 2.695538 | -0.048910 |
| Lado 1 | 20 | +10 | 2.624119 | 2.618098 | 2.696372 | -0.072253 | 2.605083 | 2.683357 | -0.059238 |
| Lado 1 | 20 | -10 | 2.639440 | 2.618098 | 2.696372 | -0.056932 | 2.605083 | 2.683357 | -0.043917 |
| Lado 1 | 10 | +0 | 2.785924 | 2.618098 | 2.950052 | -0.164128 | 2.605083 | 2.937037 | -0.151113 |
| Lado 1 | 10 | +10 | 2.658180 | 2.618098 | 2.861605 | -0.203425 | 2.605083 | 2.848590 | -0.190410 |
| Lado 1 | 10 | -10 | 2.657313 | 2.618098 | 2.861605 | -0.204292 | 2.605083 | 2.848590 | -0.191276 |
| Lado 1 | 5 | +0 | 3.211642 | 2.618098 | 3.575377 | -0.363735 | 2.605083 | 3.562362 | -0.350720 |
| Lado 1 | 5 | +10 | 2.719802 | 2.618098 | 3.210207 | -0.490406 | 2.605083 | 3.197192 | -0.477391 |
| Lado 1 | 5 | -10 | 2.719212 | 2.618098 | 3.210207 | -0.490995 | 2.605083 | 3.197192 | -0.477980 |
| Lado 2 | 50 | +0 | 2.599139 | 2.618098 | 2.605772 | -0.006633 | 2.605083 | 2.592757 | +0.006382 |
| Lado 2 | 50 | +10 | 2.600380 | 2.618098 | 2.606201 | -0.005822 | 2.605083 | 2.593186 | +0.007194 |
| Lado 2 | 50 | -10 | 2.597344 | 2.618098 | 2.606201 | -0.008857 | 2.605083 | 2.593186 | +0.004158 |
| Lado 2 | 30 | +0 | 2.582776 | 2.618098 | 2.579331 | +0.003445 | 2.605083 | 2.566315 | +0.016460 |
| Lado 2 | 30 | +10 | 2.591013 | 2.618098 | 2.582335 | +0.008677 | 2.605083 | 2.569320 | +0.021693 |
| Lado 2 | 30 | -10 | 2.588234 | 2.618098 | 2.582335 | +0.005898 | 2.605083 | 2.569320 | +0.018914 |
| Lado 2 | 20 | +0 | 2.547526 | 2.618098 | 2.527644 | +0.019882 | 2.605083 | 2.514629 | +0.032898 |
| Lado 2 | 20 | +10 | 2.557284 | 2.618098 | 2.539824 | +0.017460 | 2.605083 | 2.526809 | +0.030475 |
| Lado 2 | 20 | -10 | 2.556850 | 2.618098 | 2.539824 | +0.017026 | 2.605083 | 2.526809 | +0.030041 |
| Lado 2 | 10 | +0 | 2.361181 | 2.618098 | 2.286145 | +0.075036 | 2.605083 | 2.273129 | +0.088051 |
| Lado 2 | 10 | +10 | 2.539212 | 2.618098 | 2.374592 | +0.164620 | 2.605083 | 2.361577 | +0.177635 |
| Lado 2 | 10 | -10 | 2.542226 | 2.618098 | 2.374592 | +0.167635 | 2.605083 | 2.361577 | +0.180650 |
| Lado 2 | 5 | +0 | 1.986882 | 2.618098 | 1.660819 | +0.326063 | 2.605083 | 1.647804 | +0.339078 |
| Lado 2 | 5 | +10 | 2.512490 | 2.618098 | 2.025989 | +0.486501 | 2.605083 | 2.012974 | +0.499517 |
| Lado 2 | 5 | -10 | 2.514269 | 2.618098 | 2.025989 | +0.488279 | 2.605083 | 2.012974 | +0.501295 |

### O que cabe na deriva registrada

Em **3/30** posições, a previsão fica entre as duas tensões calculadas com as referências registradas: Lado 2, X=50, Y=+0 mm, Lado 2, X=50, Y=+10 mm, Lado 2, X=50, Y=-10 mm. Nas outras **27/30**, a escolha entre esses dois extremos não elimina o resíduo do cenário. Em X=5 mm, a menor distância do modelo à faixa é **0.326063 V**, muito acima dos **0.013015 V** de mudança de referência. Para sinais pequenos em X=50 mm, essa mudança pode ser da mesma ordem da resposta. A faixa dos dois valores não é intervalo de confiança e não garante que a linha de base real permaneceu entre eles; portanto, a classificação não prova a causa de cada discrepância.

### Verificação mínima antes de repetir a grade

A maior incerteza física é a pose relativa da fileira e do elemento Hall: qual borda fica próxima, larguras individuais, altura e significado físico de X=5 mm e Y=0. Também faltam o eixo sensível do Hall e a orientação/polaridade de cada ímã; a escala herdada de um único ímã não substitui essas informações. A foto já recebida mostra a disposição geral; antes de uma grade completa, registre **uma foto da posição real de medição com régua e vista lateral**, marcando a borda mais próxima, o elemento Hall e o sentido de X/Y. Marque o sentido de polo de cada peça com uma referência simples, sem tratar essa checagem como medida de intensidade. Depois faça apenas **três posições em X=5 mm, lado 1, Y=−10, 0, +10 mm**, com leitura sem ímã imediatamente antes e depois, guardando ADC individual e horário. Esse perfil curto testa o maior desacordo lateral e separa melhor uma mudança de referência de uma mudança de forma espacial; se persistir, confirme a pose e os polos antes de repetir as 30 posições.

## Limitações

Sem ordem temporal das médias, leituras individuais, posição física do Hall, geometria real da fileira, orientação sensível confirmada e caracterização de cada magnetização, o resíduo não separa deriva elétrica, diferenças entre os ímãs e erro de geometria. A conversão `ΔV/14 mV/mT` não foi aplicada: além de ser uma sensibilidade típica e não calibração individual, o ΔV por posição depende da referência incerta durante esta coleta. A planilha e todos os resultados das coletas anteriores foram preservados.

Reproduza com `.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_five_magnets.py`.
