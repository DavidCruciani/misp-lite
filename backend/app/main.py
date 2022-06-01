import logging
from fastapi import FastAPI
from .models.database import Base, engine
from .routers import users, events, attributes, servers, roles

# setup loggers
logging.config.fileConfig('/code/app/logging.conf', disable_existing_loggers=False)

# Bootstrap application
app = FastAPI(title="misp-lite API", version="0.1.0")

# Users resource
app.include_router(users.router, tags=["Users"])

# Roles resource
app.include_router(roles.router, tags=["Roles"])

# Events resource
app.include_router(events.router, tags=["Events"])

# Attributes resource
app.include_router(attributes.router, tags=["Attributes"])

# Servers resource
app.include_router(servers.router, tags=["Servers"])
