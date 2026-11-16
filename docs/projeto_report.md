# Relatório de Progresso do Projeto
 
> Este documento explica **o que já foi feito, porquê e em que ponto estamos**.
> Para o plano completo (divisão por pessoa, fases, branches), ver `projeto_guide.md`.
 
**Ponto de situação:** a **Fase 1 está concluída**. Temos um simulador em **Mesa** a correr do início ao fim, com visualização no browser, KPIs e 6 testes de verificação a passar. O próximo passo é a **Prioridade 1 por pessoa**: cada uma completa os seus agentes na sua branch.
 
---
 
## 1. Resumo do que está feito
 
| Fase | O quê | Estado |
|---|---|---|
| 0 | Escolha do tema e proposta | ✅ |
| 0 | Respostas às perguntas das Aulas práticas 1, 2 e 3 | ✅ |
| 0 | Divisão de tarefas, organização do repositório e branches | ✅ |
| 1 | Esqueleto do simulador (primeira versão, em SimPy) | ✅ (substituído) |
| 1 | Feedback do professor e mudança de abordagem | ✅ |
| 1 | Migração do simulador para Mesa | ✅ |
| 1 | Visualização a funcionar no browser | ✅ |
| 2 | Prioridade 1 por pessoa (agentes completos, visualização melhorada) | ⏳ A seguir |
 
---
 
## 2. Fase 0 – Conceção
 
### 2.1 Escolha do tema
 
Só podíamos escolher entre os temas 1, 2, 5, 6, 8 e 14. Analisámos várias ideias e ficámos com duas finalistas, ambas sobre a saída de um jogo no **Yankee Stadium** (Nova Iorque):
 
| Proposta | Tema | Ideia |
|---|---|---|
| 1 | 02 – Espaços urbanos lotados | Fila e plataformas do metro depois do jogo |
| 2 | 14 – Ride-sharing | Uber/TVDE depois do jogo |
 
**Escolhemos a Proposta 2 (Tema 14)** porque:
 
- os dados públicos de Nova Iorque têm, para cada viagem de Uber/Lyft, a **hora do pedido e a hora da recolha**, ou seja, o **tempo de espera real**, o que é ótimo para validar o modelo;
- o enunciado do Tema 14 pede exatamente o que queremos estudar: comparar políticas de matching, pooling e reposicionamento sob picos de procura.
### 2.2 Respostas às Aulas práticas 1–3
 
Ficaram definidas no documento da proposta:
 
- **Aula 1:** variáveis do sistema, entidades e propriedades, processos estocásticos (chegada de pedidos, destinos, paciência, tempos de viagem) e tipo de modelo (sobretudo **prescritivo**, com base descritiva e preditiva).
- **Aula 2:** variáveis exógenas/endógenas e controláveis/não controláveis, perguntas a responder, variáveis de decisão (políticas), classificação do modelo e conceitos (eventos, estados, processos, atividades, objetos, agentes).
- **Aula 3:** objetivos reformulados, modelo conceptual (ciclo do passageiro e do carro, ligados pela plataforma), modelos lógicos (matching imediato, em lote, pooling, reposicionamento, desistência) e requisitos de dados.
> ⚠️ Com a mudança para Mesa, há um ponto a atualizar: na Aula 2, o modelo passa de "eventos discretos" para **"baseado em agentes, com tempo discreto (passos)"**.
 
### 2.3 Organização
 
- **Divisão:** uma pessoa fica com a **procura** (passageiros), a outra com a **oferta** (carros); o núcleo, as experiências e a visualização fazem-se em conjunto.
- **Repositório:** Python, com `main` → `develop` → `feature/...`, nomes e código em inglês.
- **README** com objetivos, estrutura, branches e divisão de tarefas.
---
 
## 3. Fase 1 – O simulador
 
### 3.1 Primeira versão: esqueleto em SimPy
 
Construímos um primeiro esqueleto do simulador em **SimPy** (simulação de eventos discretos), passo a passo:
 
1. estrutura do repositório, `.gitignore`, `requirements.txt` e `config/base.yaml`;
2. entidades (pedido e carro, com os seus estados);
3. interfaces (contratos entre as partes) e versões provisórias da procura, dos tempos de viagem, da frota e do matching;
4. motor de simulação;
5. cálculo dos KPIs;
6. testes de verificação.
**O que são "valores provisórios":** valores simples e inventados (ex.: "20 pedidos por minuto", "250 carros") para o simulador correr **antes** de os dados reais estarem prontos. Servem para:
 
- não ficarmos à espera uma da outra;
- testar a lógica com casos que conseguimos calcular à mão;
- detetar cedo problemas de encaixe entre as partes.
Estão marcados no código com `PLACEHOLDER` e vão ser substituídos pelos valores calibrados com os dados de Nova Iorque.
 
### 3.2 Feedback do professor
 
O professor recomendou:
 
- usar o **Mesa** (simulação baseada em agentes);
- um modelo **mais abstrato e esquemático**;
- uma **lista de prioridades**;
- um **cenário baseline** e **cenários com políticas diferentes**;
- definir muito bem o que queremos fazer.
### 3.3 Decisão tomada
 
- **Grelha abstrata com o estádio no centro**, em vez do mapa real de Nova Iorque.
- **Valores reais de NYC** para calibrar o modelo (prioridade 3).
- **Mapa real de NYC** só como extensão, se houver tempo (prioridade 5).
- O "mundo" fica separado do resto do modelo, para a extensão ser possível sem refazer tudo.
### 3.4 Migração para Mesa
 
O esqueleto foi reescrito em Mesa. **Aproveitou-se quase tudo:** os estados, o matching, os KPIs, os contratos e a lógica dos testes. O que mudou foi o motor: passou de eventos discretos para **passos de 30 segundos**, com passageiros e carros como **agentes**.
 
**Ficheiros removidos:** `core/simulation.py` (motor SimPy), `supply/travel_times.py` (substituído pela grelha), `tests/test_core.py` (substituído por `tests/test_model.py`) e a pasta `demo/` (a demo passa a ser `viz/app.py`).
 
### 3.5 Problema resolvido: versão do Python
 
O ambiente tinha **Python 3.10**, e o Mesa atual precisa de **Python 3.12**. Com o 3.10 instalava-se uma versão antiga do Mesa, sem a visualização. **Solução:** criar um ambiente conda novo com Python 3.12 (ver `projeto_guide.md`, secção 10). **As duas temos de usar Python 3.12.**
 
---
 
## 4. O que existe agora no código
 
| Ficheiro | O que faz | Estado | Dono |
|---|---|---|---|
| `config/base.yaml` | Todos os parâmetros do baseline, organizados em `world`, `demand`, `supply`, `policy` e `kpi` | ✅ (valores provisórios) | Juntas |
| `src/rideshare_sim/model.py` | O modelo Mesa: a cada passo chegam pedidos, os passageiros verificam a paciência, a plataforma faz o matching e os carros andam | ✅ | Juntas |
| `world/grid_world.py` | Grelha de 41×41 com o estádio no centro; distâncias "Manhattan" (como ruas em quadrícula), tempos de viagem, movimento e sorteio de destinos | ✅ | Juntas |
| `core/entities.py` | Estados do passageiro e do carro (iguais ao modelo conceptual) | ✅ | Juntas |
| `core/interfaces.py` | Contratos: o que o mundo, a procura e o matching têm de oferecer | ✅ | Juntas |
| `core/metrics.py` | KPIs em tempo real (para os gráficos) e no fim de cada replicação | ✅ | Juntas |
| `demand/passenger.py` | Agente Passageiro: espera e desiste quando a paciência acaba | ✅ base | **A** |
| `demand/arrivals.py` | Quantos pedidos aparecem em cada passo (taxa constante) | 🟡 provisório | **A** |
| `supply/vehicle.py` | Agente Carro: anda uma célula por passo, recolhe e entrega, conta km vazios e com passageiro | ✅ base | **B** |
| `supply/fleet.py` | Cria os carros espalhados à volta do estádio | 🟡 provisório | **B** |
| `supply/matching.py` | Matching imediato: quem espera há mais tempo fica com o carro livre mais próximo | ✅ | **B** |
| `viz/app.py` | Visualização no browser: grelha, 2 gráficos, sliders | ✅ base | Juntas |
| `tests/test_model.py` | 6 testes de verificação | ✅ a passar | Juntas |
 
---
 
## 5. Valores atuais do baseline (provisórios)
 
| Parâmetro | Valor |
|---|---|
| 1 passo | 30 segundos |
| Grelha | 41 × 41 células, estádio em (20, 20) |
| 1 célula | 250 m (um carro a 30 km/h anda 1 célula por passo) |
| Pedidos | 20 por minuto durante 60 minutos (cerca de 1 200 pedidos) |
| Paciência | Exponencial, média de 15 min, máximo de 45 min |
| Frota | 250 carros, até 10 células do estádio |
| Matching | Imediato, sem pooling, sem reposicionamento |
 
Com uma replicação de teste, o baseline dá cerca de **20% de pedidos abandonados** e **11 minutos de espera média**. O número de carros foi escolhido para o sistema ficar **sob pressão sem colapsar**: com 80 carros quase 70% desistiam, e não se veria diferença entre políticas. **Estes números vão mudar** quando calibrarmos com os dados de NYC.
 
---
 
## 6. Verificação: os 6 testes
 
| Teste | Verifica | Tipo |
|---|---|---|
| `test_request_balance` | Nenhum pedido "desaparece": servidos + abandonados + em curso = total | Balanço de entidades |
| `test_same_seed_same_result` | A mesma semente dá exatamente o mesmo resultado | Reprodutibilidade |
| `test_single_trip_by_hand` | 1 carro a 3 células e destino a 4 células: recolha ao passo 3, chegada ao passo 7, km certos | Caso calculado à mão |
| `test_no_vehicles_nobody_served` | Sem carros, ninguém é servido e todos desistem | Caso extremo |
| `test_huge_fleet_nobody_abandons` | Com carros de sobra, ninguém desiste | Caso extremo |
| `test_more_vehicles_less_waiting` | Mais carros nunca aumentam a espera nem as desistências | Monotonia |
 
Esta tabela pode ir quase tal e qual para a secção de **verificação** do relatório final.
 
**Algo que os testes já nos ensinaram:** na primeira versão, com paciência exponencial sem limite, alguns passageiros tinham paciência enorme e ainda estavam à espera quando a simulação parava. Por isso limitámos a paciência a 45 minutos (`patience_max_min`).
 
---
 
## 7. A visualização
 
Corre com `solara run viz/app.py` e abre no browser (em `localhost`, só no nosso computador).
 
- **Grelha:** 🟢 carro livre · 🟠 a caminho da recolha · 🔵 com passageiro · 🟥 passageiros à espera no estádio.
- **Gráfico 1:** pedidos à espera, servidos e abandonados ao longo do tempo.
- **Gráfico 2:** carros livres vs. ocupados.
- **Sliders:** número de carros, pedidos por minuto e paciência média.
**Porquê uma página web?** O Mesa usa o **Solara** para criar as visualizações: escrevemos só Python e ele gera a página. É a visualização oficial do Mesa, e é ótima para a demo, porque se mexe nos sliders e o efeito aparece na hora.
 
**É a versão base.** Ainda vai ser melhorada: estádio bem visível, legenda, tempo em minutos, painel de KPIs, seletor de cenários e textos em português.
 
---
 
## 8. Pressupostos e limitações atuais
 
| Pressuposto | Nota para o relatório |
|---|---|
| Valores provisórios (procura, frota, paciência) | Substituídos na prioridade 3 pelos dados de NYC |
| Movimento "Manhattan": primeiro na horizontal, depois na vertical | Simplificação de ruas em quadrícula; explica as "cruzes" de carros na visualização |
| Velocidade constante (30 km/h), sem trânsito | Pode ser refinado com os tempos reais de NYC |
| Destinos uniformes na grelha (a pelo menos 6 células do estádio) | Pode passar a seguir a distribuição real de destinos |
| Fator de emissões de 0,15 kg CO₂/km | **Provisório:** precisa de um valor com fonte citada |
| Um passageiro por carro | Muda quando entrar o pooling (prioridade 4) |
 
---
 
## 9. Próximos passos
 
### Pessoa A – Procura (`feature/demand-agents`)
- [ ] Rever o agente Passageiro e a paciência (distribuição, limite)
- [ ] Preparar a curva de chegadas com pico depois do jogo (ainda provisória)
- [ ] Escrever testes para a parte da oferta (verificação cruzada)
### Pessoa B – Oferta (`feature/supply-agents`)
- [ ] Rever o agente Carro e o movimento
- [ ] Rever a criação da frota (posição inicial, número)
- [ ] Escrever testes para a parte da procura (verificação cruzada)
 
### Juntas
- [ ] `feature/visualization`: estádio visível, legenda, minutos, painel de KPIs, seletor de cenários
- [ ] `feature/experiments`: correr 30 replicações do baseline e calcular médias e intervalos de confiança
- [ ] Atualizar o README (ainda descreve a versão em SimPy)
- [ ] Atualizar a classificação do modelo na resposta à Aula 2 (agora é baseado em agentes)
- [ ] Quando a prioridade 1 estiver completa: tag `v0.1-mvp`
---
 
## 10. Questões em aberto
 
- Quem fica com a **procura (A)** e quem fica com a **oferta (B)**?
- Quais são os **prazos** das entregas e da demo?
- Confirmar com o professor se a calibração com dados de NYC (prioridade 3) e o mapa real (prioridade 5) são valorizados.
- Escolher uma **fonte para o fator de emissões**.