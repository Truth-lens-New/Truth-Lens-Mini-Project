
import asyncio
import inspect
from duckduckgo_search import DDGS

async def test():
    try:
        print("Testing DDGS...")
        with DDGS() as ddgs:
            res = ddgs.text("test")
            print(f"Type of result: {type(res)}")
            if inspect.iscoroutine(res):
                print("It IS a coroutine.")
                await res
            else:
                print("It is NOT a coroutine (Synchronous).")
                # print first result title if list
                if isinstance(res, list) and len(res) > 0:
                    print(f"Title: {res[0].get('title')}")
                elif inspect.isgenerator(res):
                    print("It is a GENERATOR.")
                    first = next(res)
                    print(f"Title: {first.get('title')}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # asyncio.run(test()) 
    # Just run sync part of test first to see if it explodes
    test_sync = DDGS().text("test", max_results=1)
    print(f"Sync call result type: {type(test_sync)}")
