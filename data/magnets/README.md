# Dimensões dos ímãs

`dimensoes-imas-original.xlsx` é uma cópia byte a byte da planilha **“Dimensões_ímãs.xlsx”** fornecida para a pesquisa. SHA-256 da cópia e do arquivo de origem: `8d7444b9b8657911bb5ea1d53b1a0a18b9fc840c7f2ee9cf0c8cdbf6711034dd`. Preserve esse arquivo como fonte original. `dimensions.csv` transcreve as dez linhas dimensionais da aba “Medições dos Ímãs” para leitura simples pelo código. Os valores estão em milímetros, na ordem comprimento (`length_mm`), largura (`width_mm`) e espessura (`thickness_mm`). `magnet_id` identifica somente a linha da tabela.

As médias aritméticas dos dez registros são **19,37 × 9,40 × 4,48 mm**. O módulo de campo magnético converte os valores para metros antes de criar o `magpylib.magnet.Cuboid`.

A planilha também tem uma coluna **Massa (g)**. Seus valores são fórmulas, com o cálculo `comprimento_mm × largura_mm × espessura_mm × 7,5 / 1000`, equivalente a assumir densidade de **7,5 g/cm³**. A média exibida é **6,11457825 g**. Essas massas são **estimativas derivadas**, não pesagens registradas; a planilha não documenta uma medição ou a origem da densidade adotada. A coluna **Observações** está vazia nas dez linhas. Massa e densidade não são entradas do modelo inicial de campo magnético.

A planilha não informa qual desses dez ímãs foi usado no experimento Hall. Portanto, não se deve ligar um `magnet_id` específico àquele ensaio sem nova evidência.
