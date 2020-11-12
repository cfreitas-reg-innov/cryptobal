import getDataCoinbase
from sys import argv

script, asset, folder_name = argv

GET_DATA = getDataCoinbase.GetData(asset=asset, folder_name = folder_name)

GET_DATA.run_forever()