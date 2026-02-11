from collections import defaultdict
import traceback


def rename_duplicate_labels(d_json: dict) -> dict:
    """Renames duplicate labels by appending an index starting from 1 for duplicates only."""
    input_json = d_json.copy()
    nodes = input_json["nodes"]
    try:
        for node in nodes:
            documents = node["children"]
            for document in documents:
                if document["type"] == "table":
                    tables = document["children"]
                    for table in tables:
                        rows = table["children"]
                        label_counts = defaultdict(int)

                        for row in rows:
                            label = row["label"]
                            if (
                                label_counts[label] > 0
                            ):
                                row["label"] = f"{label}_{label_counts[label]-1}"
                            label_counts[label] += 1
    except Exception as e:
        print(traceback.format_exc())
    return input_json
