# Guia do Projeto – Modelação e Simulação 2026/27

> Este guia explica **o que vamos fazer, como funciona o modelo, as prioridades e quem faz o quê, passo a passo**.
> Para saber **o que já está feito**, ver `projeto_report.md`.

- **Tema:** 14 – *Ride-Sharing Matching and Fleet Management*
- **Grupo:** 2 pessoas
  - **Pessoa A – Procura (passageiros):** Catarina
  - **Pessoa B – Oferta (carros):** Diana
- **Ferramenta:** Python + **Mesa** (simulação baseada em agentes) + **Solara** (visualização no browser)

---

## Índice

1. [O projeto numa frase](#1-o-projeto-numa-frase)
2. [O modelo conceptual, explicado de forma simples](#2-o-modelo-conceptual-explicado-de-forma-simples)
3. [Lista de prioridades](#3-lista-de-prioridades)
4. [Estrutura do repositório](#4-estrutura-do-repositório)
5. [Divisão do trabalho por passos](#5-divisão-do-trabalho-por-passos)
6. [Branches e forma de trabalhar](#6-branches-e-forma-de-trabalhar)
7. [Preparar o computador](#7-preparar-o-computador)
8. [Regras de ouro](#8-regras-de-ouro)

---

## 1. O projeto numa frase

> **Simulamos uma cidade com um serviço de TVDE e estudamos como a plataforma deve gerir a frota quando um evento (a saída de um jogo) cria um pico de procura numa zona, sem deixar o resto da cidade sem serviço.**

### O que mudou face à primeira versão (e porquê)

Antes modelávamos **só a zona do estádio**. O professor apontou o problema: assim, mandar carros para o estádio parece sempre bom, porque **o custo não existe no modelo**: na realidade, esses carros saem de algum lado, e o resto da cidade fica sem Ubers.

Agora modelamos **a cidade inteira**. O jogo passa a ser **um cenário** que põe o sistema à prova. Isto cria um *trade-off* real, que é exatamente o que o Tema 14 pede para analisar.

---

## 2. O modelo conceptual, explicado de forma simples

O modelo conceptual segue a estrutura de **Robinson (2008)**, que responde a 6 perguntas: qual o problema, o que queremos descobrir, o que medimos, o que fazemos variar, o que entra no modelo e que simplificações fazemos.

### 2.1 O problema

Numa cidade, uma plataforma TVDE tem uma frota a servir pedidos espalhados por todo o lado. Quando acaba um jogo, aparecem de repente centenas de pedidos numa só zona:

- se a plataforma **não fizer nada**, essa zona fica com filas enormes e muitas desistências;
- se **mandar muitos carros** para lá, o resto da cidade fica sem carros.

**O dilema:** servir o pico do evento **vs.** manter o serviço no resto da cidade.
**Quem decide:** a plataforma TVDE.

### 2.2 O que queremos descobrir (objetivos)

**Objetivo geral:** perceber como a plataforma deve gerir a frota durante um pico de procura localizado, equilibrando o serviço na zona do evento e no resto da cidade.

**Perguntas da simulação:**
1. Qual o impacto do pico, sem nenhuma política especial?
2. O **matching em lote** melhora o serviço durante o pico?
3. **Reposicionar carros** para o evento ajuda lá, e quanto custa ao resto da cidade?
4. Qual a **percentagem máxima da frota** a reposicionar que dá o melhor equilíbrio?

### 2.3 O mundo

```
┌───────────────────────────────────────┐
│                                       │
│            RESTO DA CIDADE            │
│     (pedidos normais em todo o lado)  │
│                                       │
│            ┌───────────────┐          │
│            │ ZONA DO EVENTO│          │
│            └───────────────┘          │
│                                       │
└───────────────────────────────────────┘
```

- **Cidade:** grelha de 41 × 41 células; cada célula tem 250 m.
- **Zona do evento:** até 3 células à volta do estádio, que fica no centro.
- **Resto da cidade:** tudo o resto.
- **Tempo:** cada passo vale **30 segundos**. A simulação começa **60 min antes** do fim do jogo (a cidade a funcionar normalmente) e acaba **120 min depois**.
- **Movimento:** um carro anda **1 célula por passo** (≈ 30 km/h), primeiro na horizontal e depois na vertical, como ruas em quadrícula.

### 2.4 Os agentes

| Agente | Propriedades | O que faz |
|---|---|---|
| 🧍 **Passageiro** | origem, destino, tipo (*cidade* ou *evento*), paciência, hora do pedido, estado | Pede carro, espera, viaja ou desiste |
| 🚗 **Carro** | posição, estado, passageiro, destino atual, km vazios, km com passageiro | Vai buscar passageiros, leva-os, e quando está livre fica parado ou reposiciona-se |
|  **Plataforma** | as regras ativas (a política) | Decide que carro vai buscar que passageiro e para onde vão os carros livres |

### 2.5 De onde vem a procura

Há **duas fontes de pedidos**:

| Fonte | Onde | Quando | Ritmo (provisório) |
|---|---|---|---|
| **Procura normal** | Qualquer célula da cidade | O tempo todo | 5 pedidos/min na cidade toda |
| **Pico do evento** | No estádio | A partir do fim do jogo | Sobe até 20 pedidos/min em 10 min e desce até 0 em 60 min |

```
pedidos/min
   25 │            ╭╮
   20 │           ╭╯╰╮        ← pico do evento
   15 │           │   ╰╮
   10 │           │     ╰─╮
    5 │───────────┴───────┴──────── ← procura normal (sempre)
      └──────────┬──────────────── tempo
            fim do jogo
```

### 2.6 Os dois ciclos

**Passageiro:**
```
pede carro → À ESPERA DE MATCH ──(match)──→ À ESPERA DO CARRO → EM VIAGEM → SERVIDO 
                    │
                    └──(paciência esgotada)──→ DESISTIU  (vai de metro / a pé)
```

**Carro:**
```
LIVRE ──(match)──→ A CAMINHO DA RECOLHA ──→ OCUPADO ──→ LIVRE (fica no destino)
  │
  └──(reposicionamento)──→ A REPOSICIONAR (vazio) ──→ LIVRE (na zona do evento)
```

A **plataforma** liga os dois ciclos: quando faz um match, o passageiro passa a "à espera do carro" e o carro passa a "a caminho da recolha" **ao mesmo tempo**.

### 2.7 O que acontece em cada passo (30 s)

```
1. CHEGADAS       → aparecem pedidos novos (procura normal + pico do evento)
2. PACIÊNCIA      → passageiros sem carro que esperaram demais desistem
3. MATCHING       → a plataforma atribui carros livres a passageiros à espera
4. REPOSICIONAR   → se for altura, a plataforma manda carros livres para o evento
5. MOVIMENTO      → todos os carros com destino andam uma célula
6. REGISTO        → guardam-se os dados para os KPIs e os gráficos
```

### 2.8 As decisões da plataforma (as políticas)

**Decisão 1 – Matching: como emparelhar pedidos e carros?**

| Opção | Como funciona |
|---|---|
| **Imediato** | Quem espera há mais tempo fica logo com o carro livre mais próximo |
| **Em lote** | Juntam-se os pedidos durante 1 minuto e escolhe-se a distribuição que minimiza a distância **total** de recolha (problema de afetação) |

**Decisão 2 – Reposicionamento: o que fazem os carros livres?**

| Opção | Como funciona |
|---|---|
| **Ficar onde estão** | O carro livre espera onde deixou o último passageiro |
| **Ir para o evento, com limite X%** | 15 min antes do fim do jogo, os carros livres **mais próximos** do estádio vão, vazios, para a zona do evento, até um máximo de **X% da frota** |

O limite X é onde está o *trade-off*: **poucos** carros e o estádio fica com filas; **muitos** e a cidade fica sem serviço. **Encontrar o melhor X é a parte de "otimizar".**

### 2.9 O que medimos (outputs / KPIs)

| KPI | O que mede | Onde |
|---|---|---|
| Tempo de espera (médio e P90) | Minutos do pedido até à recolha | **Evento** e **cidade**, separado |
| % de desistências | Abandonados ÷ pedidos totais | **Evento** e **cidade**, separado |
| Utilização da frota | % do tempo em que os carros não estão livres | Sistema todo |
| Km vazios | Km sem passageiro (recolhas + reposicionamento) | Sistema todo |
| Emissões | Km totais × fator de emissão | Sistema todo |

**P90:** o tempo de espera abaixo do qual estão 90% dos passageiros. Mostra os piores casos.

**Critério de otimização (definido antes de ver resultados):**
> A melhor política é a que **minimiza as desistências na zona do evento**, desde que as desistências no resto da cidade **não aumentem mais de 2 pontos percentuais** face a um dia normal (E0).

A simulação **não otimiza sozinha**: compara alternativas. "Otimizar" é testar vários valores de X e escolher o que cumpre este critério.

### 2.10 O que fazemos variar (inputs)

| Tipo | Variável | Valores |
|---|---|---|
| **Decisão** (controlável) | Regra de matching | Imediato · Em lote |
| **Decisão** (controlável) | Reposicionamento | Não · Sim, com X = 10, 20, 30, 40, 50% · sem limite |
| **Cenário** (não controlável) | Tamanho do evento | Sem evento · Normal · Grande |

**Parâmetros fixos** (provisórios, a calibrar):

| Parâmetro | Valor |
|---|---|
| Grelha | 41 × 41, célula de 250 m |
| Passo | 30 s |
| Zona do evento | Até 3 células do estádio |
| Duração | De −60 min a +120 min (0 = fim do jogo) |
| Procura normal | 5 pedidos/min |
| Pico do evento | Até 20 pedidos/min |
| Paciência | Exponencial, média de 10 min, máximo de 30 min |
| Frota | N carros, **calibrada** para um dia normal ter menos de 5% de desistências |
| Reposicionamento | 15 min antes do fim do jogo |

### 2.11 Âmbito: o que entra e o que fica de fora

| Entra ✅ | Fica de fora ❌ |
|---|---|
| Cidade inteira (procura normal) | Metro e outros transportes (só como destino de quem desiste) |
| Zona do evento (pico) | Preços e preço dinâmico |
| Passageiros, carros, plataforma | Trânsito (velocidade constante) |
| Matching e reposicionamento | Motoristas a entrar e sair de serviço (frota fixa) |
| | Pooling (extensão) |

### 2.12 Processos aleatórios

| Processo | Distribuição |
|---|---|
| Chegada de pedidos normais | Poisson, taxa constante |
| Chegada de pedidos do evento | Poisson, taxa variável (a curva do pico) |
| Origem dos pedidos normais | Uniforme na grelha |
| Destinos | Uniforme, com distância mínima à origem |
| Paciência | Exponencial, com máximo |
| Posição inicial dos carros | Uniforme na grelha |

### 2.13 Pressupostos

| # | Pressuposto | Porquê |
|---|---|---|
| P1 | Cidade em grelha, distâncias Manhattan | Simples e fácil de verificar (recomendação do professor) |
| P2 | Velocidade constante, sem trânsito | Foco nas decisões da plataforma |
| P3 | Frota fixa | Isola o efeito das políticas |
| P4 | O passageiro só desiste **antes** do match | Simplifica; é onde está a maioria das desistências no pico |
| P5 | Procura normal uniforme na cidade | Sem dados por zona |
| P6 | Os motoristas aceitam sempre a viagem | Sem comportamento individual |
| P7 | Sem preços, sem pooling | Fora do âmbito |

### 2.14 Classificação do modelo

Baseado em **agentes** · tempo **discreto** (passos de 30 s) · **estocástico** · **dinâmico** · **terminante** · estudo **prescritivo** (recomenda uma política).

### 2.15 As experiências

| # | Evento | Matching | Reposicionamento | Para quê |
|---|---|---|---|---|
| **E0** | Sem evento | Imediato | Não | Referência: um dia normal |
| **E1** | Normal | Imediato | Não | **Baseline**: ver o problema |
| **E2** | Normal | **Em lote** | Não | Efeito do matching |
| **E3** | Normal | Imediato | **Sim, sem limite** | Efeito do reposicionamento |
| **E4** | Normal | Imediato | **Sim, X = 10…50%** | Encontrar o equilíbrio |
| **E5** | **Grande** | Melhor | Melhor | Robustez sob mais pressão |

Cada experiência: **30 replicações**, média e intervalo de confiança a 95%.

**Resultado principal:** um gráfico de E4, com o limite X no eixo horizontal e as desistências no evento e na cidade no eixo vertical. O ponto que cumpre o critério é a política recomendada.

### 2.16 Hipóteses

- **H1:** sem política (E1), as desistências no evento disparam e a cidade quase não é afetada.
- **H2:** reposicionar sem limite (E3) ajuda o evento, mas prejudica a cidade.
- **H3:** existe um X intermédio (E4) que cumpre o critério.
- **H4:** o matching em lote (E2) ajuda mais durante o pico do que num dia normal.

### 2.17 Como sabemos que o modelo está certo

- **Verificação** (faz o que queremos?): casos calculados à mão, casos extremos (sem carros / carros de sobra), balanço de passageiros, reprodutibilidade.
- **Validação** (representa a realidade?): apresentar o modelo ao professor; E0 estável (a fila não cresce sem parar); mais carros → menos espera; *(extra)* comparar com dados de NYC.

---

## 3. Lista de prioridades

Se o tempo apertar, corta-se **de baixo para cima** e o projeto continua completo.

| Prioridade | O quê | Experiências |
|---|---|---|
| **1. Essencial** | Cidade com zona do evento; procura normal + pico; agentes; matching imediato; KPIs por evento e cidade; visualização básica; replicações | E0, E1 |
| **2. Importante** | Reposicionamento com limite X; matching em lote; gráfico do *trade-off*; visualização bonita para a demo | E2, E3, E4 |
| **3. Robustez** | Evento grande; análise de sensibilidade; análise estatística completa | E5 |
| **4. Valores reais** | Calibrar o pico, a procura normal e as viagens com dados de NYC | – |
| **5. Extensões** | Pooling; mapa real (mesa-geo) | – |

**Para uma boa nota:** as prioridades 1, 2 e 3 bem feitas. A 4 dá pontos extra. A 5 só se sobrar muito tempo.

---

## 4. Estrutura do repositório

```
modelasimu/
├── README.md                              
├── requirements.txt                       
├── pyproject.toml                         
├── config/
│   ├── base.yaml                          ️  parâmetros do baseline
│   └── scenarios/                           um ficheiro por experiência
│       ├── e0_normal_day.yaml
│       ├── e1_baseline.yaml
│       ├── e2_batch.yaml
│       ├── e3_relocation.yaml
│       ├── e4_relocation_cap.yaml
│       └── e5_big_event.yaml
├── src/rideshare_sim/
│   ├── model.py                           ️  o modelo Mesa (junta tudo)
│   ├── core/
│   │   ├── entities.py                    ️  estados + tipo de passageiro
│   │   ├── interfaces.py                  ️  contratos entre as partes
│   │   └── metrics.py                       junta os KPIs das duas partes
│   ├── world/
│   │   └── grid_world.py                  ️  grelha + zona do evento
│   ├── demand/                            PESSOA A
│   │   ├── arrivals.py                    ️  procura normal + pico do evento
│   │   ├── passenger.py                     agente Passageiro
│   │   └── metrics.py                       KPIs de espera e desistências por zona
│   ├── supply/                            PESSOA B
│   │   ├── fleet.py                       ️  frota espalhada pela cidade
│   │   ├── vehicle.py                     ️  agente Carro
│   │   ├── matching.py                    ️  imediato + em lote
│   │   ├── relocation.py                    reposicionamento com limite X
│   │   └── metrics.py                       KPIs de utilização, km e emissões
│   ├── analysis/
│   │   └── stats.py                         intervalos de confiança, comparações
│   └── data/                              (prioridade 4)
│       ├── extract_nyc.py                 
│       ├── calibrate_demand.py              PESSOA A
│       └── calibrate_supply.py              PESSOA B
├── experiments/
│   ├── run.py                               corre uma experiência com N replicações
│   ├── tradeoff_plot.py                     gráfico principal (E4)
│   ├── sensitivity.py                       análise de sensibilidade
│   └── results/                           (fora do git)
├── viz/
│   └── app.py                             ️  visualização no browser
├── tests/
│   ├── test_model.py                      ️  testes do modelo (juntas)
│   ├── test_demand.py                       escrito pela Pessoa B
│   └── test_supply.py                       escrito pela Pessoa A
├── data/                                  dados (os brutos fora do git)
├── notebooks/                             exploração
├── proposta/
└── report/
```

**Porquê `demand/metrics.py` e `supply/metrics.py` separados?** Para as duas não editarem o mesmo ficheiro ao mesmo tempo (evita conflitos no git). O `core/metrics.py` só junta os dois.

---

## 5. Divisão do trabalho por passos

### Passo 0 – Fechar o modelo (juntas)

- [x] Modelo conceptual escrito (documento da proposta e secção 2 deste guia)
- [ ] As duas leem e concordam
- [ ] Validar com o professor

### Passo 1 – Adaptar o núcleo ao novo modelo (juntas, na `develop`)

Pequeno, mas tem de vir **primeiro**: as duas dependem disto.

| Ficheiro | Ação | O que muda |
|---|---|---|
| `config/base.yaml` | ✏️ | Novos parâmetros: início em −60 min, fim em +120, procura normal, curva do pico, raio da zona do evento, paciência (10 min), limite X, momento do reposicionamento |
| `world/grid_world.py` | ✏️ | Zona do evento (`is_in_event_zone(cell)`) e sorteio de uma célula qualquer da cidade |
| `core/entities.py` | ✏️ | Novo `PassengerType` (CITY, EVENT) |
| `core/interfaces.py` | ✏️ | O passageiro passa a ter **origem** e **tipo**; contrato do reposicionamento |
| `model.py` | ✏️ | Relógio a começar em −60 min; chamar as duas fontes de procura; passo 4 (reposicionamento) no ciclo; parar aos +120 min |
| `tests/test_model.py` | ✏️ | Ajustar os testes ao novo relógio |

### Passo 2 – Prioridade 1: o baseline a funcionar (em paralelo)

| | Pessoa A – Procura | Pessoa B – Oferta (Diana) |
|---|---|---|
| **Branch** | `feature/demand-city-event` | `feature/supply-fleet` |
| **Tarefas** | Procura normal em toda a cidade · pico do evento no estádio (curva) · passageiro com tipo e origem · paciência com máximo | Frota espalhada pela cidade · carro livre fica parado · rever movimento e contadores de km · rever o matching imediato |
| **Editar** | `demand/arrivals.py`, `demand/passenger.py` | `supply/fleet.py`, `supply/vehicle.py`, `supply/matching.py` |
| **Criar** | `demand/metrics.py` (espera e desistências **por zona**) · `tests/test_supply.py` (testes da parte da B) | `supply/metrics.py` (utilização, km vazios, emissões) · `tests/test_demand.py` (testes da parte da A) |

| Juntas | Branch | Ficheiros |
|---|---|---|
| Juntar os KPIs das duas partes | `develop` | ️ `core/metrics.py` |
| Visualização: zona do evento sombreada, estádio marcado, cores por estado e tipo, legenda, tempo em minutos | `feature/visualization` |  `viz/app.py` |
| Correr 30 replicações e guardar os KPIs; experiências E0 e E1 | `feature/experiments` |  `experiments/run.py`, `config/scenarios/e0_normal_day.yaml`, `e1_baseline.yaml`, `analysis/stats.py` |

🏁 **Marco:** E0 e E1 a correr → tag `v0.1-mvp`

### Passo 3 – Prioridade 2: as políticas

| | Pessoa A – Procura | Pessoa B – Oferta (Diana) |
|---|---|---|
| **Branch** | `feature/experiments-policies` | `feature/relocation` e `feature/batch-matching` |
| **Tarefas** | Configurar E2, E3 e E4 · gráfico do *trade-off* · painel de KPIs (evento vs. cidade) na visualização | Reposicionamento com limite X% · matching em lote (janela de 1 min, afetação ótima) · seletor de experiência na visualização |
| **Editar** | `viz/app.py` (painel de KPIs) | `supply/matching.py` (`match_batch`), `model.py` (ligar o reposicionamento), `viz/app.py` (seletor) |
| **Criar** | `config/scenarios/e2_batch.yaml`, `e3_relocation.yaml`, `e4_relocation_cap.yaml` · `experiments/tradeoff_plot.py` | `supply/relocation.py` · testes das políticas em `tests/test_model.py` |

| Juntas |
|---|
| Correr E2, E3 e E4 e escolher a melhor política com o critério de otimização |

**Marco:** políticas a funcionar e o *trade-off* visível → tag `v0.2-policies`

**Atenção:** no passo 3, as duas mexem no `viz/app.py`. Combinem quem faz primeiro, ou façam-no juntas.

### Passo 4 – Prioridade 3: robustez

| | Pessoa A – Procura | Pessoa B – Oferta (Diana) |
|---|---|---|
| **Tarefas** | Cenário de evento grande · sensibilidade à paciência | Sensibilidade ao tamanho da frota e ao momento do reposicionamento |
| **Criar / editar** |  `config/scenarios/e5_big_event.yaml` · ️ `experiments/sensitivity.py` (parte da procura) |  `experiments/sensitivity.py` (parte da oferta) |

| Juntas |
|---|
| Correr E5 · análise estatística (️ `analysis/stats.py`): intervalos de confiança e comparação entre políticas |

 **Marco:** resultados completos → tag `v0.3-results`

### Passo 5 – Prioridade 4: valores reais de NYC (se houver tempo)

| | Pessoa A – Procura | Pessoa B – Oferta (Diana) |
|---|---|---|
| **Tarefas** | Forma do pico à saída dos jogos; procura numa noite normal | Velocidade e duração das viagens; calibrar o tamanho da frota |
| **Criar** | `data/calibrate_demand.py` | `data/calibrate_supply.py` |

| Juntas |
|---|
|  `data/extract_nyc.py`: extrair os dados **uma só vez** e partilhar um CSV pequeno · atualizar  `config/base.yaml` com os valores calibrados · comparar a espera simulada com a real |

### Passo 6 – Relatório e demo (juntas)

| Pessoa A escreve | Pessoa B escreve | Juntas |
|---|---|---|
| Procura, processos aleatórios, cenários, resultados | Oferta, regras de decisão, verificação, implementação | Introdução, modelo conceptual, conclusões, demo, ✏️ `README.md` |

Tag final: `v1.0-final`.

### Passo 7 – Extensões (só se sobrar tempo)

- **Pooling:** Pessoa A, com apoio da B no matching ( `demand/pooling.py`)
- **Mapa real com mesa-geo:** juntas ( `world/nyc_world.py`)

### Resumo das branches

| Branch | Passo | Quem |
|---|---|---|
| `develop` | 1 | Juntas |
| `feature/demand-city-event` | 2 | A |
| `feature/supply-fleet` | 2 | B |
| `feature/visualization` | 2–3 | Juntas |
| `feature/experiments` | 2 | Juntas |
| `feature/experiments-policies` | 3 | A |
| `feature/relocation` | 3 | B |
| `feature/batch-matching` | 3 | B |
| `feature/nyc-calibration` | 5 | Juntas |

---

## 6. Branches e forma de trabalhar

```
main                     ← versões estáveis (marcos)
└── develop              ← integração; tudo entra aqui primeiro
    └── feature/...      ← uma branch por tarefa
```

```bash
git checkout develop
git pull
git checkout -b feature/supply-fleet

# ... trabalhar, commits pequenos ...
git add <ficheiros>
git commit -m "supply: spread initial fleet across the city"
git push -u origin feature/supply-fleet
# abrir Pull Request para a develop no GitHub
```

- Cada Pull Request é **revisto pela outra pessoa** antes do merge.
- Antes de abrir o PR: `git pull origin develop` e `pytest` (os testes têm de passar).
- Nunca fazer commit diretamente na `main`.
- Nos marcos: juntar a `develop` na `main` e criar a tag.
- Branches, código e commits em **inglês**; documentação em português.
- Prefixos dos commits: `demand:`, `supply:`, `core:`, `viz:`, `exp:`, `docs:`, `test:`.

---

## 7. Preparar o computador

O Mesa atual precisa de **Python 3.12**.

```bash
conda create -n modelasimu python=3.12 -y
conda activate modelasimu
cd <pasta-do-repositorio>
pip install -r requirements.txt
pip install -e .
```

No PyCharm: *Settings → Project → Python Interpreter → Add Interpreter → Conda →* `modelasimu`.

| Para… | Comando |
|---|---|
| Correr os testes | `pytest -v` |
| Abrir a visualização | `solara run viz/app.py` (abre no browser, em `localhost`) |
| Ver a versão do Mesa | `python -c "import mesa; print(mesa.__version__)"` |

A visualização **não se corre com o ▶ do PyCharm**: é uma página web local criada pelo Mesa através do Solara.

---

## 8. Regras de ouro

1. **Nada de código novo sem estar no modelo conceptual.** Se surgir uma ideia nova, primeiro discute-se e escreve-se aqui.
2. **Respeitar os contratos** em `core/interfaces.py`: o interior das funções muda à vontade, as assinaturas só se combinadas.
3. **Parâmetros no `config/`**, nunca escritos diretamente no código.
4. **Os testes passam sempre** antes de um Pull Request.
5. **Cada uma testa a parte da outra** (verificação cruzada).
6. **Seguir as prioridades**: âmbito pequeno e bem feito é melhor do que muito e mal validado.
7. **Valores provisórios** estão marcados com `PLACEHOLDER` no código: são para substituir quando calibrarmos.

---

**Referência:** Robinson, S. (2008). Conceptual modelling for simulation Part I: definition and requirements. *Journal of the Operational Research Society*, 59(3), 278–290.