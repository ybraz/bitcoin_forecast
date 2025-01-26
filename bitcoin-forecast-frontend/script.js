const API_BASE_URL = "http://127.0.0.1:8000";

async function fetchData() {
    const symbol = document.getElementById("symbol").value;
    const exchange = document.getElementById("exchange").value;
    const timeframe = document.getElementById("timeframe").value;
    const limit = document.getElementById("limit").value;

    try {
        const response = await fetch(`${API_BASE_URL}/fetch-data?symbol=${symbol}&exchange_name=${exchange}&timeframe=${timeframe}&limit=${limit}`, {
            method: "POST"
        });

        const data = await response.json();
        document.getElementById("result").innerHTML = `Dados coletados: ${data.rows_inserted}`;
    } catch (error) {
        document.getElementById("result").innerHTML = `Erro: ${error.message}`;
    }
}

async function trainModel() {
    try {
        const response = await fetch(`${API_BASE_URL}/train-model`, {
            method: "POST"
        });

        const data = await response.json();
        document.getElementById("result").innerHTML = `Modelo treinado até: ${data.last_date}`;
    } catch (error) {
        document.getElementById("result").innerHTML = `Erro: ${error.message}`;
    }
}

async function predictProfit() {
    const targetProfit = parseFloat(document.getElementById("targetProfit").value);
    const maxDays = parseInt(document.getElementById("maxDays").value);

    try {
        const response = await fetch(`${API_BASE_URL}/predict-days-profit`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                target_profit: targetProfit,
                max_days: maxDays
            })
        });

        const data = await response.json();
        document.getElementById("result").innerHTML = data.days_needed !== null
            ? `Dias necessários: ${data.days_needed}`
            : "Lucro não alcançado dentro do período especificado.";
    } catch (error) {
        document.getElementById("result").innerHTML = `Erro: ${error.message}`;
    }
}
