"""
Organization: AIDocbuilder Inc.
File: test.py
Version: 6.0
 
Authors:
    - Vivek - Initial implementation
 
Last Updated By: Vivek
Last Updated At: 2023-11-01
 
Description:
    This script is used for testing file operations in the in-memory file.
 
Dependencies:
    - io, os, shutil, sys
    - InMemoryUploadedFile from django.core.files.uploadedfile
 
Main Features:
    - In-memory file operations.
"""
import io
import os
import shutil
import sys

from django.core.files.uploadedfile import InMemoryUploadedFile

user_input_path = sys.argv[1]


def create_inmemory_file(file_path):
    """Creates an InMemoryUploadedFile from the given file path"""
    file_name = os.path.basename(file_path)
    stream = io.BytesIO()
    with open(file_path, "rb") as f:
        content = f.read()
    stream.write(content)
    file = InMemoryUploadedFile(
        stream, None, file_name, "text/plain", stream.tell(), None
    )
    file.seek(0)
    return file


def test(base_path):
    """Testing file operations in memory"""
    path = os.path.join(base_path, "test-folder")

    print(f"Creating folder {path}")
    if not os.path.exists(path):
        os.makedirs(path)

    file_path = os.path.join(path, "test.txt")
    with open(file_path, "w+") as f:
        f.write("DUMMY CONTENT")

    in_memory_file = create_inmemory_file(file_path)
    print(f"Deleting folder {path}")
    shutil.rmtree(path)

    print(in_memory_file.read())
    print("Operation completed")


test(user_input_path)
