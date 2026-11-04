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

O repositório está na fase inicial. O módulo de campo magnético contém as dimensões médias, a montagem geométrica e uma [comparação horizontal em volts com Magpylib](data/processed/hall-sensor/comparacao-horizontal.md), ainda dependente de hipóteses não calibradas. A [análise de sensibilidade](data/processed/hall-sensor/sensibilidade-geometrica-horizontal.md) explora altura relativa e deslocamento do zero. A planilha Hall recebida está preservada em `data/experiments/hall-sensor/`; sua [análise reproduzível das tensões medidas](data/processed/hall-sensor/resumo.md), inclusive em 0 mm nominal, está em `data/processed/hall-sensor/`. As próximas tarefas são formalizar parâmetros e calibração, confirmar a geometria da coleta e definir interfaces entre módulos. Não há licença definida; a decisão cabe aos responsáveis pelo projeto.
