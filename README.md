Esse é o readme que precisa ser atualizado:

# API de Previsão de Preços de Bitcoin com Prophet

Esta API permite a coleta de dados históricos de preços do Bitcoin, o treinamento de um modelo de previsão utilizando o Prophet e a realização de previsões para estimar o tempo necessário para atingir uma meta de lucro percentual.

## Funcionalidades Principais

1. **Coleta de Dados**  
   - Obtém dados históricos de preços de Bitcoin de uma exchange e os armazena localmente em um banco de dados SQLite.
   
2. **Validação de Dados**  
   - Verifica os dados armazenados para garantir que estejam corretos e completos.

3. **Treinamento do Modelo**  
   - Treina um modelo de previsão Prophet usando os dados coletados.

4. **Previsão de Lucro-Alvo**  
   - Estima quantos dias serão necessários para atingir uma meta de lucro percentual especificada.

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

Este endpoint coleta dados de preços históricos de Bitcoin de uma exchange e os armazena no banco de dados local.

- **Método:** `POST`  
- **URL:** `/fetch-data`  
- **Parâmetros:**  
  - `symbol` (string): Par de negociação (ex: `BTC/USDT`)
  - `exchange_name` (string): Nome da exchange (ex: `binance`)
  - `timeframe` (string): Intervalo de tempo dos dados (ex: `1d`, `1h`)
  - `limit` (int): Quantidade de registros a serem coletados (ex: `2000`)

**Exemplo de requisição via cURL:**

> curl -X POST "http://127.0.0.1:8000/fetch-data?symbol=BTC/USDT&exchange_name=binance&timeframe=1d&limit=2000"

**Resposta esperada:**

> {
>   "status": "OK",
>   "rows_inserted": 2000
> }

---

### 2. Validar dados coletados

Este endpoint retorna um resumo dos dados armazenados no banco de dados, mostrando as primeiras e últimas linhas disponíveis.

- **Método:** `GET`  
- **URL:** `/validate-data`  
- **Parâmetros:**  
  - `limit` (int): Número de registros a serem exibidos (padrão: `5`)

**Exemplo de requisição via cURL:**

> curl -X GET "http://127.0.0.1:8000/validate-data?limit=5"

**Resposta esperada:**

> {
>   "total_rows": 2000,
>   "head": [
>     {"timestamp": "2024-01-01 00:00:00", "close": 45000.0},
>     {"timestamp": "2024-01-02 00:00:00", "close": 45500.0}
>   ],
>   "tail": [
>     {"timestamp": "2024-01-09 00:00:00", "close": 47000.0},
>     {"timestamp": "2024-01-10 00:00:00", "close": 47200.0}
>   ]
> }

---

### 3. Treinar o modelo

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

### 4. Fazer previsões para atingir um lucro-alvo

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

- Certifique-se de coletar novos dados antes de treinar o modelo para melhorar a precisão.
- A previsão se baseia em dados históricos e não garante exatidão em cenários futuros.
- Este projeto pode ser facilmente expandido para suportar outros ativos além do Bitcoin.

---

## Licença

Este projeto está licenciado sob a licença MIT.