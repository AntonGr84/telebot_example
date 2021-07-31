import sys
from os import getenv
from os.path import join, abspath, dirname
from dotenv import load_dotenv


env_path = join(
    dirname(abspath(sys.argv[0])),
    'env'
)
load_dotenv(dotenv_path=env_path)
BOT_TOKEN = getenv('BOT_TOKEN')
HOTELS_KEY = getenv('HOTELS_KEY')
HOTELS_HOST = getenv('HOTELS_HOST')
