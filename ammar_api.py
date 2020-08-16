import requests

base = 'http://127.0.0.1:5000/'


def create_user(user_id, user):
    response = requests.put(base + 'user/' + str(user - id), {'user': user})
    return response.json()


def buy(user_id, ticker, shares):
    response = requests.put(base + 'buy/' + str(user_id), {'ticker': ticker, 'shares': shares})
    return response.json()


def sell(user_id, ticker, shares):
    response = requests.put(base + 'sell/' + str(user_id), {'ticker': ticker, 'shares': shares})
    return response.json()


def cash(user_id):
    response = requests.get(base + 'cash/' + str(user_id))
    return response.json()


def portfolio(user_id):
    response = requests.get(base + 'portfolio/' + str(user_id))
    return response.json()


def value(user_id):
    response = requests.get(base + 'value/' + str(user_id))
    return response.json()


def price(ticker):
    response = requests.get(base + 'price/', {'ticker': ticker})
    return response.json()
