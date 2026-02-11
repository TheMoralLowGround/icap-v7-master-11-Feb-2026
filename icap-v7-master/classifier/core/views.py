import traceback
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.forms.models import model_to_dict
from pathlib import Path
import time
import json

from core.title_classfication_v2.schemas.models import ClassificationItem
from core.title_classfication_v2.app import predictLabel, predictLabelWithMajorityVoting
from core.title_classfication_v2.utils.json_text_layout_renderer import _render_multipage_with_layout, _render_multipage_with_layout_filewise
from core.dense_page_detector_v2.app import detect_dense_pages
from core.manual_classification_v2.app import train
from core.models import CustomCategory
from core.title_classfication_v2.utils.config import is_majority_voting, is_sync_mode

def process_title_classification(data):
    """
    Core classification logic that can be called from both API endpoint and RabbitMQ.
    
    Args:
        data (dict): Dictionary containing classification parameters
            - layout_xml_paths: List of paths to RA JSON files
            - page_directions: Dict containing system_prompt, user_prompt, category
    
    Returns:
        dict: Classification results with doctypes
    """
    start_time = time.time()
    print("Classifier Requested")
    print("$$"*20)

    layout_ra_json_paths = data.get("layout_xml_paths")
    
    page_directions = data.get("page_directions", None)
    system_prompt = page_directions.get("system_prompt", None)
    user_prompt = page_directions.get("user_prompt", None)
    
    doc_types = page_directions.get("category", None)
    doc_types = list(doc_types)
    ClassificationItem.set_labels(doc_types)
    
    if not layout_ra_json_paths:
        error = "RAJSON_file_path not found."
        print(f"{error=}")
        return {"error": error}
    
    doctypes = {}

    try:
        layout_ra_json_path = layout_ra_json_paths[0]
        ra_json = json.loads(open(layout_ra_json_path, "r", encoding="utf-8").read())
        all_files = _render_multipage_with_layout_filewise(ra_json)
        total_pages = sum([len(file) for file in all_files])

        if total_pages <= 20 or (is_majority_voting() and total_pages <= 100):
            doctypes = predictLabelWithMajorityVoting(
                all_files=all_files,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                total_runs=3
            )
        else:
            doctypes = predictLabel(
                all_files=all_files,
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
    
    except Exception as e:
        print(f"Classification error: {e}")
        print(traceback.format_exc())
        return {"error": str(e)}

    response = {"doctypes": doctypes}
    print(f"{response=}")
    end_time = time.time()
    print("\n" + "+" + "-" * 48 + "+")
    print("|" + " SETUP ".center(48) + "|")
    print("+" + "-" * 48 + "+")
    print(f"| SYNC MODE       : {str(is_sync_mode()).ljust(28)} |")
    print(f"| MAJORITY VOTING : {str(is_majority_voting()).ljust(28)} |")
    print("+" + "-" * 48 + "+\n")
    print(f"Time taken for classification: {end_time - start_time} seconds")

    return response

@api_view(["POST"])
def title_classification(request):
    """
    API endpoint for title classification.
    Calls the core classification logic and returns HTTP response.
    """
    result = process_title_classification(request.data)
    
    if "error" in result:
        return Response({"error": result["error"]}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(result, status=status.HTTP_200_OK)

@api_view(["POST"])
def manual_classification(request):
    print("Classifier Requested")
    print("$$"*20)

    data = request.data
    layout_ra_json_paths = data.get("ra_json_paths")
    
    page_directions = data.get("page_directions", None)
    system_prompt = page_directions.get("system_prompt", None)
    user_prompt = page_directions.get("user_prompt", None)
    
    doc_types = page_directions.get("category", None)
    doc_types = list(doc_types)
    ClassificationItem.set_labels(doc_types)
    
    
    if not layout_ra_json_paths:
        error = "RAJSON_file_path not found."
        print(f"{error=}")
        return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

    try:
        layout_ra_json_path = layout_ra_json_paths[0]

        doctypes = train(
            layout_ra_json_path=layout_ra_json_path,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
    
    except Exception as e:
        print(e)

    response = {"doctypes": doctypes}
    print(f"{response=}")

    return Response(response, status=status.HTTP_200_OK)


@api_view(["POST"])
def ignore_dense_pages(request):
    print("Ignore Dense Page API Called")

    data = request.data
    print(f"Data = {data}")
    image_dir_paths = data.get("image_dir_paths", None)

    if not image_dir_paths:
        error = "image_dir_paths not found."
        print(f"{error=}")
        return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

    image_dir_paths = [Path(p) for p in image_dir_paths]

    try:
        dense_pages_list = detect_dense_pages(
            img_folders=image_dir_paths
        )
    except Exception as e:
        print(e)
    
    response = {"dense_pages_list": dense_pages_list}

    print(f"{response}")

    return Response(response, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_custom_category(request):
    print("Custom Category Data Requested")

    data = request.data
    if not data:
        return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

    profile = data.get("profile", None)

    # Fetch custom_category from db
    custom_category = {}
    custom_category_qs = CustomCategory.objects.filter(profile=profile)

    if custom_category_qs.exists():
        custom_category_instance = custom_category_qs.first()
        custom_category = model_to_dict(custom_category_instance)
        custom_category["manual_classification_data"] = []

    response = custom_category
    print(f"{response=}")

    return Response(response, status=status.HTTP_200_OK)


@api_view(["POST"])
def create_custom_category(request):
    print("Custom Category Creation Requested")

    data = request.data
    if not data:
        return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)
    
    profile = data.get("profile", None)
    custom_category_qs = CustomCategory.objects.filter(profile=profile)
    if custom_category_qs.exists():
        custom_category_instance = custom_category_qs.first()
        custom_category_data = data.get("data", None)
        if custom_category_data:
            custom_category_instance.data = custom_category_data
            custom_category_instance.save()
    else:
        custom_category_instance = CustomCategory.objects.create(**data)

    response = model_to_dict(custom_category_instance)
    print(f"{response=}")

    return Response(response, status=status.HTTP_200_OK)