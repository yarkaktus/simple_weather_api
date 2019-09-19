import json
import os
import time
from datetime import datetime

import aiohttp
from aiohttp import web

LISTEN_PORT = os.getenv('LISTEN_PORT', 8000)
WEATHER_API_URL = os.getenv('WEATHER_API_URL', 'https://api.worldweatheronline.com/premium/v1/past-weather.ashx')
API_KEY = os.getenv('API_KEY', '0b204008392d4723a0d152329191909')


def json_response_handler(data: dict, status=200) -> web.Response:
    return web.Response(
        text=json.dumps(data, ensure_ascii=False), status=status
    )


def error_response_handler(text='Wrong request', status=400) -> web.Response:
    return web.Response(
        text=text, status=status
    )


async def get_forecast_data(city: str, dt: int) -> json:
    date = datetime.fromtimestamp(dt).strftime("%Y-%m-%d")
    params = {
        'key': API_KEY,
        "format": "json",
        'q': city,
        'date': date,
        'enddate': date,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(WEATHER_API_URL, params=params) as response:
            return await response.json()


async def history_forecast(request) -> web.Response:
    try:
        city = request.query.get('city')
        dt = int(request.query.get('dt') or time.time())

        forecast_data = await get_forecast_data(city, dt)

        response_data = {
            "city": forecast_data['data']['request'][0]['query'],
            "unit": "celsius",
            "temperature": forecast_data['data']['weather'][0]['avgtempC']
        }
    except:
        return error_response_handler()
    return json_response_handler(response_data)


async def current_forecast(request) -> web.Response:
    try:
        city = request.query.get('city')
        dt = int(time.time())

        forecast_data = await get_forecast_data(city, dt)

        response_data = {
            "city": forecast_data['data']['request'][0]['query'],
            "unit": "celsius",
            "temperature": forecast_data['data']['weather'][0]['avgtempC']
        }
    except:
        return error_response_handler()
    return json_response_handler(response_data)


app = web.Application()

app.add_routes([
    web.get('/v1/forecast/', history_forecast),
    web.get('/v1/current/', current_forecast),
])

if __name__ == '__main__':
    web.run_app(app, port=LISTEN_PORT)
