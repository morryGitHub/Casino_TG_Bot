import aiomysql

from config_data.config import load_config, Config

db_config: Config = load_config(".env")


async def create_pool():
    pool = await aiomysql.create_pool(
        host=db_config.db.db_host,
        port=db_config.db.db_port,
        user=db_config.db.db_user,
        password=db_config.db.db_password,
        db=db_config.db.database,
        minsize=1,
        maxsize=2,
        connect_timeout=10,
        autocommit=True
    )
    return pool


async def close_pool(db_pool):
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()


user_messages = {}
users_bet = {}  # ключ: user_id, значение: список ставок [[amount, target, username], ...]
bet_messages = {}  # user_id -> {"chat_id": ..., "message_id": ...}
roulette_messages = {}
double_messages = {}
roulette_states = {}  # { chat_id: True/False }
total_bet = {}  # {"user_id": 0 }
bonus_messages = {}
