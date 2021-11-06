from asyncio.locks import Semaphore
from typing import Any, Coroutine, Dict, List
#import requests
import json
from itertools import chain, accumulate
import asyncio
from aiohttp import ClientSession

url = "http://localhost:1800/"
max_number_of_requests = 2000

class Output(object):
    __slots__ = 'index', 'amount'
    def __init__(self, index, amount) -> None:
        self.index = index
        self.amount = amount

    def __str__(self) -> str:
        return "(index: {}, amount: {})".format(self.index, self.amount)

    def __repr__(self) -> str:
        return "(index: {}, amount: {})".format(self.index, self.amount)
    
    def __hash__(self) -> int:
        return hash(self.__repr__())

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Output):
            return (self.index == o.index) and (self.amount == o.amount)
        else:
            return False
    
    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)


class Input(object):
    __slots__ = 'keys', 'block_height', 'block_timestamp', 'number_of_mixins'
    def __init__(self, keys: List[Output], block_height: int, block_timestamp: int):
        self.keys: List[Output] = keys
        self.block_height: int = block_height
        self.block_timestamp: int = block_timestamp
        self.number_of_mixins: int = len(keys) - 1

    def __str__(self) -> str:
        return str(self.keys)
    
    def __repr__(self) -> str:
        return str(self.keys)#str(self.keys)

def get_height():
    response = requests.get(url + "get_height")
    print(response.json())

get_block_url = url + "json_rpc"

def get_block(height: int):
    data = {"jsonrpc": "2.0", "id": "0", "method": "get_block", "params": { "height":height} }
    response = requests.get(url + "json_rpc", json=data)
    hashes = json.loads(json.loads(response.text)["result"]["json"])["tx_hashes"][0]
    print(hashes)

get_outputs_url = url + "get_outs"
async def get_outputs_async(offsets: List[int], amount: int, session: ClientSession) -> Coroutine[None, None, List[str]]:
    data = {
        "outputs": list(map(lambda o: {
            "index": o.index,
            "amount": amount
        }, offsets))
    }
    async with session.get(get_outputs_url, json=data) as response:
        payload = await response.read()
        txo_keys = list(map(lambda out: out["key"], json.loads(payload)["outs"]))
        return txo_keys

async def get_block_async(height: int, session: ClientSession) -> Coroutine[None, None, Dict[str, Any]]:
    data = {
        "jsonrpc": "2.0", 
        "id": "0",
        "method": "get_block",
        "params": { "height": height}
    }
    try:
        async with session.get(get_block_url, json=data) as response:
            payload = await response.read()
            return json.loads(json.loads(payload)["result"]["json"])
    except asyncio.TimeoutError:
        print("TimeoutError on block with height: {}".format(height))
    except:
        print("Unexpected error occurred when retrieving block with height: {}".format(height))
    return {}

get_transactions_url = url + "get_transactions"

async def get_transaction_inputs_async(tx_hashes: List[str], session: ClientSession) -> Coroutine[None, None, List[List[List[Output]]]]:
    data = {
        "txs_hashes": tx_hashes,
        "decode_as_json": True,
    }
    async with session.get(get_transactions_url, json=data) as response:
        payload = await response.read()
        return list(map(lambda tx:
            list(map(lambda k_in:
                list(map(lambda index: Output(index, k_in["key"]["amount"]),
                # need to accumulate here because key_offsets uses differential encoding
                accumulate(k_in["key"]["key_offsets"]))),
            json.loads(tx)["vin"])),
        json.loads(payload)["txs_as_json"]))


async def bound_get_input_keys_async(sem: Semaphore, height: int, session: ClientSession) -> Coroutine[None, None, List[Input]]:
    async with sem:
        block = await get_block_async(height, session)
        # Check if block contains non-coinbase transactions
        if "tx_hashes" not in block or len(block["tx_hashes"]) == 0:
            return None
        block_tx_keys = await get_transaction_inputs_async(block["tx_hashes"], session)
        return list(chain.from_iterable(map(lambda tx_keys:
            list(map(lambda txo: Input(txo, height, block["timestamp"]), tx_keys)),
        block_tx_keys)))

async def get_input_keys_async(heights: range) -> Coroutine[None, None, List[Input]]: 
    tasks = []
    sem = asyncio.Semaphore(max_number_of_requests)

    async with ClientSession() as session:
        for height in heights:
            task = asyncio.ensure_future(bound_get_input_keys_async(sem, height, session))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        # Filter None values and flatten list
        filtered: List[Input] = list(chain(*filter(None, responses)))
        return filtered

async def test(heights: range) -> Coroutine[None, None, List[Input]]: 
    tasks = []

    async with ClientSession() as session:
        for height in heights:
            task = asyncio.ensure_future(get_block_async(height, session))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        filtered = list(map(lambda x: x["tx_hashes"], responses))
        print(filtered)

async def test2() -> Coroutine[None, None, List[Input]]: 
    tasks = []

    async with ClientSession() as session:
        task = asyncio.ensure_future(get_transaction_inputs_async(['beb76a82ea17400cd6d7f595f70e1667d2018ed8f5a78d1ce07484222618c3cd'], session))
        tasks.append(task)
        responses = await asyncio.gather(*tasks)
        print(responses)    

async def test3() -> Coroutine[None, None, List[str]]: 
    tasks = []

    async with ClientSession() as session:
        task = asyncio.ensure_future(get_outputs_async([Output(0, 307304)], session))
        tasks.append(task)
        responses = await asyncio.gather(*tasks)
        print(responses)
