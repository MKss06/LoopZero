# Escala elétrica comum na grade Hall vigente

Fonte: [planilha revisada](../../experiments/hall-sensor/mapeamento_hall_grade_revisado_x5.xlsx) (SHA-256 `bfb6452d861a87b4c51acc3a07377e46d3301aa26b65477821cd8ae61045ed71`). Usamos as **30 médias vigentes**, inclusive os seis retestes de X=5 mm; os valores substituídos não entram no ajuste. A [grade anterior e seu ajuste exploratório](mapeamento-hall-escala-exploratoria.md) permanecem históricos. As referências sem ímã são as conferidas na [revisão de X=5](mapeamento-hall-x5-revisado.md).

## Método e métricas

Cada posição tem peso igual. A componente candidata do campo calculada pelo Magpylib usa o mesmo modelo horizontal: Hall fixo, aproximação horizontal, virada rígida da mesma peça, polarização local +Z de referência (1 T matemático), projeção candidata `vertical_z`, altura relativa 0 mm e deslocamento nominal–físico 0 mm. Não foram ajustados geometria, orientação, eixo sensível ou referências. A escala é obtida por mínimos quadrados sem intercepto: `s = Σ(B_ref · ΔV) / Σ(B_ref²)`, com `B_ref` em T e `ΔV` em V, somando os **dois lados**.

Escala fixa anterior: **-12.320751 V/T**. Nova escala **exploratória, ajustada nestes mesmos 30 pontos**: **-9.413388 V/T**. Ela não é magnetização medida nem sensibilidade Hall calibrada; a avaliação a seguir é feita no próprio conjunto do ajuste e não é validação independente.

| Conjunto | Posições | MAE fixa (V) | RMSE fixa (V) | MAE exploratória (V) | RMSE exploratória (V) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ambos os lados | 30 | 0.048615 | 0.081033 | 0.026072 | 0.047484 |
| Lado 1 | 15 | 0.042080 | 0.068255 | 0.027284 | 0.052242 |
| Lado 2 | 15 | 0.055151 | 0.092054 | 0.024859 | 0.042193 |

No conjunto usado, o RMSE cai de 0.081033 para 0.047484 V (41.4%). Essa redução descreve somente o ajuste interno.

[Tabela com os 30 resíduos por lado, X e Y](mapeamento-hall-x5-escala-exploratoria.csv) · [Mapas de ΔV medido e calculado](mapeamento-hall-x5-escala-exploratoria-mapas.png) · [Mapas de resíduos](mapeamento-hall-x5-escala-exploratoria-residuos.png). Resíduo = ΔV medido − ΔV calculado, em volts. Os mapas usam a mesma escala de cor entre as variantes; as linhas X são posições discretas.

## Resíduos por lado e X nominal

| Lado e X | Posições | MAE fixa (V) | RMSE fixa (V) | MAE exploratória (V) | RMSE exploratória (V) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lado 1, X=5 mm | 3 | 0.104274 | 0.123236 | 0.086776 | 0.106862 |
| Lado 1, X=10 mm | 3 | 0.088410 | 0.089216 | 0.043790 | 0.047023 |
| Lado 1, X=20 mm | 3 | 0.010497 | 0.010735 | 0.002798 | 0.003230 |
| Lado 1, X=30 mm | 3 | 0.004931 | 0.005157 | 0.001881 | 0.001887 |
| Lado 1, X=50 mm | 3 | 0.002289 | 0.002321 | 0.001175 | 0.001242 |
| Lado 2, X=5 mm | 3 | 0.187014 | 0.189766 | 0.082762 | 0.087009 |
| Lado 2, X=10 mm | 3 | 0.079316 | 0.079340 | 0.034695 | 0.036000 |
| Lado 2, X=20 mm | 3 | 0.007091 | 0.007509 | 0.003792 | 0.005120 |
| Lado 2, X=30 mm | 3 | 0.002168 | 0.002616 | 0.002099 | 0.002772 |
| Lado 2, X=50 mm | 3 | 0.000165 | 0.000196 | 0.000949 | 0.000952 |

## Resíduos por lado e Y nominal

| Lado e Y | Posições | MAE fixa (V) | RMSE fixa (V) | MAE exploratória (V) | RMSE exploratória (V) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lado 1, Y=-10 mm | 5 | 0.055452 | 0.082540 | 0.023044 | 0.035433 |
| Lado 1, Y=+0 mm | 5 | 0.021043 | 0.037024 | 0.041471 | 0.079088 |
| Lado 1, Y=+10 mm | 5 | 0.049745 | 0.076109 | 0.017337 | 0.026025 |
| Lado 2, Y=-10 mm | 5 | 0.060684 | 0.100103 | 0.029057 | 0.048728 |
| Lado 2, Y=+0 mm | 5 | 0.044698 | 0.072231 | 0.016030 | 0.022628 |
| Lado 2, Y=+10 mm | 5 | 0.060070 | 0.100915 | 0.029491 | 0.049542 |

## Estrutura dos resíduos e limites

- Lado 1: maior resíduo absoluto após o ajuste em X=5 mm, Y=+0 mm: +0.174974 V.
- Lado 2: maior resíduo absoluto após o ajuste em X=5 mm, Y=+10 mm: +0.103505 V.

O modelo prevê valores iguais em Y=−10 e +10 mm para o mesmo lado e X; diferenças medidas entre essas posições, bem como padrões por distância, não podem ser removidos por uma escala multiplicativa comum. Os resíduos não identificam por si só a causa geométrica ou instrumental. A posição física do elemento Hall, seu eixo sensível, a magnetização da peça e a relação entre distância nominal e física continuam indeterminados. A conversão opcional de ΔV em mT usa 14 mV/mT típicos do SS49E, sem calibração individual; este ajuste permanece integralmente em volts.

Reproduza com `.\.venv\Scripts\python.exe simulation/magnetic-field/src/hall_grid_revised_scale_exploration.py`.
