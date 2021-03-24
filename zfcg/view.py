from web.routers import router
import zfcg.service as srv


@router.get("/zfcg/supplier", tags=['zfcg'])
async def to_suppliers():
    return srv.offer()


@router.get("/zfcg/notice", tags=['zfcg'])
async def to_notices():
    return srv.offer()


@router.get("/zfcg", tags=['zfcg'])
async def greeting():
    return 'a nice day we have'
