from app.database import Base

# Importer depuis database.py pour éviter les imports circulaires
__all__ = ["Base"]
