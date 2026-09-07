"""MongoDB connection and collection handles for LabStock."""
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Collection handles (entities)
reagen_col = db['master_reagen']
stock_period_col = db['stock_period']
pemakaian_col = db['pemakaian_harian']
penerimaan_col = db['penerimaan']
prf_col = db['prf']
mapping_col = db['mapping_test']
lis_raw_col = db['lis_raw']
import_log_col = db['import_log']
users_col = db['users']
settings_col = db['settings']
periode_meta_col = db['periode_meta']


async def ensure_indexes():
    await reagen_col.create_index('nama_reagen', unique=True)
    await stock_period_col.create_index([('reagen_id', 1), ('year', 1), ('month', 1)], unique=True)
    await pemakaian_col.create_index([('reagen_id', 1), ('date', 1)])
    await penerimaan_col.create_index('period')
    await prf_col.create_index('period')
    await mapping_col.create_index('lis_name')
    await lis_raw_col.create_index('period')
    await users_col.create_index('username', unique=True)
    await periode_meta_col.create_index([('year', 1), ('month', 1)], unique=True)
