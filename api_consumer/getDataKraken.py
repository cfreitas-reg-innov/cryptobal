import websocket, copy, json, os, time, zlib, bisect, traceback
import pandas as pd
import numpy as np
from json import loads
from os.path import join
from datetime import datetime
from modules.helpers import create_folder_structure, write_file, upload_to_aws

class GetData():
    def __init__(self, asset='["XBT/USD"]', folder_name='noname', debug = False):
        """
        with open('AWS_keys.json') as json_file:
            aws_keys = json.load(json_file)

        self.access_key = aws_keys["access_key"]
        self.secret_key = aws_keys["secret_key"]
        """
        
        # initializing string variables
        self.asset = asset.split(',')
        self.folder_name = folder_name
        self.depth = '100'
        self.orderbook_subscription = 'book-' + self.depth
        self.token = 'uGuvmjij9MRa305SGm++IrRxOZvwZvF5Ra3hracbpG4'
        self.count = {'trade' : [1,1], self.orderbook_subscription : [1,1]} # counts how many messages were processed, [0] = resets to '0' once maxLength is reached | [1] = total count
        
        # initializing stream connection instance
        self.ws = self.websocket_connection()
        
        # initializing variables for orderbooks and trades
        self.subscription_values = {self.orderbook_subscription:[], 'trade':[]}
        self.paths = set()
        self.orderbook = {'bids': {}, 'asks': {}}
        self.orderbook_dataframe = pd.DataFrame()

        
        self.dataframe_levels = 50
        self.maxLength = 1000
    
    # define stream connection instance
    def websocket_connection(self):
        url = "wss://ws.kraken.com"
        return websocket.WebSocketApp(
            url=url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
    
    # catch message
    def on_message(self, message):
        print('\n', message)
        self.process_message(message)
            
    # catch errors
    def on_error(self, error):
        print(error)

    # run when websocket is closed
    def on_close(self):
        for fullpath in self.paths:
            write_file(fullpath) # closes the lists of trades and orderbooks once the program is over
            #upload_to_aws(fullpath, 'exchange-data-bucket', fullpath, self.access_key, self.secret_key) 

        self.export_dataframe()  
        print("\n*End of processing")

    # run when websocket is initialised
    def on_open(self):
        print('\n*Connecting to Kraken')

        self.subscribe({"name": "book", "depth": int(self.depth), "token": self.token})
        self.subscribe({"name": "trade", "token": self.token})

    def subscribe(self, subscription_args):
        print('\n*Subscribed to channel: ' + subscription_args['name'])
        
        return self.ws.send(json.dumps({
            "event": "subscribe",
            "pair": self.asset,
            "subscription": subscription_args
        }))
                    
    # start and keep connection
    def run_forever(self):
        for asset in self.asset:
            try:
                create_folder_structure(self.folder_name, 'kraken', asset, ['trade', self.orderbook_subscription])
            except Exception as e:
                print(e)

        self.ws.run_forever()

    
    # keep and store messages
    def process_message(self, data):
        message = copy.deepcopy(data)
        message_json = json.loads(message)
        content_list = message_json[1:-2]
        subscription = message_json[-2]
        asset = message_json[-1]

        if type(message_json) is list:
            for content in content_list:
                if subscription == self.orderbook_subscription:
                    self.save_orderbook(content)
                    self.place_order(content)

                date = "{:%Y_%m_%d}".format(datetime.now())
                path = join('data', self.folder_name, 'kraken', asset, subscription + '/')

                try:
                    filename = 'kraken_' + asset.replace('/', '_') + '_' + subscription + '_' + str(self.count[subscription][0]) + '_' + str(date) + '.json'
                    print(filename)
                    fullpath = path + filename
                    self.paths.add(fullpath)

                    write_file(fullpath, content)
                    self.count[subscription][1] += 1 

                    if self.count[subscription][1] == self.maxLength:
                        self.count[subscription][0] += 1
                        self.count[subscription][1] = 0

                except Exception:
                    print(traceback.format_exc())

    def save_orderbook(self, content):
        try:
            if not self.orderbook['bids'] and not self.orderbook['asks']:
                self.orderbook['bids'] = content['bs']
                self.orderbook['asks'] = content['as']
                columns = self.get_column_names(self.dataframe_levels)
                self.orderbook_dataframe = self.create_dataframe(columns)

        except Exception:
            print(traceback.format_exc())


    def place_order(self, new_update):
        order_asks_list = []
        order_bids_list = []
        timestamp = ''

        try:
            new_asks_list = self.orderbook['asks']
            new_bids_list = self.orderbook['bids']

            if 'a' in new_update:
                order_asks_list = new_update['a']
                new_asks_list = self.verify_and_insert(order_asks_list, 'asks')

                if timestamp == '':
                    timestamp = new_update['a'][0][2]
            
            if 'b' in new_update:
                order_bids_list = new_update['b']
                new_bids_list = self.verify_and_insert(order_bids_list, 'bids')

                if timestamp == '':
                    timestamp = new_update['b'][0][2]

            if 'c' in new_update:
                checksum = new_update['c']
                print('checksum:', checksum)

            if self.verify_checksum(new_asks_list, new_bids_list, checksum):
                self.orderbook['asks'] = new_asks_list
                self.orderbook['bids'] = new_bids_list
                self.update_dataframe(self.dataframe_levels, timestamp)

        except Exception:
            print(traceback.format_exc())



    def verify_and_insert(self, new_order_list, type):
        index = -1
        aux_orderbook_list = self.orderbook[type]

        def get_price(elem):
            return elem[0]

        aux_orderbook_list.sort(key = get_price)

        try:
            for new_order in new_order_list:
                if new_order[-1] != 'r':
                    prices = [order[0] for order in aux_orderbook_list]

                    if new_order[0] in prices:
                        index = prices.index(new_order[0])

                        if new_order[1] != '0.00000000':
                            aux_orderbook_list[index] = new_order
                        else:
                            aux_orderbook_list.pop(index)
                    else:
                        bisect.insort(aux_orderbook_list, new_order)

            if type == 'bids':
                aux_orderbook_list.sort(key=get_price, reverse=True)
                
        except Exception:
            print(traceback.format_exc())

        return aux_orderbook_list



    def verify_checksum(self, asks, bids, original_checksum):
        valid_checksum = False

        def apply_transformation(value):
            value = str(value).replace('.', '')
            value = str(value).lstrip('0')
            return str(value)

        checksum = ''

        try:
            for ask in asks[0:10]:
                checksum = checksum + apply_transformation(ask[0])
                checksum = checksum + apply_transformation(ask[1])

            for bid in bids[0:10]:
                checksum = checksum + apply_transformation(bid[0])
                checksum = checksum + apply_transformation(bid[1])

            self.checksum = zlib.crc32(bytes(checksum, encoding='UTF-8'))
            print('crc32 verific:', self.checksum)
            valid_checksum = str(self.checksum) == original_checksum

        except Exception:
            print(traceback.format_exc())

        return valid_checksum

    def get_column_names(self, depth):
        columns = ['timestamp']
        for i in range(depth):
            columns.append('B' + str(i+1))
            columns.append('VB' + str(i+1))
        for i in range(depth):
            columns.append('A' + str(i+1))
            columns.append('VA' + str(i+1))
        return columns


    def create_dataframe(self, columns):
        return pd.DataFrame(columns = columns)


    def update_dataframe(self, depth, timestamp):
        new_update = []

        try:
            new_update.append(timestamp)

            for i in range(depth):
                new_update.append(np.round(float(self.orderbook['bids'][i][0]),2))
                new_update.append(float(self.orderbook['bids'][i][1]))

            for i in range(depth):
                new_update.append(np.round(float(self.orderbook['asks'][i][0]),2))
                new_update.append(float(self.orderbook['asks'][i][1]))

            self.orderbook_dataframe = self.orderbook_dataframe.append(pd.Series(new_update, index=self.orderbook_dataframe.columns ), ignore_index=True)

        except Exception:
            print(traceback.format_exc())


    def export_dataframe(self):
        try:
            date = "{:%Y_%m_%d}".format(datetime.now())
            path = join('data', self.folder_name, 'kraken', self.asset[0], self.orderbook_subscription + '/')
            filename = 'kraken_' + self.asset[0].replace('/', '_') + '_' + self.orderbook_subscription + '_' + 'dataframe' + '_' + str(date) + '.csv'
            self.orderbook_dataframe.to_csv(path + filename, index = True) 

        except Exception:
            print(traceback.format_exc())


