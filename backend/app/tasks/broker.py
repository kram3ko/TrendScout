from taskiq import AsyncBroker, TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from app.core.config import get_settings

CRON_EVERY_N_HOURS = "0 */{hours} * * *"

_settings = get_settings()

# Streams (not a plain list) so an in-flight task survives a worker restart.
broker: AsyncBroker = RedisStreamBroker(url=_settings.redis_url).with_result_backend(
    RedisAsyncResultBackend(redis_url=_settings.redis_url)
)
scheduler = TaskiqScheduler(broker, sources=[LabelScheduleSource(broker)])

SCRAPE_CRON = CRON_EVERY_N_HOURS.format(hours=_settings.scrape_interval_hours)
