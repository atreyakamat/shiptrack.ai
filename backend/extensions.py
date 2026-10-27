import os
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
cors = CORS()
migrate = Migrate()

# Use a shared Redis store for rate limits when REDIS_URL is set (so limits survive
# restarts and are shared across workers); otherwise fall back to in-memory for dev.
_RATE_LIMIT_STORAGE = os.getenv('REDIS_URL') or 'memory://'
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=_RATE_LIMIT_STORAGE,
)
