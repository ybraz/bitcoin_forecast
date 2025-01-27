const API_BASE_URL = "http://127.0.0.1:8000";

async function fetchData() {
    const symbol = document.getElementById("symbol").value;
    const timeframe = document.getElementById("timeframe").value;
    const limit = parseInt(document.getElementById("limit").value);
    const fetchAll = document.getElementById("fetchAll").checked;

    document.getElementById("result").innerHTML = "Limpando banco de dados...";

    try {
        // Primeiro, limpar o banco de dados antes de coletar os dados
        await fetch(`${API_BASE_URL}/clear-database`, {
            method: "POST"
        });

        document.getElementById("result").innerHTML = "Banco de dados limpo. Coletando novos dados...";

        // Enviar solicitação para coletar os dados
        const requestData = {
            symbol: symbol,
            timeframe: timeframe,
            limit: limit,
            fetch_all: fetchAll
        };

        const response = await fetch(`${API_BASE_URL}/fetch-data`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();
        document.getElementById("result").innerHTML = `Dados coletados: ${data.rows_inserted}`;
    } catch (error) {
        document.getElementById("result").innerHTML = `Erro: ${error.message}`;
    }
}

async function trainModel() {
    document.getElementById("result").innerHTML = "Treinando modelo, por favor aguarde...";

    try {
        const response = await fetch(`${API_BASE_URL}/train-model`, {
            method: "POST"
        });

        const data = await response.json();
        document.getElementById("result").innerHTML = `Modelo treinado até: ${data.last_date}, Preço: $${data.last_price}`;
    } catch (error) {
        document.getElementById("result").innerHTML = `Erro: ${error.message}`;
    }
}

async function predictProfit() {
    const targetProfit = parseFloat(document.getElementById("targetProfit").value);
    const maxDays = parseInt(document.getElementById("maxDays").value);

    document.getElementById("result").innerHTML = "Calculando previsão, por favor aguarde...";

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
            ? `Dias necessários para alcançar o lucro alvo: ${data.days_needed}`
            : "Lucro não alcançado dentro do período especificado.";
    } catch (error) {
        document.getElementById("result").innerHTML = `Erro: ${error.message}`;
    }
}
