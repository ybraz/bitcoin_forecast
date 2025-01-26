import os
import sqlite3
import joblib
import ccxt
import pandas as pd
import numpy as np

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from prophet import Prophet
from datetime import datetime

# -------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------
DATABASE_FILE = "bitcoin_data.db"
MODEL_FILE = "prophet_model.pkl"

app = FastAPI(
    title="API de Previsão BTC com Prophet",
    description="Coleta dados, treina modelo Prophet e faz previsões de longo prazo para atingir lucro alvo.",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens. Para produção, especifique domínios confiáveis.
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, OPTIONS, DELETE, etc.)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)


# -------------------------------------------------------------
# Pydantic
# -------------------------------------------------------------
class PredictRequest(BaseModel):
    target_profit: float  # em %
    max_days: int = 365

# -------------------------------------------------------------
# DB FUNCS
# -------------------------------------------------------------
def init_db():
    """
    Inicializa o banco de dados SQLite criando a tabela se não existir.
    """
    with sqlite3.connect(DATABASE_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS bitcoin_prices (
                timestamp TEXT PRIMARY KEY,
                close REAL
            )
        """)
        conn.commit()

def insert_data_to_db(df: pd.DataFrame):
    """
    Insere (ou ignora, se já existir) registros no banco.
    """
    with sqlite3.connect(DATABASE_FILE) as conn:
        c = conn.cursor()
        for _, row in df.iterrows():
            t = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""
                INSERT OR IGNORE INTO bitcoin_prices (timestamp, close) VALUES (?, ?)
            """, (t, row["close"]))
        conn.commit()

def fetch_data_from_db() -> pd.DataFrame:
    """
    Retorna todo o histórico de closes, ordenado por timestamp.
    """
    with sqlite3.connect(DATABASE_FILE) as conn:
        df = pd.read_sql_query("SELECT * FROM bitcoin_prices ORDER BY timestamp", conn)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

# -------------------------------------------------------------
# COLETA DE DADOS (CCXT)
# -------------------------------------------------------------
def fetch_bitcoin_data(symbol='BTC/USDT', exchange_name='binance', timeframe='1d', limit=2000):
    """
    Usa ccxt para buscar OHLCV do par/timeframe desejado.
    Retorna DataFrame com timestamp e close, ordenado.
    """
    exchange = getattr(ccxt, exchange_name)()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[['timestamp','close']].sort_values('timestamp')
    return df

# -------------------------------------------------------------
# TREINAMENTO DO MODELO (Prophet)
# -------------------------------------------------------------
def train_model():
    """
    1. Lê dados do DB
    2. Converte para formato Prophet (colunas ds, y)
    3. Cria e treina Prophet
    4. Salva em disco
    5. Retorna um 'summary' (opcional) ou a última data treinada
    """
    df = fetch_data_from_db().sort_values('timestamp')
    if len(df) < 10:
        raise ValueError("Poucos dados no DB para treinar.")

    # Formato Prophet: ds = datas, y = valor
    prophet_df = pd.DataFrame({
        'ds': df['timestamp'],
        'y': df['close']
    })

    # Instancia o modelo Prophet
    model = Prophet(
        # Você pode customizar sazonalidade, intervalo de mudança, etc.
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False
        # adicionar .add_seasonality(), .add_regressor(), etc. se quiser
    )
    model.fit(prophet_df)

    # Salva
    joblib.dump(model, MODEL_FILE)

    return {
        "status": "trained",
        "last_date": str(df.iloc[-1]['timestamp']),
        "last_price": float(df.iloc[-1]['close']),
        "rows_used": len(df)
    }

# -------------------------------------------------------------
# PREVISÃO E CÁLCULO DE DIAS ATÉ LUCRO-ALVO
# -------------------------------------------------------------
def predict_days_to_profit(target_profit: float, max_days: int=365):
    """
    Carrega o modelo Prophet, gera forecast para max_days futuros e
    checa o primeiro dia em que a previsão (yhat) ultrapassa o
    'last_close_real * (1 + target_profit/100)'.
    
    Retorna quantos dias são necessários ou -1 se não atingir até max_days.
    """
    if not os.path.exists(MODEL_FILE):
        raise FileNotFoundError("Modelo Prophet não encontrado. Treine primeiro.")

    model = joblib.load(MODEL_FILE)
    df = fetch_data_from_db().sort_values('timestamp')
    if len(df) < 10:
        raise ValueError("Poucos dados para previsão.")

    last_close_real = df.iloc[-1]['close']
    price_target = last_close_real * (1 + target_profit / 100.0)
    last_date = df.iloc[-1]['timestamp']

    # Cria um dataframe de futuro de max_days dias
    future = model.make_future_dataframe(periods=max_days, freq='D')
    forecast = model.predict(future)

    # No forecast, as colunas principais são: ds (data), yhat (previsão central),
    # yhat_lower, yhat_upper (intervalos de incerteza), etc.
    # Vamos iterar a partir do "dia seguinte" ao last_date.

    # Filtra apenas datas > last_date
    mask_future = forecast['ds'] > last_date
    forecast_future = forecast.loc[mask_future].copy()

    # Itera para achar o primeiro dia que yhat >= price_target
    for i, row in forecast_future.iterrows():
        if row['yhat'] >= price_target:
            # Descobre quantos dias do last_date até row['ds']
            delta_days = (row['ds'] - last_date).days
            return delta_days

    # Se não encontrou até o último dia, retorna -1
    return -1

# -------------------------------------------------------------
# ROTAS FASTAPI
# -------------------------------------------------------------
@app.get("/")
def root():
    return {"msg": "API de Previsão BTC com Prophet"}

@app.post("/fetch-data")
def api_fetch_data(symbol: str='BTC/USDT', exchange_name: str='binance', timeframe: str='1d', limit: int=2000):
    """
    Coleta dados via CCXT e salva no DB local.
    """
    try:
        df = fetch_bitcoin_data(symbol, exchange_name, timeframe, limit)
        insert_data_to_db(df)
        return {"status": "OK", "rows_inserted": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/validate-data")
def validate_data(limit: int = 5):
    """
    Exibe quantas linhas e head/tail do banco.
    """
    try:
        df = fetch_data_from_db().sort_values('timestamp')
        total_rows = len(df)
        head_ = df.head(limit).to_dict(orient='records')
        tail_ = df.tail(limit).to_dict(orient='records')
        return {
            "total_rows": total_rows,
            "head": head_,
            "tail": tail_
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train-model")
def api_train_model():
    """
    Treina (ou re-treina) o modelo Prophet com todo o histórico do DB.
    """
    try:
        result = train_model()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-days-profit")
def api_predict_days_to_profit(req: PredictRequest):
    """
    Gera previsão com Prophet para max_days e retorna quantos dias até atingir
    target_profit%. Se não atingir, retorna -1.
    
    (O parâmetro lag_window aqui não é usado, mas mantemos para compatibilidade)
    """
    try:
        days_needed = predict_days_to_profit(
            target_profit=req.target_profit,
            max_days=req.max_days
        )
        if days_needed == -1:
            return {
                "status": "NÃO ALCANÇOU NO HORIZONTE",
                "days_needed": None,
                "target_profit": req.target_profit
            }
        return {
            "status": "OK",
            "days_needed": days_needed,
            "target_profit": req.target_profit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------
# MAIN
# -------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
