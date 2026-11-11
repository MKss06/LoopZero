# Simulação de campo magnético

Área para modelar os campos estáticos dos ímãs permanentes e comparar previsões com dados experimentais. `src/` contém a leitura das dimensões e a montagem geométrica inicial; `tests/` verifica médias, unidades e orientação; `notebooks/` fica reservado para estudos exploratórios. Não há cálculo de campo validado.

## Ambiente

Use Python 3.12 a 3.14. A partir da raiz do repositório:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r simulation/magnetic-field/requirements.txt
```

Em Linux/macOS: `python3 -m venv .venv`, `source .venv/bin/activate` e o mesmo comando `pip`. As faixas de dependências iniciam uma série compatível para desenvolvimento; registre versões exatas no relatório de cada estudo reproduzível. O Magpylib 6 introduziu mudanças incompatíveis com exemplos da versão 5; consulte a documentação da versão instalada antes de adaptar código antigo.

## Convenções futuras

Documente a geometria, orientação e magnetização dos ímãs, sistema de coordenadas, unidades, hipóteses e versão das bibliotecas. Identifique claramente saídas de simulação e medições. Salve dados derivados em `data/processed/`, com referência aos dados brutos e ao script que os produziu.

## Dados e montagem inicial

[`data/magnets/dimensions.csv`](../../data/magnets/dimensions.csv) transcreve as dez linhas dimensionais da [planilha original](../../data/magnets/dimensoes-imas-original.xlsx) em milímetros. `src/magnet_geometry.py` calcula a média aritmética (**19,37 × 9,40 × 4,48 mm**). A conversão para SI ocorre antes da chamada a `magpylib.magnet.Cuboid`, que recebe `dimension=(0.01937, 0.00940, 0.00448)` no modelo do ensaio. A função `dimensions_for(magnet_id)` permite consultar uma linha individual para outros estudos, mas `build_hall_setup` usa sempre a média: nenhuma linha foi associada ao ensaio Hall. A massa na planilha é calculada a partir de uma densidade presumida e não é usada neste modelo.

Na função `build_hall_setup`, o eixo local X do ímã acompanha seu comprimento e deve ficar horizontal (Z global é vertical). O plano de referência do sensor é o XY local; sua normal é o Z local. As posições e orientações do `Cuboid` e do `Sensor` são entradas obrigatórias. A trajetória de aproximação é paralela à normal do sensor; `magnet_position_at` aceita um deslocamento **assinado** a partir de uma pose fornecida, sem converter uma distância nominal em distância real. A direção da trajetória vem da orientação do sensor, não da ordem comprimento/largura/espessura. Essas convenções codificam apenas a informação geométrica do esquema B.

Os parâmetros `magnetization_a_per_m` (vetor nos eixos locais do ímã), `hall_sensitive_axis_local` e `nominal_zero_to_sensitive_element_m` são `None` enquanto desconhecidos. O vetor de magnetização reúne direção e intensidade, sem valor suposto. O eixo sensível local do Hall é distinto da normal mecânica escolhida para o plano do sensor. O deslocamento entre o zero nominal e o elemento sensível não é inferido da planilha. Para uma simulação física completa, ainda são necessárias posições e orientações reais, alinhamento lateral, identificação da face na pose, calibração tensão-campo e incertezas. Não interprete a geometria isolada como uma previsão física validada.

A [planilha Hall](../../data/experiments/hall-sensor/loopzero_hall_tensao_distancia.xlsx) fornece leituras ADC e tensão para duas posições após a virada da mesma peça e distâncias **nominais**. Ela não fornece por si só magnetização, distância ao elemento sensível ou uma calibração que converta tensão em campo. A face antes apoiada ficou para cima no lado 2; a posição do Hall em relação à superfície continua pendente.

## Análise reproduzível das tensões

`src/hall_analysis.py` lê diretamente as 904 linhas da aba `Leituras`, calcula referências sem ímã separadas por lado e gera médias e `ΔV = (média com ímã − referência do lado) × 1000`, em mV. Antes de escrever resultados, confere os valores contra a aba `Comparação`. Os arquivos derivados ficam em [`data/processed/hall-sensor/`](../../data/processed/hall-sensor/): tabela CSV, curvas de tensão e ΔV, e um resumo com proveniência e limites da interpretação. A tabela também traz `ΔV (mV)/14` em mT como **estimativa condicional**. O experimentador identificou o sensor como Honeywell SS49E do kit Elegoo de 37 sensores; os 14 mV/mT são o valor típico do fabricante, sem calibração individual.

Para reproduzir a partir da raiz do repositório:

```powershell
.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_analysis.py
```

## Comparação com aproximação horizontal

`src/compare_hall_mountings.py` representa a **aproximação horizontal** descrita para o ensaio: Z é vertical à superfície, X é a trajetória, o Hall está fixo e o comprimento do ímã fica horizontal ao longo de Y. Quando a distância cai de 50 para 0 mm, apenas o ímã se move em −X. Para o lado 2, ele gira 180° em torno do comprimento; a face antes apoiada fica para cima. A hipótese provisória de polarização através da espessura permanece `(0,0,+1)` T nos eixos locais da mesma peça e gira com ela.

O [esquema](../../data/processed/hall-sensor/esquema-montagem-horizontal.svg) é gerado antes do ajuste. A altura do elemento Hall, o zero geométrico e o eixo sensível não foram medidos; o script explicita as duas primeiras hipóteses como parâmetros e compara as projeções candidatas X (frente do módulo), Z (vertical) e Y (comprimento). Usa as 904 leituras, ajusta uma escala comum aos lados para cada projeção não nula nas 14 médias de 5 a 50 mm e mostra 0 mm separadamente. Veja o [relatório, resíduos, tabela e gráficos](../../data/processed/hall-sensor/comparacao-horizontal.md). Um erro menor dentro dessas hipóteses não confirma eixo sensível, magnetização ou polos Norte/Sul.

As médias de 0 mm são **tensões medidas** na planilha. Os valores para 0 mm desenhados ou tabulados pelo script Magpylib são **tensões calculadas**, fora do ajuste de 5–50 mm. A distância física ao elemento sensível, o eixo de leitura e a resposta elétrica real permanecem desconhecidos; não há campo calibrado em mT.

`src/hall_field_estimate.py` compara a estimativa `ΔV (mV)/14` à componente candidata `Bz` do **modelo horizontal**, mantendo separado o campo calculado com polarização de referência de 1 T e o campo do modelo com escala efetiva ajustada nas 14 médias de 5–50 mm. Inclui as medições de 0 mm nominal, com o cálculo Magpylib nesse ponto identificado como extrapolação fora do ajuste. A conversão de 14 mV/mT decorre da [ficha técnica do SS49E Honeywell](https://prod-edam.honeywell.com/content/dam/honeywell-edam/sps/siot/en-us/products/sensors/magnetic-sensors/linear-and-angle-sensor-ics/common/documents/sps-siot-ss39et-ss49e-ss59et-product-sheet-005850-3-en-ciid-50359.pdf), que informa 1,4 mV/G típico a 25 °C; a unidade identificada pelo experimentador não foi calibrada individualmente. Veja a [tabela, o gráfico e o relatório](../../data/processed/hall-sensor/comparacao-campo-estimado-horizontal.md). O eixo sensível, a magnetização e a lacuna física permanecem hipóteses.

```powershell
.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_field_estimate.py
```

```powershell
.\.venv\Scripts\python.exe simulation/magnetic-field/src/compare_hall_mountings.py
```

## Sensibilidade à altura relativa e ao zero nominal

`src/hall_geometry_sensitivity.py` varia a altura do Hall **em relação ao centro do ímã** e o deslocamento horizontal entre distância nominal e lacuna física. A grade padrão cobre −2 a +2 mm e 0 a 6 mm, respectivamente, em passos de 0,25 mm; são intervalos exploratórios. Cada combinação ajusta somente uma escala efetiva comum aos lados para a projeção candidata Z, usando as 14 médias de 5 a 50 mm. As tensões **medidas** em 0 mm são preservadas e comparadas separadamente com as tensões **calculadas**, sem participar do ajuste. O limite nominal ADC de 0–5 V foi inferido dos dados; a faixa linear da unidade SS49E não foi confirmada.

O [relatório consolidado](../../data/processed/hall-sensor/relatorio-consolidado.md) reúne a montagem, os dados, os resultados já calculados e as limitações, sem ajuste adicional.

## Grade Hall de 30 posições

`src/hall_grid_analysis.py` lê a [nova planilha preservada](../../data/experiments/hall-sensor/mapeamento_hall_grade.xlsx), verifica as 30 posições e os cálculos em cache das abas `Mapa` e `Médias por posição`, e produz [tabela, mapas e relatório](../../data/processed/hall-sensor/mapeamento-hall-horizontal.md). A planilha contém médias de blocos seriais, não cada leitura individual. A referência aplicada é a média simples das médias de início e fim de cada lado, com contagens próprias. A tensão usa `ADC × 5/1023 V` nominal; o campo em mT é estimado por 14 mV/mT típicos do SS49E, sem calibração individual.

Para comparar a grade, o script **reutiliza** o cenário horizontal e a escala elétrica `−12.320751 V/T` publicados na comparação anterior, sem ajustar nenhum parâmetro à nova coleta. X é tratado como distância horizontal nominal e Y, provisoriamente, como deslocamento ao longo do comprimento; as coordenadas físicas, a altura do Hall, o eixo sensível e o zero real permanecem incertos. Os mapas mostram observado, calculado e resíduo em **volts** para ambos os lados.

```powershell
.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_grid_analysis.py
```

`src/hall_grid_scale_exploration.py` lê as mesmas 30 posições e compara os [resíduos por lado, X e Y](../../data/processed/hall-sensor/mapeamento-hall-escala-exploratoria.md) da escala fixa anterior com os de **uma escala elétrica comum exploratória** ajustada às médias da grade. O ajuste é por mínimos quadrados sem intercepto e com peso igual por posição. Geometria, projeção candidata, polarização de referência e referências sem ímã não mudam; a escala ajustada não é magnetização medida. A comparação com escala fixa continua salva separadamente.

**Histórico:** seis médias X=5 mm dessa primeira grade foram substituídas por um reteste. A escala `−6,831328 V/T` continua identificada como ajuste exploratório à **grade anterior**, não à revisada.

```powershell
.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_grid_scale_exploration.py
```

`src/hall_grid_x5_revision.py` lê a [planilha revisada](../../data/experiments/hall-sensor/mapeamento_hall_grade_revisado_x5.xlsx), verifica a distribuição dos códigos ADC e o histórico das seis substituições, e produz [mapas, tabela e relatório vigentes](../../data/processed/hall-sensor/mapeamento-hall-x5-revisado.md). Primeiro compara as 30 posições com a escala fixa `−12,320751 V/T` do modelo horizontal; também mostra a escala exploratória `−6,831328 V/T`, ajustada à grade anterior, apenas para rastreabilidade. **Nenhuma nova escala, geometria, orientação ou referência foi ajustada.** A referência de X=5 é a específica do reteste, conforme a própria planilha.

```powershell
.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_grid_x5_revision.py
```

`src/hall_grid_revised_scale_exploration.py` compara a mesma escala fixa com [uma nova escala comum exploratória](../../data/processed/hall-sensor/mapeamento-hall-x5-escala-exploratoria.md), ajustada sem intercepto às **30 posições vigentes**. O CSV traz resíduos por lado, X e Y; os mapas mostram ΔV medido, calculado e resíduos. O erro da escala ajustada é avaliado nesses mesmos pontos, sem validação independente. Geometria, orientação, eixo sensível e referências não mudam.

```powershell
.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_grid_revised_scale_exploration.py
```

## Nova coleta com cinco ímãs

`src/hall_five_magnets.py` confere as [30 médias e fórmulas da nova planilha](../../data/experiments/hall-sensor/mapeamento_cinco_imans.xlsx) e gera [relatório, CSV, mapas e curvas](../../data/processed/hall-sensor/mapeamento-cinco-imans-horizontal.md). A foto mostra o Hall fixo perto de X=0, cinco peças em sequência no eixo X e os deslocamentos Y laterais. O código já representa essa disposição: comprimentos em Y, centros separados pelas larguras médias em X e aproximação em −X. Os cuboides médios ficam com **separação entre faces zero**, como confirmado pelo experimentador, e mantêm a mesma polarização local provisória. As larguras individuais, a distância ao elemento sensível, o eixo sensível e os polos de cada peça não são conhecidos. A escala elétrica fixa `−12,320751 V/T`, o eixo candidato `vertical_z` (+Z global), a altura relativa e o zero nominal do modelo anterior são reutilizados, sem ajuste a esta coleta. No cenário, essa escala negativa transforma a componente modelada negativa do lado 1 em aumento de tensão e a positiva do lado 2 em diminuição; não estabelece a orientação sensível física do SS49E.

A referência sem ímã caiu de 535,662921 para 533 ADC. Como não há horário por posição e uma linha do bloco final foi inferida na fonte, o script mostra ΔV sob ambas as referências e uma referência intermediária apenas ilustrativa. Esta coleta não recebe conversão para mT.

```powershell
.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_five_magnets.py
```

Veja o [mapa, as curvas, a grade e os resíduos](../../data/processed/hall-sensor/sensibilidade-geometrica-horizontal.md). O código rejeita deslocamento negativo e confere que o ponto Hall não fique dentro do cuboide. Várias combinações produzem erros próximos; a grade não mede altura nem identifica o zero físico.

```powershell
.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_geometry_sensitivity.py
```

Execute as verificações a partir da raiz do repositório:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s simulation/magnetic-field/tests -v
```

`src/compare_single_five_grid.py` gera a [comparação direta das grades de um e cinco ímãs](../../data/processed/hall-sensor/comparacao-grade-um-cinco-imans.md). Lê a planilha revisada com o reteste X=5 mm e a coleta da fileira, cruza as 30 coordenadas, mantém as referências separadas e aplica a mesma escala fixa do modelo horizontal às duas configurações. Exporta tabela e mapas medidos, calculados e de resíduos sem reajustar parâmetros. A razão entre respostas só aparece quando o ΔV do ímã único supera duas vezes a maior deriva registrada nas referências das duas coletas; esse limite é descritivo, não estatístico.
