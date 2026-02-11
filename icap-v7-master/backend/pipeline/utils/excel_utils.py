import os
import time
import xlrd
import shutil
import pathlib
import traceback
import subprocess


def validate_xls_file(file_path):
    """
    Check the xls file invalid or valid.

    Args:
        file_path (str): Path to input XLS file.

    Returns:
        bool: If the file valid return True, otherwise False.

    Process Details:
        - Open XLS file using 'xlrd.open_workbook'.
        - If there are no sheets in the workbook, the file is considered invalid.
        - If the workbook has sheets then iterates through each sheet for data.
        - Release the workbook resource after validation.

    Notes:
        - Catche exception 'xlrd.XLRDError' for invalid XLS file.
    """
    try:
        workbook = xlrd.open_workbook(file_path, on_demand=True)
        if workbook.nsheets == 0:
            print("File contains no worksheets")
            return False

        has_content = False
        for sheet_idx in range(workbook.nsheets):
            sheet = workbook.sheet_by_index(sheet_idx)
            if sheet.nrows > 0 or sheet.ncols > 0:
                has_content = True
                break

        if not has_content:
            print("File contains no data")
            return False

        workbook.release_resources()
        return True

    except xlrd.XLRDError as e:
        print(f"Invalid XLS file: {str(e)}")
        print(traceback.format_exc())
        return False
    except Exception as e:
        print(f"File validation failed: {str(e)}")
        print(traceback.format_exc())
        return False


def check_libreoffice_installation():
    """Checking libreoffice installed or not"""
    try:
        process = subprocess.run(
            ["soffice", "--version"], capture_output=True, text=True
        )
        return True
    except Exception:
        return False


def convert_xls_to_xlsx(input_file, output_file):
    """
    Convert XLS file to XLSX using LibreOffice in headless mode.

    Args:
        input_file (str): Path to input XLS file.
        output_file (str): Path for output XLSX file.

    Returns:
        output_path (str): Path to converted file.

    Process Details:
        - Validate 'LibreOffice' installation to ensure the 'soffice' command is available.
        - Check the existence of the input file and ensure the output directory exists.
        - Create a temporary instance profile for 'LibreOffice' to isolate the conversion process.
        - Execute the 'soffice' command to perform the conversion in headless mode.
        - Validate the output by checking the existence and size of the resulting XLSX file.
        - Rename the temporary output file to the specified output path.

    Notes:
        - Require 'LibreOffice' to be installed on the system.
    """
    try:
        if not check_libreoffice_installation():
            raise EnvironmentError("LibreOffice headless installation not found")

        input_path = pathlib.Path(input_file).resolve()
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        output_path = pathlib.Path(output_file).resolve()
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        instance_profile = f"/tmp/libreoffice_instance_{int(time.time())}"
        os.makedirs(instance_profile, exist_ok=True)

        cmd = [
            "soffice",
            f"-env:UserInstallation=file://{instance_profile}",
            "--headless",
            "--convert-to",
            "xlsx:Calc MS Excel 2007 XML",
            "--outdir",
            str(output_dir),
            str(input_path),
        ]

        process = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if process.returncode != 0:
            raise Exception(f"Conversion failed: {process.stderr}")

        temp_output = output_dir / f"{input_path.stem}.xlsx"
        if temp_output.exists():
            temp_output.rename(output_path)

        if not output_path.exists():
            raise Exception("Output file was not created")

        if output_path.stat().st_size == 0:
            raise Exception("Output file is empty")

        return str(output_path)

    except subprocess.TimeoutExpired:
        raise Exception("Conversion timed out after 5 minutes")
    except Exception as e:
        raise
    finally:
        instance_profile = f"/tmp/libreoffice_instance_{int(time.time())}"
        subprocess.run(
            [
                "soffice",
                f"-env:UserInstallation=file://{instance_profile}",
                "--terminate",
            ],
            capture_output=True,
        )
        try:

            shutil.rmtree(instance_profile, ignore_errors=True)
        except:
            pass