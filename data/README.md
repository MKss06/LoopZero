# Dados da pesquisa

`experiments/` guarda os arquivos recebidos e metadados da coleta. `processed/` guarda resultados derivados. Nunca altere um arquivo de origem após o registro; se houver correção, preserve o original e documente a nova versão. O arquivo do experimento Hall contém leituras transcritas e uma aba de resultados calculados; consulte suas notas de proveniência antes de analisá-lo.

`magnets/` contém a planilha original preservada e uma transcrição das dimensões individuais dos dez ímãs para a modelagem. São dados dimensionais, não medições de campo. As massas exibidas na planilha são valores calculados, não pesagens observadas.

`processed/hall-sensor/` contém médias, curvas e um resumo derivados da primeira planilha Hall por um script reproduzível. As curvas originais representam tensão e ΔV; as colunas adicionais em mT são estimativas condicionais pela sensibilidade típica do fabricante.

A [grade Hall de 30 posições](processed/hall-sensor/mapeamento-hall-horizontal.md) usa a segunda [planilha experimental preservada](experiments/hall-sensor/mapeamento_hall_grade.xlsx). A tabela e os mapas comparam as tensões agregadas ao cenário Magpylib horizontal já publicado, sem reajustar seus parâmetros. A planilha apresenta médias de blocos, não as leituras seriais individuais.

Um [estudo separado dos resíduos](processed/hall-sensor/mapeamento-hall-escala-exploratoria.md) compara a escala anterior com **uma escala elétrica comum exploratória**, ajustada às 30 posições, e mostra o erro por lado, X e Y. A comparação original com escala fixa continua disponível.

O [reteste vigente de X=5 mm](processed/hall-sensor/mapeamento-hall-x5-revisado.md) substitui **seis** posições da primeira grade; a [planilha revisada](experiments/hall-sensor/mapeamento_hall_grade_revisado_x5.xlsx) e a planilha anterior estão preservadas. Os mapas anteriores e a escala exploratória ajustada à primeira grade são **históricos**. A revisão compara as duas versões mantendo fixas as escalas já publicadas.

A [escala comum exploratória da grade vigente](processed/hall-sensor/mapeamento-hall-x5-escala-exploratoria.md) é ajustada somente às 30 posições revisadas. O relatório apresenta métricas e resíduos da escala fixa e da ajustada nos mesmos pontos; não constitui validação independente.

A [comparação com aproximação horizontal](processed/hall-sensor/comparacao-horizontal.md) usa o Hall fixo e a virada rígida do mesmo ímã. A tabela experimental preserva as tensões **medidas**, inclusive em 0 mm nominal; as tabelas do modelo rotulam separadamente as tensões **calculadas**. Os parâmetros ajustados não substituem medições físicas de magnetização ou calibração do Hall.

A [comparação em campo estimado](processed/hall-sensor/comparacao-campo-estimado-horizontal.md) apresenta `ΔV (mV)/14` ao lado da componente calculada pelo Magpylib. O experimentador identificou o sensor como Honeywell SS49E do kit Elegoo de 37 sensores. Os **14 mV/mT** são a sensibilidade típica do fabricante; a unidade não foi calibrada individualmente. As tensões e curvas originais continuam disponíveis no [relatório consolidado](processed/hall-sensor/relatorio-consolidado.md).

A [análise de sensibilidade geométrica](processed/hall-sensor/sensibilidade-geometrica-horizontal.md) explora altura relativa e deslocamento do zero, preservando 0 mm fora do ajuste. Os limites da grade são cenários de cálculo, não medidas da montagem.

Use nomes descritivos, por exemplo `aaaa-mm-dd_id-experimento_tipo.csv`, e acompanhe cada conjunto com documentação de origem, unidades, instrumento, condições, incertezas e procedimento. Evite dados pessoais e credenciais.
