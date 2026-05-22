import asyncio
from gotrue.types import SignInWithIdTokenCredentials
import inspect

async def test():
    print(SignInWithIdTokenCredentials.__annotations__)

asyncio.run(test())
