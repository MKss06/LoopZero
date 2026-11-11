# LoopZero

O **LoopZero** é um projeto de pesquisa PIBIC vinculado à Universidade de Brasília (UnB). Investiga um sistema experimental de levitação magnética com uma pastilha supercondutora YBCO e ímãs permanentes de neodímio distribuídos em uma pista com geometria de fita de Möbius.

Este repositório reúne código, documentação, desenhos técnicos e dados da pesquisa. A estrutura inicial organiza o trabalho; ainda não representa um sistema validado ou resultados científicos.

## Objetivos da pesquisa

- Modelar e simular os campos dos ímãs e a dinâmica da pastilha.
- Projetar a pista, os circuitos de medição e os mecanismos de atuação.
- Investigar sensores, aquisição de dados e controle de aceleração e frenagem.
- Comparar previsões computacionais com medições reproduzíveis.
- Preparar a integração futura de um gêmeo digital.

## Tecnologias previstas

Python, Magpylib, NumPy, SciPy e Matplotlib para modelagem e análise; Arduino UNO, Arduino Mega e ESP32 para instrumentação; Fusion 360 para CAD. Backend Python, frontend e recursos de inteligência artificial são possibilidades futuras, sem arquitetura definida nesta etapa.

## Organização

| Diretório | Finalidade |
| --- | --- |
| `simulation/magnetic-field/` | Campos magnéticos dos ímãs e exploração numérica. |
| `simulation/dynamics/` | Modelos de movimento da pastilha. |
| `simulation/superconductivity/` | Hipóteses e modelos do comportamento supercondutor. |
| `firmware/` | Código embarcado por plataforma e tipo de sensor. |
| `control/` | Bobinas, atuação e algoritmos de controle. |
| `digital-twin/` | Integração futura de backend e frontend. |
| `hardware/` | Esquemas, CAD e componentes. |
| `data/experiments/` | Arquivos experimentais recebidos, preservados com notas de proveniência. |
| `data/processed/` | Dados derivados e rastreáveis. |
| `data/magnets/` | Dimensões individuais dos dez ímãs e sua proveniência. |
| `docs/` | Metodologia, protocolos, arquitetura e referências. |
| `tests/` | Testes de integração entre módulos, quando existirem. |

## Método de trabalho

O ciclo previsto é: registrar hipóteses e parâmetros; construir modelos computacionais; documentar a montagem e a calibração; coletar dados brutos com metadados; processar cópias desses dados; comparar medições e previsões, incluindo incertezas. Cada experimento deve ter protocolo e identificação próprios antes da análise. Os primeiros pontos de distância informados para o sensor Hall constam em [`data/experiments/hall-sensor/README.md`](data/experiments/hall-sensor/README.md).

## Desenvolvimento local

Para o módulo de campo magnético, use Python 3.12 a 3.14 e crie um ambiente virtual na raiz do repositório:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r simulation/magnetic-field/requirements.txt
```

Em Linux/macOS, substitua a ativação por `source .venv/bin/activate` e crie o ambiente com `python3 -m venv .venv`. A instalação é necessária apenas para quem trabalhar nesse módulo. Veja também o [README do módulo](simulation/magnetic-field/README.md).

## Estado e próximos passos

O repositório está na fase inicial. O [relatório consolidado do experimento Hall](data/processed/hall-sensor/relatorio-consolidado.md) reúne as tensões medidas, a comparação horizontal com Magpylib e o campo estimado. O experimentador identificou o sensor como Honeywell SS49E do kit Elegoo de 37 sensores; a conversão usa 14 mV/mT típicos da ficha do fabricante, sem calibração individual. A [análise de sensibilidade](data/processed/hall-sensor/sensibilidade-geometrica-horizontal.md) explora altura relativa e deslocamento do zero. A planilha Hall recebida está preservada em `data/experiments/hall-sensor/`, inclusive com as medições em 0 mm nominal. As próximas tarefas são formalizar parâmetros e calibração, confirmar a geometria da coleta e definir interfaces entre módulos. Não há licença definida; a decisão cabe aos responsáveis pelo projeto.

A [grade Hall de 30 posições](data/processed/hall-sensor/mapeamento-hall-horizontal.md) foi incorporada como **segunda coleta** em `data/experiments/hall-sensor/`. Seus mapas são comparados ao mesmo cenário Magpylib horizontal, com a escala anterior e sem novo ajuste. A planilha original permanece preservada.

Uma [análise exploratória dos resíduos da grade](data/processed/hall-sensor/mapeamento-hall-escala-exploratoria.md) compara essa escala fixa com uma única escala comum ajustada às 30 posições, sem mudar a geometria nem as referências experimentais.

O [reteste vigente de X=5 mm](data/processed/hall-sensor/mapeamento-hall-x5-revisado.md) substitui seis médias da grade anterior. As duas planilhas originais e os resultados anteriores permanecem como histórico. A nova comparação transporta as escalas já publicadas, sem ajustar a geometria ou a orientação.

A [nova análise exploratória da escala comum](data/processed/hall-sensor/mapeamento-hall-x5-escala-exploratoria.md) usa as 30 médias vigentes e compara o ajuste multiplicativo com a escala fixa, em volts. Seu erro é calculado nos próprios pontos do ajuste.

Uma [coleta adicional com cinco ímãs lado a lado](data/processed/hall-sensor/mapeamento-cinco-imans-horizontal.md) foi incorporada sem alterar as anteriores. Ela contém 30 médias ADC; o relatório compara um cenário Magpylib explícito em volts e trata a mudança da referência sem ímã como deriva possível, sem novo ajuste nem conversão para mT.

A [comparação direta das grades de um e cinco ímãs](data/processed/hall-sensor/comparacao-grade-um-cinco-imans.md) usa o reteste vigente de X=5 mm, cruza 30 posições por lado/X/Y e mostra diferenças medidas, previsões Magpylib e resíduos com referências separadas.
