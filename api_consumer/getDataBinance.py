import websocket, requests, copy, json, os
from json import loads
from os.path import join
from datetime import datetime
from modules.helpers import create_folder_structure, write_file, upload_to_aws

class GetData():
    def __init__(self, asset='btcusdt', folder_name='noname', debug=False):
        with open('AWS_keys.json') as json_file:
            aws_keys = json.load(json_file)

        self.access_key = aws_keys["access_key"]
        self.secret_key = aws_keys["secret_key"]

        # initializing string variables
        self.asset = asset
        self.aggTrade_stream = self.asset + "@aggTrade"
        self.trade_stream = self.asset + "@trade"
        self.depth_stream = self.asset + "@depth@100ms"
        self.folder_name = folder_name
        
        # initializing stream connection instance
        self.ws = self.websocket_connection()
        
        # initializing variables for aggTrades and trades
        self.aggTrade = {}
        self.trade = {}
        self.maxLenTrades = 100 # updated for tests
        
        # intializing variables for orderbook
        self.orderbook = {}
        self.historical_orderbook = {}
        self.flag = False
        self.for_sync = 0
        self.max_len = 100        # max lenght of orderbook instances per file
        self.max_depth = 10        # max depth of each stored orderbook instance
        self.debug = debug
        
        if self.debug:
            self.updates = []           # for debugging
            
    # define stream connection instance
    def websocket_connection(self):
        all_streams = join(self.aggTrade_stream, self.trade_stream, self.depth_stream)
        url = "wss://stream.binance.com:9443/stream?streams=" + all_streams
        return websocket.WebSocketApp(
            url=url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
    
    # catch message
    def on_message(self, message):
        data = loads(message)
        if data['stream'] == self.aggTrade_stream:
            self.process_aggTrade(data['data'])
        elif data['stream'] == self.trade_stream:
            self.process_trade(data['data'])
        elif data['stream'] == self.depth_stream:
            self.process_depth(data['data'])
        else:
            print('Message not processed.')
            
    # catch errors
    def on_error(self, error):
        print(error)

    # run when websocket is closed
    def on_close(self):
        print("### closed ###")

    # run when websocket is initialised
    def on_open(self):
        print('Connected to Binance\n')
        
    # start and keep connection
    def run_forever(self):
        if create_folder_structure(self.folder_name, 'binance', self.asset, ['aggTrade', 'trade', 'orderbook']):
            self.ws.run_forever()
        else:
            print('Please give another folder location')
    
    # keep and store aggregated trades
    def process_aggTrade(self, data):
        try:
            aggTrade = copy.deepcopy(data)
            self.aggTrade[aggTrade['E']] = aggTrade
            # save aggTrade
            if len(self.aggTrade) == self.maxLenTrades :
                path = join('data', self.folder_name, 'binance', self.asset, 'aggTrade/')
                filename = str(aggTrade['E']) + '.json'
                with open(path + filename, 'w') as json_file:
                    json.dump(self.aggTrade, json_file)
                # clean memory
                self.aggTrade = {}
                upload_to_aws(path + filename, 'exchange-data-bucket', path + filename, self.access_key, self.secret_key)
                print('Aggregated trades saved.')
        except Exception as e:
            print(e)
    
    # keep and store trades
    def process_trade(self, data):
        try:
            trade = copy.deepcopy(data)
            self.trade[trade['E']] = trade
            # save trade
            if len(self.trade) == self.maxLenTrades :
                path = join('data', self.folder_name, 'binance', self.asset, 'trade/')
                filename = str(trade['E']) + '.json'
                with open(path + filename, 'w') as json_file:
                    json.dump(self.trade, json_file)
                # clean memory
                self.trade = {}
                upload_to_aws(path + filename, 'exchange-data-bucket', path + filename, self.access_key, self.secret_key)
                print('Trades saved.')
        except Exception as e:
            print(e)
    
    # manage orderbook
    def process_depth(self, data):
        try:
            # initialize orderbook
            if len(self.orderbook) == 0:
                self.orderbook = self.get_snapshot()
                aux = copy.deepcopy(self.orderbook)
                self.historical_orderbook[0] = {
                    'U':0,
                    'u':aux['lastUpdateId'],
                    'bids':aux['bids'][:self.max_depth],
                    'asks':aux['asks'][:self.max_depth],
                }
            # flag to find first update to be processed and ignore previous updates
            if not self.flag:
                if (data['U'] <= (self.orderbook['lastUpdateId'] + 1) and (self.orderbook['lastUpdateId'] + 1) <= data['u']):
                    self.flag = True
                    # initilize for sync
                    self.for_sync = data['U'] - 1
            #  update orderbook and store
            if self.flag:
                
                # check for sync
                if data['U'] == (self.for_sync + 1):
                    
                    if self.debug:
                        self.updates.append(data)
                    
                    self.process_updates(data)
                    copy_orderbook = copy.deepcopy(self.orderbook)
                    self.historical_orderbook[data['E']] = {
                        'U':data['U'],
                        'u':data['u'],
                        'bids':copy_orderbook['bids'][:self.max_depth],
                        'asks':copy_orderbook['asks'][:self.max_depth],
                    }
                    
                    # update for sync
                    self.for_sync = data['u']
                    
                    # save orderbook
                    if len(self.historical_orderbook) == self.max_len :
                        path = join('data', self.folder_name, 'binance', self.asset, 'orderbook/')
                        filename = str(data['E']) + '.json'
                        with open(path + filename, 'w') as json_file:
                            json.dump(self.historical_orderbook, json_file)
                        # clean memory
                        self.historical_orderbook = {}
                        if self.debug:
                            self.updates = []
                        upload_to_aws(path + filename, 'exchange-data-bucket', path + filename, self.access_key, self.secret_key)
                        print('Orderbook saved: ', datetime.fromtimestamp(int(data['E'])/1000))
                else:
                    print('Process out of sync. Abort.')
        except Exception as e:
            print(e)
    
    # retrieve orderbook snapshot
    def get_snapshot(self):
        r = requests.get('https://www.binance.com/api/v3/depth?symbol=' + self.asset.upper() + '&limit=1000')
        return loads(r.content.decode())
    
    # Loop through all bid and ask updates
    def process_updates(self, data):
        # process bids updates
        for order in data['b']:
            self.updateByOrder(order=order, side='bids')
        # process asks updates
        for order in data['a']:
            self.updateByOrder(order=order, side='asks')
        # delete zero entries
        self.orderbook['bids'] = [x for x in self.orderbook['bids'] if float(x[1]) != 0]
        self.orderbook['asks'] = [x for x in self.orderbook['asks'] if float(x[1]) != 0]
    
    # process order to orderbook
    def updateByOrder(self, order, side):
        if side == 'bids':
            # check for price increase
            y = self.orderbook['bids'][0]
            if float(y[0]) < float(order[0]):
                self.orderbook['bids'].insert(0, order)
            else:
                for i in range(len(self.orderbook['bids'])):
                    # check for price update
                    y = self.orderbook['bids'][i]
                    if order[0] == y[0]:
                        self.orderbook['bids'][i] = order
                        break
                    # check if price is lower than last observation
                    elif (i+1) == len(self.orderbook['bids']):
                        self.orderbook['bids'].insert(i+1, order)
                        break
                    # check for new price
                    else:
                        y_ = self.orderbook['bids'][i+1]
                        if (float(y_[0]) < float(order[0])) and (float(order[0]) < float(y[0])):
                            self.orderbook['bids'].insert(i+1, order)
                            break
        elif side == 'asks':
            # check for price decrease
            y = self.orderbook['asks'][0]
            if float(y[0]) > float(order[0]):
                self.orderbook['asks'].insert(0, order)
            else:
                for i in range(len(self.orderbook['asks'])):
                    # check for price update
                    y = self.orderbook['asks'][i]
                    if order[0] == y[0]:
                        self.orderbook['asks'][i] = order
                        break
                    # check if price is higher than last observation
                    elif (i+1) == len(self.orderbook['asks']):
                        self.orderbook['asks'].insert(i+1, order)
                        break
                    # check for new price
                    else:
                        y_ = self.orderbook['asks'][i+1]
                        if (float(y[0]) < float(order[0])) and (float(order[0]) < float(y_[0])):
                            self.orderbook['asks'].insert(i+1, order)
                            break
        else:
            print('Invalid side option.')