import asyncio
import json
import os
import sys

from .main import pyallama_prompt_all

PREVIOUS_FILE = os.path.expanduser("~/.pyallama-hellaswag")


def previously_used():
    try:
        with open(PREVIOUS_FILE, "r") as pu:
            return json.load(pu)
    except FileNotFoundError:
        return []


def id_from_dataset_obj(obj):
    return str(obj["ind"]) + "__" + obj["source_id"]


def main():
    previous = previously_used()
    dataset = []

    # https://github.com/rowanz/hellaswag/blob/master/data/hellaswag_test.jsonl
    with open(sys.argv[-1], "r") as hsjsonl:
        for line in hsjsonl.readlines():
            dataset.append(json.loads(line))

    print(f"Loaded {len(dataset)} rows")
    rand_index = int(float(int.from_bytes(os.urandom(1), "big") / 0xFF) * len(dataset))
    try:
        rand_index = int(sys.argv[-2])
    except ValueError:
        pass
    rand_obj = dataset[rand_index]
    rand_id = id_from_dataset_obj(rand_obj)

    if rand_id in previous:
        print(f"ID {rand_id} has already been used! Try again.\n")
        sys.exit(-1)

    previous.append(rand_id)
    with open(PREVIOUS_FILE, "w+") as pu_w:
        json.dump(previous, pu_w)

    print(f"Using index {rand_index}, ID {rand_id}, prompt:\n")
    print(rand_obj["ctx"])
    print()

    asyncio.run(pyallama_prompt_all(rand_obj["ctx"]))


if __name__ == "__main__":
    main()
