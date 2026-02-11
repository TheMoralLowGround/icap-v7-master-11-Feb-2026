import fitz  # PyMuPDF library
import numpy as np
import cv2
from pdf2image import convert_from_path
import time
from math import ceil
from PIL import Image
import io
import os
import glob

def is_electronic_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        num_pages = doc.page_count
        
        # Create a subfolder for this PDF's images
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_folder = os.path.dirname(pdf_path)
        pdf_images_folder = os.path.join(output_folder, pdf_name)
        os.makedirs(pdf_images_folder, exist_ok=True)
        
        if num_pages == 0:
            return False  # Empty PDF
        
        # Check first few pages
        pages_to_check = num_pages  # min(3, num_pages)
        
        total_text_length = 0
        pages_with_large_images = 0
        pages_with_content_images = 0  # Images that are likely content, not decorations
        pages_with_only_small_images = 0  # Pages with only tiny images like signatures
        pages_with_text_selectable = 0  # Count pages with selectable text
        pages_with_text_non_selectable = 0  # Count pages with non-selectable text
        pages_with_high_image_density = 0  # Pages with high image-to-text ratio
        
        for page_num in range(pages_to_check):
            page = doc.load_page(page_num)
            
            # Extract text and check length
            text = page.get_text().strip()
            total_text_length += len(text)
            
            # Check text selectability by analyzing text spans and their properties
            text_instances = 0
            try:
                # Get text spans to check if text is properly embedded
                blocks = page.get_text("dict")  # Get text as dictionary
                selectable_text_chars = 0
                total_text_chars = len(text)
                
                for block in blocks["blocks"]:
                    if "lines" in block:  # Text block
                        for line in block["lines"]:
                            for span in line["spans"]:
                                # Check if the span has proper font info and position
                                # This indicates properly embedded text vs OCR text on images
                                if span.get("font", "") and span.get("size", 0) > 0:
                                    selectable_text_chars += len(span["text"])
                
                # If there's text but very few properly embedded characters, it might be a scanned PDF with OCR
                if total_text_chars > 0 and selectable_text_chars < total_text_chars * 0.5:  # Less than 50% of text is properly embedded
                    pages_with_text_non_selectable += 1
                elif total_text_chars > 0:
                    pages_with_text_selectable += 1
                    
            except:
                # If there's an error getting text spans, assume it's selectable
                if len(text) > 0:
                    pages_with_text_selectable += 1
            
            # Get page dimensions
            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height
            page_area = page_width * page_height
            
            image_list = page.get_images()

            # Per-page image metrics
            total_image_area = 0
            large_images_on_page = 0
            content_images_on_page = 0
            small_images_on_page = 0

            # Save each image with the naming format: pdfname_pageno_imageno
            image_no = 0
            for img in image_list:
                xref = img[0]
                try:
                    pix = fitz.Pixmap(doc, xref)

                    # Calculate image dimensions and ratios
                    img_width = pix.width
                    img_height = pix.height
                    img_area = img_width * img_height
                    total_image_area += img_area
                    img_area_ratio = img_area / page_area if page_area > 0 else 0
                    img_width_ratio = img_width / page_width if page_width > 0 else 0
                    img_height_ratio = img_height / page_height if page_height > 0 else 0

                    # Decide output format and save
                    if pix.n - pix.alpha < 4:
                        img_data = pix.tobytes("png")
                        img_ext = ".png"
                    else:
                        img_data = pix.tobytes("jpeg")
                        img_ext = ".jpg"

                    img_filename = f"{pdf_name}_{page_num}_{image_no}{img_ext}"
                    img_path = os.path.join(pdf_images_folder, img_filename)
                    with open(img_path, "wb") as img_file:
                        img_file.write(img_data)

                    # Classify image
                    is_content_image = (
                        img_area_ratio > 0.15
                        or img_area_ratio > 0.05
                        or (img_area_ratio > 0.01 and img_width_ratio > 0.1 and img_height_ratio > 0.1)
                        or img_width_ratio > 0.5
                        or img_height_ratio > 0.5
                    )

                    if img_area_ratio > 0.85:
                        large_images_on_page += 1
                    elif img_area_ratio <= 0.01:
                        small_images_on_page += 1
                    elif is_content_image:
                        content_images_on_page += 1

                    pix = None
                    image_no += 1
                except Exception as e:
                    print(f"Error saving image {image_no} from page {page_num} of {pdf_path}: {e}")
                    continue

            # Check image density
            total_image_ratio = total_image_area / page_area if page_area > 0 else 0
            
            # Check image density
            total_image_ratio = total_image_area / page_area if page_area > 0 else 0
            if total_image_ratio > 0.6:  # More than 60% of page is covered by images
                pages_with_high_image_density += 1
            
            # Update page counters
            if large_images_on_page > 0:
                pages_with_large_images += 1
            
            if content_images_on_page > 0:
                pages_with_content_images += 1
            
            if len(image_list) > 0 and small_images_on_page == len(image_list):
                # Only tiny images on this page
                pages_with_only_small_images += 1
            
            # PER-PAGE SCANNED DETECTION: If this page is scanned, immediately return False
            page_text_length = len(text)
            page_has_non_selectable_text = (pages_with_text_non_selectable > 0)
            
            # Check if current page is scanned
            if large_images_on_page > 0 and page_text_length < 80:
                # Large image with minimal text
                doc.close()
                return False
            
            if total_image_ratio > 0.85:
                # Very high image density on this page
                doc.close()
                return False
            
            if content_images_on_page > 0 and page_text_length < 100:
                # Content images with minimal text
                doc.close()
                return False
            
            if page_has_non_selectable_text and content_images_on_page > 0:
                # Non-selectable text with content images indicates scanned
                doc.close()
                return False
            
            if total_image_ratio > 0.6 and page_text_length < 200:
                # High image density with low text
                doc.close()
                return False
        
        doc.close()
        
        # Calculate ratios
        avg_text_per_page = total_text_length / pages_to_check
        large_image_ratio = pages_with_large_images / pages_to_check
        content_image_ratio = pages_with_content_images / pages_to_check
        non_selectable_text_ratio = pages_with_text_non_selectable / pages_to_check
        high_image_density_ratio = pages_with_high_image_density / pages_to_check
        
        # NEW: Check if there's non-selectable text which indicates scanned PDF with OCR
        if non_selectable_text_ratio > 0.3:  # More than 30% of pages have non-selectable text
            print("non_selectable_text_ratio > 0.3")
            return False  # Scanned - text exists but not truly selectable
        
        # NEW: High image density with non-selectable text
        if high_image_density_ratio > 0.5 and non_selectable_text_ratio > 0.2:
            print("high_image_density_ratio > 0.5 and non_selectable_text_ratio > 0.2")
            return False  # Scanned - high image density with partially non-selectable text
        
        # Decision logic:
        
        # Strong indicators of scanned PDF:
        # 1. Large images covering significant page area
        if large_image_ratio >= 0.85:  # 50% of pages have large images
            print("large_image_ratio >= 0.85")
            if large_image_ratio >= 0.85 and avg_text_per_page < 80:
                print("large_image_ratio >= 0.85 and avg_text_per_page < 80")
                return False
            if large_image_ratio >= 0.85 and avg_text_per_page >= 80 and pages_with_text_non_selectable == 0:
                print("large_image_ratio >= 0.85 but text is substantial and selectable")
                return True
            # return False  # Scanned
        
        # 2. High ratio of content images (not just tiny decorations)
        if content_image_ratio >= 0.7 and avg_text_per_page < 200:
            print("content_image_ratio >= 0.7 and avg_text_per_page < 200")
            return False  # Scanned - many content images with little text
        
        # 3. High content image density with moderate text
        if content_image_ratio >= 0.5 and avg_text_per_page < 100:
            print("content_image_ratio >= 0.5 and avg_text_per_page < 100")
            return False  # Scanned - significant content images with minimal text
        
        # NEW: If there are images AND text is not fully selectable, it's likely scanned
        if content_image_ratio > 0.3 and non_selectable_text_ratio > 0.1:
            print("content_image_ratio > 0.3 and non_selectable_text_ratio > 0.1")
            return False  # Scanned - images present with partially non-selectable text
        
        # NEW: If there are many images but text selectability is low
        if content_image_ratio > 0.4 and pages_with_text_selectable < pages_to_check * 0.5:
            print("content_image_ratio > 0.4 and pages_with_text_selectable < pages_to_check * 0.5")
            return False  # Scanned - many images with poor text selectability
        
        # NEW: High image density even if some text exists
        if high_image_density_ratio > 0.7:
            print("high_image_density_ratio > 0.7")
            return False  # Scanned - very high image density
        
        # Strong indicators of electronic PDF:
        # 1. Substantial text with few content images and good selectability
        if avg_text_per_page > 150 and content_image_ratio < 0.3 and pages_with_text_non_selectable == 0:
            print("avg_text_per_page > 150 and content_image_ratio < 0.3 and pages_with_text_non_selectable == 0")
            return True  # Electronic - lots of text, few content images, all text selectable
        
        # 2. Moderate text with only small decorative images and good selectability
        if avg_text_per_page > 50 and content_image_ratio < 0.2 and pages_with_text_non_selectable == 0:
            print("avg_text_per_page > 50 and content_image_ratio < 0.2 and pages_with_text_non_selectable == 0")
            return True  # Electronic - text exists, only small decorations, all text selectable
        
        # 3. Good text-to-content-image ratio with good selectability
        if avg_text_per_page > 80 and content_image_ratio < 0.4 and pages_with_text_non_selectable == 0:
            print("avg_text_per_page > 80 and content_image_ratio < 0.4 and pages_with_text_non_selectable == 0")
            return True  # Electronic - reasonable text amount with few content images, all text selectable
        
        # NEW: If text exists but has poor selectability, lean towards scanned
        if avg_text_per_page > 50 and non_selectable_text_ratio > 0.2:
            print("avg_text_per_page > 50 and non_selectable_text_ratio > 0.2")
            return False  # Scanned - some text exists but not properly selectable
        
        # NEW: If high image density exists, even with some text, likely scanned
        if high_image_density_ratio > 0.4 and content_image_ratio > 0.4:
            print("high_image_density_ratio > 0.4 and content_image_ratio > 0.4")
            return False  # Scanned - high image density with content images
        
        # Fallback: if text is substantial and selectable, consider electronic
        if avg_text_per_page > 100 and pages_with_text_non_selectable == 0:
            print("avg_text_per_page > 100 and pages_with_text_non_selectable == 0")
            return True
        
        # If there's text but poor selectability, consider scanned
        if avg_text_per_page > 0 and non_selectable_text_ratio > 0.4:
            print("avg_text_per_page > 0 and non_selectable_text_ratio > 0.4")
            return False  # Scanned - text exists but mostly non-selectable
        
        # Default to scanned if text is minimal
        print("default")
        return False
            
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return False