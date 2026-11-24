"""Vercel entrypoint: expone la aplicación FastAPI en la raíz."""

from api.server import app

__all__ = ["app"]
