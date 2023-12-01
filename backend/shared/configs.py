import os
from pathlib import Path

from dotenv.main import load_dotenv

BASE_PATH = Path(__file__).parent

env_file = BASE_PATH / '..' / '..' / '.env'

assert env_file.exists(), f'File {env_file} not found'

load_dotenv(env_file)

db_parameters = {
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT'),
    'dbname': os.getenv('POSTGRES_DB'),
    'driver': 'postgresql+asyncpg'
}