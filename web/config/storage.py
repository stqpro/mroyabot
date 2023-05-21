from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.contrib.fsm_storage.memory import MemoryStorage


storage = RedisStorage2(host="redis", db=0, prefix='mb')  # PRODUCTION
# storage = MemoryStorage() # DEBUG
