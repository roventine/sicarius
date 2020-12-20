import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import gsxt.service as srv

from web import routers

app = FastAPI()
app.include_router(routers.router, prefix="/api/v1/sicarius")

origins = [
    '*'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    srv.invoke()

    uvicorn.run(app=app,
                host='0.0.0.0',
                port=8000)



