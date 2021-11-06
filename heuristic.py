from typing import Set, Generator
from rpc_utils import *

max_block_height = 200 #1240503

async def heuristic_1(eta: int, T: int) -> Generator[List[Input], None, None]:
    """Implementation of Alogorithm 1: Heuristic I

    Args:
        eta (int): The number of iterations
        T (int): The maximum block height to analyze
    """
    spent_keys: Set[Output] = set()
    keys_to_analyze : List[Input] = []

    # Fill keysToAnalyze list, corresponds to lines 3-10
    # Asynchronous implementation to reduce waiting times
    keys_to_analyze = await get_input_keys_async(range(0, T))
    
    print("Done with async RPC, found {} different outputs".format(len(keys_to_analyze)))

    # Determine spent keys, corresponds to lines 11-19
    for _ in range(1, eta + 1):
        for input in keys_to_analyze:
            in_keys = input.keys

            # small optimization: if |in_keys| = 1, key is spent
            if (len(in_keys) == 1):
                spent_keys.add(in_keys[0])
                continue

            # Determine untraced keys in input keys
            untraced: List[Output] = []
            untraced = list(filter(lambda key: key not in spent_keys, in_keys))

            # if |untraced| = 1, add to spent keys and update input keys for next iteration
            if (len(untraced) == 1):
                spent_keys.add(untraced[0])
                input.keys = untraced

            # write to file for later use
            # with open('data/keys_{}.pkl'.format(eta), 'wb') as outfile:
            #     pickle.dump(keys_to_analyze, outfile)

        print(len(spent_keys) / len(keys_to_analyze))
        yield keys_to_analyze
    # return (spent_keys, keys_to_analyze)
