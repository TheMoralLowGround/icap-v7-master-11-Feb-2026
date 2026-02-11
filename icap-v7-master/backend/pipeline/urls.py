"""
Organization: AIDocbuilder Inc.
File: pipeline/urls.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Add api endpoints

Last Updated By: Nayem
Last Updated At: 2024-09-19

Description:
    This file defines the URL routing for 'pipeline' app.

Dependencies:
    - path from django.urls
    - views from pipeline

Main Features:
    - API endpoints.
"""
from django.urls import path

from pipeline import views

urlpatterns = [
    path(
        "pre_upload_batch_status/",
        views.pre_upload_batch_status,
        name="pre_upload_batch_status",
    ),
    path("upload_email_batch/", views.upload_email_batch, name="upload_email_batch"),
    path("classify_batch/", views.classify_batch, name="classify_batch"),
    path("upload_batch/", views.upload_batch, name="upload_batch"),
    path("process_batch/", views.process_batch, name="process_batch"),
    path("process_atm_data/", views.process_atm_data, name="process_atm_data"),
    path("atm_chunk_data/", views.atm_chunk_data, name="atm_chunk_data"),
    path(
        "position_shift_data/",
        views.position_shift_data,
        name="position_shift_data",
    ),
    path("test_models/", views.test_models, name="test_models"),
    path("chunk_data/", views.chunk_data, name="chunk_data"),
    path("chunk_data_plain_text/", views.chunk_data_plain_text, name="chunk_data_plain_text"),
    path(
        "remove_not_in_use_batches/",
        views.remove_not_in_use_batches,
        name="remove_not_in_use_batches",
    ),
    path(
        "upload_batch_to_datacap/",
        views.upload_batch_to_datacap,
        name="upload_batch_to_datacap",
    ),
    path("train_documents/", views.train_documents),
    path("re_process_extraction/", views.re_process_extraction),
    path("re_process_training_batches/", views.re_process_training_batches),
    path("re_process_email_batches/", views.re_process_email_batches),
    path("get_docbuilder_payload/", views.get_docbuilder_payload),
    path("get_chars_from_xml/", views.get_chars_from_xml),
    path("get_text_by_pos/", views.get_text_by_pos),
    path("batch_path_content/", views.batch_path_content),
    path("download_batch_zip/", views.download_batch_zip),
    path("upload_batch_zip/", views.upload_batch_zip),
    path("download_email_batch/", views.download_email_batch),
    path("download_transaction/", views.download_transaction),
    path("upload_transaction/", views.upload_transaction),
    path("check_definitions_exist/", views.check_definitions_exist),
    path("import_definitions/", views.import_definitions),
    path("export_definitions/", views.export_definitions),
    path(
        "get_verification_details/<str:email_batch_id>/", views.get_verification_details
    ),
    path(
        "save_verification_details/<str:email_batch_id>/",
        views.save_verification_details,
    ),
    path("release_transaction/<str:email_batch_id>/", views.release_transaction),
    path("project_validation/", views.project_validation),
    path("automatic_classifiable_doc_types/", views.automatic_classifiable_doc_types),
    path("get_manual_classification_data/", views.get_manual_classification_data),
    path("test_manual_classification/", views.test_manual_classification),
    path("verify_manual_classification/", views.verify_manual_classification),
    path("download_training_batch/", views.download_training_batch),
    path("upload_training_batch/", views.upload_training_batch),
    path("classify_batch_sync/", views.classify_batch_sync),
    path("get_transaction_batches/", views.get_transaction_batches),
    path("update_batch/",views.update_batch),
    # path("get_ra_json_from_pdf/",views.get_ra_json_from_pdf),
    path("semantic_address_match/",views.semantic_address_match),
    path("get_annotation_batches/",views.get_annotation_batches),
    path("create_training_dataset_batch/",views.create_training_dataset_batch),
    path("test_graph_config/",views.test_graph_config),
    path("test_imap_config/",views.test_imap_config),
    path("get_service_logs/",views.get_service_logs),
    path("get_sharepoint_sites/",views.get_sharepoint_sites),
    path("get_sharepoint_drive/",views.get_sharepoint_drive),
    path("get_onedrive_folder/",views.get_onedrive_folder),
    path("get_drive_folder/",views.get_drive_folder),
    path("process_transaction/",views.process_transaction),
    path("process_training/",views.process_training),
    path("test_output_connection/",views.test_output_connection),
    path("get_test_json/",views.get_test_json),
    path("qdrant_vector_db/",views.qdrant_vector_db),
    path("get_spreadjs_license/",views.get_spreadjs_license),
]
