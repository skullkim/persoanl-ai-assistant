from controller.model.response.exchange_rate_response import ExchangeRateResponse
from external.exchang_rate import get_latest_exchange_rate

def get_exchange_rate_service():
    exchange_data = get_latest_exchange_rate()

    # Extract the numeric part from change_percentage string (e.g., "+1.23%")
    change_percentage_str = exchange_data["change_percentage"]
    change_percentage_float = float(change_percentage_str.replace('%', ''))

    return ExchangeRateResponse(
        rate=exchange_data["rate"],
        change=change_percentage_float,
        lastUpdated=exchange_data["date"],
    )