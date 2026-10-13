# Aurora SIGER — MGPEB (MEDA)

Protótipo acadêmico em Python do **Módulo de Gerenciamento de Pouso e Estabilização de Base (MGPEB)**, desenvolvido para a missão fictícia Aurora SIGER, no contexto de uma atividade integradora da FIAP.

## Funcionalidades

- Cadastro e gerenciamento de módulos de pouso
- Organização de fila (FIFO), listas e pilha de histórico (LIFO)
- Busca linear e busca binária de módulos
- Ordenação por inserção (*insertion sort*) e reorganização por prioridade
- Regras de autorização com operadores booleanos AND, OR e NOT
- Condições ambientais simuladas e consulta a referências históricas do **MEDA**, instrumento do rover Perseverance
- Modelo linear didático de altitude e interpolação histórica de temperatura

## Estrutura

```text
codigo/
  mgpeb_aurora_meda.py       # Programa principal
  testes_mgpeb_meda.py      # Testes automatizados
  meda_observacoes_nasa.csv # Valores históricos simplificados com fontes
diagramas/                  # Circuito lógico e fluxograma (PNG, SVG e DOT)
graficos/                   # Modelos matemáticos e gráficos
```

## Como executar

Requer **Python 3**. Não utiliza bibliotecas externas.

```bash
cd codigo
python3 mgpeb_aurora_meda.py
```

Para executar os testes:

```bash
cd codigo
python3 -m unittest -v testes_mgpeb_meda.py
```

## Importante: dados reais × simulação

Os dados ambientais usados como referência foram publicados pela NASA/JPL sobre o instrumento MEDA em Marte. **Os valores são observações históricas de momentos diferentes, não uma leitura simultânea do ambiente.** Os limites de segurança, módulos, combustível, condições de pouso e modelo de altitude são **hipóteses acadêmicas**, não parâmetros oficiais da NASA ou de uma missão espacial real. O MEDA integra o Perseverance, não a nave fictícia Aurora.

Fontes:

- [NASA/JPL — First Weather Report from Jezero Crater](https://www.jpl.nasa.gov/news/nasas-first-weather-report-from-jezero-crater-on-mars/)
- [NASA Planetary Data System — MEDA](https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/PERSEVERANCE/meda.html)

## Contexto

Projeto acadêmico demonstrativo. Esta versão pública omite o relatório identificado com dados acadêmicos pessoais. Se o repositório for privado, o relatório completo poderá ser incluído separadamente.
