# Dados da pesquisa

`experiments/` guarda os arquivos recebidos e metadados da coleta. `processed/` guarda resultados derivados. Nunca altere um arquivo de origem após o registro; se houver correção, preserve o original e documente a nova versão. O arquivo do experimento Hall contém leituras transcritas e uma aba de resultados calculados; consulte suas notas de proveniência antes de analisá-lo.

`magnets/` contém a planilha original preservada e uma transcrição das dimensões individuais dos dez ímãs para a modelagem. São dados dimensionais, não medições de campo. As massas exibidas na planilha são valores calculados, não pesagens observadas.

`processed/hall-sensor/` contém médias, curvas e um resumo derivados da planilha Hall por um script reproduzível. As curvas representam tensão e ΔV, sem conversão para campo magnético.

A [comparação com aproximação horizontal](processed/hall-sensor/comparacao-horizontal.md) usa o Hall fixo e a virada rígida do mesmo ímã. A tabela experimental preserva as tensões **medidas**, inclusive em 0 mm nominal; as tabelas do modelo rotulam separadamente as tensões **calculadas**. Os parâmetros ajustados não substituem medições físicas de magnetização ou calibração do Hall.

A [análise de sensibilidade geométrica](processed/hall-sensor/sensibilidade-geometrica-horizontal.md) explora altura relativa e deslocamento do zero, preservando 0 mm fora do ajuste. Os limites da grade são cenários de cálculo, não medidas da montagem.

Use nomes descritivos, por exemplo `aaaa-mm-dd_id-experimento_tipo.csv`, e acompanhe cada conjunto com documentação de origem, unidades, instrumento, condições, incertezas e procedimento. Evite dados pessoais e credenciais.
