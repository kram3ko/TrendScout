"""Single import point that binds every mapped model to `Base.metadata`.

Alembic autogenerate only sees tables whose module has been imported; importing
this module is what makes a new feature's tables appear in a migration.
"""

from app.auth import models as auth_models
from app.core.db import Base
from app.products import models as product_models
from app.salesboost import models as salesboost_models
from app.scraping import models as scraping_models

__all__ = ["Base", "auth_models", "product_models", "salesboost_models", "scraping_models"]

target_metadata = Base.metadata
