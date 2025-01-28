import os
import sqlite3
import joblib
import ccxt
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
from prophet import Prophet

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Pydantic
# -------------------------------------------------------------
class PredictRequest(BaseModel):
    target_profit: float  
    max_days: int = 365

class FetchDataRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "1d"
    limit: int = 1000
    fetch_all: bool = False  # Parâmetro para baixar todos os dados históricos

# -------------------------------------------------------------
# DB FUNCS
# -------------------------------------------------------------
def init_db():
    with sqlite3.connect(DATABASE_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS bitcoin_prices (
                timestamp TEXT PRIMARY KEY,
                close REAL
            )
        """)
        conn.commit()

def clear_database():
    """
    Remove todos os registros do banco de dados SQLite.
    """
    with sqlite3.connect(DATABASE_FILE) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM bitcoin_prices")
        conn.commit()

def insert_data_to_db(df: pd.DataFrame):
    with sqlite3.connect(DATABASE_FILE) as conn:
        c = conn.cursor()
        for _, row in df.iterrows():
            t = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""
                INSERT OR IGNORE INTO bitcoin_prices (timestamp, close) VALUES (?, ?)
            """, (t, row["close"]))
        conn.commit()

def fetch_data_from_db() -> pd.DataFrame:
    with sqlite3.connect(DATABASE_FILE) as conn:
        df = pd.read_sql_query("SELECT * FROM bitcoin_prices ORDER BY timestamp", conn)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

# -------------------------------------------------------------
# COLETA DE DADOS (CCXT)
# -------------------------------------------------------------
def fetch_binance_data(symbol='BTC/USDT', timeframe='1d', limit=1000):
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[['timestamp', 'close']].sort_values('timestamp')
    return df

def fetch_all_binance_data(symbol='BTC/USDT', timeframe='1d'):
    exchange = ccxt.binance()
    since = exchange.parse8601('2017-01-01T00:00:00Z')
    all_data = []
    max_limit = 1000

    while True:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=max_limit)
        if not ohlcv:
            break
        all_data.extend(ohlcv)
        since = ohlcv[-1][0] + 1
        print(f"Baixados {len(all_data)} registros...")
        time.sleep(1)

    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[['timestamp', 'close']].sort_values('timestamp')
    return df

# -------------------------------------------------------------
# TREINAMENTO DO MODELO (Prophet)
# -------------------------------------------------------------
def train_model():
    df = fetch_data_from_db().sort_values('timestamp')
    if len(df) < 10:
        raise ValueError("Poucos dados no banco para treinar.")

    prophet_df = pd.DataFrame({
        'ds': df['timestamp'],
        'y': df['close']
    })

    model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
    model.fit(prophet_df)

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
def predict_days_to_profit(target_profit: float, max_days: int = 365):
    if not os.path.exists(MODEL_FILE):
        raise FileNotFoundError("Modelo Prophet não encontrado. Treine primeiro.")

    model = joblib.load(MODEL_FILE)
    df = fetch_data_from_db().sort_values('timestamp')
    if len(df) < 10:
        raise ValueError("Poucos dados para previsão.")

    last_close_real = df.iloc[-1]['close']
    price_target = last_close_real * (1 + target_profit / 100.0)
    last_date = df.iloc[-1]['timestamp']

    future = model.make_future_dataframe(periods=max_days, freq='D')
    forecast = model.predict(future)

    mask_future = forecast['ds'] > last_date
    forecast_future = forecast.loc[mask_future].copy()

    for _, row in forecast_future.iterrows():
        if row['yhat'] >= price_target:
            delta_days = (row['ds'] - last_date).days
            return delta_days

    return -1

# -------------------------------------------------------------
# ROTAS FASTAPI
# -------------------------------------------------------------
@app.get("/")
def root():
    return {"msg": "API de Previsão BTC com Prophet"}

@app.post("/fetch-data")
def api_fetch_data(req: FetchDataRequest):
    """
    Coleta dados da Binance e insere no banco de dados.
    Se `fetch_all` for True, limpa o banco e coleta todo o histórico.
    """
    try:
        if req.fetch_all:
            clear_database()  # Limpar banco antes de coletar tudo
            df = fetch_all_binance_data(req.symbol, req.timeframe)
        else:
            df = fetch_binance_data(req.symbol, req.timeframe, req.limit)
        
        insert_data_to_db(df)
        return {"status": "OK", "rows_inserted": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clear-database")
def api_clear_database():
    """
    Limpa completamente o banco de dados.
    """
    try:
        clear_database()
        return {"status": "OK", "message": "Banco de dados limpo com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train-model")
def api_train_model():
    try:
        result = train_model()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-days-profit")
def api_predict_days_to_profit(req: PredictRequest):
    try:
        days_needed = predict_days_to_profit(
            target_profit=req.target_profit,
            max_days=req.max_days
        )
        return {"days_needed": days_needed} if days_needed != -1 else {"status": "Lucro não alcançado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------
# MAIN
# -------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
