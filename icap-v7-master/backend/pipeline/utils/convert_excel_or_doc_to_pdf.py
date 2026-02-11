import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


EXCEL_FORMATS = {".xlsx", ".xls", ".xlsm", ".xlsb", ".ods"}
WORD_FORMATS = {".docx", ".doc", ".docm", ".odt", ".rtf", ".txt"}
ALL_SUPPORTED_FORMATS = EXCEL_FORMATS | WORD_FORMATS | {".pdf"}


def check_libreoffice():
    """Checks for the presence of LibreOffice."""
    for cmd in ["libreoffice", "soffice"]:
        try:
            result = subprocess.run(
                [cmd, "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                logger.info(f"LibreOffice detected: {result.stdout.strip()}")
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    logger.critical(
        "LibreOffice not found. This script cannot function without it. Please install LibreOffice."
    )
    return False


LIBREOFFICE_AVAILABLE = check_libreoffice()


class DocumentConverter:
    """
    A class focused on high-fidelity document conversion using a robust,
    two-step process for difficult Excel files.
    """

    def _create_instance_profile(self):
        """Create a temporary LibreOffice instance profile directory."""
        instance_profile = f"/tmp/libreoffice_instance_{int(time.time())}_{os.getpid()}"
        os.makedirs(instance_profile, exist_ok=True)
        return instance_profile

    def convert_file(self, input_file: str, output_pdf: str) -> bool:
        """Routes the conversion to the appropriate high-fidelity method."""
        if not LIBREOFFICE_AVAILABLE:
            return False

        extension = Path(input_file).suffix.lower()
        if not Path(input_file).exists():
            logger.error(f"Input file does not exist: {input_file}")
            return False
        if extension not in ALL_SUPPORTED_FORMATS:
            logger.error(f"Unsupported file type: {extension}")
            return False

        if extension == ".pdf":
            shutil.copy2(input_file, output_pdf)
            logger.info("Input is already a PDF. File copied.")
            return True

        if extension in EXCEL_FORMATS:
            return self._convert_excel_two_step(input_file, output_pdf)
        else:
            return self._convert_generic_with_libreoffice(input_file, output_pdf)

    def _sanitize_print_settings(self, input_file: str) -> str:
        """
        Remove Print_Titles/Print_Area defined names so LibreOffice does not repeat
        header rows on every page. Returns a temp copy path; caller must delete it.
        """
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=Path(input_file).suffix)
        os.close(tmp_fd)

        ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        try:
            with zipfile.ZipFile(input_file, "r") as zin:
                if "xl/workbook.xml" not in zin.namelist():
                    # Likely a legacy XLS/binary file; skip sanitization and use the original.
                    os.remove(tmp_path)
                    return input_file

                with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.infolist():
                        data = zin.read(item.filename)
                        if item.filename == "xl/workbook.xml":
                            try:
                                root = ET.fromstring(data)
                                defined_names = root.find("main:definedNames", ns)
                                if defined_names is not None:
                                    removed = False
                                    for dn in list(defined_names):
                                        if dn.get("name") in {
                                            "_xlnm.Print_Titles",
                                            "_xlnm.Print_Area",
                                        }:
                                            defined_names.remove(dn)
                                            removed = True
                                    if removed:
                                        data = ET.tostring(
                                            root, encoding="utf-8", xml_declaration=True
                                        )
                                        logger.info(
                                            "Removed Print_Titles/Print_Area from workbook to avoid repeated headers."
                                        )
                            except ET.ParseError:
                                logger.warning(
                                    "Failed to parse workbook.xml while sanitizing print settings; proceeding without modifications."
                                )
                        zout.writestr(item, data)
        except Exception as exc:
            logger.error(f"Failed to sanitize print settings: {exc}")
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            return input_file

        return tmp_path

    def _set_ods_page_size(
        self,
        ods_file: str,
        width: str = "20in",
        height: str = "20in",
        orientation: str = "landscape",
    ) -> bool:
        """
        Modifies all page styles within an ODS file to a specified size and orientation.
        This involves unzipping the ODS, editing styles.xml, and re-zipping the contents.
        """
        temp_dir = tempfile.mkdtemp()
        try:
            with zipfile.ZipFile(ods_file, "r") as original_zip:
                try:
                    styles_xml_path = original_zip.extract("styles.xml", temp_dir)
                except KeyError:
                    logger.warning(
                        f"'styles.xml' not found in {os.path.basename(ods_file)}. Cannot set page size."
                    )
                    return True

                namespaces = {
                    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
                    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
                }
                ET.register_namespace("style", namespaces["style"])
                ET.register_namespace("fo", namespaces["fo"])

                tree = ET.parse(styles_xml_path)
                root = tree.getroot()

                modified = False
                for page_layout_props in root.findall(
                    ".//style:page-layout-properties", namespaces
                ):
                    page_layout_props.set(f"{{{namespaces['fo']}}}page-width", width)
                    page_layout_props.set(f"{{{namespaces['fo']}}}page-height", height)
                    page_layout_props.set(
                        f"{{{namespaces['style']}}}print-orientation", orientation
                    )
                    modified = True

                if not modified:
                    logger.warning(
                        f"No page styles found in 'styles.xml' for {os.path.basename(ods_file)}. Page size not set."
                    )

                tree.write(styles_xml_path, xml_declaration=True, encoding="UTF-8")

                new_ods_file = os.path.join(temp_dir, "modified.ods")
                with zipfile.ZipFile(
                    new_ods_file, "w", zipfile.ZIP_DEFLATED
                ) as new_zip:
                    for item in original_zip.infolist():
                        if item.filename == "styles.xml":
                            new_zip.write(styles_xml_path, "styles.xml")
                        else:
                            new_zip.writestr(item, original_zip.read(item.filename))

            shutil.move(new_ods_file, ods_file)
            logger.info(
                f"Successfully set page size to {width}x{height} for {os.path.basename(ods_file)}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to set page size for {os.path.basename(ods_file)}: {e}"
            )
            return False
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _convert_excel_two_step(self, input_file: str, output_pdf: str) -> bool:
        """
        Uses a robust two-step process (XLSX -> ODS -> PDF) to ensure
        layout commands are respected.
        """
        logger.info(f"Starting robust two-step conversion for {Path(input_file).name}")
        temp_dir = tempfile.mkdtemp()
        sanitized_source = input_file
        instance_profile = self._create_instance_profile()
        try:
            sanitized_source = self._sanitize_print_settings(input_file)

            logger.info("Step 1: Converting to intermediate ODS format...")
            cmd_step1 = [
                "libreoffice",
                f"-env:UserInstallation=file://{instance_profile}",
                "--headless",
                "--convert-to",
                "ods",
                "--outdir",
                temp_dir,
                sanitized_source,
            ]
            result_step1 = subprocess.run(
                cmd_step1, capture_output=True, text=True, timeout=180
            )

            if result_step1.returncode != 0:
                logger.error(
                    f"Step 1 (to ODS) failed. Stderr: {result_step1.stderr.strip()}"
                )
                logger.info("Attempting direct PDF export fallback for Excel file.")
                return self._convert_generic_with_libreoffice(
                    sanitized_source, output_pdf
                )

            intermediate_ods = os.path.join(
                temp_dir, f"{Path(sanitized_source).stem}.ods"
            )
            if not os.path.exists(intermediate_ods):
                # Fallback: pick any ODS LibreOffice dropped in the temp directory.
                fallback = next(
                    (p for p in Path(temp_dir).glob("*.ods")),
                    None,
                )
                if fallback and fallback.exists():
                    intermediate_ods = str(fallback)
                    logger.warning(
                        "Expected ODS not found, but found %s. Using it.",
                        fallback.name,
                    )
                else:
                    logger.error(
                        "Step 1 seemed to succeed, but intermediate ODS file was not created."
                    )
                    logger.error(
                        "LibreOffice stdout: %s", result_step1.stdout.strip()
                    )
                    logger.error(
                        "LibreOffice stderr: %s", result_step1.stderr.strip()
                    )
                    logger.info(
                        "Attempting direct PDF export fallback for Excel file."
                    )
                    return self._convert_generic_with_libreoffice(
                        sanitized_source, output_pdf
                    )

            logger.info("Step 1 successful. Intermediate ODS file created.")

            logger.info('Step 1.5: Setting page size to Tabloid (100"x100" landscape)...')
            if not self._set_ods_page_size(
                intermediate_ods, width="20in", height="20in", orientation="landscape"
            ):
                logger.error(
                    "Failed to modify ODS page size to Tabloid. Conversion will be aborted."
                )
                return False

            logger.info(
                "Step 2: Converting ODS to PDF with aggressive scaling to fit Tabloid page..."
            )
            filter_data = {
                "SinglePageSheets": True,
                "FitToPage": True,
                "FitWidth": 1,
                "FitHeight": 1,
            }
            final_filter = f"pdf:calc_pdf_Export:{json.dumps(filter_data)}"
            cmd_step2 = [
                "libreoffice",
                f"-env:UserInstallation=file://{instance_profile}",
                "--headless",
                "--convert-to",
                final_filter,
                "--outdir",
                temp_dir,
                intermediate_ods,
            ]
            result_step2 = subprocess.run(
                cmd_step2, capture_output=True, text=True, timeout=180
            )

            if result_step2.returncode != 0:
                logger.error(
                    f"Step 2 (ODS to PDF) failed. Stderr: {result_step2.stderr.strip()}"
                )
                return False

            final_pdf_temp = os.path.join(
                temp_dir, f"{Path(intermediate_ods).stem}.pdf"
            )
            if os.path.exists(final_pdf_temp):
                shutil.move(final_pdf_temp, output_pdf)
                logger.info("Two-step conversion successful.")
                return True
            else:
                logger.error("Step 2 seemed to succeed, but final PDF was not created.")
                return False

        except Exception as e:
            logger.error(f"Two-step conversion process failed with an exception: {e}")
            return False
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            if sanitized_source != input_file:
                try:
                    os.remove(sanitized_source)
                except OSError:
                    pass
            try:
                subprocess.run(
                    [
                        "libreoffice",
                        f"-env:UserInstallation=file://{instance_profile}",
                        "--terminate",
                    ],
                    capture_output=True,
                    timeout=10,
                )
                shutil.rmtree(instance_profile, ignore_errors=True)
            except:
                pass

    def _convert_generic_with_libreoffice(
        self, input_file: str, output_file: str
    ) -> bool:
        """Standard LibreOffice conversion for non-Excel documents."""
        temp_output_dir = tempfile.mkdtemp()
        instance_profile = self._create_instance_profile()
        try:
            cmd = [
                "libreoffice",
                f"-env:UserInstallation=file://{instance_profile}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                temp_output_dir,
                input_file,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                expected_pdf = os.path.join(
                    temp_output_dir, f"{Path(input_file).stem}.pdf"
                )
                if os.path.exists(expected_pdf):
                    shutil.move(expected_pdf, output_file)
                    return True
            logger.error(
                f"Standard LibreOffice conversion failed. Stderr: {result.stderr.strip()}"
            )
            return False
        finally:
            shutil.rmtree(temp_output_dir, ignore_errors=True)
            try:
                subprocess.run(
                    [
                        "libreoffice",
                        f"-env:UserInstallation=file://{instance_profile}",
                        "--terminate",
                    ],
                    capture_output=True,
                    timeout=10,
                )
                shutil.rmtree(instance_profile, ignore_errors=True)
            except:
                pass

    def print_capabilities(self):
        print("=" * 60)
        print("DOCUMENT TO PDF CONVERTER - ROBUST TWO-STEP STRATEGY")
        print("=" * 60)
        print(
            f"  LibreOffice:    {'Available' if LIBREOFFICE_AVAILABLE else 'Not Available (CRITICAL)'}"
        )
        print("\nSTRATEGY: This definitive version uses a robust two-step process for")
        print("complex Excel files (XLSX -> ODS -> PDF). This forces LibreOffice to")
        print("correctly apply page scaling and ensures the highest layout fidelity.")
        print("\nEXCEL NOTE: For Excel files, the page size is programmatically set to")
        print('Tabloid (20"x20") to ensure wide sheets fit on a single page.')
        print("=" * 60 + "\n")


def get_unique_pdf_path(base_path: str) -> str:
    """
    Generate a unique PDF file path. If the file exists, append _0, _1, _2, etc.

    Args:
        base_path: The desired output PDF path (e.g., /path/to/file.pdf)

    Returns:
        A unique file path that doesn't exist yet
    """
    if not os.path.exists(base_path):
        return base_path

    directory = os.path.dirname(base_path)
    filename = Path(base_path).stem
    extension = Path(base_path).suffix

    counter = 0
    while True:
        new_path = os.path.join(directory, f"{filename}_{counter}{extension}")
        if not os.path.exists(new_path):
            return new_path
        counter += 1


def convert_excel_or_doc_to_pdf(file_paths: list) -> dict:
    """
    Convert a list of file paths to PDF format, saving in the same directory with .pdf extension.

    Args:
        file_paths: List of absolute file paths to convert

    Returns:
        Dictionary with 'successful' and 'failed' lists of file paths
    """
    converter = DocumentConverter()

    if not LIBREOFFICE_AVAILABLE:
        logger.error("Cannot proceed without LibreOffice installed.")
        return {"successful": [], "failed": file_paths}

    if not file_paths:
        logger.warning("No files provided for conversion.")
        return {"successful": [], "failed": []}

    successful = []
    failed = []

    logger.info(f"Processing {len(file_paths)} files for PDF conversion")

    for index, input_file_path in enumerate(file_paths, 1):
        if not os.path.exists(input_file_path):
            logger.error(
                f"[{index}/{len(file_paths)}] File does not exist: {input_file_path}"
            )
            failed.append(input_file_path)
            continue

        # Get the directory and base name
        directory = os.path.dirname(input_file_path)
        base_name = Path(input_file_path).stem

        # Create the desired output path
        desired_output_path = os.path.join(directory, f"{base_name}.pdf")

        # Get a unique path if the file already exists
        output_file_path = get_unique_pdf_path(desired_output_path)

        logger.info(
            f"[{index}/{len(file_paths)}] Processing: {os.path.basename(input_file_path)}"
        )

        try:
            if converter.convert_file(input_file_path, output_file_path):
                logger.info(
                    f"  ✓ Successfully converted to {os.path.basename(output_file_path)}"
                )
                successful.append(output_file_path)
            else:
                logger.error(
                    f"  ✗ Conversion failed for {os.path.basename(input_file_path)}"
                )
                failed.append(input_file_path)
        except Exception as e:
            logger.error(f"  ✗ An unexpected error occurred: {e}")
            failed.append(input_file_path)

    logger.info("=" * 80)
    logger.info("CONVERSION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total files processed: {len(file_paths)}")
    logger.info(f"Successful conversions: {len(successful)}")
    logger.info(f"Failed conversions: {len(failed)}")

    result = {"successful": successful}

    if failed:
        result["failed"] = failed

    return result