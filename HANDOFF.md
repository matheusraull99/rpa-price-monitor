# Briefing de transferência — PriceWatch RPA

> Cole este arquivo (ou seu conteúdo) no Claude Code / Cowork do seu computador
> para ele continuar o projeto a partir daqui.

## Contexto do projeto
Robô de RPA em **Python + Playwright** que monitora preços em `books.toscrape.com`
(sandbox público feito para scraping), valida os dados, e gera um **relatório Excel**
formatado (tabela estilizada, aba de resumo com KPIs e gráfico de barras).
Objetivo: peça de **portfólio** para chamar atenção de empresas no LinkedIn.

## Estado atual (já feito)
- Arquitetura limpa: Page Object Model, camadas `core / pages / models / services`.
- Resiliência: retry com backoff exponencial (Tenacity) + screenshot em falha.
- Config type-safe (Pydantic Settings via `.env`), logging estruturado (Loguru).
- Testes: 14 passando (`pytest`), lint limpo (`ruff`), CI no GitHub Actions.
- Docker e docker-compose prontos.
- **Repositório Git já inicializado com 1 commit** (branch `main`).
- Relatório de exemplo versionado em `output/sample_report.xlsx`.

## Decisão técnica importante (não refazer)
O relatório usa **XlsxWriter**, NÃO openpyxl. Motivo: o openpyxl 3.1.5 gravava
strings inline e não criava `xl/sharedStrings.xml`, o que quebrava visualizadores
de Excel baseados em JavaScript (erro "Cannot read properties of null
(reading 'getElementsByTagName')"). XlsxWriter sempre emite sharedStrings, então
abre em qualquer lugar. openpyxl ficou só como dependência de teste (lê e valida).

## Observação sobre execução
A execução ao vivo (`python -m pricewatch.main`) precisa de internet para acessar
o site-alvo. No ambiente onde foi criado a rede era restrita, então só a geração
do relatório foi validada com dados de amostra. Na sua máquina deve rodar completo.

## TAREFAS QUE QUERO QUE VOCÊ FAÇA
1. Verifique o ambiente: crie venv, instale `requirements.txt`, rode
   `playwright install chromium`, e confirme que `pytest` e `ruff check .` passam.
2. Rode o robô de verdade: `PYTHONPATH=src:. python -m pricewatch.main --pages 5`
   e confirme que o `.xlsx` é gerado em `output/`.
3. Me ajude a subir no GitHub (vou te dar meu usuário exato quando perguntar):
   - Corrija o autor do commit para o meu nome/email do GitHub
     (`git commit --amend --reset-author`), senão não conta como contribuição.
   - Crie o repo `rpa-price-monitor` (público) e faça push da branch `main`.
   - Sugira topics: python, rpa, playwright, automation, web-scraping.
4. Depois, implemente o próximo item do roadmap:
   **persistir histórico em SQLite e detectar variação de preço entre execuções**
   (comparar a captura atual com a anterior, marcar quais produtos subiram/caíram
   e quanto, e incluir isso numa nova aba/coluna do relatório).

## Comandos de referência
```bash
# setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# qualidade
ruff check .
pytest

# rodar
PYTHONPATH=src:. python -m pricewatch.main --pages 5
PYTHONPATH=src:. python -m pricewatch.main --pages 3 --headed   # navegador visivel
```
