import json
import os
from dotenv import load_dotenv

from core.title_classfication_v2.utils.json_text_layout_renderer import _render_multipage_with_layout, _render_multipage_with_layout_filewise
from core.title_classfication_v2.app import predictLabel, predictLabelWithMajorityVoting

load_dotenv()

MAJORITY_VOTING = os.getenv("MAJORITY_VOTING", "false").lower() == "true"

def train(
    layout_ra_json_path, system_prompt, user_prompt
):
    ra_json = json.loads(open(layout_ra_json_path, "r", encoding="utf-8").read())
    all_files = _render_multipage_with_layout_filewise(ra_json)
    total_pages = sum([len(file) for file in all_files])
    
    if total_pages <= 20 or (MAJORITY_VOTING and total_pages <= 100):
        return predictLabelWithMajorityVoting(
            all_files=all_files,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            total_runs=3
        )
    
    return predictLabel(
        all_files=all_files,
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )