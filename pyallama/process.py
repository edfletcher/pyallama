import json
import os
import re
import sys
from functools import reduce

import chevron
import mistune

FILE_PATTERN = r"^pyallama-output_([\w\d]+)\.json$"
FILES = {}
ROOT_DIR = os.path.normpath(sys.argv[-1])


def main():
    global_style = ""
    with open(f"{ROOT_DIR}/process_templates/global_style.css", "r") as gcss:
        global_style = gcss.readlines()
    global_style = "".join(global_style)

    for file in list(
        filter(lambda f: re.match(FILE_PATTERN, f) is not None, os.listdir(ROOT_DIR))
    ):
        with open(file, "r") as f:
            try:
                parsed = json.load(f)
                if not (
                    isinstance(parsed, dict)
                    and "prompt" in parsed
                    and "results" in parsed
                ):
                    raise BaseException("Bad format")
                FILES[file] = parsed
            except BaseException as e:
                print(f"Loading {file} failed:")
                print(e)

    index = {"reports": [], "global_style": global_style}

    for file_name, record in FILES.items():
        datetime = re.match(FILE_PATTERN, file_name).group(1)
        record["prompt"] = mistune.html(record["prompt"])
        shared = {
            "datetime": datetime,
            "models_count": len(record["results"]),
            "total_tokens": reduce(
                lambda a, x: a + x,
                map(lambda e: e["response"]["tokens"], record["results"]),
            ),
            "global_style": global_style,
        }
        index["reports"].append(
            {
                **shared,
                "prompt": record["prompt"],
            }
        )
        for res in record["results"]:
            res["response"]["response"] = mistune.html(res["response"]["response"])
        with open(f"{ROOT_DIR}/process_templates/model.html", "r") as f:
            with open(f"{ROOT_DIR}/process_output/reports/{datetime}.html", "w") as o:
                o.write(chevron.render(f, {**shared, **record}))

    index["reports"].sort(key=lambda e: e["datetime"], reverse=True)
    with open(f"{ROOT_DIR}/process_templates/index.html", "r") as f:
        with open(f"{ROOT_DIR}/process_output/index.html", "w") as o:
            o.write(chevron.render(f, index))


if __name__ == "__main__":
    main()
