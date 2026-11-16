# Guia do Projeto – Modelação e Simulação 2026/27

> Este guia explica **o que vamos fazer, como está organizado e quem faz o quê**.
> Para saber **o que já está feito**, ver `projeto_report.md`.

---

## 1. O projeto numa frase

Simulamos um serviço de TVDE (tipo Uber) no momento em que acaba um jogo num estádio: milhares de pessoas pedem carro ao mesmo tempo e não há carros para todos. Comparamos diferentes **formas de a plataforma organizar a frota** para ver qual reduz mais a espera e as desistências, e a que custo.

- **Tema:** 14 – *Ride-Sharing Matching and Fleet Management*
- **Grupo:** 2 pessoas
- **Ferramenta:** Python + **Mesa** (simulação baseada em agentes), recomendada pelo professor

---

## 2. Problema e pergunta de investigação

Quando o jogo acaba, a procura dispara de repente, mas os carros livres estão espalhados pela cidade. Se a plataforma emparelhar mal pedidos e carros:

- as pessoas esperam muito;
- algumas desistem (e vão de metro);
- os carros fazem muitos quilómetros vazios.

**Pergunta principal:** que regras de operação (matching, pooling, reposicionamento) reduzem mais a espera e as desistências após um jogo, e a que custo em quilómetros vazios e emissões?

---

## 3. A abordagem (e porquê)

O professor recomendou:

1. **Usar o Mesa** (biblioteca de Python para simulação baseada em agentes);
2. um modelo **abstrato e esquemático**;
3. uma **lista de prioridades**;
4. um **cenário baseline** comparado com **cenários com políticas diferentes**.

Por isso, a abordagem é:

| Decisão | O quê | Porquê |
|---|---|---|
| Mundo | **Grelha abstrata** de 41×41 células com o **estádio no centro** | Mais fácil de verificar, de visualizar e de explicar; foco nas políticas e não na geografia |
| Valores | Começam **provisórios**; depois são **calibrados com dados reais de Nova Iorque** (pico de pedidos, durações, espera real) | Dá realismo ao modelo sem o trabalho de construir um mapa |
| Mapa real de NYC | **Só como extensão**, se houver tempo | Dá muito trabalho (zonas, matriz de tempos, visualização com mesa-geo) e não é o centro da cadeira |

**Ideia importante:** o "mundo" (grelha) está separado do resto do modelo. Os agentes e as políticas só perguntam ao mundo *"qual a distância?"* e *"para onde dou o próximo passo?"*. Assim, se houver tempo, trocar a grelha pelo mapa real de NYC é trocar **uma peça**, não refazer o projeto.

---

## 4. Como funciona o modelo

### Agentes

| Agente | O que faz | Estados |
|---|---|---|
| **Passageiro** | Aparece no estádio, pede carro, espera; desiste se a espera passar a paciência | à espera → com carro atribuído → em viagem → servido (ou desistiu) |
| **Carro** | Vai buscar o passageiro, leva-o ao destino e fica livre lá | livre → a caminho da recolha → ocupado → livre (ou a reposicionar-se) |
| **Plataforma** (o modelo) | Decide que carro vai buscar que passageiro (matching) | – |

### Um passo da simulação (1 passo = 30 segundos)

1. Chegam **pedidos novos** ao estádio;
2. os passageiros à espera **verificam a paciência** (desistem ou não);
3. a plataforma faz o **matching**;
4. os carros **andam uma célula** (1 célula = 250 m, cerca de 30 km/h);
5. recolhem-se os **dados para os gráficos**.

A simulação acaba quando já não chegam pedidos e não há ninguém à espera nem em viagem.

### Classificação do modelo (para o relatório)

Baseado em agentes · tempo discreto (passos) · estocástico · dinâmico · terminante.

---

## 5. Baseline, políticas e cenários

### Baseline (a referência)

Jogo normal · matching **imediato** · **sem** pooling · **sem** reposicionamento.

### Políticas a testar (uma de cada vez em relação ao baseline)

| Cenário | O que muda |
|---|---|
| Baseline + **matching em lote** | Em vez de atribuir carro a cada pedido logo que chega, junta os pedidos durante uma janela curta e escolhe a melhor distribuição para todos ao mesmo tempo |
| Baseline + **reposicionamento** | Carros livres são enviados para perto do estádio antes do fim do jogo |
| Baseline + **pooling** | Dois passageiros com destinos próximos partilham o mesmo carro |
| *(se houver tempo)* Melhor combinação | Juntar as políticas que funcionaram |

### Cenários de procura

| Cenário | Descrição |
|---|---|
| Jogo normal | Procura habitual |
| Estádio esgotado | Mais pedidos ao mesmo tempo |
| Pico agravado | Chuva ou metro avariado: quase toda a gente quer TVDE |

### Métricas (KPIs)

- Tempo de espera (médio e percentil 90)
- % de pedidos abandonados
- Utilização dos carros
- Quilómetros vazios e emissões
- Tempo até a fila esvaziar
- Desvio médio (quando houver pooling)

Cada cenário corre **várias vezes** (replicações, ex.: 30), porque o modelo é aleatório; os resultados apresentam-se com **média e intervalo de confiança**.

---

## 6. Lista de prioridades

Se o tempo apertar, corta-se **de baixo para cima**: o projeto continua completo.

| Prioridade | O quê |
|---|---|
| **1. Essencial** | Modelo Mesa em grelha, baseline a funcionar, desistência por paciência, KPIs, visualização esquemática, replicações |
| **2. Importante** | Matching em lote, reposicionamento, cenários de procura |
| **3. Valores reais** | Calibrar a procura e as viagens com dados de Nova Iorque |
| **4. Desejável** | Pooling |
| **5. Extensão** | Mapa real de Nova Iorque |

**Regra:** o mapa real só começa depois de as prioridades 1 a 4 estarem feitas e com resultados.

---

## 7. Divisão por pessoa

Cada pessoa fica com **um lado do sistema** e faz tudo nesse lado: código, dados, testes e a sua parte da análise. O núcleo, as experiências e a visualização fazem-se em conjunto.

- **Pessoa A – Procura (passageiros):** _[nome]_
- **Pessoa B – Oferta (carros):** _[nome]_

| Prioridade | Pessoa A – Procura | Pessoa B – Oferta | Juntas |
|---|---|---|---|
| **1** | Agente Passageiro, chegadas, paciência e desistência | Agente Carro, movimento, frota, matching imediato | Modelo Mesa, grelha, KPIs, visualização, replicações |
| **2** | Cenários de procura (esgotado, pico agravado) | Matching em lote, reposicionamento | Baseline vs. cenários |
| **3** | Curva de pedidos e espera real (dados NYC) | Durações das viagens (dados NYC) | Comparar o baseline com a realidade |
| **4** | Pooling | Apoio ao pooling (entra no matching) | – |
| **5** | – | – | Mapa real de NYC |
| **Testes** | Testa a parte da oferta | Testa a parte da procura | Testes do modelo |

**Verificação cruzada:** cada pessoa escreve os testes da parte da **outra**. Assim apanhamos erros que quem os fez não vê, e as duas conhecem o projeto todo (importante para a defesa).

### Quem mexe em que ficheiros

| Pasta / ficheiro | Dono |
|---|---|
| `src/rideshare_sim/demand/` | Pessoa A |
| `src/rideshare_sim/supply/` | Pessoa B |
| `src/rideshare_sim/data/calibrate_demand.py` | Pessoa A |
| `src/rideshare_sim/data/calibrate_supply.py` | Pessoa B |
| `src/rideshare_sim/model.py`, `core/`, `world/` | Juntas |
| `viz/`, `experiments/`, `config/` | Juntas |

Se precisares de mexer numa parte "juntas" ou da outra pessoa, **avisa primeiro**.

---

## 8. Fases do trabalho

| Fase | O quê | Marco |
|---|---|---|
| 0 | Conceção: tema, proposta, respostas às Aulas 1–3 | ✅ Feito |
| 1 | Esqueleto do simulador + migração para Mesa | ✅ Feito |
| 2 | **Prioridade 1:** cada uma completa os seus agentes; visualização melhorada; replicações | Tag `v0.1-mvp` |
| 3 | **Prioridade 2:** políticas e cenários de procura; primeiras experiências baseline vs. cenários | Tag `v0.2-policies` |
| 4 | **Prioridade 3:** calibração com dados de NYC; validação | Tag `v0.3-calibrated` |
| 5 | **Prioridade 4:** pooling | – |
| 6 | Experiências finais, análise estatística, relatório e demo | Tag `v1.0-final` |
| 7 | *(se houver tempo)* Mapa real de NYC | – |

---

## 9. Repositório

### Estrutura

```
modelasimu/
├── README.md
├── requirements.txt
├── pyproject.toml
├── config/
│   ├── base.yaml                 # parâmetros do baseline
│   └── scenarios/                # um ficheiro por cenário (a criar)
├── data/                         # dados (os brutos não vão para o git)
├── notebooks/                    # exploração
├── src/rideshare_sim/
│   ├── model.py                  # o modelo Mesa (junta tudo)
│   ├── core/
│   │   ├── entities.py           # estados dos agentes
│   │   ├── interfaces.py         # contratos entre as partes
│   │   └── metrics.py            # KPIs
│   ├── world/
│   │   └── grid_world.py         # grelha abstrata
│   ├── demand/                   # PESSOA A
│   │   ├── passenger.py
│   │   └── arrivals.py
│   ├── supply/                   # PESSOA B
│   │   ├── vehicle.py
│   │   ├── fleet.py
│   │   └── matching.py
│   ├── data/                     # scripts de calibração (NYC)
│   └── analysis/                 # estatística dos resultados
├── viz/
│   └── app.py                    # visualização (página web local)
├── experiments/                  # correr baseline vs. cenários
├── tests/
│   └── test_model.py
├── proposta/
└── report/
```

### Branches

```
main                     ← versões estáveis (marcos)
└── develop              ← integração; tudo entra aqui primeiro
    └── feature/...      ← uma branch por tarefa
```

| Branch | Prioridade | Quem |
|---|---|---|
| `feature/demand-agents` | 1 | A |
| `feature/supply-agents` | 1 | B |
| `feature/visualization` | 1 | Juntas |
| `feature/experiments` | 1–2 | Juntas |
| `feature/demand-scenarios` | 2 | A |
| `feature/batch-matching` | 2 | B |
| `feature/relocation` | 2 | B |
| `feature/demand-calibration` | 3 | A |
| `feature/supply-calibration` | 3 | B |
| `feature/pooling` | 4 | A |
| `feature/nyc-map` | 5 | Juntas |

### Como trabalhar numa branch

```bash
git checkout develop
git pull
git checkout -b feature/demand-agents

# ... trabalhar, commits pequenos ...
git add <ficheiros>
git commit -m "demand: add patience cap to passenger"
git push -u origin feature/demand-agents
# abrir Pull Request para a develop no GitHub
```

- Cada Pull Request é **revisto pela outra pessoa** antes do merge.
- Antes de abrir o PR: `git pull origin develop` e `pytest` (os testes têm de passar).
- Nunca fazer commit diretamente na `main`.
- Branches, código e mensagens de commit em **inglês**; documentação em português.
- Prefixos dos commits: `demand:`, `supply:`, `core:`, `viz:`, `exp:`, `docs:`, `test:`.

---

## 10. Preparar o computador

O Mesa atual precisa de **Python 3.12**.

```bash
conda create -n modelasimu python=3.12 -y
conda activate modelasimu
cd <pasta-do-repositorio>
pip install -r requirements.txt
pip install -e .
```

No PyCharm: *Settings → Project → Python Interpreter → Add Interpreter → Conda →* `modelasimu`.

### Comandos do dia a dia

| Para… | Comando |
|---|---|
| Correr os testes | `pytest -v` |
| Abrir a visualização | `solara run viz/app.py` (abre no browser, em `localhost`) |
| Ver a versão do Mesa | `python -c "import mesa; print(mesa.__version__)"` |

A visualização **não se corre com o ▶ do PyCharm**: é uma página web local criada pelo Mesa (através do Solara), e corre-se com o comando acima.

---

## 11. Regras de ouro

1. **Respeitar os contratos** em `core/interfaces.py`: podes mudar o interior das tuas funções à vontade, mas não as assinaturas sem combinar.
2. **Parâmetros no `config/`**, nunca escritos diretamente no código.
3. **Os testes passam sempre** antes de um Pull Request.
4. **Valores provisórios** estão marcados com `PLACEHOLDER` no código: são para substituir.
5. **Âmbito pequeno e bem feito** é melhor do que muito e mal validado: seguir a lista de prioridades.