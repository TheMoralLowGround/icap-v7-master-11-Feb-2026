import pdfplumber
import os
import json
import math
import re
import glob
import shutil
from datetime import datetime
from collections import defaultdict
from pdf2image import convert_from_path
import gc


def extract_font_info(word_info):
    """Extract detailed font information from word_info with improved font family detection"""
    font_info = {
        'font': 'arial',  # Default font
        'family': 'swiss',  # Default family
        'size': 10,  # Default size
        'bold': False,
        'italic': False,
        'underline': False
    }
    
    # Get font name from pdfplumber
    font_name = word_info.get('fontname', '')
    if font_name:
        # Clean font name
        font_name = font_name.lower()
        
        # Remove common prefixes
        if '+' in font_name:
            font_name = font_name.split('+')[-1]
        
        # Extract base font name and style information
        if 'bold' in font_name.lower() or 'bd' in font_name.lower():
            font_info['bold'] = True
        if 'italic' in font_name.lower() or 'oblique' in font_name.lower() or 'it' in font_name.lower():
            font_info['italic'] = True
        if 'underline' in font_name.lower() or 'under' in font_name.lower() or 'ul' in font_name.lower():
            font_info['underline'] = True
        
        # Extract base font name without style suffixes
        base_font = font_name
        for suffix in ['-bold', '-bd', '-italic', '-it', '-oblique', '-regular', '-underline', '-ul']:
            base_font = base_font.replace(suffix, '')
        
        # Clean up font name for better matching
        base_font = base_font.split('-')[0].split(',')[0]
        font_info['font'] = base_font
        
        # Determine font family based on common font classifications
        # Serif fonts
        if any(serif in font_name for serif in ['times', 'georgia', 'garamond', 'cambria', 'serif', 
                                               'bookman', 'palatino', 'century', 'baskerville', 'didot']):
            font_info['family'] = 'serif'
            
        # Sans-serif fonts (swiss is the term used for sans-serif in some systems)
        elif any(sans in font_name for sans in ['arial', 'helvetica', 'verdana', 'tahoma', 'calibri', 'sans',
                                                'gothic', 'trebuchet', 'century gothic', 'futura', 'geneva']):
            font_info['family'] = 'swiss'
            
        # Monospace fonts
        elif any(mono in font_name for mono in ['courier', 'consolas', 'monaco', 'mono', 'typewriter',
                                               'lucida console', 'fixed', 'terminal']):
            font_info['family'] = 'monospace'
            
        # Script/cursive fonts
        elif any(script in font_name for script in ['script', 'brush', 'cursive', 'handwriting', 'calligraphy']):
            font_info['family'] = 'script'
            
        # Decorative fonts
        elif any(deco in font_name for deco in ['decorative', 'ornamental', 'display', 'fantasy', 'comic']):
            font_info['family'] = 'decorative'
            
        # Specific font mappings
        font_family_map = {
            'arial': 'swiss',
            'helvetica': 'swiss',
            'times': 'serif',
            'timesnewroman': 'serif',
            'courier': 'monospace',
            'couriernew': 'monospace',
            'symbol': 'symbol',
            'zapfdingbats': 'dingbats',
            'wingdings': 'dingbats',
            'webdings': 'dingbats'
        }
        
        # Check if the base font is in our direct mapping
        cleaned_base = ''.join(c for c in base_font if c.isalpha()).lower()
        if cleaned_base in font_family_map:
            font_info['family'] = font_family_map[cleaned_base]
    
    # Get font size
    font_size = word_info.get('size', 10)
    if font_size:
        try:
            font_info['size'] = float(font_size)
        except (ValueError, TypeError):
            # Keep default if conversion fails
            pass
    
    return font_info


def process_word(chars, span_info, page_num, page_height, scale_factor, output_data, pixel_block_bbox):
    """Process a single word with enhanced style information"""
    if not chars:
        return
        
    word_text = ''.join(c['text'] for c in chars)
    
    # Skip if word is empty or just spaces
    if not word_text.strip():
        return

    word_text = word_text.replace('\x00', '')

    x0 = min(c['x0'] for c in chars)
    y0_pdf = min(c['top'] for c in chars)
    x1 = max(c['x1'] for c in chars)
    y1_pdf = max(c['bottom'] for c in chars)
    
    pixel_x0 = x0 * scale_factor
    pixel_x1 = x1 * scale_factor
    pixel_y_top = y0_pdf * scale_factor
    pixel_y_bottom = y1_pdf * scale_factor
    
    output_data.append({
        "page": page_num + 1,
        "text": word_text.strip(),
        "bbox": [
            round(pixel_x0, 2),
            round(pixel_y_top, 2),
            round(pixel_x1, 2),
            round(pixel_y_bottom, 2)
        ],
        "font": span_info['font'],
        "family": span_info.get('family', 'swiss'),
        "size": span_info['size'],
        "bold": span_info['bold'],
        "italic": span_info['italic'],
        "underline": span_info.get('underline', False),
        "block_bbox": [round(v, 2) for v in pixel_block_bbox]
    })


def extract_words_with_pdfplumber(pdf_path, dpi=300):
    """Extract words using PDFPlumber with enhanced style detection"""
    scale_factor = dpi / 72.0
    output_data = []
    page_dims = {}

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Get page dimensions
            width_pts = page.width
            height_pts = page.height
            width_px = math.ceil(width_pts * scale_factor)
            height_px = math.ceil(height_pts * scale_factor)
            page_dims[page_num + 1] = (width_px, height_px)

            # Extract words with additional attributes
            words_data = page.extract_words(
                x_tolerance=3, 
                y_tolerance=3, 
                keep_blank_chars=False,
                use_text_flow=True,
                extra_attrs=['fontname', 'size', 'non_stroking_color']
            )
            
            # Group words by position to form blocks
            blocks = detect_blocks_from_words(words_data)
            
            for block in blocks:
                block_bbox_pdf = block['bbox']
                pixel_block_bbox = [
                    block_bbox_pdf[0] * scale_factor,
                    block_bbox_pdf[1] * scale_factor,
                    block_bbox_pdf[2] * scale_factor,
                    block_bbox_pdf[3] * scale_factor
                ]
                
                # Process each word in the block
                for word_info in block['words']:
                    # Extract detailed font information
                    font_info = extract_font_info(word_info)
                    
                    # Create a char-like structure for the word
                    word_char = [{
                        'text': word_info['text'],
                        'x0': word_info['x0'],
                        'top': word_info['top'],
                        'x1': word_info['x1'],
                        'bottom': word_info['bottom']
                    }]
                    
                    process_word(word_char, font_info, page_num, height_pts, 
                               scale_factor, output_data, pixel_block_bbox)
    
    return output_data, page_dims


def detect_blocks_from_words(words, block_threshold=50):
    """Detect blocks from words instead of characters"""
    if not words:
        return []
    
    # Sort words by position
    sorted_words = sorted(words, key=lambda w: (w['top'], w['x0']))
    
    blocks = []
    current_block = {'words': [], 'bbox': None}
    
    for word in sorted_words:
        if not current_block['words']:
            current_block['words'].append(word)
            current_block['bbox'] = [word['x0'], word['top'], word['x1'], word['bottom']]
        else:
            # Check if word belongs to current block
            last_word = current_block['words'][-1]
            x_diff = word['x0'] - last_word['x1']
            y_diff = abs(word['top'] - last_word['top'])
            
            # More lenient check for block membership
            if (x_diff < block_threshold * 2 and y_diff < block_threshold) or \
               (y_diff < 5 and x_diff < 100):  # Same line, allow larger x gaps
                current_block['words'].append(word)
                # Update block bbox
                current_block['bbox'] = [
                    min(current_block['bbox'][0], word['x0']),
                    min(current_block['bbox'][1], word['top']),
                    max(current_block['bbox'][2], word['x1']),
                    max(current_block['bbox'][3], word['bottom'])
                ]
            else:
                # Start new block
                blocks.append(current_block)
                current_block = {'words': [word], 'bbox': [word['x0'], word['top'], word['x1'], word['bottom']]}
    
    if current_block['words']:
        blocks.append(current_block)
    
    return blocks

def convert_and_save_tiffs_batched(pdf_path, batch_folder, tm_no, pdf_info, pdf_key, parent_image, dpi=300, batch_size=5):
    """
    Convert PDF to TIFF images in batches and save immediately to manage memory.
    
    Args:
        pdf_path: Path to the PDF file
        batch_folder: Folder where TIFF files will be saved
        tm_no: Starting TM number for file naming
        pdf_info: Dictionary to store page information
        pdf_key: Key for pdf_info dictionary
        parent_image: Parent image name
        dpi: Resolution for TIFF conversion (default: 300)
        batch_size: Number of pages to process at once (default: 5)
    
    Returns:
        Tuple of (tif_files dict, updated tm_no)
    """
    # Get total page count
    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
    
    print(f"Converting PDF to images in batches to manage memory...")
    tif_files = {}
    page_counter = 1
    
    # Process in batches
    for start_page in range(1, num_pages + 1, batch_size):
        end_page = min(start_page + batch_size - 1, num_pages)
        print(f"Converting pages {start_page}-{end_page} of {num_pages}...")
        
        batch_pages = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=start_page,
            last_page=end_page
        )
        
        # Save TIFF files immediately
        for page in batch_pages:
            tif_id = f"tm{str(tm_no).zfill(6)}"
            tif_filename = f"{tif_id}.tif"
            output_file = os.path.join(batch_folder, tif_filename)
            
            # Save the TIF
            page.save(output_file, 'TIFF', dpi=(dpi, dpi), compression='tiff_lzw')
            tif_files[page_counter] = tif_filename
            
            # Store page info in PDF info
            pdf_info[pdf_key][f'TM{str(tm_no).zfill(6)}'] = {
                'pdf': os.path.basename(pdf_path),
                'tiff': tif_filename,
                'parent': parent_image,
                'xml': f"TM{str(tm_no).zfill(6)}_layout.xml",
            }
            
            print(f"Saved TIFF file: {tif_filename} (Page {page_counter} of {num_pages})")
            
            tm_no += 1
            page_counter += 1
        
        # Clear batch from memory
        del batch_pages
        gc.collect()
    
    print(f"Converted {num_pages} pages from PDF to image")
    return tif_files, tm_no


def generate_font_style_string(word):
    """Generate style string in the format expected by the new RAJson format"""
    font_style = "font-name: " + word['font'].lower() + "; font-family: " + word.get('family', 'swiss') + ";"
    
    if word.get('bold', False):
        font_style += " font-weight: bold;"
    
    font_style += f" font-size: {word['size']:.1f}pt;"
    
    if word.get('underline', False):
        font_style += " text-decoration: underline;"
        
    return font_style


def convert_to_ra_json(extracted_data, tif_files, original_file_path, page_dims, base_id, parent_image):
    """Convert extracted data to new RA JSON format"""
    # First, create nodes structure
    ra_json = {
        "id": "", 
        "TYPE": "AIDBSERVICE",
        "bvOCR": "S",
        "nodes": []
    }
    
    # Create document node
    document_node = {
        "id": "",  
        "ext": ".pdf",
        "type": "document",
        "Vendor": "", 
        "file_path": original_file_path,  # Set the file_path to the PDF path
        "DocType": "",  
        "Project": "",  
        "Language": "English",
        "children": []
    }
    
    # Group words by page
    pages_group = group_words_by_page(extracted_data)
    
    for page_num, words in sorted(pages_group.items()):
        # Get the TIF filename for this page
        tif_filename = tif_files.get(page_num, "")
        
        # Extract page ID from TIF filename (remove .tif extension)
        page_id = tif_filename[:-4] if tif_filename else f"{base_id}"
        
        width, height = page_dims.get(page_num, (2480, 3507))
        
        # Create style map for this page
        style_map = {}
        style_list = []
        style_counter = 0
        
        # Create page node
        page_node = {
            "id": page_id.upper(),
            "pos": f"0,0,{width},{height}",
            "TYPE": "GenericDoc" if page_num == 1 else "GenericDocTrailingPage",
            "lang": "en-us",
            "s_lg": "0",
            "type": "page",
            "xdpi": "300",
            "ydpi": "300",
            "STATUS": "49",
            "layout": f"{page_id.upper()}_layout.xml",
            "styles": [],
            "children": [],
            "IMAGEFILE": tif_filename,
            "ParentImage": parent_image,  # Use the provided parent image
            "RecogStatus": "0",
            "ScanSrcPath": None,
            "NewSourceDoc": "True" if page_num == 1 else "False",
            "s_srbatchdir": "",
            "y_AutoRotate": "false"
        }
        
        if page_num == 1:
            page_node["DATAFILE"] = f"{page_id}_layout.xml"
            page_node["OCRSLang"] = "0"
        
        # Process blocks
        blocks = group_words_by_block(words)
        block_index = 1
        
        for block_bbox, block_words in blocks.items():
            block_words.sort(key=lambda w: (w["bbox"][1], w["bbox"][0]))
            block_bbox_int = [int(math.ceil(block_bbox[0])),
                             int(math.ceil(block_bbox[1])),
                             int(math.ceil(block_bbox[2])),
                             int(math.ceil(block_bbox[3]))]
            block_pos = ",".join(map(str, block_bbox_int))
            
            # Create block node
            block_node = {
                "id": f"{page_id}.{block_index:03d}",
                "pos": block_pos,
                "type": "block",
                "children": []
            }
            
            # Process lines
            lines = group_words_by_line(block_words)
            line_index = 1
            
            for line in lines:
                line.sort(key=lambda w: w["bbox"][0])
                x0 = int(math.ceil(min(w["bbox"][0] for w in line)))
                y0 = int(math.ceil(min(w["bbox"][1] for w in line)))
                x1 = int(math.ceil(max(w["bbox"][2] for w in line)))
                y1 = int(math.ceil(max(w["bbox"][3] for w in line)))
                line_pos = f"{x0},{y0},{x1},{y1}"
                
                # Create line node
                line_node = {
                    "id": f"{page_id}.{block_index:03d}.{line_index:03d}",
                    "pos": line_pos,
                    "type": "line",
                    "children": []
                }
                
                # Process words
                word_index = 1
                for w in line:
                    word_bbox = w["bbox"]
                    word_pos = ",".join([
                        str(int(math.ceil(word_bbox[0]))),
                        str(int(math.ceil(word_bbox[1]))),
                        str(int(math.ceil(word_bbox[2]))),
                        str(int(math.ceil(word_bbox[3])))
                    ])
                    
                    # Generate style key
                    style_key = generate_font_style_string(w)
                    
                    # Add style to style map if new
                    if style_key not in style_map:
                        style_map[style_key] = str(style_counter)
                        style_list.append({"v": style_key, "id": str(style_counter)})
                        style_counter += 1
                    
                    style_id = style_map[style_key]
                    
                    # Create word node
                    word_node = {
                        "s": style_id,
                        "v": w["text"],
                        "cn": "9" * len(w["text"]),  # Replace with 9s based on text length
                        "id": f"{page_id}.{block_index:03d}.{line_index:03d}.{word_index:03d}",
                        "pos": word_pos,
                        "type": "word"
                    }
                    
                    line_node["children"].append(word_node)
                    word_index += 1
                
                block_node["children"].append(line_node)
                line_index += 1
            
            page_node["children"].append(block_node)
            block_index += 1
        
        # Set styles for the page
        page_node["styles"] = style_list
        
        # Add page to document
        document_node["children"].append(page_node)
    
    # Add document to nodes
    ra_json["nodes"].append(document_node)
    
    return ra_json


def increment_id(base_id):
    """Increment ID with proper formatting for tm000001 style"""
    # For tm000001 style IDs
    if base_id.startswith("tm"):
        prefix = "tm"
        number_part = base_id[2:]
        try:
            number = int(number_part)
            new_number = number + 1
            return f"{prefix}{new_number:06d}"
        except ValueError:
            # If conversion fails, use the original method
            return base_id + "_1"
    else:
        # For other ID formats
        m = re.match(r"([A-Z]+)(\d+)", base_id)
        if m:
            prefix, number = m.groups()
            new_number = int(number) + 1
            return prefix + str(new_number).zfill(len(number))
        else:
            return base_id + "_1"


def group_words_by_page(words):
    """Group words by page"""
    pages = defaultdict(list)
    for word in words:
        pages[word["page"]].append(word)
    return pages


def group_words_by_block(page_words):
    """Group words by block based on block bounding box"""
    blocks = defaultdict(list)
    for word in page_words:
        block_key = tuple(word["block_bbox"])
        blocks[block_key].append(word)
    return blocks


def group_words_by_line(block_words, tolerance=3):
    """Group words by line with improved tolerance"""
    words = sorted(block_words, key=lambda w: (w["bbox"][1], w["bbox"][0]))
    lines = []
    current_line = []
    current_y = None
    
    for word in words:
        y = word["bbox"][1]
        if current_y is None:
            current_y = y
            current_line.append(word)
        else:
            if abs(y - current_y) <= tolerance:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(current_line)
                current_line = [word]
                current_y = y
    
    if current_line:
        lines.append(current_line)
    
    return lines


def rename_pdf_files(file_paths, output_folder):
    """Rename PDF files with sequential tm numbers and copy to output folder"""
    renamed_pdfs = {}
    tm_no = 1
    print(f"{file_paths}")
    
    for pdf_path in file_paths:
        if not os.path.exists(pdf_path):
            print(f"WARNING: PDF not found: {pdf_path}")
            continue
        
        new_pdf_name = f"tm{str(tm_no).zfill(6)}.pdf"
        new_pdf_path = os.path.join(output_folder, new_pdf_name)
        shutil.copy(pdf_path, new_pdf_path)
        renamed_pdfs[new_pdf_path] = (new_pdf_name, pdf_path)
        tm_no += 1
    
    return renamed_pdfs, tm_no


def generate_batch_id(base_output_folder):
    """Generate batch ID in the format YYYYMMDD.U##### using current date"""
    # Get current date in YYYYMMDD format
    date_str = datetime.now().strftime("%Y%m%d")
    
    # Find existing batch folders with today's date to determine next U number
    existing_batches = glob.glob(os.path.join(base_output_folder, f"{date_str}.U*"))
    
    if existing_batches:
        # Extract U numbers and find the highest
        u_numbers = []
        for batch_path in existing_batches:
            batch_name = os.path.basename(batch_path)
            if '.' in batch_name:
                u_part = batch_name.split('.')[1]
                if u_part.startswith('U'):
                    try:
                        u_numbers.append(int(u_part[1:]))
                    except ValueError:
                        pass
        
        # Get the next U number
        next_u_number = max(u_numbers) + 1 if u_numbers else 1
    else:
        # No existing batches today, start with 1
        next_u_number = 1
    
    # Format the batch ID
    batch_id = f"{date_str}.U{next_u_number:05d}"
    print(f"Generated batch ID: {batch_id}")
    return batch_id


def process_files(file_paths, output_folder, batch_id, profile_name, project, doc_type="", dpi=300):
    """Process a list of PDF files and combine them into a single RAJson output
    
    Args:
        file_paths: List of paths to PDF files
        output_folder: Folder where output files will be saved
        batch_id: ID for the batch
        doc_type: Document type for metadata
        dpi: Resolution for TIFF conversion
    """
    electronic_pdf_script_version = "v6.14042025.0-ElectronicPdf"
    print("ElectronicPdfScriptVersion", electronic_pdf_script_version)
    vendor = ""
    language = "English"
    
    # Create output folder with the batch ID format
    batch_folder = output_folder
    if not os.path.exists(batch_folder):
        os.makedirs(batch_folder)
    
    if not file_paths:
        print("No PDF files provided")
        return None
    
    print(f"Processing {len(file_paths)} PDF files")
    
    # Initialize the combined RAJson structure
    combined_ra_json = {
        "id": batch_id,
        "TYPE": "AIDBSERVICE",
        "bvOCR": "S",
        "nodes": [],
        "STATUS": "0",
        "Vendor": vendor,
        "DocType": doc_type,
        "DocumentType": doc_type,
        "Project": project,
        "Customer": vendor,
        "Language": language,
        "batch_type": ".pdf",
        "bvFilePath": ",".join(file_paths),
        "bvBatchType": "Process",
        "DefinitionID": profile_name,
        "aidbServerIP": "None",
        "bvPageRotate": "N",
        "bvAIDBProfile": "",
        "bvBarcodeRead": "N",
        "NameMatchingText": None,
        "bvSelectedDocTypes": ""
    }
    
    # Rename PDF files and get initial tm_no
    renamed_pdfs, tm_no = rename_pdf_files(file_paths, batch_folder)
    
    # PDF info dictionary for tracking
    pdf_info = {}
    
    # Process each renamed PDF
    for doc_index, pdf_path in enumerate(renamed_pdfs.keys(), 1):
        try:
            print(f"\n===== Processing {pdf_path} ({doc_index} of {len(renamed_pdfs)}) =====")
            
            # Create document ID with sequential numbering 
            document_id = f"{batch_id}.{doc_index:02d}"
            
            # Get the parent image (the renamed PDF name)
            parent_image, original_file_path = renamed_pdfs[pdf_path]
            
            # Extract base_id from parent_image (remove .pdf extension)
            base_id = parent_image[:-4]
            
            # Create a unique key for this PDF
            pdf_key = f"{batch_folder}_{os.path.basename(pdf_path)}"
            pdf_info[pdf_key] = {}
            
            # Count pages in PDF
            with pdfplumber.open(pdf_path) as pdf:
                num_pages = len(pdf.pages)
                print(f"PDF contains {num_pages} pages")
            
            # Extract text data using PDFPlumber's word extraction
            print(f"Extracting text from PDF: {pdf_path}")
            extracted_data, page_dims = extract_words_with_pdfplumber(pdf_path, dpi=dpi)
            print(f"Extracted {len(extracted_data)} words from {len(page_dims)} pages")
            
            # Convert PDF to images in batches and save immediately
            tif_files, tm_no = convert_and_save_tiffs_batched(
                pdf_path=pdf_path,
                batch_folder=batch_folder,
                tm_no=tm_no,
                pdf_info=pdf_info,
                pdf_key=pdf_key,
                parent_image=parent_image,
                dpi=dpi,
                batch_size=5
            )

            # Convert to RA JSON format for this document
            ra_json = convert_to_ra_json(extracted_data, tif_files, original_file_path, page_dims, base_id=base_id, parent_image=parent_image)
            
            # We only take the first document node
            if ra_json["nodes"] and len(ra_json["nodes"]) > 0:
                document_node = ra_json["nodes"][0]
                
                # Update document node properties
                document_node["id"] = document_id
                document_node["Vendor"] = vendor
                document_node["DocType"] = doc_type
                document_node["Project"] = project
                document_node["Language"] = language
                document_node["DefinitionID"] = profile_name
                document_node["NameMatchingText"] = None
                
                # Add this document node to the combined result
                combined_ra_json["nodes"].append(document_node)
                print(f"Added document node {document_id} with {len(document_node['children'])} pages")
            else:
                print(f"WARNING: No document nodes in RA JSON for {pdf_path}")
                
        except Exception as e:
            print(f"ERROR processing {pdf_path}: {e}")
            import traceback
            traceback.print_exc()
    
    # Save the final combined JSON with the output.json name
    output_ra_json_path = os.path.join(batch_folder, "output.json")
    with open(output_ra_json_path, "w", encoding="utf-8") as f:
        json.dump(combined_ra_json, f, indent=4, ensure_ascii=False)
        
    print(f"\nCombined RA JSON conversion complete, saved to {output_ra_json_path}")
    print(f"Finished processing {len(file_paths)} PDF files.")
    print(f"Total pages processed: {tm_no-1}")
    
    return combined_ra_json

