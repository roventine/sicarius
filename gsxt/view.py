from web.routers import router
import gsxt.service as srv


@router.get("/gsxt/{id_uni}", tags=['gsxt'])
async def offer(id_uni: str):
    return srv.offer(id_uni)


@router.get("/gsxt", tags=['gsxt'])
async def greeting():
    return 'a nice day we have'