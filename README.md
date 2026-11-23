# Gestão de Frota TVDE num Pico de Procura Localizado

Projeto da unidade curricular **Modelação e Simulação 2026/27** – Tema 14: *Ride-Sharing Matching and Fleet Management*.

Simulamos uma **cidade** com um serviço de TVDE (tipo Uber) e estudamos como a plataforma deve gerir a frota quando um **evento** (a saída de um jogo) cria um **pico de procura numa zona**, sem deixar o resto da cidade sem serviço.

Modelo **baseado em agentes**, feito em Python com [Mesa](https://mesa.readthedocs.io/) e visualizado no browser com Solara.

>  Documentação completa: `projeto_guide.md` (modelo conceptual, prioridades, divisão do trabalho) e `projeto_report.md` (progresso e decisões).

---

## Índice

1. [Pergunta de investigação](#1-pergunta-de-investigação)
2. [O modelo em resumo](#2-o-modelo-em-resumo)
3. [Experiências](#3-experiências)
4. [KPIs e critério de otimização](#4-kpis-e-critério-de-otimização)
5. [Prioridades](#5-prioridades)
6. [Estrutura do repositório](#6-estrutura-do-repositório)
7. [Instalação e execução](#7-instalação-e-execução)
8. [Divisão de tarefas](#8-divisão-de-tarefas)
9. [Branches e fluxo de trabalho](#9-branches-e-fluxo-de-trabalho)
10. [Marcos](#10-marcos)
11. [Dados e referências](#11-dados-e-referências)
12. [Equipa](#12-equipa)

---

## 1. Pergunta de investigação

> **Como deve uma plataforma TVDE gerir a frota durante um pico de procura localizado (a saída de um jogo), equilibrando o serviço na zona do evento e no resto da cidade?**

1. Qual o impacto do pico, sem nenhuma política especial?
2. O **matching em lote** melhora o serviço durante o pico?
3. **Reposicionar carros** para o evento ajuda lá, e quanto custa ao resto da cidade?
4. Qual a **percentagem máxima da frota** a reposicionar que dá o melhor equilíbrio?

---

## 2. O modelo em resumo

| Elemento | Descrição |
|---|---|
| **Mundo** | Cidade abstrata em grelha (41 × 41 células de 250 m) com uma **zona do evento** à volta do estádio, no centro |
| **Tempo** | Passos de 30 s, de 60 min antes a 120 min depois do fim do jogo |
| **Procura** | Pedidos **normais** em toda a cidade (sempre) + **pico do evento** no estádio (depois do jogo) |
| **Passageiro** | Pede carro, espera; desiste se a espera passar a paciência |
| **Carro** | Vai buscar o passageiro, leva-o ao destino e fica livre lá; pode ser reposicionado |
| **Plataforma** | Decide o **matching** (que carro vai buscar que passageiro) e o **reposicionamento** (para onde vão os carros livres) |

**Ordem de cada passo:** chegadas → paciência → matching → reposicionamento → movimento → registo.

**Políticas estudadas:**

| Decisão | Opções |
|---|---|
| Matching | **Imediato** (o mais próximo, logo) · **Em lote** (janela de 1 min, afetação ótima) |
| Reposicionamento | **Não** · **Sim, com limite de X% da frota** (X = 10…50%) · Sim, sem limite |

**Classificação:** baseado em agentes · tempo discreto · estocástico · dinâmico · terminante · estudo prescritivo.

---

## 3. Experiências

| # | Evento | Matching | Reposicionamento | Objetivo |
|---|---|---|---|---|
| E0 | Sem evento | Imediato | Não | Referência: um dia normal |
| E1 | Normal | Imediato | Não | **Baseline** |
| E2 | Normal | Em lote | Não | Efeito do matching |
| E3 | Normal | Imediato | Sim, sem limite | Efeito do reposicionamento |
| E4 | Normal | Imediato | Sim, X = 10…50% | Encontrar o equilíbrio |
| E5 | Grande | Melhor | Melhor | Robustez |

Cada experiência: 30 replicações, média e intervalo de confiança a 95%.

---

## 4. KPIs e critério de otimização

| KPI | Medido em |
|---|---|
| Tempo de espera (médio e P90) | Zona do evento e resto da cidade, separado |
| % de desistências | Zona do evento e resto da cidade, separado |
| Utilização da frota | Sistema |
| Km vazios e emissões | Sistema |

**Critério:** a melhor política minimiza as desistências na zona do evento, sem que as desistências no resto da cidade aumentem mais de 2 pontos percentuais face a E0.

---

## 5. Prioridades

| Prioridade | O quê |
|---|---|
| **1. Essencial** | Cidade + pico, agentes, matching imediato, KPIs por zona, visualização, replicações (E0, E1) |
| **2. Importante** | Reposicionamento com limite, matching em lote, gráfico do *trade-off* (E2–E4) |
| **3. Robustez** | Evento grande, análise de sensibilidade, estatística (E5) |
| **4. Valores reais** | Calibração com dados TVDE de Nova Iorque |
| **5. Extensões** | Pooling, mapa real (mesa-geo) |

---

## 6. Estrutura do repositório

```
modelasimu/
├── config/
│   ├── base.yaml              # parâmetros do baseline
│   └── scenarios/             # uma configuração por experiência (E0–E5)
├── src/rideshare_sim/
│   ├── model.py               # modelo Mesa (junta tudo)
│   ├── core/                  # estados, interfaces, agregação dos KPIs
│   ├── world/                 # grelha e zona do evento
│   ├── demand/                # passageiros, chegadas, KPIs da procura
│   ├── supply/                # carros, frota, matching, reposicionamento, KPIs da oferta
│   ├── analysis/              # estatística dos resultados
│   └── data/                  # calibração com dados de NYC (prioridade 4)
├── experiments/               # correr experiências, gráficos, sensibilidade
├── viz/app.py                 # visualização no browser
├── tests/                     # testes de verificação
├── data/                      # dados (os brutos não vão para o git)
├── notebooks/                 # exploração
├── proposta/                  # proposta e modelo conceptual
└── report/                    # relatório final
```

---

## 7. Instalação e execução

Requer **Python 3.12** (o Mesa atual não funciona em versões anteriores).

```bash
conda create -n modelasimu python=3.12 -y
conda activate modelasimu
pip install -r requirements.txt
pip install -e .
```

| Para… | Comando |
|---|---|
| Correr os testes | `pytest -v` |
| Abrir a visualização | `solara run viz/app.py` |
| Correr uma experiência | `python experiments/run.py config/scenarios/e1_baseline.yaml` *(previsto)* |

A visualização abre no browser em `localhost` (só no próprio computador).

---

## 8. Divisão de tarefas

Cada pessoa fica com um lado do sistema; o núcleo, as experiências e a visualização fazem-se em conjunto.

| | Pessoa A – Procura (passageiros) | Pessoa B – Oferta (carros) |
|---|---|---|
| **Pastas** | `src/rideshare_sim/demand/` | `src/rideshare_sim/supply/` |
| **Prioridade 1** | Procura normal + pico do evento, tipo de passageiro, paciência, KPIs por zona | Frota espalhada, movimento, matching imediato, KPIs de frota |
| **Prioridade 2** | Configuração de E2–E4, gráfico do *trade-off*, painel de KPIs | Reposicionamento com limite, matching em lote, seletor de experiências |
| **Prioridade 3** | Evento grande, sensibilidade à paciência | Sensibilidade à frota e ao momento do reposicionamento |
| **Prioridade 4** | Calibrar a procura (NYC) | Calibrar velocidade e duração das viagens (NYC) |
| **Testes** | Escreve os testes da oferta | Escreve os testes da procura |

**Juntas:** modelo conceptual, `model.py`, `core/`, `world/`, visualização, experiências, análise estatística, relatório e demo.

O plano detalhado, passo a passo e com os ficheiros a criar e editar, está no `projeto_guide.md`.

---

## 9. Branches e fluxo de trabalho

```
main                              ← versões estáveis (marcos)
└── develop                       ← integração
    ├── feature/demand-city-event       (A)
    ├── feature/supply-fleet            (B)
    ├── feature/visualization           (juntas)
    ├── feature/experiments             (juntas)
    ├── feature/experiments-policies    (A)
    ├── feature/relocation              (B)
    ├── feature/batch-matching          (B)
    └── feature/nyc-calibration         (juntas)
```

1. Cada `feature/...` sai da `develop` e volta à `develop` por Pull Request.
2. Cada Pull Request é revisto pela outra pessoa, com os testes a passar.
3. Nos marcos, a `develop` é integrada na `main` e é criada uma tag.

```bash
git checkout develop
git pull
git checkout -b feature/supply-fleet
# ... trabalho ...
git commit -m "supply: spread initial fleet across the city"
git push -u origin feature/supply-fleet
```

**Convenções:** branches, código e commits em inglês; documentação em português. Prefixos: `demand:`, `supply:`, `core:`, `viz:`, `exp:`, `docs:`, `test:`. Nunca fazer commit diretamente na `main`.

---

## 10. Marcos

| Tag | Marco |
|---|---|
| `v0.1-mvp` | E0 e E1 a correr, com KPIs por zona e visualização |
| `v0.2-policies` | Reposicionamento e matching em lote a funcionar (E2–E4) |
| `v0.3-results` | E5, sensibilidade e análise estatística |
| `v1.0-final` | Entrega final: relatório e demo |

---

## 11. Dados e referências

Os dados de NYC são opcionais (prioridade 4) e servem só para dar valores realistas aos parâmetros. Os dados brutos não estão no repositório.

| Recurso | Uso |
|---|---|
| [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) | Viagens Uber/Lyft: pedidos, esperas, durações |
| [Dicionário de dados HVFHV](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_hvfhs.pdf) | Significado das colunas |
| [Baseball-Reference – Yankees 2025](https://www.baseball-reference.com/teams/NYY/2025-schedule-scores.shtml) | Hora de fim e assistência dos jogos |
| [Documentação do Mesa](https://mesa.readthedocs.io/) | Framework de simulação |

**Referência metodológica:** Robinson, S. (2008). Conceptual modelling for simulation Part I: definition and requirements. *Journal of the Operational Research Society*, 59(3), 278–290.

---

## 12. Equipa

| Nome | Papel |
|---|---|
| Catarina | Pessoa A – Procura (passageiros) |
| Diana | Pessoa B – Oferta (carros) |