from flask import Flask, request
from flask_restful import Resource, Api, abort, reqparse, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
import requests
import json

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main_database.db'
db = SQLAlchemy(app)


# table 1: user_model
class user_model(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100), nullable=False)
    cash = db.Column(db.Integer, nullable=False)
    stocks = db.relationship('stocks', backref='owner')


# table 2: stocks
class stocks(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(100), nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user_model.user_id'))


new_user_args = reqparse.RequestParser()
new_user_args.add_argument('user', type=str, help='user is required', required=True)

trade_stock_args = reqparse.RequestParser()
trade_stock_args.add_argument('ticker', type=str, help='ticker is required', required=True)
trade_stock_args.add_argument('shares', type=int, help='# of shares is required', required=True)

get_price_args = reqparse.RequestParser()
get_price_args.add_argument('ticker', type=str, help='ticker is required', required=True)

resource_fields = {
    'stock_id': fields.Integer,
    'user_id': fields.Integer,
    'user': fields.String,
    'cash': fields.Integer,
    'ticker': fields.String,
    'shares': fields.Integer,
    'price': fields.Integer
}


def get_price(ticker):
    API_KEY = 'PK1RKACF8RBOE9UP41UD'
    SECRET_KEY = 'KfYSoJ3vZqUHec4Yvczo3g2Bxz0SIvsGWp6eIGuw'
    headers = {'APCA-API-KEY-ID': API_KEY, 'APCA-API-SECRET-KEY': SECRET_KEY}
    market_url = 'https://data.alpaca.markets/v1'
    last_quote = '{}/last_quote/stocks/{}'.format(market_url, ticker)
    r = requests.get(last_quote, headers=headers)
    quote = json.loads(r.content)
    return quote['last']['askprice']


class users(Resource):
    @marshal_with(resource_fields)
    def put(self, user_id):
        args = new_user_args.parse_args()
        result = user_model.query.filter_by(user_id=user_id).first()
        if result:
            abort(409, message='User_id is already take...')
        user = user_model(user_id=user_id, user=args['user'], cash=100000)
        db.session.add(user)  # adds the object video to the current db session
        db.session.commit()  # permanently put in the video object into the db
        return user, 201


class price(Resource):
    def get(self):
        args = get_price_args.parse_args()
        ticker = args['ticker']
        return get_price(ticker)


class buy(Resource):
    @marshal_with(resource_fields)
    def put(self, user_id):
        args = trade_stock_args.parse_args()
        result = user_model.query.filter_by(user_id=user_id).first()
        if not result:
            abort(404, message='user_id doesnt exist...')
        ticker = args['ticker']
        price = get_price(ticker)

        cash_change = result.cash - price * args['shares']
        if cash_change < 0:
            abort(404, message='not enough funds...')
        result.cash = cash_change

        result = stocks.query.filter_by(owner_id=user_id, ticker=ticker).first()
        if result:
            result.price = ((result.price * result.shares) + (price * args['shares'])) / (
                    result.shares + args['shares'])
            result.shares += args['shares']
            db.session.commit()
            return result, 201
        else:
            trade = stocks(owner_id=user_id, ticker=ticker, shares=args['shares'], price=price)
            db.session.add(trade)
            db.session.commit()
            return trade, 201


class sell(Resource):
    @marshal_with(resource_fields)
    def put(self, user_id):
        args = trade_stock_args.parse_args()
        result_user = user_model.query.filter_by(user_id=user_id).first()
        if not result_user:
            abort(404, message='user_id doesnt exist...')
        ticker = args['ticker']
        price = get_price(ticker)
        result = stocks.query.filter_by(owner_id=user_id, ticker=ticker).first()
        if not result:
            abort(404, message='you dont own this stock...')
        if result.shares < args['shares']:
            abort(404, message='you dont own enough shares...')
        if result.shares == args['shares']:
            result_user.cash = result_user.cash + price * result.shares
            result.price = 0
            result.shares = 0
        else:
            result_user.cash = result_user.cash + price * args['shares']
            result.price = ((result.price * result.shares) - (price * args['shares'])) / (
                    result.shares - args['shares'])
            result.shares -= args['shares']

        db.session.commit()
        return result, 201


class cash(Resource):
    # @marshal_with(resource_fields)
    def get(self, user_id):
        result = user_model.query.filter_by(user_id=user_id).first()
        if not result:
            abort(404, message='user_id doesnt exist...')
        return result.cash, 201


class portfolio(Resource):
    def get(self, user_id):
        result = user_model.query.filter_by(user_id=user_id).first()
        if not result:
            abort(404, message='user_id doesnt exist...')
        data = stocks.query.all()
        all_stocks = []
        for s in data:
            if s.owner_id == user_id:
                all_stocks.append(['ticker: ' + s.ticker, 'shares: ' + str(s.shares), 'avg price: ' + str(s.price)])
        return all_stocks


class value(Resource):
    def get(self, user_id):
        result = user_model.query.filter_by(user_id=user_id).first()
        if not result:
            abort(404, message='user_id doesnt exist...')
        cur_value = result.cash
        data = stocks.query.all()
        for s in data:
            if s.owner_id == user_id:
                cur_value += s.shares * s.price
        return cur_value


api.add_resource(users, '/user/<int:user_id>')
api.add_resource(price, '/price/')
api.add_resource(buy, '/buy/<int:user_id>')
api.add_resource(sell, '/sell/<int:user_id>')
api.add_resource(cash, '/cash/<int:user_id>')
api.add_resource(portfolio, '/portfolio/<int:user_id>')
api.add_resource(value, '/value/<int:user_id>')
# db.create_all()
if __name__ == "__main__":
    app.run(debug=True)  # debug-True lets u see logs of what goes wrong
