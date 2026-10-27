# Matching e Gestão de Frota TVDE no Pico Pós-Jogo

Projeto da unidade curricular **Modelação e Simulação 2026/27** – Tema 14: *Ride-Sharing Matching and Fleet Management*.

Simulamos um serviço de TVDE (tipo Uber/Lyft) a responder ao pico de pedidos à saída de um jogo no **Yankee Stadium** (Nova Iorque) e comparamos políticas de **matching**, **pooling** e **reposicionamento da frota**. O modelo é calibrado e validado com dados reais de viagens da NYC Taxi & Limousine Commission (TLC).

---

## Índice

1. [Objetivo e pergunta de investigação](#1-objetivo-e-pergunta-de-investigação)
2. [Políticas, cenários e KPIs](#2-políticas-cenários-e-kpis)
3. [Dados](#3-dados)
4. [Estrutura do repositório](#4-estrutura-do-repositório)
5. [Instalação e execução](#5-instalação-e-execução)
6. [Divisão de tarefas](#6-divisão-de-tarefas)
7. [Branches e fluxo de trabalho](#7-branches-e-fluxo-de-trabalho)
8. [Marcos](#8-marcos)
9. [Equipa](#9-equipa)

---

## 1. Objetivo e pergunta de investigação

Quando um jogo acaba, milhares de pedidos de TVDE surgem em poucos minutos na mesma zona, enquanto os carros livres estão espalhados pelas zonas à volta. Um mau emparelhamento gera esperas longas, pedidos abandonados e muitos quilómetros feitos sem passageiros.

**Pergunta principal:** que combinação de regra de matching, pooling e reposicionamento da frota minimiza a espera e os pedidos rejeitados após um jogo, e a que custo em desvios, quilómetros vazios e emissões?

**Subperguntas:**

1. Emparelhar em lote (a cada 30 s) é melhor do que emparelhar cada pedido logo que chega? A partir de que nível de procura?
2. O pooling reduz os pedidos rejeitados o suficiente para compensar os desvios?
3. Enviar carros para perto do estádio antes do fim do jogo compensa os quilómetros vazios que isso gera?
4. Como mudam as respostas quando o pico é maior (estádio esgotado, chuva, metro avariado)?

**Tipo de modelo:** simulação de eventos discretos, estocástica, dinâmica e terminante (começa no fim do jogo e acaba quando a fila de pedidos esvazia), com passageiros, veículos e plataforma como agentes.

---

## 2. Políticas, cenários e KPIs

### Políticas (fatores)

| Fator | Nível A | Nível B |
|---|---|---|
| Matching | Imediato: cada pedido fica com o carro livre mais próximo | Em lote: a cada 30 s, afetação ótima de todos os pedidos e carros livres |
| Pooling | Sem pooling | Junta 2 pedidos com destino na mesma região e desvio ≤ 5 min |
| Reposicionamento | Sem reposicionamento | Carros livres enviados para o estádio X min antes do fim do jogo |

### Cenários

| Cenário | Descrição |
|---|---|
| C1 – Jogo normal | Procura média observada nos dados |
| C2 – Estádio esgotado | Procura escalada para a assistência máxima |
| C3 – Pico agravado | Chuva ou metro avariado: mais pedidos e mais paciência |

Desenho fatorial 2³ × 3 cenários = **24 configurações**, cada uma com pelo menos 30 replicações, números aleatórios comuns entre políticas e intervalos de confiança a 95%.

### KPIs

- Tempo de espera médio e percentil 90
- % de pedidos rejeitados ou abandonados
- Desvio médio dos passageiros em pooling
- Utilização dos veículos
- Quilómetros vazios e emissões estimadas
- Tempo até a fila de pedidos esvaziar

---

## 3. Dados

Os dados brutos **não estão no repositório** (são demasiado grandes). Os scripts em `src/rideshare_sim/data/` descarregam-nos e filtram-nos.

| Dados | Fonte | Uso |
|---|---|---|
| Viagens Uber/Lyft (HVFHV, Parquet mensal) | [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) | Pedidos, tempos de espera, destinos, tempos de viagem |
| Dicionário de dados HVFHV | [PDF da TLC](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_hvfhs.pdf) | Significado das colunas |
| Lookup das zonas TLC | [taxi_zone_lookup.csv](https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv) | Nomes das zonas |
| Shapefile das zonas TLC | [taxi_zones.zip](https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip) | Zona do estádio, zonas vizinhas, mapas |
| Jogos dos Yankees 2025 | [Baseball-Reference](https://www.baseball-reference.com/teams/NYY/2025-schedule-scores.shtml) | Hora de fim e assistência |

Ficheiro de um mês: `https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_AAAA-MM.parquet`

**Limitações conhecidas:** os dados só têm viagens concluídas (procura censurada) e não incluem a posição dos carros (a oferta é calibrada).

---

## 4. Estrutura do repositório

```
rideshare-sim/
├── README.md
├── requirements.txt
├── .gitignore                  # ignora data/raw, *.parquet, resultados grandes
│
├── config/
│   ├── base.yaml               # parâmetros comuns e sementes
│   └── scenarios/              # c1_normal.yaml, c2_soldout.yaml, c3_surge.yaml
│
├── data/
│   ├── raw/                    # Parquet TLC (fora do git)
│   ├── interim/                # viagens filtradas pela zona do estádio
│   └── processed/              # parâmetros ajustados (json/csv)
│
├── notebooks/
│   ├── demand/                 # EDA dos pedidos, ajuste das chegadas
│   └── supply/                 # EDA dos tempos de viagem, matriz de tempos
│
├── src/rideshare_sim/
│   ├── core/
│   │   ├── simulation.py       # motor de eventos e relógio
│   │   ├── entities.py         # Passenger, Vehicle, Request
│   │   └── metrics.py          # recolha dos KPIs
│   ├── demand/
│   │   ├── arrivals.py         # Poisson não homogéneo
│   │   ├── destinations.py
│   │   ├── abandonment.py      # desistência por paciência
│   │   └── pooling.py
│   ├── supply/
│   │   ├── travel_times.py     # matriz de tempos entre zonas
│   │   ├── fleet.py            # frota inicial e chegada de carros
│   │   ├── matching.py         # imediato e em lote
│   │   └── relocation.py       # reposicionamento
│   ├── data/
│   │   ├── extract_demand.py   # pedidos TLC + jogos
│   │   └── extract_supply.py   # tempos de viagem entre zonas
│   └── analysis/
│       └── stats.py            # ICs e comparações emparelhadas
│
├── experiments/
│   ├── run.py                  # fatorial políticas × cenários
│   └── results/
│
├── demo/
│   ├── app.py                  # aplicação da demo
│   ├── kpi_panel.py            # painel de KPIs em tempo real
│   └── map_view.py             # animação do mapa com os carros
│
└── tests/
    ├── test_core.py
    ├── test_demand.py          # escrito pela responsável pela oferta
    └── test_supply.py          # escrito pela responsável pela procura
```

**Regras:**

- Parâmetros e sementes vivem em `config/`, nunca no código.
- A lógica usada pelo modelo fica em `src/`; os notebooks servem só para exploração.
- Os testes de cada parte são escritos pela outra pessoa (verificação cruzada).

---

## 5. Instalação e execução

> Comandos previstos; serão atualizados à medida que o código for criado.

```bash
# instalar
git clone <url-do-repositorio>
cd rideshare-sim
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
nbstripout --install               # limpa outputs dos notebooks antes do commit

# preparar os dados
python src/rideshare_sim/data/extract_demand.py
python src/rideshare_sim/data/extract_supply.py

# correr as experiências
python experiments/run.py

# testes
pytest

# demo
streamlit run demo/app.py
```

---

## 6. Divisão de tarefas

Cada pessoa fica com um lado do sistema e faz tudo nesse lado: dados, código, análise e a sua parte da demo.

| | Pessoa A – Procura (passageiros) | Pessoa B – Oferta (veículos) |
|---|---|---|
| Dados | Pedidos após o jogo, destinos, volume vs. assistência | Tempos de viagem entre zonas, zonas vizinhas, frota |
| Inputs | Chegada de pedidos, destinos, paciência | Matriz de tempos de viagem, chegada de carros |
| Lógica no modelo | Desistência e pooling | Matching (imediato e em lote) e reposicionamento |
| Validação | Comparação da espera simulada com a real | Calibração da oferta de carros |
| Testes | Testes da parte da oferta | Testes da parte da procura |
| KPIs | Espera, rejeições, desvios | Utilização, km vazios, emissões |
| Demo | Painel de KPIs | Animação do mapa |

**Em conjunto:** modelo conceptual, motor do simulador (eventos e estados), interfaces entre módulos, desenho experimental, conclusões, relatório e apresentação.

### Interfaces combinadas

```python
# demand → core
def generate_requests(game, scenario, rng) -> list[Request]: ...

# supply → core
def match(pending_requests, free_vehicles, now) -> list[tuple[Request, Vehicle]]: ...
```

O pooling (procura) é chamado pelo matching (oferta) antes de atribuir um carro novo.

---

## 7. Branches e fluxo de trabalho

```
main                              ← versões estáveis (marcos e entrega)
└── develop                       ← integração
    ├── feature/demand-data
    ├── feature/demand-model
    ├── feature/demand-validation
    ├── feature/supply-data
    ├── feature/supply-model
    ├── feature/supply-verification
    ├── feature/experiments
    └── feature/demo
```

| Branch | O que faz | Responsável |
|---|---|---|
| `main` | Versões estáveis | – |
| `develop` | Estrutura, interfaces e motor do simulador; recebe todas as features | Ambas |
| `feature/demand-data` | Extração dos pedidos e jogos, EDA, chegadas e destinos | Pessoa A |
| `feature/demand-model` | Desistência e pooling | Pessoa A |
| `feature/demand-validation` | Validação da espera + testes da parte da oferta | Pessoa A |
| `feature/supply-data` | Tempos de viagem, matriz entre zonas, frota e calibração | Pessoa B |
| `feature/supply-model` | Matching (imediato e em lote) e reposicionamento | Pessoa B |
| `feature/supply-verification` | Testes da parte da procura + verificação do modelo | Pessoa B |
| `feature/experiments` | Fatorial, sensibilidade e análise estatística | Ambas |
| `feature/demo` | Painel de KPIs, mapa e app | Ambas |

### Fluxo

1. O esqueleto (estrutura, interfaces, motor) é feito diretamente na `develop`.
2. Cada `feature/...` sai da `develop` e volta à `develop` por Pull Request.
3. Cada Pull Request é revisto pela outra pessoa antes do merge.
4. Nos marcos, a `develop` é integrada na `main` e é criada uma tag.

```bash
git checkout develop
git pull
git checkout -b feature/demand-data

# ... trabalho ...
git add .
git commit -m "demand: fit non-homogeneous Poisson arrivals"
git push -u origin feature/demand-data
# abrir Pull Request para a develop
```

Se a `develop` avançou entretanto: `git pull origin develop` antes de abrir o Pull Request.

### Convenções

- Nomes de branches, código e commits em inglês.
- Commits pequenos, com prefixo da área: `demand:`, `supply:`, `core:`, `exp:`, `demo:`, `docs:`.
- Nunca fazer commit diretamente na `main`.
- Rever os Pull Requests da outra pessoa em menos de 24 h.

---

## 8. Marcos

| Tag | Marco | Condição |
|---|---|---|
| `v0.1-mvp` | Modelo mínimo a correr | Matching imediato, sem pooling nem reposicionamento, verificado |
| `v0.2-validated` | Modelo validado | Oferta calibrada e espera validada com jogos fora da calibração |
| `v1.0-final` | Entrega final | Todas as políticas, experiências, demo e relatório |

---

## 9. Equipa

| Nome | Papel |
|---|---|
| _[nome]_ | Pessoa A – Procura (passageiros) |
| _[nome]_ | Pessoa B – Oferta (veículos) |