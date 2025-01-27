# API de Previsão de Preços de Bitcoin com Prophet

Esta API permite a coleta de dados históricos de preços do Bitcoin, o treinamento de um modelo de previsão utilizando o Prophet e a realização de previsões para estimar o tempo necessário para atingir uma meta de lucro percentual.

## Funcionalidades Principais

1. **Coleta de Dados**  
   - Obtém dados históricos de preços de Bitcoin de uma exchange e os armazena localmente em um banco de dados SQLite.
   - O banco de dados é automaticamente limpo antes de cada nova coleta de dados.

2. **Treinamento do Modelo**  
   - Treina um modelo de previsão Prophet usando os dados coletados.

3. **Previsão de Lucro-Alvo**  
   - Estima quantos dias serão necessários para atingir uma meta de lucro percentual especificada.

4. **Coleta Completa de Dados**  
   - Permite baixar todo o histórico de preços disponível na Binance desde 2017.

---

## Requisitos

Antes de iniciar, instale as dependências necessárias com o seguinte comando:

> pip install fastapi uvicorn ccxt joblib pandas numpy prophet sqlite3

---

## Como Executar

1. Inicialize o banco de dados e execute a API com o comando:

> python main.py

2. Acesse a API através da URL:

> http://127.0.0.1:8000

3. Utilize a interface de documentação interativa do Swagger para explorar os endpoints:

> http://127.0.0.1:8000/docs

---

## Endpoints da API e Exemplos de Uso

### 1. Coletar dados e inserir no banco de dados

Este endpoint coleta dados de preços históricos de Bitcoin de uma exchange e os armazena no banco de dados local. O banco de dados será automaticamente **limpo antes da coleta** para evitar duplicação de dados.

- **Método:** `POST`  
- **URL:** `/fetch-data`  
- **Parâmetros:**  
  - `symbol` (string): Par de negociação (ex: `BTC/USDT`)
  - `timeframe` (string): Intervalo de tempo dos dados (ex: `1d`, `1h`)
  - `limit` (int): Quantidade de registros a serem coletados (ex: `1000`)
  - `fetch_all` (bool): Se verdadeiro, coleta todos os dados disponíveis desde 2017.

**Exemplo de requisição via cURL (coletando dados limitados):**

> curl -X POST "http://127.0.0.1:8000/fetch-data" \
>   -H "Content-Type: application/json" \
>   -d '{"symbol": "BTC/USDT", "timeframe": "1d", "limit": 1000, "fetch_all": false}'

**Exemplo de requisição via cURL (coletando todos os dados históricos):**

> curl -X POST "http://127.0.0.1:8000/fetch-data" \
>   -H "Content-Type: application/json" \
>   -d '{"symbol": "BTC/USDT", "timeframe": "1d", "fetch_all": true}'

**Resposta esperada:**

> {
>   "status": "OK",
>   "rows_inserted": 3650
> }

---

### 2. Treinar o modelo

Este endpoint treina um modelo Prophet com os dados disponíveis no banco de dados.

- **Método:** `POST`  
- **URL:** `/train-model`  
- **Parâmetros:** Nenhum

**Exemplo de requisição via cURL:**

> curl -X POST "http://127.0.0.1:8000/train-model"

**Resposta esperada:**

> {
>   "status": "trained",
>   "last_date": "2024-01-10",
>   "last_price": 47200.0,
>   "rows_used": 2000
> }

---

### 3. Fazer previsões para atingir um lucro-alvo

Este endpoint utiliza o modelo Prophet para prever em quantos dias o preço do Bitcoin atingirá um lucro percentual especificado.

- **Método:** `POST`  
- **URL:** `/predict-days-profit`  
- **Corpo da requisição (JSON):**  
  - `target_profit` (float): Percentual de lucro desejado (ex: `10.0`)
  - `max_days` (int): Número máximo de dias para previsão (ex: `365`)

**Exemplo de requisição via cURL:**

> curl -X POST "http://127.0.0.1:8000/predict-days-profit" \
>   -H "Content-Type: application/json" \
>   -d '{"target_profit": 10.0, "max_days": 365}'

**Resposta esperada:**

> {
>   "status": "OK",
>   "days_needed": 150,
>   "target_profit": 10.0
> }

---

## Observações

- O banco de dados é automaticamente limpo antes da coleta de dados para garantir previsões consistentes.
- O treinamento do modelo deve ser realizado após cada nova coleta de dados para garantir previsões mais precisas.
- A previsão se baseia em dados históricos e não garante exatidão em cenários futuros.
- O projeto pode ser facilmente expandido para suportar outros ativos além do Bitcoin.

---

## Interface Web

Este projeto inclui uma interface web simples para interação com a API, localizada nos arquivos:

- `index.html` → Interface de usuário para coletar dados, treinar modelo e fazer previsões.
- `script.js` → Contém as funções de interação com a API via AJAX.

Para utilizar a interface web, basta abrir o arquivo `index.html` em um navegador e preencher os campos necessários.

---

## Licença

Este projeto está licenciado sob a licença MIT.
