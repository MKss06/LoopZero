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

`src/hall_analysis.py` lê diretamente as 904 linhas da aba `Leituras`, calcula referências sem ímã separadas por lado e gera médias e `ΔV = (média com ímã − referência do lado) × 1000`, em mV. Antes de escrever resultados, confere os valores contra a aba `Comparação`. Os arquivos derivados ficam em [`data/processed/hall-sensor/`](../../data/processed/hall-sensor/): tabela CSV, curvas de tensão e ΔV, e um resumo com proveniência e limites da interpretação. Nenhum campo magnético é calculado nessa análise.

Para reproduzir a partir da raiz do repositório:

```powershell
.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_analysis.py
```

## Comparação com aproximação horizontal

`src/compare_hall_mountings.py` representa a **aproximação horizontal** descrita para o ensaio: Z é vertical à superfície, X é a trajetória, o Hall está fixo e o comprimento do ímã fica horizontal ao longo de Y. Quando a distância cai de 50 para 0 mm, apenas o ímã se move em −X. Para o lado 2, ele gira 180° em torno do comprimento; a face antes apoiada fica para cima. A hipótese provisória de polarização através da espessura permanece `(0,0,+1)` T nos eixos locais da mesma peça e gira com ela.

O [esquema](../../data/processed/hall-sensor/esquema-montagem-horizontal.svg) é gerado antes do ajuste. A altura do elemento Hall, o zero geométrico e o eixo sensível não foram medidos; o script explicita as duas primeiras hipóteses como parâmetros e compara as projeções candidatas X (frente do módulo), Z (vertical) e Y (comprimento). Usa as 904 leituras, ajusta uma escala comum aos lados para cada projeção não nula nas 14 médias de 5 a 50 mm e mostra 0 mm separadamente. Veja o [relatório, resíduos, tabela e gráficos](../../data/processed/hall-sensor/comparacao-horizontal.md). Um erro menor dentro dessas hipóteses não confirma eixo sensível, magnetização ou polos Norte/Sul.

As médias de 0 mm são **tensões medidas** na planilha. Os valores para 0 mm desenhados ou tabulados pelo script Magpylib são **tensões calculadas**, fora do ajuste de 5–50 mm. A distância física ao elemento sensível, o eixo de leitura e a resposta elétrica real permanecem desconhecidos; não há campo calibrado em mT.

```powershell
.\.venv\Scripts\python.exe simulation/magnetic-field/src/compare_hall_mountings.py
```

## Sensibilidade à altura relativa e ao zero nominal

`src/hall_geometry_sensitivity.py` varia a altura do Hall **em relação ao centro do ímã** e o deslocamento horizontal entre distância nominal e lacuna física. A grade padrão cobre −2 a +2 mm e 0 a 6 mm, respectivamente, em passos de 0,25 mm; são intervalos exploratórios. Cada combinação ajusta somente uma escala efetiva comum aos lados para a projeção candidata Z, usando as 14 médias de 5 a 50 mm. As tensões **medidas** em 0 mm são preservadas e comparadas separadamente com as tensões **calculadas**, sem participar do ajuste. O limite nominal ADC de 0–5 V foi inferido dos dados; a faixa linear do AH49E não foi confirmada.

Veja o [mapa, as curvas, a grade e os resíduos](../../data/processed/hall-sensor/sensibilidade-geometrica-horizontal.md). O código rejeita deslocamento negativo e confere que o ponto Hall não fique dentro do cuboide. Várias combinações produzem erros próximos; a grade não mede altura nem identifica o zero físico.

```powershell
.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_geometry_sensitivity.py
```

Execute as verificações a partir da raiz do repositório:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s simulation/magnetic-field/tests -v
```
