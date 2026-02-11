"""
Organization: AIDocbuilder Inc.
File: scripts/OrganizeFiles.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization

Last Updated By: Nayem
Last Updated At: 2024-12-04

Description:
    This script manage file operations.

Dependencies:
    - os

Main Features:
    - Organize tif images and excel files.
"""
import os


class OrganizeFiles:
    def __init__(self, batch_id, input_path, batch_instance):
        """Initialize the OrganizeFiles class instance"""
        self.batch_id = batch_id
        self.input_path = input_path
        self.batch_instance = batch_instance
    

    def process(self):
        """
        This function rename files to lowercase and update file paths
        
        Args:
            Operate on class attributes.

        Process Details:
            - Construct the batch path using the input path and batch ID.
            - Retrieve all files in the batch directory.
            - Filter TIF images and Excel files.
            - Rename the selected files to lowercase and update file paths.

        Notes:
            - Only file with '.tif' extension and Excel files '.xlsx' starting with 'tm' are processed.
            - Modify files directly in the specified directory.
        """
        batch_path = os.path.join(self.input_path, self.batch_id)
        batch_files = os.listdir(batch_path)

        # For PDF Batches
        # Rename TIF files to lowercase:
        tif_images = [i for i in batch_files if i.endswith(".tif")]

        # For excel batches
        excel_files = [
            i for i in batch_files if i.endswith(".xlsx") and i.lower().startswith("tm")
        ]

        file_names = tif_images + excel_files

        for file_name in file_names:
            os.rename(
                os.path.join(batch_path, file_name),
                os.path.join(batch_path, file_name.lower()),
            )
