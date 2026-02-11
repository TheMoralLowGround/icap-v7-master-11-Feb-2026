from pydantic import BaseModel, Field, model_validator, field_validator
from typing import List, Tuple

class ClassificationItem(BaseModel):
    label: str = Field(..., description="Document type label.")
    pages: List[Tuple[int, int]] = Field(..., description="List of (start, end) page ranges.")

    @classmethod
    def set_labels(cls, labels: List[str]):
        cls.DOC_TYPE_LABELS = labels

    @field_validator("label", mode="before")
    @classmethod
    def validate_label(cls, v):
        if not isinstance(v, str):
            raise ValueError("Label must be a string.")
        v_clean = v.strip()
        for allowed in cls.DOC_TYPE_LABELS:
            if v_clean.lower() == allowed.lower():
                return allowed
        raise ValueError(f"Invalid label: {v}")

    @field_validator("pages", mode="before")
    @classmethod
    def normalize_pages(cls, v):
        # If already ranges like [(1,2)], keep as is
        if all(isinstance(i, (list, tuple)) and len(i) == 2 for i in v):
            return [tuple(i) for i in v]

        # If flat list like [1,2,3], convert to ranges [(1,3)]
        if all(isinstance(i, int) for i in v):
            pages = sorted(set(v))
            ranges = []
            start = prev = pages[0]
            for p in pages[1:]:
                if p == prev + 1:
                    prev = p
                else:
                    ranges.append((start, prev))
                    start = prev = p
            ranges.append((start, prev))
            return ranges

        raise ValueError("Pages must be a list of ints or (start, end) pairs.")


class ClassificationResponse(BaseModel):
    classes: List[ClassificationItem] = Field(...)

    @model_validator(mode="before")
    @classmethod
    def merge_same_labels(cls, values):
        """
        Merge duplicate labels **per contiguous block** and compress pages.
        Preserves input order.
        """
        classes = values.get("classes", [])
        if not classes:
            return values

        merged_classes: List[dict] = []

        for item in classes:
            label = item["label"]
            pages = item["pages"]

            # Normalize pages to flat list
            flat_pages = []
            for p in pages:
                if isinstance(p, int):
                    flat_pages.append(p)
                elif isinstance(p, (list, tuple)) and len(p) == 2:
                    flat_pages.extend(range(p[0], p[1] + 1))

            # Compress consecutive pages
            if flat_pages:
                flat_pages = sorted(set(flat_pages))
                ranges = []
                start = prev = flat_pages[0]
                for p in flat_pages[1:]:
                    if p == prev + 1:
                        prev = p
                    else:
                        ranges.append([start, prev])
                        start = prev = p
                ranges.append([start, prev])

                # If last item in merged_classes has same label, append ranges
                if merged_classes and merged_classes[-1]["label"] == label:
                    merged_classes[-1]["pages"].extend(ranges)
                else:
                    merged_classes.append({"label": label, "pages": ranges})

        return {"classes": merged_classes}
