# Gestão de Frota TVDE num Pico de Procura Localizado

Projeto da unidade curricular **Modelação e Simulação 2026/27** – Tema 14: *Ride-Sharing Matching and Fleet Management*.

Simulamos uma **cidade** com um serviço de TVDE (tipo Uber) e estudamos como a plataforma deve gerir a frota quando um **evento** (a saída de um jogo) cria um **pico de procura numa zona**, sem deixar o resto da cidade sem serviço.

Modelo **baseado em agentes**, feito em Python com [Mesa](https://mesa.readthedocs.io/) e visualizado com Pygame.

>  Documentação completa: `projeto_guide.md` (modelo conceptual, prioridades, divisão do trabalho) e `projeto_report.md` (progresso e decisões).

---

## Índice

1. [Pergunta de investigação](#1-pergunta-de-investigação)
2. [O modelo em resumo](#2-o-modelo-em-resumo)
3. [Experiências](#3-experiências)
4. [KPIs e critério de otimização](#4-kpis-e-critério-de-otimização)
5. [Fases do trabalho](#5-fases-do-trabalho)
6. [Estrutura do repositório](#6-estrutura-do-repositório)
7. [Instalação e execução](#7-instalação-e-execução)
8. [Divisão do trabalho por fases](#8-divisão-do-trabalho-por-fases)
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

## 5. Fases do trabalho

O trabalho está dividido em **fases completas**: cada fase tem código, experiências, gráficos e análise, e responde a uma pergunta. As fases estão ordenadas por prioridade: se o tempo apertar, corta-se de baixo para cima.

| Fase | Tema | Experiências | Pergunta | Prioridade |
|---|---|---|---|---|
| **1** | Baseline | E0, E1 | Qual o impacto do pico sem nenhuma política? | Essencial |
| **2** | Política: matching em lote | E2 | O lote ajuda durante o pico? | Importante |
| **3** | Política: reposicionamento com limite | E3, E4 | Quanto ajuda o evento, quanto custa à cidade e qual o melhor limite? | Importante |
| **4** | Robustez | E5 + sensibilidade | As conclusões aguentam mais pressão e outros pressupostos? | Robustez |
| **5** | Extensão (se houver tempo) | – | Pooling **ou** calibração com dados de NYC | Extra |
| **6** | Relatório e demo | – | – | Essencial |

**Políticas estudadas:** 2 (matching em lote e reposicionamento), com 7 variantes comparadas contra o baseline. O **pooling**, também referido no enunciado do Tema 14, ficou fora do núcleo por ser o mais complexo e não responder à pergunta principal; é a extensão preferida para a Fase 5 e, se não for feito, entra no relatório como trabalho futuro.

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
│   └── data/                  # calibração com dados de NYC (Fase 5)
├── experiments/               # correr experiências, gráficos, sensibilidade
├── viz/
│   ├── pygame_app.py          # visualização principal (janela Pygame)
│   └── app.py                 # visualização alternativa no browser (Solara)
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
| Abrir a visualização (Pygame) | `python viz/pygame_app.py` |
| Visualização com mais carros / dia normal | `python viz/pygame_app.py --vehicles 300` · `--no-event` |
| Guardar uma imagem de um minuto | `python viz/pygame_app.py --snapshot figura.png --at 25` |
| Visualização alternativa (browser) | `solara run viz/app.py` |
| Correr uma experiência | `python experiments/run.py config/scenarios/e1_baseline.yaml` *(previsto, Fase 1)* |

Teclas do Pygame: `Espaço` pausa · `+`/`−` velocidade · `R` reinicia · `Esc` sai.

---

## 8. Divisão do trabalho por fases

Cada pessoa fica com **fases inteiras**: programa a política ou a base, corre as experiências, faz os gráficos e interpreta os resultados. As duas programam, analisam e escrevem.

| | Pessoa X – Diana | Pessoa Y – Catarina |
|---|---|---|
| **Fases** | **1 – Baseline** · **2 – Matching em lote** · 5 – Extensão (se houver tempo) | **3 – Reposicionamento** · **4 – Robustez** |
| **Código** | `experiments/run.py` · `analysis/stats.py` · KPIs por zona (`core/metrics.py`) · curva do pico e frota · `match_batch` (`supply/matching.py`) | `supply/relocation.py` · ligação ao `model.py` · `experiments/sensitivity.py` · cenário de evento grande |
| **Experiências** | E0, E1, E2 | E3, E4, E5, sensibilidade |
| **Gráficos** | Pessoas à espera (E0 vs. E1) · tabela de KPIs com intervalos de confiança · imediato vs. lote | **Gráfico do *trade-off*** (limite X vs. desistências) · gráficos de sensibilidade |
| **Análise** | Impacto do pico (H1) · efeito do lote (H4) | Melhor limite X (H2, H3) · robustez das conclusões |
| **Visualização** | Modo de matching visível no Pygame | Carros a reposicionar visíveis no Pygame |
| **Testes (verificação cruzada)** | Escreve os testes do reposicionamento | Escreve os testes do matching em lote |

**Juntas:** introdução, modelo conceptual, conclusões, relatório final e demo.

### Como trabalham ao mesmo tempo

| Período | Pessoa X | Pessoa Y |
|---|---|---|
| 1 | Fase 1 completa | Fase 3: código do reposicionamento + testes + Pygame |
| 2 | Fase 2 completa | Fase 3: experiências E3/E4 (com o `run.py` da Fase 1), *trade-off*, análise |
| 3 | Fase 5 (extensão) ou revisão | Fase 4 completa |
| 4 | Relatório e demo (juntas) | Relatório e demo (juntas) |

**Contratos combinados no primeiro dia**, para não dependerem uma da outra: os **nomes dos KPIs** que o `compute_kpis` devolve (ex.: `pct_abandoned_event`, `wait_mean_city`) e as **chaves das políticas** no `config/base.yaml` (`policy.matching`, `policy.relocation.enabled`, `cap_pct`, `lead_min`).

O plano detalhado, com os ficheiros a criar e editar, está no `projeto_guide.md`.

---

## 9. Branches e fluxo de trabalho

```
main                              ← versões estáveis (marcos)
└── develop                       ← integração
    ├── feature/phase1-baseline         (X)
    ├── feature/phase2-batch-matching   (X)
    ├── feature/phase3-relocation       (Y)
    ├── feature/phase4-robustness       (Y)
    └── feature/phase5-extension        (X, se houver tempo)
```

1. Cada `feature/...` sai da `develop` e volta à `develop` por Pull Request.
2. Cada Pull Request é revisto pela outra pessoa, com os testes a passar.
3. Nos marcos, a `develop` é integrada na `main` e é criada uma tag.

```bash
git checkout develop
git pull
git checkout -b feature/phase1-baseline
# ... trabalho ...
git commit -m "exp: add replication runner for E0 and E1"
git push -u origin feature/phase1-baseline
```

**Convenções:** branches, código e commits em inglês; documentação em português. Prefixos: `demand:`, `supply:`, `core:`, `viz:`, `exp:`, `analysis:`, `docs:`, `test:`. Nunca fazer commit diretamente na `main`.

---

## 10. Marcos

| Tag | Marco |
|---|---|
| `v0.1-baseline` | Fase 1: E0 e E1 com KPIs por zona, replicações e intervalos de confiança |
| `v0.2-policies` | Fases 2 e 3: matching em lote e reposicionamento a funcionar (E2–E4) e gráfico do *trade-off* |
| `v0.3-results` | Fase 4: E5, sensibilidade e análise estatística completa |
| `v1.0-final` | Fase 6: relatório e demo |

---

## 11. Dados e referências

Os dados de NYC são opcionais (possível extensão da Fase 5) e servem só para dar valores realistas aos parâmetros. Os dados brutos não estão no repositório.

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
| Diana | Pessoa X – Fases 1 (baseline), 2 (matching em lote) e 5 (extensão) |
| _[nome]_ | Pessoa Y – Fases 3 (reposicionamento) e 4 (robustez) |