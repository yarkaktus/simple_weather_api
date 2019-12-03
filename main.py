import asyncio
import json
import os
import time
from datetime import datetime

import aiohttp
import aioredis
from aiohttp import web

LISTEN_PORT = os.getenv('LISTEN_PORT', 8000)
WEATHER_API_URL = os.getenv('WEATHER_API_URL', 'https://api.worldweatheronline.com/premium/v1/past-weather.ashx')
API_KEY = os.getenv('API_KEY', '01993009d97d441497f161347192811')

REDIS_HOST = os.getenv('REDIS_HOST', '0.0.0.0')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')


def json_response_handler(data: dict, status=200) -> web.Response:
    return web.Response(
        text=json.dumps(data, ensure_ascii=False), status=status
    )


def error_response_handler(text='Wrong request', status=400) -> web.Response:
    return web.Response(
        text=text, status=status
    )


async def get_forecast_data(request: web.Request, city: str, dt: int, now=True) -> json:

    date = datetime.fromtimestamp(dt).strftime("%Y-%m-%d")
    redis: aioredis.Redis = request.app['redis']

    key = f'{city}_{"now" if now else dt}'
    try:
        value = await redis.get(key)
    except:
        value = None

    if value:
        value = json.loads(value)
    else:

        params = {
            'key': API_KEY,
            "format": "json",
            'q': city,
            'date': date,
            'enddate': date,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(WEATHER_API_URL, params=params) as response:
                value = await response.json()

        if now:
            await redis.set(key, json.dumps(value), expire=30)
        else:
            await redis.set(key, json.dumps(value))

    return value


async def history_forecast(request) -> web.Response:
    try:
        city = request.query.get('city')
        dt = int(request.query.get('dt') or time.time())

        forecast_data = await get_forecast_data(request, city, dt, now=False)
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

        forecast_data = await get_forecast_data(request, city, dt, now=True)
        response_data = {
            "city": forecast_data['data']['request'][0]['query'],
            "unit": "celsius",
            "temperature": forecast_data['data']['weather'][0]['avgtempC']
        }
    except:
        return error_response_handler()
    return json_response_handler(response_data)


async def get_app():
    app = web.Application()

    app['redis'] = await aioredis.create_redis((REDIS_HOST, REDIS_PORT))

    app.add_routes([
        web.get('/v1/forecast/', history_forecast),
        web.get('/v1/current/', current_forecast),
    ])

    return app


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(get_app())
    web.run_app(app, host='0.0.0.0', port=LISTEN_PORT)
