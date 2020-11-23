import getDataKraken, getDataBinance, getDataCoinbase
import sys
from sys import argv

print(str(argv))
script, exchange, asset, folder_name = argv

exchange_class = getattr(sys.modules[__name__], 'getData' + exchange) # transforms exchange string into a class

GET_DATA = getattr(exchange_class,'GetData')(asset=asset, folder_name=folder_name) # call method GetData from the requested class

GET_DATA.run_forever()

