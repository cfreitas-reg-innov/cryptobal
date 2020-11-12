import websocket, requests, copy, json, os, time
from json import loads
from os.path import join
from datetime import datetime
from modules.helpers import create_folder_structure, write_file

class GetData():

    def __init__(self, asset='BTC-EUR', folder_name = 'noname', debug = False):
        
        # initializing string variables
        self.asset = asset
        self.folder_name = folder_name
        self.count = {'trade' : [1,1], 'orderbook' : [1,1]} # counts how many messages were processed, [0] = resets to '0' once maxLength is reached | [1] = total count
        
        # initializing stream connection instance
        self.ws = self.websocket_connection()
        
        # initializing variables for orderbook and trades
        self.subscription_values = {'snapshot':'orderbook', 'l2update': 'orderbook', 'match':'trade'}
        self.paths = set()

        self.maxLength = 100
   
    # define stream connection instance
    def websocket_connection(self):
        url = "wss://ws-feed.pro.coinbase.com"
        return websocket.WebSocketApp(
            url=url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
    
    # catch message
    def on_message(self, message):
        print(message)
        self.process_message(message)
            
    # catch errors
    def on_error(self, error):
        print(error)

    # run when websocket is closed
    def on_close(self):
        for fullpath in self.paths:
            write_file(fullpath) # closes the lists of trades and orderbooks once the program is over
        
        print("\n*End of processing")

    # run when websocket is initialised
    def on_open(self):
        print('\n*Connecting to Coinbase\n')

        return self.ws.send(json.dumps({
            "type": "subscribe",
            "product_ids": [
                self.asset
            ],
            "channels": [
                "level2", # Depth = 50
                "matches"
            ]
        }))
                
    # start and keep connection
    def run_forever(self):
        if create_folder_structure(self.folder_name, 'coinbase', self.asset, ['trade', 'orderbook']):
            self.ws.run_forever()
        else:
            print('\n*Please give another folder location')

    # keep and store messages
    def process_message(self, data):
        message_json = json.loads(data)
        message_type = self.subscription_values[message_json['type']]

        date = datetime.now().date()
        path = join('data', self.folder_name, 'coinbase', self.asset, message_type + '/')

        filename = message_type + '_' + str(self.count[message_type][0]) + '_' + str(date) + '.json'
        fullpath = path + filename
        self.paths.add(fullpath)

        try:
            write_file(fullpath, message_json)
            self.count[message_type][1] += 1

            if self.count[message_type][1] == self.maxLength:
                self.count[message_type][0] += 1
                self.count[message_type][1] = 0

        except Exception as e:
            print(e)
        



    