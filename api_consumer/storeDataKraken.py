import getDataKraken
from sys import argv

script, asset, folder_name = argv

GET_DATA = getDataKraken.GetData(asset=asset, folder_name=folder_name)

GET_DATA.run_forever()