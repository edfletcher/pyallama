import asyncio
import collections
import datetime
import json
import re
import sys
from typing import *

import aiohttp

HOST = "http://localhost:42000"
REQ_COMPLETE_PRCNT = 95
CHECK_WAIT_TIME_MINS = 7


async def get_models() -> Tuple[List[Tuple[str, str]], Dict[str, Any]]:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{HOST}/models") as response:
            models_json: Dict[str, Any] = await response.json()
            model_tuples = list(
                map(
                    lambda m: (
                        m[0],
                        m[1]["displayName"],
                    ),
                    models_json.items(),
                )
            )
            return (
                model_tuples,
                models_json,
            )


async def prompt_model(user_prompt: str, model_key: str) -> str:
    async with aiohttp.ClientSession() as session:
        payload = {"prompt": user_prompt, "model": model_key, "priority": "LOW"}
        async with session.post(f"{HOST}/prompt", json=payload) as response:
            if response.status == 413:
                print("PROMPT TOO LARGE!")
                sys.exit(-1)
            return await response.json()


async def check_response(prompt_id: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{HOST}/prompt/{prompt_id}") as response:
            if response.status == 200:
                return await response.json()
            if response.status == 404:
                print(f"BAD PROMPT ID? {prompt_id}")
                sys.exit(-1)
    return None


async def pyallama_prompt_all(user_prompt: str):
    QUEUE = collections.deque()
    COMPLETE = list()
    (model_tuples, models) = await get_models()
    print(f"Prompting {len(models)} models:")
    for key, display_name in model_tuples:
        model_prompt_id = (await prompt_model(user_prompt, key))["promptId"]
        QUEUE.append({"name": key, "id": model_prompt_id})
        print(f"  * '{display_name}' is queued with ID {model_prompt_id}")

    print("\n")
    total_expected_prompts = int(len(QUEUE) * (REQ_COMPLETE_PRCNT / 100))
    print(
        f"Expecting at least {total_expected_prompts} prompts (of {len(models)}) to complete..."
    )
    while len(COMPLETE) < total_expected_prompts:
        completed_this_round = []
        for cur_ele in collections.deque(QUEUE):
            response = await check_response(cur_ele["id"])
            if response is not None:
                COMPLETE.append({**cur_ele, "response": response})
                QUEUE.remove(cur_ele)
                completed_this_round.append(cur_ele["id"])
            await asyncio.sleep(0.01)
        if len(completed_this_round):
            print(
                f"{len(completed_this_round)} finished ({len(QUEUE)} remaining): {', '.join(completed_this_round)}"
            )
        await asyncio.sleep(CHECK_WAIT_TIME_MINS * 60)

    print(
        f"Done! {len(COMPLETE)} completed, success rate of {int((len(COMPLETE) / len(models)) * 100)}%\n"
    )
    fname_date = re.sub(r"[\-:\.]", "", datetime.datetime.now().isoformat())
    fname = f"pyallama-output_{fname_date}.json"
    with open(fname, "w+") as f:
        json.dump({"prompt": user_prompt, "results": COMPLETE}, f)
    print(f"Output written to: {fname}")


def main():
    print("Enter prompt, CTRL+D ends:\n")
    prompt = ""
    try:
        for line in iter(input, "\x04"):
            prompt += line + "\n"
    except EOFError:
        pass
    print("\n")
    asyncio.run(pyallama_prompt_all(prompt))


if __name__ == "__main__":
    main()
