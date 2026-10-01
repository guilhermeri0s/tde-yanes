# Painel de Reposição de Prateleiras

Sistema web responsivo que monitora em tempo real o estoque de prateleiras (via balança) e alerta sobre reposição e produtos fora do padrão.

**Endereço publicado:** https://painel-reposicao.web.app
**Banco de dados:** Firebase Realtime Database (`painel-reposicao-default-rtdb`)
**Projeto Firebase:** `painel-reposicao`

## Atendimento aos requisitos da etapa

| Requisito | Como foi atendido |
|---|---|
| Sistema web responsivo (mobile e desktop) | Layout em grid fluido; abaixo de 760px a barra lateral vira barra superior e a tabela do histórico rola na horizontal |
| Banco de dados em nuvem | Firebase Realtime Database, com login via Firebase Authentication (e-mail/senha) |
| Comunicação em tempo real | `onValue` mantém prateleiras, alertas e histórico sincronizados; indicador "Tempo real: conectado" no topo usa `.info/connected` |
| CRUD | **C**: aba Admin → "Adicionar prateleira" · **R**: abas Prateleiras, Alertas, Movimentações e Histórico · **U**: abrir prateleira → "Salvar alterações" · **D**: abrir prateleira → "Remover prateleira" |
| Produtos, pesos e quantidades | Cada prateleira guarda um produto com peso unitário, peso atual e a quantidade disponível (`availableUnits`), recalculada e salva no banco a cada leitura |
| Registros de movimentação | Toda variação de quantidade gera uma entrada/saída em `movements`, exibida na aba Movimentações com filtros e totais |
| Estoque baixo | Status aviso (≤ 50%) e crítico (≤ 25%), aba Alertas e contador no topo |
| Interface funcional e organizada | Navegação por abas, cards com status por cor, modal de detalhe, filtros no histórico |
| Preparado para o sistema embarcado | Conta com papel `dispositivo` que só pode escrever o peso; contrato REST documentado abaixo e simulador `simulador_balanca.py` |

## Arquivos

- `index (1).html` — o sistema web completo (HTML, CSS e JS num arquivo só)
- `database.rules.json` — regras de segurança publicadas no Realtime Database
- `simulador_balanca.py` — simula a balança/ESP32 enviando peso para o Firebase
- `firestore.rules` — versão antiga (Firestore), não é mais usada

## Como acessar

1. Abra https://painel-reposicao.web.app
2. Entre com um usuário cadastrado no Firebase Authentication que tenha papel em `users/{uid}`.

Usuário já configurado: `guirios85@gmail.com` (papel **gerente**).

### Cadastrar mais usuários

1. Console do Firebase → Authentication → Usuários → **Adicionar usuário** (e-mail e senha).
2. Copie o **UID** do usuário criado.
3. Realtime Database → Dados → dentro de `users`, clique em **+** e crie a chave com o UID e o valor:
   ```json
   {"name": "Nome", "email": "email@exemplo.com", "role": "repositor"}
   ```
   Papéis: `gerente` (tudo, inclusive Admin), `repositor` (só visualiza), `dispositivo` (balança, só envia peso).

## Lógica

Cada prateleira guarda `unitWeightKg`, `toleranceFraction` e `capacityUnits`. A balança atualiza `currentWeightKg`. O painel calcula:

1. **Unidades** = peso atual ÷ peso unitário, arredondado.
2. **Ocupação** = unidades ÷ capacidade.
3. **Status**: `ok` (> 50%), `aviso` (25–50%), `crítico` (≤ 25%).
4. **Produto estranho**: o peso não fecha em unidades inteiras dentro da tolerância.

A quantidade calculada é salva em `shelves/{id}/availableUnits`. Cada variação de quantidade gera um registro em `movements` (entrada ou saída, de quanto para quanto) e cada mudança de status gera um registro em `history`. O status atual de cada prateleira fica em `shelfStatus/{id}` e é atualizado por transação, então mesmo com vários painéis abertos o evento é registrado uma única vez.

## Estrutura do banco

```
users/{uid}           { name, email, role }
shelves/{shelfId}     { name, productType, unitWeightKg, toleranceFraction,
                        capacityUnits, currentWeightKg, availableUnits, updatedAt }
shelfStatus/{shelfId} { stockStatus, anomaly, units }
movements/{entryId}   { shelfId, shelfName, productType, type: entrada|saida,
                        delta, fromUnits, toUnits, weightKg, timestamp }
history/{entryId}     { shelfId, shelfName, type, weightKg, occupancyPct, timestamp }
```

## Integração com o sistema embarcado

A balança não fala com o painel: ela escreve no banco e o painel reage em tempo real.

1. Crie no Authentication uma conta para o dispositivo (ex.: `balanca@reposicao.app`) e em `users/{uid}` coloque `"role": "dispositivo"`.
2. O dispositivo faz login pela API REST do Firebase Auth:
   ```
   POST https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=API_KEY
   {"email": "...", "password": "...", "returnSecureToken": true}
   ```
   e guarda o `idToken` (válido por 1 hora).
3. A cada leitura, envia o peso:
   ```
   PATCH https://painel-reposicao-default-rtdb.firebaseio.com/shelves/SHELF_ID.json?auth=ID_TOKEN
   {"currentWeightKg": 12.36, "updatedAt": {".sv": "timestamp"}}
   ```

As regras garantem que essa conta só altera `currentWeightKg` e `updatedAt` de prateleiras existentes.

### Simulador (sem hardware)

Edite `DEVICE_EMAIL` e `DEVICE_PASSWORD` em `simulador_balanca.py` com a conta do dispositivo e rode (Python 3, sem dependências):

```bash
python simulador_balanca.py ID_DA_PRATELEIRA              # leituras contínuas
python simulador_balanca.py ID_DA_PRATELEIRA --peso 5.15  # uma leitura só
```

O ID da prateleira aparece no Realtime Database, em `shelves`.

Sem a conta de dispositivo, o gerente pode simular pelo próprio painel: abra a prateleira e mude "Peso atual — teste manual".

## Republicar após alterar o HTML

```bash
npm i -g firebase-tools
firebase login
firebase deploy --only hosting,database --project painel-reposicao
```
(com `firebase.json` apontando `public` para a pasta do `index.html`).
