"""
for testing comment out,
from rabbitmq_publisher import publish
self.base_output_dir = "/batches"
publish("create_batch_ocr_response", "to_pipeline", request_data)

uncomment,
self.base_output_dir = "output"     # for testing
self.draw_bbox_and_save(image_np, text_regions, output_folder, page_number, pdf_name)
"""

import gc

import requests
from flask import Flask, request, jsonify # type: ignore
import os
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance
import cv2
import numpy as np
from datetime import datetime, timedelta
import time
import re
import logging
from typing import List, Dict
import shutil
import traceback
import re
import torch
from doctr.models import ocr_predictor, db_resnet50, vgg16_bn_r
from doctr.models import page_orientation_predictor
from doctr.io import read_pdf
import json
import xml.etree.ElementTree as ET
from rabbitmq_publisher import publish
from deskew import determine_skew

os.environ['DOCTR_CACHE_DIR'] = 'core'

class OCREngine:

    def __init__(self):
        """Initialize OCR Engine with base output directory"""
        self.base_output_dir = "/batches"
        # self.base_output_dir = "output"     # for testing
        self.setup_logging()
        self.tm_no = 0
        self.dpi = 300
        # self.output_dpi = 300
        # if not os.path.exists('.EasyOCR/'):
        #     os.makedirs('.EasyOCR/', exist_ok=True)
        # user_network_dir = os.path.join(os.path.abspath('.EasyOCR'), 'user_network')

        # Load custom recognition model
        # self.reco_model = vgg16_bn_r(pretrained=False, pretrained_backbone=False)
        # self.reco_params = torch.load('.EasyOCR/best_accuracy3.pth', map_location="cpu")
        # self.reco_model.load_state_dict(self.reco_params)
        self.text_detector = "fast_base"

        # Load custom detection and recognition model
        # det_model = db_resnet50(pretrained=False, pretrained_backbone=False)
        # det_params = torch.load('<path_to_pt>', map_location="cpu")
        # det_model.load_state_dict(det_params)
        self.text_recognizer = "crnn_mobilenet_v3_large"

        # self.orientation_detector_model = "mobilenet_v3_small_page_orientation"

        self.predictor = ocr_predictor(det_arch=self.text_detector, 
                                    reco_arch=self.text_recognizer, 
                                    pretrained=True,
                                    assume_straight_pages=True,
                                    # straighten_pages=True,
                                    # detect_orientation=True,
                                    )
        # self.predictor.page_orientation_predictor = page_orientation_predictor(arch=self.orientation_detector_model, 
        #                                                         pretrained=True)

        self.page_orientation = page_orientation_predictor(pretrained=True, batch_size=1)

        self.logger.info("OCR Engine initialized with models")
        self.logger.info(f"text detector model: {self.text_detector}")
        self.logger.info(f"text recognizer model: {self.text_recognizer}")
        # self.logger.info(f"page orientation detection model: {self.orientation_detector_model}")

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ocr_engine.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
            
    def create_batch(self, pdf_paths, batch_id, profile_name, project):
        """
        Process multiple PDFs as a single batch
        
        Args:
            pdf_paths: List of PDF file paths to process
            
        Returns:
            Dict containing batch processing results and metadata
        """
        try:
            # Create batch batch_id and folder
            batch_folder = os.path.join(self.base_output_dir, batch_id)
            os.makedirs(batch_folder, exist_ok=True)
            
            batch_info = {
                'batch_id': batch_id,
                'file_paths': pdf_paths,
                'output_folder': batch_folder,
                'pdf_info': {},
                'processing_stats': {
                    'total_pdfs': len(pdf_paths),
                    'processed_pdfs': 0,
                    'total_pages': 0,
                    'start_time': time.time()
                }
            }
            
            # Copy and rename PDFs
            renamed_pdfs = {}
            original_file_paths = {}
            self.tm_no = 1
            print(f"{pdf_paths}")
            for pdf_path in pdf_paths:
                if not os.path.exists(pdf_path):
                    self.logger.warning(f"PDF not found: {pdf_path}")
                    continue
                
                new_pdf_name = f"tm{str(self.tm_no).zfill(6)}.pdf"
                new_pdf_path = os.path.join(batch_folder, new_pdf_name)
                shutil.copy(pdf_path, new_pdf_path)
                renamed_pdfs[new_pdf_path] = new_pdf_name
                original_file_paths[new_pdf_path] = pdf_path
                self.tm_no += 1
            
            # Process each renamed PDF
            for pdf_path in renamed_pdfs.keys():
                try:
                    self.logger.info(f"Processing PDF: {pdf_path}")
                    pdf_info = self._process_pdf(pdf_path, batch_folder, renamed_pdfs[pdf_path], original_file_paths[pdf_path])
                    batch_info['pdf_info'].update(pdf_info)
                    batch_info['processing_stats']['processed_pdfs'] += 1
                    
                    # Update this line to loop through all keys in the returned pdf_info
                    for key in pdf_info:
                        batch_info['processing_stats']['total_pages'] += len(pdf_info[key].keys())
                        
                except Exception as e:
                    self.logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
                    print(traceback.format_exc())
            
            # Create batch XML files
            self._create_batch_xml_files(batch_info['pdf_info'], batch_folder, renamed_pdfs, profile_name, project)
            
            # Calculate processing time
            end_time = time.time()
            processing_time = end_time - batch_info['processing_stats']['start_time']
            batch_info['processing_stats']['duration'] = str(timedelta(seconds=processing_time))
            
            return batch_info
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {str(e)}")
            raise
            
    def _process_pdf(self, pdf_path, batch_folder, pdf_name, original_file_path):
        """Process a single PDF file"""
        pdf_info = {}
        # Use a unique key for each PDF to prevent overwriting
        pdf_key = f"{batch_folder}_{os.path.basename(pdf_path)}"
        pdf_info[pdf_key] = {}
        
        # Convert PDF to TIFF
        tiff_files = self.convert_pdf_to_tif(pdf_path, batch_folder)
        
        # Process each page
        for tiff_file in tiff_files:
            start_page_time = time.time()
            # Run OCR and create outputs
            self.easyOCR_bbox(tiff_file, batch_folder, self.tm_no, os.path.basename(pdf_path))
            
            # Save TIFF file
            output_file_name = f"tm{str(self.tm_no).zfill(6)}.tif"
            output_path = os.path.join(batch_folder, output_file_name)
            tiff_file = tiff_file.convert('L')
            tiff_file.save(
                output_path,
                'TIFF',
                dpi=(self.dpi, self.dpi),
                compression='tiff_lzw'
            )
            
            # Store page info
            pdf_info[pdf_key][f'TM{str(self.tm_no).zfill(6)}'] = {
                'pdf': os.path.basename(pdf_path),
                'tiff': output_file_name,
                'parent': pdf_name,
                'original_file_path': original_file_path,
                'xml': f"TM{str(self.tm_no).zfill(6)}_layout.xml",
            }
            finish_page_time = time.time()
            print(f"Processing page {self.tm_no} took {finish_page_time - start_page_time} seconds")
            self.tm_no += 1
            tiff_file.close()
            del tiff_file
        gc.collect()
        
        return pdf_info


    
    def create_ocr_files(self, text_regions, page_num, output_folder, page_width, page_height):
        """Create XML files for OCR results"""
        # Sort regions by vertical position for line grouping
        text_regions.sort(key=lambda x: (x['top'], x['left']))
        
        xml_path = os.path.join(output_folder, f'TM{str(page_num).zfill(6)}_layout.xml')
        txt_path = os.path.join(output_folder, f'TM{str(page_num).zfill(6)}.txt')
        
        with open(xml_path, 'w', encoding='utf-16') as xml_file, \
            open(txt_path, 'w', encoding='utf-8') as txt_file:
            
            # Initialize styling list
            style_list = []
            
            # Write XML header
            xml_file.write('<?xml version="1.0" encoding="utf-16"?>\n')
            xml_file.write('<!--This file is generated by OCR engine of AIDocbuilder Inc.-->\n')
            xml_file.write('<Page xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                        'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
                        f'pos="0,0,{page_width},{page_height}" '
                        f'id="TM{str(page_num).zfill(6)}" '
                        f'xdpi="{self.dpi}" ydpi="{self.dpi}">\n')

            # Group regions into blocks based on vertical position
            current_block_y = None
            block_threshold = 20  # Pixels threshold for considering same block
            current_block_regions = []
            blocks = []
            
            for region in text_regions:
                if current_block_y is None or abs(region['top'] - current_block_y) > block_threshold:
                    if current_block_regions:
                        blocks.append(current_block_regions)
                    current_block_regions = [region]
                    current_block_y = region['top']
                else:
                    current_block_regions.append(region)
            
            # Add last block
            if current_block_regions:
                blocks.append(current_block_regions)
            
            # Prepare individual word data for spatial positioning
            word_layout_data = []
            
            # Process each block
            for block_regions in blocks:
                # Calculate block boundaries
                block_left = min(r['left'] for r in block_regions)
                block_top = min(r['top'] for r in block_regions)
                block_right = max(r['right'] for r in block_regions)
                block_bottom = max(r['bottom'] for r in block_regions)
                
                # Write Block element
                xml_file.write(f'  <Block pos="{block_left},{block_top},{block_right},{block_bottom}">\n')
                
                # Group regions into lines within the block
                current_line_y = None
                line_regions = []
                line_threshold = 15
                
                for region in block_regions:
                    if current_line_y is None or abs(region['top'] - current_line_y) > line_threshold:
                        # End previous line if exists
                        if line_regions:
                            line_left = min(r['left'] for r in line_regions)
                            line_top = min(r['top'] for r in line_regions)
                            line_right = max(r['right'] for r in line_regions)
                            line_bottom = max(r['bottom'] for r in line_regions)
                            xml_file.write('    </L>\n')

                        # Start new line
                        current_line_y = region['top']
                        line_regions = [region]
                        # Calculate line coordinates for the new line
                        line_left = min(r['left'] for r in line_regions)
                        line_top = min(r['top'] for r in line_regions)
                        line_right = max(r['right'] for r in line_regions)
                        line_bottom = max(r['bottom'] for r in line_regions)
                        xml_file.write(f'    <L pos="{line_left},{line_top},{line_right},{line_bottom}">\n')
                        
                        # Process text style
                        if region["font_weight"] == 'bold':
                            text_style = f'font-weight: {region["font_weight"]}; font-size: {region["font_size"]};'
                        else:
                            text_style = f'font-size: {region["font_size"]};'
                        
                        if text_style not in style_list:
                            style_list.append(text_style)
                            s = len(style_list)-1
                        else:
                            s = style_list.index(text_style)
                        
                        # Write word element
                        region["text"] = str(region["text"]).replace('&', '&amp;')
                        region["text"] = region["text"].replace('"', '&quot;')
                        region["text"] = region["text"].replace('<', '&lt;')
                        region["text"] = region["text"].replace('>', '&gt;')
                        region["text"] = region["text"].replace("'", '&apos;')
                        
                        xml_file.write(f'      <W pos="{region["left"]},{region["top"]},{region["right"]},{region["bottom"]}" '
                                    f'v="{region["text"]}" s="{s}" cn="{round(region["cn"], 2)}"/>\n')
                        
                        # Store individual word data for text layout - convert XML entities back to original
                        original_text = str(region["text"]).replace('&amp;', '&')
                        original_text = original_text.replace('&quot;', '"')
                        original_text = original_text.replace('&lt;', '<')
                        original_text = original_text.replace('&gt;', '>')
                        original_text = original_text.replace('&apos;', "'")
                        
                        word_layout_data.append({
                            'text': original_text,
                            'left': region['left'],
                            'top': region['top'],
                            'right': region['right'],
                            'bottom': region['bottom']
                        })
                    else:
                        # Continue current line
                        line_regions.append(region)
                        
                        # Process text style
                        if region["font_weight"] == 'bold':
                            text_style = f'font-weight: {region["font_weight"]}; font-size: {region["font_size"]};'
                        else:
                            text_style = f'font-size: {region["font_size"]};'
                        
                        if text_style not in style_list:
                            style_list.append(text_style)
                            s = len(style_list)-1
                        else:
                            s = style_list.index(text_style)
                        
                        # Write word element
                        region["text"] = str(region["text"]).replace('&', '&amp;')
                        region["text"] = region["text"].replace('"', '&quot;')
                        region["text"] = region["text"].replace('<', '&lt;')
                        region["text"] = region["text"].replace('>', '&gt;')
                        region["text"] = region["text"].replace("'", '&apos;')
                        
                        xml_file.write(f'      <W pos="{region["left"]},{region["top"]},{region["right"]},{region["bottom"]}" '
                                    f'v="{region["text"]}" s="{s}" cn="{round(region["cn"], 2)}"/>\n')
                        
                        # Store individual word data for text layout - convert XML entities back to original
                        original_text = str(region["text"]).replace('&amp;', '&')
                        original_text = original_text.replace('&quot;', '"')
                        original_text = original_text.replace('&lt;', '<')
                        original_text = original_text.replace('&gt;', '>')
                        original_text = original_text.replace('&apos;', "'")
                        
                        word_layout_data.append({
                            'text': original_text,
                            'left': region['left'],
                            'top': region['top'],
                            'right': region['right'],
                            'bottom': region['bottom']
                        })
                
                # End the last line in the block
                if line_regions:
                    line_left = min(r['left'] for r in line_regions)
                    line_top = min(r['top'] for r in line_regions)
                    line_right = max(r['right'] for r in line_regions)
                    line_bottom = max(r['bottom'] for r in line_regions)
                    xml_file.write('    </L>\n')
        
                # End the block
                xml_file.write('  </Block>\n')
            
            # Write style definitions
            for i, style in enumerate(style_list):
                xml_file.write(f'  <Style id="{i}" v="{style}" />\n')
            
            xml_file.write('</Page>\n')
            
            # Generate spatially positioned text for TXT file using individual words
            if word_layout_data:
                spatial_text = self._create_text_layout(word_layout_data, page_width, page_height)
                txt_file.write(spatial_text)


    def _create_text_layout(self, word_layout_data, page_width, page_height):
        """
        Create spatially positioned text that preserves PDF layout, using individual word positions
        """
        if not word_layout_data:
            return ""
        
        try:
            # Configuration parameters - adjusted for better line grouping
            space_unit = 8  # Reduced from 10 for better horizontal spacing
            line_height = 30  # Increased from 20 for better line separation
            
            # Calculate grid dimensions based on page size
            cols = page_width // space_unit + 1
            rows = page_height // line_height + 1
            
            # Ensure minimum grid size for readability
            cols = max(120, cols)
            rows = max(50, rows)
            
            # Create an empty grid initialized with spaces
            grid = [[' ' for _ in range(cols)] for _ in range(rows)]
            
            # Helper functions to convert pixel coordinates to grid coordinates
            def to_grid_x(px_x):
                return min(cols - 1, max(0, int(px_x / space_unit)))
            
            def to_grid_y(px_y):
                return min(rows - 1, max(0, int(px_y / line_height)))
            
            # Group words by lines first to prevent splitting
            line_groups = {}
            line_threshold = 15  # Pixels threshold for considering words on same line
            
            for word_data in word_layout_data:
                word_top = word_data['top']
                word_bottom = word_data['bottom']
                word_middle_y = (word_top + word_bottom) // 2
                
                # Find existing line group or create new one
                matched_line = None
                for line_y, words in line_groups.items():
                    if abs(word_middle_y - line_y) <= line_threshold:
                        matched_line = line_y
                        break
                
                if matched_line is not None:
                    line_groups[matched_line].append(word_data)
                else:
                    line_groups[word_middle_y] = [word_data]
            
            # Sort line groups by vertical position
            sorted_lines = sorted(line_groups.items())
            
            # Process each line group
            for line_y, words in sorted_lines:
                # Sort words in the line by horizontal position
                words.sort(key=lambda x: x['left'])
                
                # Calculate grid row for this line
                grid_row = to_grid_y(line_y)
                
                # Place words in the line
                for word_data in words:
                    text = word_data['text']
                    word_left = word_data['left']
                    
                    # Skip empty text
                    if not text.strip():
                        continue
                    
                    # Calculate grid column for this word
                    grid_col_start = to_grid_x(word_left)
                    
                    # Ensure the grid position is within bounds
                    if not (0 <= grid_row < rows) or not (0 <= grid_col_start < cols):
                        continue
                    
                    # Place each character of the word at its calculated position
                    for char_idx, char in enumerate(text):
                        current_col = grid_col_start + char_idx
                        
                        # Check if current position is within grid bounds
                        if not (0 <= current_col < cols):
                            break  # Stop if we go out of bounds
                        
                        # Only place character if the grid position is empty or it's a space
                        if grid[grid_row][current_col] == ' ':
                            grid[grid_row][current_col] = char
            
            # Convert grid to string output
            output_lines = []
            for row in grid:
                # Convert row to string and remove trailing spaces
                line = "".join(row).rstrip()
                output_lines.append(line)
            
            # Remove leading and trailing empty lines
            while output_lines and not output_lines[0].strip():
                output_lines.pop(0)
            while output_lines and not output_lines[-1].strip():
                output_lines.pop()
            
            # Join all lines with newlines
            return "\n".join(output_lines)
            
        except Exception as e:
            self.logger.error(f"Error in _create_text_layout: {str(e)}")
            # Fallback: return simple concatenated text
            return "\n".join(item['text'] for item in word_layout_data if item.get('text', '').strip())

    def _create_batch_xml_files(self, pdf_info, batch_folder, renamed_pdfs, profile_name, project):
        """Create Import.xml, Processor.xml, and RA_JSON for the batch"""
        import_xml_path = os.path.join(batch_folder, "Import.xml")
        processor_xml_path = os.path.join(batch_folder, "Processor.xml")
        
        # Create Import.xml
        with open(import_xml_path, 'w', encoding='utf-16') as import_xml:
            import_xml.write('<?xml-stylesheet type="text/xsl" href="..\..\dco.xsl"?>\n')
            import_xml.write(f'<B id="{os.path.basename(batch_folder)}">\n')
            # import_xml.write(page_file)
            for i, pdf_path in enumerate(renamed_pdfs, start=1):
                import_xml.write(f'\t<P id="TM{str(i).zfill(6)}">\n')
                import_xml.write(f'\t\t<V n="TYPE">GenericDocument</V>\n')
                import_xml.write(f'\t\t<V n="STATUS">49</V>\n')
                import_xml.write(f'\t\t<V n="IMAGEFILE">{os.path.basename(pdf_path)}</V>\n')
                import_xml.write(f'\t</P>\n')
            import_xml.write(f'</B>\n')
                    
        # Create Processor.xml
        with open(processor_xml_path, 'w', encoding='utf-16') as processor_xml:
            processor_xml.write('<?xml-stylesheet type="text/xsl" href="..\..\dco.xsl"?>\n')
            processor_xml.write(f'<B id="{os.path.basename(batch_folder)}">\n')
            # processor_xml.write(page_file)
            page_number = len(renamed_pdfs) + 1
            doc_number = 1
            for folder_name in pdf_info.keys():
                processor_xml.write(f'\t<D id="{os.path.basename(batch_folder)}.{str(doc_number).zfill(2)}">\n')
                processor_xml.write(f'\t\t<V n="TYPE">GenericDocument</V>\n')
                processor_xml.write(f'\t\t<V n="STATUS">49</V>\n')
                processor_xml.write(f'\t\t<V n="ext">.pdf</V>\n')
                for page in pdf_info[folder_name].keys():
                    processor_xml.write(f'\t\t<P id="TM{str(page_number).zfill(6)}">\n')
                    processor_xml.write(f'\t\t\t<V n="TYPE">GenericDoc</V>\n')
                    processor_xml.write(f'\t\t\t<V n="STATUS">49</V>\n')
                    processor_xml.write(f'\t\t\t<V n="IMAGEFILE">{pdf_info[folder_name][page]["tiff"]}</V>\n')
                    processor_xml.write(f'\t\t\t<V n="ParentImage">{pdf_info[folder_name][page]["parent"]}</V>\n')
                    processor_xml.write(f'\t\t\t<V n="ScanSrcPath"></V>\n')
                    processor_xml.write(f'\t\t\t<V n="root">C:\\</V>\n')
                    processor_xml.write(f'\t\t\t<V n="path">C:\\Datacap\\DGF\\batches\\{os.path.basename(batch_folder)}</V>\n')
                    processor_xml.write(f'\t\t\t<V n="sourceFileName">TM{str(page_number).zfill(6)}</V>\n')
                    processor_xml.write(f'\t\t\t<V n="ext">.tif</V>\n')
                    processor_xml.write(f'\t\t\t<V n="processingSettings"></V>\n')
                    processor_xml.write(f'\t\t\t<V n="layout">TM{str(page_number).zfill(6)}_layout.xml</V>\n')
                    processor_xml.write(f'\t\t</P>\n')
                    page_number += 1
                processor_xml.write(f'\t</D>\n')
                doc_number += 1
                    
            processor_xml.write(f'</B>\n')
            
        # Generate RA_JSON file
        try:
            ra_json_path = self.generate_ra_json(batch_folder, pdf_info, renamed_pdfs, profile_name, project)
            self.logger.info(f"Successfully generated RA_JSON at: {ra_json_path}")
        except Exception as e:
            self.logger.error(f"Error generating RA_JSON: {str(e)}")
            self.logger.error(traceback.format_exc())

    def generate_ra_json(self, batch_folder, pdf_info, renamed_pdfs, profile_name, project):
        """
        Generate a RA_JSON file from OCR results to match the required format

        Args:
            batch_folder: Folder containing OCR results
            pdf_info: Dictionary containing PDF and page information
            renamed_pdfs: Dictionary mapping original paths to new PDF names

        Returns:
            Path to the generated JSON file
        """
        # Structure to store the JSON data based on sample structure
        json_data = {
            "id": os.path.basename(batch_folder),
            "TYPE": "AIDBSERVICE",
            "bvOCR": "S",
            "nodes": [],
            "STATUS": "0",
            "Vendor": "",
            "DocType": "",
            "DocumentType": "",
            "Project": project,
            "Customer": "",
            "Language": "English",
            "batch_type": ".pdf",
            "bvFilePath": "",
            "bvBatchType": "Process",
            "DefinitionID": profile_name,
            "aidbServerIP": "None",
            "bvPageRotate": "N",
            "bvAIDBProfile": "",
            "bvBarcodeRead": "N",
            "NameMatchingText": None,
            "bvSelectedDocTypes": ""
        }

        # For each PDF in the batch, create a document node
        doc_number = 1
        for folder_name in pdf_info.keys():
            # Get the first page to fetch the new PDF name
            try:
                first_page = next(iter(pdf_info[folder_name].values()))
                # Correct file path construction
                original_file_path = first_page["original_file_path"]
            except Exception:
                original_file_path = ""

            doc_node = {
                "file_path": original_file_path,
                "DefinitionID": profile_name,
                "NameMatchingText": None,
                "id": f"{os.path.basename(batch_folder)}.{str(doc_number).zfill(2)}",
                "ext": ".pdf",
                "type": "document",
                "Vendor": "KAERCHER",
                "DocType": "Packing List",
                "Project": "ShipmentCreate",
                "Language": "German",
                "children": []
            }

            # Process each page in the PDF
            for page_id in pdf_info[folder_name].keys():
                # Path to the XML layout file
                xml_path = os.path.join(batch_folder, pdf_info[folder_name][page_id]["xml"])

                if not os.path.exists(xml_path):
                    self.logger.warning(f"XML layout file not found: {xml_path}")
                    continue

                try:
                    # Parse the XML
                    with open(xml_path, 'r', encoding='utf-16') as xml_file:
                        xml_content = xml_file.read()
                    # Fix potential XML parsing issues
                    xml_content = re.sub(r'<!DOCTYPE[^>]*>', '', xml_content)

                    # Parse the XML string directly
                    root = ET.fromstring(xml_content)

                    # Create page node
                    page_node = {
                        "id": root.get('id'),
                        "EXT": ".pdf",
                        "pos": root.get('pos'),
                        "TYPE": "GenericDoc",
                        "lang": "de-de",
                        "s_lg": "1",
                        "type": "page",
                        "xdpi": self.dpi,
                        "ydpi": self.dpi,
                        "STATUS": "49",
                        "layout": pdf_info[folder_name][page_id]["xml"],
                        "styles": [],
                        "DATAFILE": f"{root.get('id').lower()}.xml",
                        "OCRSLang": "1",
                        "children": [],
                        "IMAGEFILE": pdf_info[folder_name][page_id]["tiff"],
                        "ParentImage": pdf_info[folder_name][page_id]["parent"],
                        "RecogStatus": "0",
                        "ScanSrcPath": None,
                        "NewSourceDoc": str(doc_number == 1).capitalize(),
                        "s_srbatchdir": f"\\\\phx-dc.dhl.com\\Sites\\dgfdocscancert\\DC9\\Datacap\\AIDBSERVICE\\batches\\{os.path.basename(batch_folder)}",
                        "y_AutoRotate": "false"
                    }

                    # Extract styles
                    for i, style in enumerate(root.findall('./Style')):
                        style_obj = {
                            "v": style.get('v'),
                            "id": str(i)
                        }
                        page_node["styles"].append(style_obj)

                    # Process blocks
                    block_id = 1
                    for block in root.findall('./Block'):
                        # Calculate block position
                        block_pos = block.get('pos')

                        # Create block object
                        block_obj = {
                            "id": f"{root.get('id')}.{str(block_id).zfill(3)}",
                            "pos": block_pos,
                            "type": "block",
                            "children": []
                        }

                        # Process lines
                        line_id = 1
                        for line in block.findall('./L'):
                            line_pos = line.get('pos')

                            line_obj = {
                                "id": f"{root.get('id')}.{str(block_id).zfill(3)}.{str(line_id).zfill(3)}",
                                "pos": line_pos,
                                "type": "line",
                                "children": []
                            }
                            # Process words
                            word_id = 1
                            for word in line.findall('./W'):
                                word_pos = word.get('pos')
                                text = word.get('v')
                                style = word.get('s', '0')
                                confidence = word.get('cn', '9' * len(text))

                                word_obj = {
                                    "s": style,
                                    "v": text,
                                    "cn": confidence,
                                    "id": f"{root.get('id')}.{str(block_id).zfill(3)}.{str(line_id).zfill(3)}.{str(word_id).zfill(3)}",
                                    "pos": word_pos,
                                    "type": "word"
                                }
                                line_obj["children"].append(word_obj)
                                word_id += 1

                            block_obj["children"].append(line_obj)
                            line_id += 1

                        page_node["children"].append(block_obj)
                        block_id += 1

                    # Add page to document
                    doc_node["children"].append(page_node)

                except Exception as e:
                    self.logger.error(f"Error parsing XML file {xml_path}: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    
            # Add document to nodes
            json_data["nodes"].append(doc_node)
            doc_number += 1

        # Write to JSON file with the batch name
        json_filename = "ra_json.json"
        json_path = os.path.join(batch_folder, json_filename)
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, indent=4)

        self.logger.info(f"Generated RA_JSON file: {json_path}")

        return json_path



    def _is_likely_table(self, block):
        """Determine if a block is likely a table based on layout patterns"""
        lines = block.findall('./L')
        
        # If there are few lines, probably not a table
        if len(lines) < 4:
            return False
        
        # Check for grid-like arrangement of lines
        line_positions = []
        for line in lines:
            line_pos = line.get('pos')
            match = re.match(r'(\d+),(\d+),(\d+),(\d+)', line_pos)
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                line_positions.append((x1, y1, x2, y2))
        
        # Sort by y-coordinate
        line_positions.sort(key=lambda pos: pos[1])
        
        # Check for regular spacing between lines (a characteristic of tables)
        y_diffs = [line_positions[i+1][1] - line_positions[i][1] for i in range(len(line_positions)-1)]
        if len(y_diffs) > 0:
            avg_diff = sum(y_diffs) / len(y_diffs)
            # Check if most differences are close to the average
            regular_spacing = sum(1 for diff in y_diffs if abs(diff - avg_diff) < avg_diff * 0.2) / len(y_diffs) > 0.7
            if regular_spacing and avg_diff < 50:  # Reasonably close lines
                return True
        
        return False

    def _process_regular_block(self, block, page_id, block_id):
        """Process a regular (non-table) block"""
        block_obj = {
            "id": f"{page_id}.{str(block_id).zfill(3)}",
            "pos": block.get('pos'),
            "type": "block",
            "children": []
        }
        
        # Extract lines
        line_id = 1
        for line in block.findall('./L'):
            line_obj = {
                "id": f"{page_id}.{str(block_id).zfill(3)}.{str(line_id).zfill(3)}",
                "pos": line.get('pos'),
                "type": "line",
                "children": []
            }
            
            # Extract words
            word_id = 1
            for word in line.findall('./W'):
                # Generate a confidence value similar to the example JSON
                # The length varies between 1 and 15 characters with multiple 9's
                text = word.get('v')
                conf_length = min(max(len(text), 1), 15)
                fake_conf = "9" * conf_length
                
                word_obj = {
                    "s": word.get('s'),
                    "v": text,
                    "cn": fake_conf,
                    "id": f"{page_id}.{str(block_id).zfill(3)}.{str(line_id).zfill(3)}.{str(word_id).zfill(3)}",
                    "pos": word.get('pos'),
                    "type": "word"
                }
                line_obj["children"].append(word_obj)
                word_id += 1
            
            block_obj["children"].append(line_obj)
            line_id += 1
        
        return block_obj

    def _process_block_as_table(self, block, page_id, block_id):
        """Process a block as a table structure"""
        # Extract table dimensions and position
        block_pos = block.get('pos')
        lines = block.findall('./L')
        
        # Group lines into rows based on y-coordinate
        rows = {}
        for line in lines:
            line_pos = line.get('pos')
            match = re.match(r'(\d+),(\d+),(\d+),(\d+)', line_pos)
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                # Use a tolerance for y-coordinate grouping
                row_key = y1 // 5 * 5  # Group by 5 pixels
                if row_key not in rows:
                    rows[row_key] = []
                rows[row_key].append((line, (x1, y1, x2, y2)))
        
        # Sort rows by y-coordinate
        sorted_row_keys = sorted(rows.keys())
        
        # Calculate number of columns - use the maximum number of cells in any row
        num_columns = max(len(rows[key]) for key in sorted_row_keys)
        
        # Create table object
        table_obj = {
            "id": f"{page_id}.{str(block_id).zfill(3)}",
            "pos": block_pos,
            "rows": str(len(sorted_row_keys)),
            "type": "table",
            "columns": str(num_columns),
            "children": []
        }
        
        # Process each row
        for row_idx, row_key in enumerate(sorted_row_keys):
            row_contents = rows[row_key]
            
            # Sort cells in the row by x-coordinate
            row_contents.sort(key=lambda item: item[1][0])
            
            # Calculate row position
            row_x1 = min(x1 for _, (x1, _, _, _) in row_contents)
            row_y1 = min(y1 for _, (_, y1, _, _) in row_contents)
            row_x2 = max(x2 for _, (_, _, x2, _) in row_contents)
            row_y2 = max(y2 for _, (_, _, _, y2) in row_contents)
            
            row_obj = {
                "id": f"{page_id}.{str(block_id).zfill(3)}.{str(row_idx+1).zfill(3)}",
                "pos": f"{row_x1},{row_y1},{row_x2},{row_y2}",
                "type": "row",
                "children": []
            }
            
            # Process each cell in the row
            for cell_idx, (line, (x1, y1, x2, y2)) in enumerate(row_contents):
                cell_obj = {
                    "id": f"{page_id}.{str(block_id).zfill(3)}.{str(row_idx+1).zfill(3)}.{str(cell_idx+1).zfill(3)}",
                    "col": str(cell_idx),
                    "pos": f"{x1},{y1},{x2},{y2}",
                    "row": str(row_idx),
                    "type": "cell",
                    "rowSpan": "1",  # Default values
                    "children": [],
                    "columnSpan": "1"
                }
                
                # Create a line object for the cell
                line_obj = {
                    "id": f"{page_id}.{str(block_id).zfill(3)}.{str(row_idx+1).zfill(3)}.{str(cell_idx+1).zfill(3)}.001",
                    "pos": f"{x1},{y1},{x2},{y2}",
                    "type": "line",
                    "children": []
                }
                
                # Process words in the line
                word_id = 1
                for word in line.findall('./W'):
                    word_pos = word.get('pos')
                    text = word.get('v')
                    # Generate a confidence value
                    conf_length = min(max(len(text), 1), 15)
                    fake_conf = "9" * conf_length
                    
                    word_obj = {
                        "s": word.get('s'),
                        "v": text,
                        "cn": fake_conf,
                        "id": f"{page_id}.{str(block_id).zfill(3)}.{str(row_idx+1).zfill(3)}.{str(cell_idx+1).zfill(3)}.001.{str(word_id).zfill(3)}",
                        "pos": word_pos,
                        "type": "word"
                    }
                    line_obj["children"].append(word_obj)
                    word_id += 1
                
                cell_obj["children"].append(line_obj)
                row_obj["children"].append(cell_obj)
            
            table_obj["children"].append(row_obj)
        
        # Enhance the table with rowSpan and columnSpan information
        self._enhance_table_spans(table_obj)
        
        return table_obj

    def _enhance_table_spans(self, table_obj):
        """
        Try to improve row and column spans in a table by analyzing cell positions
        """
        rows = table_obj["children"]
        num_rows = len(rows)
        if num_rows <= 1:
            return
        
        # Create a grid to track cell positions
        cell_grid = {}
        
        # First pass: identify cells that might span multiple rows or columns
        for row_idx, row in enumerate(rows):
            for cell in row["children"]:
                try:
                    cell_pos = cell["pos"].split(",")
                    if len(cell_pos) != 4:
                        continue
                    
                    x1, y1, x2, y2 = map(int, cell_pos)
                    cell_width = x2 - x1
                    cell_height = y2 - y1
                    
                    # Store cell in grid
                    cell_grid[(row_idx, int(cell["col"]))] = (cell, x1, y1, x2, y2, cell_width, cell_height)
                except (ValueError, KeyError, IndexError):
                    continue
        
        # Second pass: analyze the grid to detect spans
        for (row_idx, col_idx), (cell, x1, y1, x2, y2, width, height) in cell_grid.items():
            # Check for row spans
            row_span = 1
            for next_row in range(row_idx + 1, num_rows):
                if (next_row, col_idx) in cell_grid:
                    _, nx1, ny1, nx2, ny2, _, _ = cell_grid[(next_row, col_idx)]
                    # If this cell overlaps significantly with the one below
                    if (min(x2, nx2) - max(x1, nx1)) / width > 0.5 and y2 > ny1:
                        break
                row_span += 1
                # If we've reached beyond table bounds or no more overlap
                if next_row >= num_rows - 1:
                    break
            
            if row_span > 1:
                cell["rowSpan"] = str(row_span)
            
            # Check for column spans
            col_span = 1
            for next_col in range(col_idx + 1, int(table_obj["columns"])):
                if (row_idx, next_col) in cell_grid:
                    _, nx1, ny1, nx2, ny2, _, _ = cell_grid[(row_idx, next_col)]
                    # If cells are very close or overlapping horizontally
                    if nx1 - x2 < 10 or (min(y2, ny2) - max(y1, ny1)) / height > 0.5:
                        break
                col_span += 1
                # If we've reached beyond table bounds
                if next_col >= int(table_obj["columns"]) - 1:
                    break
            
            if col_span > 1:
                cell["columnSpan"] = str(col_span)
        

    def preprocess_image(self, image):
        """Preprocess image with enhancement for better OCR results"""
        # Convert PIL Image to cv2 format
        img_array = np.array(image)

        # Convert to BGR if grayscale to ensure 3 channels
        # if len(img_array.shape) == 2:  # Grayscale image
        #     img_array_RGB = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)

        # docs = DocumentFile.from_images([image])
        # result = self.page_orientation(docs)
        # self.logger.info(f"page orientation: {result[1][0]} with confidence: {result[2][0]:.2f}")
        # if result[1][0] == "rotated":
        #     img_array = cv2.rotate(img_array, cv2.ROTATE_90_CLOCKWISE)
        #     img_array = cv2.flip(img_array, 1)
        # elif result[1][0] == "upside_down":
        #     img_array = cv2.rotate(img_array, cv2.ROTATE_180)
        # elif result[1][0] == "rotated_anticlockwise":
        #     img_array = cv2.rotate(img_array, cv2.ROTATE_90_COUNTERCLOCKWISE)

        
        # Convert to grayscale if not already (for fine skew correction)
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # self.page_orientation_detector
        
        # # Calculate fine skew angle and rotate if needed
        # fine_angle = determine_skew(gray_img)
        # if abs(fine_angle) > 0.5:  # Only rotate if skew is significant
        #     (h, w) = img_array.shape[:2]
        #     center = (w // 2, h // 2)
        #     matrix = cv2.getRotationMatrix2D(center, fine_angle, 1.0)
        #     img_array = cv2.warpAffine(
        #         img_array, 
        #         matrix, 
        #         (w, h),
        #         flags=cv2.INTER_CUBIC,
        #         borderMode=cv2.BORDER_REPLICATE
        #     )

        # Apply very light denoising
        if len(img_array.shape) == 2:
            # For grayscale images
            img_array = cv2.fastNlMeansDenoising(
                img_array,
                None,
                h=10,
                templateWindowSize=7,
                searchWindowSize=21
            ) 
        # else:
        #     # For color images, use color image denoising
        #     img_array = cv2.fastNlMeansDenoisingColored(
        #         img_array,
        #         None,
        #         h=10,  # Higher h value for smoother denoising
        #         hColor=10,
        #         templateWindowSize=7,
        #         searchWindowSize=21
        #     )

        # Apply minimal Gaussian blur
        img_array = cv2.GaussianBlur(img_array, (3,3), 0.3)

        # If grayscale, apply CLAHE enhancement and thresholding
        if len(img_array.shape) == 2:
            # Apply gentle contrast enhancement using CLAHE
            clahe = cv2.createCLAHE(
                clipLimit=1.5,
                tileGridSize=(8,8)
            )
            img_array = clahe.apply(img_array)

            # Use Otsu's thresholding
            _, binary = cv2.threshold(
                img_array,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            
            # Apply minimal image quality enhancements
            enhanced_img = self.enhance_image_quality(binary)
            
            # Crop borders while keeping a small margin
            # coords = cv2.findNonZero(enhanced_img)
            # if coords is not None:
            #     x, y, w, h = cv2.boundingRect(coords)
            #     margin = 50  # Keep a 50-pixel margin
            #     x = max(0, x - margin)
            #     y = max(0, y - margin)
            #     w = min(enhanced_img.shape[1] - x, w + 2*margin)
            #     h = min(enhanced_img.shape[0] - y, h + 2*margin)
            #     img_array = enhanced_img[y:y+h, x:x+w]
        # else:
        #     # For color images, just keep the enhanced color image
        #     # Crop borders if needed
        #     gray_for_crop = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        #     _, binary_for_crop = cv2.threshold(gray_for_crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        #     coords = cv2.findNonZero(binary_for_crop)
        #     if coords is not None:
        #         x, y, w, h = cv2.boundingRect(coords)
        #         margin = 50  # Keep a 50-pixel margin
        #         x = max(0, x - margin)
        #         y = max(0, y - margin)
        #         w = min(img_array.shape[1] - x, w + 2*margin)
        #         h = min(img_array.shape[0] - y, h + 2*margin)
        #         img_array = img_array[y:y+h, x:x+w]

        # Convert back to PIL Image
        return Image.fromarray(enhanced_img)

    def enhance_image_quality(self, image):
        """Gentler image quality enhancements to preserve text details"""
        # Use smaller kernels for morphological operations
        kernel = np.ones((2,2), np.uint8)
        
        # Apply minimal closing operation to connect broken text
        img = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        
        # Apply very gentle bilateral filter
        img = cv2.bilateralFilter(
            img,
            d=5,  # Smaller diameter
            sigmaColor=25,  # Reduced color sigma
            sigmaSpace=25  # Reduced space sigma
        )
        
        # Apply minimal sharpening
        kernel_sharpen = np.array([
            [-0.5,-0.5,-0.5],
            [-0.5,  5,-0.5],
            [-0.5,-0.5,-0.5]
        ]) / 1.0  # Reduced sharpening intensity
        
        img = cv2.filter2D(img, -1, kernel_sharpen)

        return img

    def deskew_image(self, image):
        """
        Deskew an image using skew angle detection
        
        Args:
            image: PIL Image object
            
        Returns:
            Deskewed PIL Image
        """
        try:
            # Convert PIL Image to numpy array
            img_array = np.array(image)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Detect skew angle
            angle = determine_skew(gray)
            
            self.logger.info(f"Detected skew angle: {angle:.2f} degrees")
            
            # Only deskew if angle is significant (more than 0.5 degrees)
            if abs(angle) > 0.5:
                # Get image dimensions
                (h, w) = img_array.shape[:2]
                center = (w // 2, h // 2)
                
                # Calculate rotation matrix
                matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                
                # Perform rotation
                rotated = cv2.warpAffine(
                    img_array,
                    matrix,
                    (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
                
                self.logger.info(f"Image deskewed by {angle:.2f} degrees")
                return Image.fromarray(rotated)
            else:
                self.logger.info("Skew angle too small, no deskewing needed")
                return image
                
        except Exception as e:
            self.logger.error(f"Error in deskew_image: {str(e)}")
            # Return original image if deskewing fails
            return image

    def convert_pdf_to_tif(self, pdf_path, output_folder):
        try:
            # Use consistent DPI for both doctr and fallback
            target_dpi = self.dpi
            scl = target_dpi / 72  # Convert from points to pixels
            
            pages = read_pdf(pdf_path, scale=scl, rgb_mode=True)
            tiff_files = []
            
            for page_np in pages:
                # Convert numpy array to PIL Image
                pil_image = Image.fromarray(page_np)
                
                # Ensure DPI is set correctly
                pil_image.info['dpi'] = (target_dpi, target_dpi)
                
                # Deskew the image
                # pil_image = self.deskew_image(pil_image)
                
                # Apply minimal image preprocessing
                enhancer = ImageEnhance.Contrast(pil_image)
                pil_image = enhancer.enhance(1.1)
                
                tiff_files.append(pil_image)
            
            return tiff_files
            
        except Exception as e:
            self.logger.warning(f"Error using doctr.io for PDF reading: {str(e)}. Falling back to legacy method.")
            
            # Fallback method with same DPI
            images = convert_from_path(pdf_path, dpi=target_dpi)
            tiff_files = []
            
            for image in images:
                # Deskew the image
                image = self.deskew_image(image)
                
                # Don't preprocess in fallback to avoid dimension changes
                image.info['dpi'] = (target_dpi, target_dpi)
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.1)
                tiff_files.append(image)
            
            return tiff_files

    def draw_bbox_and_save(self, image_np, bboxes, output_folder, page_number, pdf_name=None):
        """Draw bounding boxes on the image and save as the specified format"""
        # Convert grayscale to BGR if needed
        if len(image_np.shape) == 2:  
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
        
        # Draw bounding boxes
        for bbox in bboxes:
            # Draw the bounding box
            cv2.rectangle(
                image_np,
                (bbox['left'], bbox['top']),
                (bbox['right'], bbox['bottom']),
                (0, 255, 0),  # Green color for bounding box
                1  # Thickness of the bounding box
            )
            # Add the label
            label = f"{bbox.get('text', '')}"
            cv2.putText(
                image_np,
                label,
                (bbox['left'], bbox['top'] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),  # Red text color
                1
            )
        
        # Create file name
        pdf_base_name = os.path.splitext(os.path.basename(pdf_name))[0]
        output_file_name = f"tm{str(page_number).zfill(6)}.jpg"
        output_path = os.path.join(output_folder, output_file_name)

        # Save the image
        cv2.imwrite(output_path, image_np, [int(cv2.IMWRITE_JPEG_QUALITY), 95]) 

        # Free up memory
        del image_np

        return output_path

    def detect_font_attributes(self, image_np, bbox, text, conf):
        """
        Detects font attributes (size and weight) with improved consistency
        """
        try:
            # Extract text region - bbox coordinates are for original image but image_np is processed
            left, top, right, bottom = bbox['left'], bbox['top'], bbox['right'], bbox['bottom']
            height = bottom - top
            width = right - left
            
            # ISSUE: These coordinates don't match the image_np dimensions
            # Need to scale coordinates to match processed image dimensions
            processed_height, processed_width = image_np.shape[:2]
            
            # If we know original dimensions, we can calculate scale factors
            # But this function doesn't have access to original dimensions
            
            # For now, validate bounds against processed image
            if (height <= 0 or width <= 0 or left < 0 or top < 0 or 
                right >= processed_width or bottom >= processed_height):
                return 12, 'normal'
            
            # Extract the text region from the image
            text_region = image_np[top:bottom, left:right]
            
            # Check if the region is valid
            if text_region.size == 0:
                return 12, 'normal'
            
            # Convert to grayscale if needed
            if len(text_region.shape) == 3:
                text_region = cv2.cvtColor(text_region, cv2.COLOR_BGR2GRAY)
            
            # Calculate font size more consistently
            # Standard conversion: ~4 pixels = 1 point at 300 DPI
            # But we'll use more sophisticated approach
            pixel_to_point_ratio = self.dpi / 72
            
            # Calculate font size based on character height with adaptive adjustment
            # For mixed case text, use character height / 1.6 as approximate point size
            # For uppercase or numeric text, use character height / 1.3
            if text.isupper() or text.isdigit():
                divisor = 1.3
            else:
                divisor = 1.6
                
            font_size_raw = height / divisor / pixel_to_point_ratio
            
            # Round to standard font sizes for better consistency
            standard_sizes = [6, 8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 28, 32, 36, 42, 48, 60, 72]
            font_size = min(standard_sizes, key=lambda x: abs(x - font_size_raw))
            
            # ----------------- BOLD DETECTION -----------------
            # Use more robust thresholding that adapts to the image
            
            # First ensure we have good binarization
            # Apply adaptive thresholding for better results on varied backgrounds
            binary = cv2.adaptiveThreshold(
                text_region, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Calculate pixel density more accurately
            # Dilate slightly to account for scanning artifacts
            kernel = np.ones((2, 2), np.uint8)
            dilated = cv2.dilate(binary, kernel, iterations=1)
            pixel_density = np.sum(dilated == 255) / dilated.size
            
            # Calculate relative stroke width using distance transform
            dist_transform = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
            # Consider only foreground pixels
            foreground_mask = binary == 255
            if np.sum(foreground_mask) > 0:
                max_distance = np.max(dist_transform[foreground_mask])
                mean_distance = np.mean(dist_transform[foreground_mask])
                # Normalize by text height for consistency across sizes
                relative_stroke_width = 2 * mean_distance / height
            else:
                relative_stroke_width = 0
                max_distance = 0
            
            # Create a compound score for "boldness"
            bold_score = 0
            
            # Factor 1: Pixel density contributes to bold score
            bold_score += min(pixel_density * 5, 2)  # Scale up but cap contribution
            
            # Factor 2: Stroke width contribution - different scaling based on font size
            if font_size <= 12:
                # Small fonts - more sensitive to stroke width
                bold_score += min(relative_stroke_width * 7, 2)
            else:
                # Larger fonts - less sensitive
                bold_score += min(relative_stroke_width * 5, 2)
                
            # Factor 3: ALL CAPS with high confidence gets a bonus
            if text.isupper() and len(text) > 1 and conf > 0.85:
                bold_score += 0.5
                
            # Factor 4: High confidence generally correlates with clearer, often bolder text
            bold_score += (conf - 0.5) * 0.5  # Small boost from confidence
            
            # Factor 5: Character density (width to height ratio)
            char_density = width / (height * len(text)) if len(text) > 0 and height > 0 else 0
            if 0.4 < char_density < 0.9:  # Normal range for most fonts
                bold_score += 0
            else:
                bold_score -= 0.3  # Penalize very narrow or very wide characters
                
            # Text length normalization - shorter text needs higher threshold
            threshold = 2.2
            if len(text) <= 3:
                threshold = 2.4
            if len(text) >= 8:
                threshold = 2.0
                
            # Final determination
            font_weight = 'bold' if bold_score > threshold else 'normal'
            
            # Cache the attributes for use in consistency enforcement
            # This would ideally be in a class variable and used for post-processing
            # But for now we'll just record it in the log for analysis
            self.logger.debug(f"Text: '{text}', Size: {font_size}, Weight: {font_weight}, " 
                            f"Score: {bold_score:.2f}, Threshold: {threshold:.1f}")
            
            return font_size, font_weight
        
        except Exception as e:
            # Log exception but don't let it crash the process
            self.logger.warning(f"Error in font detection: {e}")
            return 12, 'normal'  # Return default values

    def post_process_font_consistency(self, text_regions):
        """
        Post-processes detected text regions to ensure font size/weight consistency
        
        Args:
            text_regions: List of text region dictionaries
            
        Returns:
            List of text regions with adjusted font attributes
        """
        if not text_regions or len(text_regions) < 2:
            return text_regions
            
        # Group text regions by their vertical position (lines)
        line_groups = {}
        line_threshold = 15  # Pixels threshold for same line
        
        for idx, region in enumerate(text_regions):
            # Use middle of bounding box for vertical position
            y_middle = (region['top'] + region['bottom']) // 2
            line_key = y_middle // line_threshold
            
            if line_key not in line_groups:
                line_groups[line_key] = []
            line_groups[line_key].append(idx)
        
        # For each line, normalize font attributes for consistency
        for line_key, region_indices in line_groups.items():
            if len(region_indices) <= 1:
                continue
                
            # Collect font sizes and weights
            font_sizes = [text_regions[idx]['font_size'] for idx in region_indices]
            weights = [text_regions[idx]['font_weight'] for idx in region_indices]
            
            # Analyze for consistency - use most common values
            most_common_size = max(set(font_sizes), key=font_sizes.count)
            most_common_weight = max(set(weights), key=weights.count)
            
            # Only override outliers
            for idx in region_indices:
                region = text_regions[idx]
                # Check if current size is an outlier
                size_diff = abs(region['font_size'] - most_common_size)
                if size_diff > 2 and size_diff / most_common_size > 0.15:
                    region['font_size'] = most_common_size
                    
                # For font weight, be more conservative about overriding
                # Only override if it's clearly inconsistent with neighbors
                if region['font_weight'] != most_common_weight:
                    # Count neighbors with different weight
                    neighbor_indices = [i for i in region_indices if 
                                        abs(text_regions[i]['left'] - region['right']) < 30 or 
                                        abs(text_regions[i]['right'] - region['left']) < 30]
                    
                    different_weight_neighbors = sum(1 for i in neighbor_indices if 
                                                text_regions[i]['font_weight'] != region['font_weight'])
                    
                    if different_weight_neighbors > len(neighbor_indices) // 2:
                        region['font_weight'] = most_common_weight
        
        return text_regions


    def easyOCR_bbox(self, image, output_folder, page_number, pdf_name=None):
        """Create bounding boxes using DocTR"""
        try:
            # Store original dimensions
            original_height, original_width = image.height, image.width
            image_np = np.array(image)

            if len(image_np.shape) == 2:  
                image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
            
            result = self.predictor([image_np])

            text_regions = []
            for block in result.pages[0].blocks:
                for line in block.lines:
                    for word in line.words:
                        # DocTR returns normalized coordinates [0,1]
                        # Scale directly to original image dimensions
                        left = int(word.geometry[0][0] * original_width)
                        top = int(word.geometry[0][1] * original_height)
                        right = int(word.geometry[1][0] * original_width)
                        bottom = int(word.geometry[1][1] * original_height)
                        
                        text = word.value
                        conf = word.confidence
                        
                        # For font detection, create bbox scaled to processed image
                        processed_height, processed_width = image_np.shape[:2]
                        scale_x = processed_width / original_width
                        scale_y = processed_height / original_height
                        
                        processed_bbox = {
                            'left': int(left * scale_x),
                            'top': int(top * scale_y),
                            'right': int(right * scale_x),
                            'bottom': int(bottom * scale_y)
                        }

                        font_size, font_weight = self.detect_font_attributes(image_np, processed_bbox, text, conf)
                        
                        text_regions.append({
                            'left': left,
                            'top': top,
                            'right': right,
                            'bottom': bottom,
                            'text': text,
                            'cn': conf,
                            'font_size': font_size,
                            'font_weight': font_weight
                        })
            
            # Use original dimensions for XML creation
            self.create_ocr_files(text_regions, page_number, output_folder, original_width, original_height)
            
            # Add debug logging
            self.logger.info(f"Found {len(text_regions)} text regions")

            # Free up memory
            del image_np, result
        except Exception as e:
            print(f"Error processing image:")
            print(e)
            print(traceback.format_exc())
            raise

def permissions_fix(uid, gid, path):
    os.chown(path, uid, gid)
    for root, dirs, files in os.walk(path):
        # Change ownership of subdirectories
        for d in dirs:
            os.chown(os.path.join(root, d), uid, gid)
        # Change ownership of files
        for f in files:
            os.chown(os.path.join(root, f), uid, gid)
            
def create_batch(data):
    batch_id = data['batch_id']
    profile_name = data['profile_name']
    project = data['project']
    print(f"creating batch... {batch_id}")
    ocr_engine = OCREngine()
    ocr_engine.create_batch(data['files'], batch_id, profile_name, project)
    print("creating batch...done")
    gc.collect()
    path = f"/batches/{batch_id}"
    # permissions_fix(1001,0, path)
    print("Clearing memory...done")

    request_data = {
        "batch_id": batch_id,
        "status_code": 200,
    }

    publish("create_batch_ocr_response", "to_pipeline", request_data)

    print("Classifying batch...done")
    return


# Create Flask application
ocr_engine = OCREngine()

def init(app):
    @app.route('/', methods=['GET'])
    def api_testing():
        return jsonify({
                'status': 'OCR Engine API is running...'
            }), 200
    
    @app.route('/api/batch', methods=['POST'])
    def create_batch():
        """
        API endpoint to create and process a batch of PDFs
        
        Expected JSON payload:
        {
            "file_paths": ["path/to/pdf1.pdf", "path/to/pdf2.pdf", ...],

            ### Optional parameters
            server_ip = "10.10.1.9" selected_doc_types = "Commercial Invoice,Packing List" batch_type = "Train", 
            profile_name = "CA_DEMO NAME_ALL_CreateCustomsJob (B+CIV)", 
            customer = "DEMO NAME", 
            document_type = "Commercial Invoice", 
            name_matching_text = "", 
            language = "English", 
            ocr = "S", 
            page_rotate = "N", 
            barcode = "N", 
            project_name = "DEMO NAME",
        }
        """
        try:
            data = request.get_json()
            if not data or 'file_paths' not in data:
                return jsonify({'error': 'Missing file_paths in request'}), 404
            
            file_paths = data['file_paths']
            if not isinstance(file_paths, list):
                return jsonify({'error': 'file_paths must be a list'}), 400
            
            server_ip = data.get('server_ip', "10.10.1.9")
            selected_doc_types = data.get('selected_doc_types', "Commercial Invoice,Packing List")
            batch_type = data.get('batch_type', "Train")
            profile_name = data.get('profile_name', "CA_DEMO NAME_ALL_CreateCustomsJob (B+CIV)")
            customer = data.get('customer', "DEMO NAME")
            document_type = data.get('document_type', "Commercial Invoice")
            name_matching_text = data.get('name_matching_text', "")
            language = data.get('language', "English")
            ocr = data.get('ocr', "S")
            page_rotate = data.get('page_rotate', "N")
            barcode = data.get('barcode', "N")
            project_name = data.get('project_name', "DEMO NAME")
            
            page_file = (
                '\t<V n="STATUS">0</V>\n'
                f'\t<V n="aidbServerIP">{server_ip}</V>\n'
                f'\t<V n="bvFilePath">{file_paths}</V>\n'
                f'\t<V n="bvSelectedDocTypes">{selected_doc_types}</V>\n'
                f'\t<V n="bvBatchType">{batch_type}</V>\n'
                f'\t<V n="bvICapProfile">{profile_name}</V>\n'
                f'\t<V n="bvCustomer">{customer}</V>\n'
                f'\t<V n="bvDocumentType">{document_type}</V>\n'
                f'\t<V n="bvNameMatchingText">{name_matching_text}</V>\n'
                f'\t<V n="bvLanguage">{language}</V>\n'
                f'\t<V n="bvOCR">{ocr}</V>\n'
                f'\t<V n="bvPageRotate">{page_rotate}</V>\n'
                f'\t<V n="bvBarcodeRead">{barcode}</V>\n'
                f'\t<V n="bvProjectName">{project_name}</V>\n'
            )
            
            # Process batch
            # batch_info = ocr_engine.create_batch(file_paths, page_file, datetime.now().strftime("%Y%m%d.%H%M%S"))
            batch_info = ocr_engine.create_batch(file_paths, datetime.now().strftime("%Y%m%d.%H%M%S"))
            # Free up memory
            del file_paths, page_file
            gc.collect()
            
            # Return of the post request
            return jsonify({
                'status': 'success',
                'batch_info': batch_info
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
