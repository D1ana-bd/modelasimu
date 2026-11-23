# Relatório de Progresso do Projeto

> Este documento explica **o que já foi feito, porquê, o que mudou e quais são os próximos passos**.
> Para o plano completo (modelo conceptual, prioridades, divisão por passos e ficheiros), ver `projeto_guide.md`.

**Ponto de situação (23/11/2026):** o projeto foi **reenquadrado** depois do segundo feedback do professor. Deixámos de modelar só a zona do estádio e passámos a modelar **uma cidade inteira**, em que o jogo é apenas **um cenário** de pico de procura. O **modelo conceptual novo está fechado** (documento da proposta e secção 2 do `projeto_guide.md`). O código em Mesa já corre, mas ainda segue o modelo antigo: o próximo passo é **adaptá-lo ao novo modelo** (Passo 1 do guia).

---

## 1. Linha do tempo

| Fase | O quê | Estado |
|---|---|---|
| 0 | Escolha do tema e primeira proposta | ✅ |
| 0 | Respostas às Aulas práticas 1, 2 e 3 (primeira versão) | ✅ (atualizadas no reenquadramento) |
| 0 | Divisão de tarefas, repositório e branches | ✅ |
| 1 | Esqueleto do simulador em SimPy | ✅ (substituído) |
| 1 | **1.º feedback do professor:** Mesa, modelo abstrato, prioridades, baseline vs. cenários | ✅ |
| 1 | Migração do simulador para Mesa + visualização no browser | ✅ |
| 2 | **2.º feedback do professor:** modelar só o estádio esconde o custo de tirar carros à cidade | ✅ |
| 2 | **Reenquadramento:** cidade inteira + pico do evento como cenário; novo modelo conceptual | ✅ |
| 2 | Nova lista de prioridades e divisão do trabalho por passos | ✅ |
| 3 | **Passo 0:** as duas leem o modelo e validam-no com o professor | ⏳ Agora |
| 3 | **Passo 1:** adaptar o núcleo do código ao novo modelo | ⏳ A seguir |

---

## 2. Fase 0 – Conceção inicial

### 2.1 Organização

- **Divisão:** a **Pessoa A (colega)** fica com a **procura** (passageiros) e a **Pessoa B (Diana)** com a **oferta** (carros). O núcleo, as experiências e a visualização fazem-se em conjunto.
- **Repositório:** Python, com `main` → `develop` → `feature/...`, nomes e código em inglês.

---

## 3. Fase 1 – O primeiro simulador

### 3.1 Esqueleto em SimPy

Construímos um primeiro esqueleto em **SimPy** (eventos discretos): entidades, interfaces, versões provisórias da procura e da oferta, motor, KPIs e testes.

**O que são "valores provisórios":** valores simples e inventados (ex.: "20 pedidos por minuto") para o simulador correr **antes** de os valores finais estarem decididos. Servem para não ficarmos à espera uma da outra, testar a lógica com casos calculados à mão e detetar cedo problemas de encaixe. Estão marcados com `PLACEHOLDER` no código.

### 3.2 Primeiro feedback do professor

Recomendou: usar o **Mesa**, um modelo **abstrato e esquemático**, uma **lista de prioridades** e um **baseline comparado com cenários de políticas diferentes**.

### 3.3 Migração para Mesa

O esqueleto foi reescrito em Mesa, com passageiros e carros como **agentes** e o tempo em **passos de 30 segundos**, numa **grelha abstrata** com o estádio no centro. Aproveitou-se quase tudo: estados, matching, KPIs, contratos e testes. A visualização passou a correr no browser com o Solara (`solara run viz/app.py`).

**Problema resolvido:** o Mesa atual precisa de **Python 3.12**. Com Python 3.10 instalava-se uma versão antiga, sem visualização. As duas têm de usar um ambiente com Python 3.12 (ver `projeto_guide.md`, secção 7).

---

## 4. Fase 2 – O reenquadramento

### 4.1 Segundo feedback do professor

O professor apontou que **mandar os Ubers todos para o estádio deixa a cidade sem Ubers**, e que o nosso modelo não conseguia mostrar isso.

### 4.2 O que estava errado

| Problema | Consequência |
|---|---|
| Começámos pelo cenário (o estádio e os dados de NYC) e não pela pergunta | O estádio virou o projeto todo, quando o Tema 14 é sobre **gerir uma frota** |
| A fronteira do sistema era só a zona do estádio | Reposicionar carros para o estádio **parecia sempre bom**, porque o custo (a cidade sem carros) não existia no modelo |
| Passámos para o código antes de o modelo conceptual estar sólido | Cada mudança de ideia obrigava a mexer em tudo e baralhava o trabalho |
| Mudámos de abordagem várias vezes seguidas | Perdeu-se o fio à meada |
| "Otimizar" não estava definido | Não era claro como escolher a melhor política |

### 4.3 O que decidimos

- **Mantemos o Tema 14.** O problema não era o tema, era o enquadramento.
- **Modelamos uma cidade inteira** (grelha abstrata), com **procura normal em todo o lado** e um **pico de procura numa zona** quando acaba o jogo.
- **A pergunta passa a ser:** *como deve a plataforma gerir a frota durante um pico de procura localizado, sem deixar o resto da cidade sem serviço?*
- **Duas decisões a estudar:** a regra de matching (imediato vs. em lote) e o reposicionamento de carros para o evento, com um **limite de X% da frota**.
- **KPIs separados** para a zona do evento e para o resto da cidade.
- **Critério de otimização definido à partida:** minimizar as desistências no evento, sem as desistências na cidade aumentarem mais de 2 pontos percentuais face a um dia normal.
- **Experiências E0 a E5** (dia normal, baseline, matching em lote, reposicionamento sem limite, reposicionamento com limite X, evento grande).
- **Pooling sai do núcleo** e passa a extensão.
- **Nova Iorque:** a cidade é abstrata; os dados de NYC servem só, se houver tempo, para dar valores realistas aos parâmetros (prioridade 4).
- **Mapa real com mesa-geo:** só como extensão (prioridade 5).
- **Regra nova:** nada de código novo sem estar primeiro no modelo conceptual.

O modelo conceptual completo, organizado segundo **Robinson (2008)**, está no documento da proposta e na secção 2 do `projeto_guide.md`. As respostas às Aulas 1–3 foram atualizadas para este enquadramento.

---

## 5. O que existe no código hoje

O código corre e os testes passam, mas **ainda segue o modelo antigo** (só estádio). A última coluna diz o que muda.

| Ficheiro | O que faz hoje | O que falta para o novo modelo | Dono |
|---|---|---|---|
| `config/base.yaml` | Parâmetros do modelo antigo | Início em −60 min, procura normal, curva do pico, zona do evento, limite X, paciência de 10 min (máx. 30) | Juntas |
| `model.py` | Modelo Mesa: pedidos só no estádio | Relógio a começar em −60 min; duas fontes de procura; passo de reposicionamento | Juntas |
| `world/grid_world.py` | Grelha 41×41 com o estádio no centro | Zona do evento; sorteio de células em toda a cidade | Juntas |
| `core/entities.py` | Estados do passageiro e do carro | Tipo de passageiro (cidade/evento) | Juntas |
| `core/interfaces.py` | Contratos entre as partes | Origem e tipo do passageiro; contrato do reposicionamento | Juntas |
| `core/metrics.py` | KPIs gerais | Passa a juntar os KPIs da procura e da oferta | Juntas |
| `demand/arrivals.py` | Taxa constante de pedidos no estádio | Procura normal + curva do pico | **A** |
| `demand/passenger.py` | Agente Passageiro (paciência e desistência) | Origem e tipo | **A** |
| `supply/fleet.py` | Carros à volta do estádio | Carros espalhados pela cidade | **B** |
| `supply/vehicle.py` | Agente Carro (recolhe, entrega, conta km) | Estado "a reposicionar" | **B** |
| `supply/matching.py` | Matching imediato | Matching em lote (passo 3) | **B** |
| `viz/app.py` | Grelha, 2 gráficos, sliders | Zona do evento sombreada, legenda, minutos, KPIs evento vs. cidade | Juntas |
| `tests/test_model.py` | 6 testes a passar | Ajustar ao novo relógio e às duas fontes de procura | Juntas |

### Os 6 testes atuais (verificação)

| Teste | Verifica | Tipo |
|---|---|---|
| `test_request_balance` | Servidos + abandonados + em curso = total | Balanço de entidades |
| `test_same_seed_same_result` | A mesma semente dá o mesmo resultado | Reprodutibilidade |
| `test_single_trip_by_hand` | 1 carro a 3 células, destino a 4: recolha ao passo 3, chegada ao passo 7 | Caso calculado à mão |
| `test_no_vehicles_nobody_served` | Sem carros, ninguém é servido | Caso extremo |
| `test_huge_fleet_nobody_abandons` | Com carros de sobra, ninguém desiste | Caso extremo |
| `test_more_vehicles_less_waiting` | Mais carros nunca pioram a espera | Monotonia |

Continuam válidos no novo modelo; só precisam de pequenos ajustes no Passo 1. Vão para a secção de **verificação** do relatório final.

---

## 6. Próximos passos

### Passo 0 – Validar o modelo (agora)
- [ ] A colega lê o modelo conceptual (documento da proposta ou `projeto_guide.md`, secção 2)
- [ ] As duas concordam com o modelo, as experiências e o critério de otimização
- [ ] Apresentar ao professor: *"Vamos modelar uma cidade com um serviço de TVDE e estudar como gerir a frota num pico de procura localizado, como a saída de um jogo, sem prejudicar o resto da cidade."*

### Passo 1 – Adaptar o núcleo (juntas, na `develop`)
- [ ] `config/base.yaml`: novos parâmetros
- [ ] `world/grid_world.py`: zona do evento
- [ ] `core/entities.py` e `core/interfaces.py`: tipo e origem do passageiro
- [ ] `model.py`: relógio de −60 a +120 min, duas fontes de procura, passo de reposicionamento
- [ ] `tests/test_model.py`: ajustar

### Passo 2 – Prioridade 1 (em paralelo)

**Pessoa A – Procura, a colega** (`feature/demand-city-event`)
- [ ] Procura normal em toda a cidade e pico do evento no estádio
- [ ] Passageiro com tipo e origem; paciência com máximo
- [ ] `demand/metrics.py`: espera e desistências por zona
- [ ] `tests/test_supply.py`: testes da parte da oferta

**Pessoa B – Oferta, Diana** (`feature/supply-fleet`)
- [ ] Frota espalhada pela cidade; carro livre fica parado
- [ ] Rever movimento, contadores de km e matching imediato
- [ ] `supply/metrics.py`: utilização, km vazios, emissões
- [ ] `tests/test_demand.py`: testes da parte da procura

**Juntas**
- [ ] `feature/visualization`: zona do evento sombreada, estádio marcado, legenda, minutos
- [ ] `feature/experiments`: correr E0 e E1 com 30 replicações
- [ ] Tag `v0.1-mvp`

Os passos 3 a 7 (políticas, robustez, dados de NYC, relatório e extensões) estão detalhados no `projeto_guide.md`, secção 5.

---