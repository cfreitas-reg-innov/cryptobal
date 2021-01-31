import websocket, copy, json, os, time, zlib, bisect, traceback
from json import loads
from os.path import join
from datetime import datetime
from modules.helpers import create_folder_structure, write_file, upload_to_aws

class GetData():
    def __init__(self, asset='["XBT/USD"]', folder_name='noname', debug = False):
        with open('AWS_keys.json') as json_file:
            aws_keys = json.load(json_file)

        self.access_key = aws_keys["access_key"]
        self.secret_key = aws_keys["secret_key"]
        
        # initializing string variables
        self.asset = asset.split(',')
        self.folder_name = folder_name
        self.token = 'uGuvmjij9MRa305SGm++IrRxOZvwZvF5Ra3hracbpG4'
        self.count = {'trade' : [1,1], 'book-100' : [1,1]} # counts how many messages were processed, [0] = resets to '0' once maxLength is reached | [1] = total count
        
        # initializing stream connection instance
        self.ws = self.websocket_connection()
        
        # initializing variables for orderbooks and trades
        self.subscription_values = {'book-100':[], 'trade':[]}
        self.paths = set()
        self.orderbook = {'bids': {}, 'asks': {}}

        self.maxLength = 100
    
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
        print(message)
        self.process_message(message)
            
    # catch errors
    def on_error(self, error):
        print(error)

    # run when websocket is closed
    def on_close(self):
        for fullpath in self.paths:
            write_file(fullpath) # closes the lists of trades and orderbooks once the program is over
            #upload_to_aws(fullpath, 'exchange-data-bucket', fullpath, self.access_key, self.secret_key)    
        print("\n*End of processing")

    # run when websocket is initialised
    def on_open(self):
        print('\n*Connecting to Kraken')

        self.subscribe({"name": "book", "depth": 100, "token": self.token})
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
                create_folder_structure(self.folder_name, 'kraken', asset, ['trade', 'book-100'])
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
                if subscription == 'book-100':
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

                except Exception as e:
                    print(e)

    def save_orderbook(self, content):
        try:
            self.orderbook['bids'] = content['bs']
            self.orderbook['asks'] = content['as']

        except Exception as e:
            print('Not snapshot, only orderbook', e)


    def place_order(self, new_update):
        order_asks_list = []
        order_bids_list = []

        new_asks_list = self.orderbook['asks']
        new_bids_list = self.orderbook['bids']

        checksum = new_update['c']
        print('\nchecksum:', checksum)

        if 'a' in new_update:
            order_asks_list = new_update['a']
            new_asks_list = self.verify_and_insert(order_asks_list, 'asks')
        
        if 'b' in new_update:
            order_bids_list = new_update['b']
            new_bids_list = self.verify_and_insert(order_bids_list, 'bids')

        if self.verify_checksum(new_asks_list, new_bids_list, checksum):
            self.orderbook['asks'] = new_asks_list
            self.orderbook['bids'] = new_bids_list


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
                
        except Exception as e:
            print(traceback.format_exc())
            pass

        print('novo orderbook:', aux_orderbook_list)
        
        return aux_orderbook_list



    def verify_checksum(self, asks, bids, original_checksum):
            valid_checksum = False
            print('asks to be verified:', asks[0:10])
            print('bids to be verified:', bids[0:10])

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

                #print('Entire checksum: ' + checksum)

                self.checksum = zlib.crc32(bytes(checksum, encoding='UTF-8'))
                print('crc32 verific:', self.checksum)
                valid_checksum = self.checksum is original_checksum

            except Exception as e:
                print(e, 'error getting checksum')

            return valid_checksum