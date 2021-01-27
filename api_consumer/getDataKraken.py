import websocket, copy, json, os, time
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
        self.count = {'trade' : [1,1], 'book-10' : [1,1]} # counts how many messages were processed, [0] = resets to '0' once maxLength is reached | [1] = total count
        
        # initializing stream connection instance
        self.ws = self.websocket_connection()
        
        # initializing variables for orderbooks and trades
        self.subscription_values = {'book-10':[], 'trade':[]}
        self.paths = set()

        self.maxLength = 10
    
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

        self.subscribe({"name": "book", "depth": 10, "token": self.token})
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
                create_folder_structure(self.folder_name, 'kraken', asset, ['trade', 'book-10'])
            except Exception as e:
                print(e)

        self.ws.run_forever()

    
    # keep and store messages
    def process_message(self, data):
        message = copy.deepcopy(data)
        message_json = json.loads(message)
        content = message_json[1]
        subscription = message_json[2]
        asset = message_json[3]

        if type(message_json) is list:
            date = "{:%Y_%m_%d}".format(datetime.now())
            path = join('data', self.folder_name, 'kraken', asset, subscription + '/')

            try:
                filename = 'kraken_' + asset.replace('/', '_') + '_' + subscription + '_' + str(self.count[subscription][0]) + '_' + str(date) + '.json'
                print(filename)
                fullpath = path + filename
                self.paths.add(fullpath)

                write_file(fullpath, content)
                self.count[asset][1] += 1 

                if self.count[asset][1] == self.maxLength:
                    self.count[asset][0] += 1
                    self.count[asset][1] = 0

            except Exception as e:
                print(e)        