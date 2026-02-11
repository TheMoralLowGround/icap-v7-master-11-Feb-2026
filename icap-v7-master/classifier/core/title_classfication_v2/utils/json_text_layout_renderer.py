"""
JSON Text Layout Renderer

This module provides functions for rendering RA JSON data to text format
with preserved spatial layout using coordinate-based positioning.

Provides interface functions for use by other modules.
"""

import re

from dataclasses import dataclass, field
from statistics import median


@dataclass
class Glyph:
    """Represents a text element with position and styling information."""
    text: str
    left: float
    right: float
    top: float
    bottom: float
    width: float
    height: float
    confidence: float
    style_id: int
    style: dict = field(default_factory=dict)

    @property
    def center_y(self):
        return (self.top + self.bottom) / 2.0

    @property
    def char_width(self):
        stripped = self.text.strip()
        if not stripped:
            return 0.0
        return self.width / max(len(stripped), 1)


@dataclass
class TextLayoutConfig:
    """Configuration for text rendering with proper spacing and scaling."""
    px_per_char: float
    px_per_row: float

    @property
    def scale_x(self):
        return 1.0 / self.px_per_char

    @property
    def scale_y(self):
        return 1.0 / self.px_per_row


def should_join(prev_text, next_text):
    """Determine if two text elements should be joined without a space."""
    if not prev_text:
        return False
    if not next_text:
        return True
    join_after = {'-', '/', '(', '[', '"', "'"}
    join_before = {'.', ',', ';', ':', ')', ']', '?', '!', '"', "'"}
    if prev_text[-1] in join_after:
        return True
    if next_text[0] in join_before:
        return True
    return False


def get_md_wrap(text, style):
    """Get markdown-wrapped text based on style."""
    if not style:
        return text
    bold = 'font-weight' in style and 'bold' in style['font-weight'].lower()
    italic = 'font-style' in style and 'italic' in style['font-style'].lower()
    if bold:
        return f"**{text}**"
    elif italic:
        return f"*{text}*"
    else:
        return text


def estimate_px_per_char(glyphs, fallback=10.0):
    """Estimate pixels per character based on glyph dimensions."""
    widths = []
    for glyph in glyphs:
        text = glyph.text.strip()
        if not text:
            continue
        char_count = len(text)
        if char_count <= 0:
            continue
        widths.append(glyph.width / char_count)
    if not widths:
        return fallback
    return max(1.0, float(median(widths)))


def estimate_px_per_row(glyphs, fallback=18.0):
    """Estimate pixels per row based on actual line spacing."""
    if not glyphs:
        return fallback

    # Group glyphs by approximate rows to find actual line spacing
    centers = sorted(set(glyph.center_y for glyph in glyphs))
    spacings = []

    # Calculate spacing between consecutive line centers
    for i in range(1, len(centers)):
        spacing = centers[i] - centers[i-1]
        # Filter reasonable line spacings (exclude very small gaps within lines)
        if 10 < spacing < 100:
            spacings.append(spacing)

    if spacings:
        # Use a balanced approach to avoid both over-merging and over-splitting
        estimated = float(median(spacings))
        min_spacing = min(spacings) if spacings else estimated

        # Use different strategies based on minimum spacing
        if min_spacing < 30:
            # Very tight layout - use median to avoid over-splitting
            return max(1.0, estimated * 0.7)
        else:
            # Normal layout - be conservative to avoid merging separate logical rows
            return max(1.0, min_spacing * 0.8)

    # Fallback to height-based estimation if no line spacing found
    heights = [glyph.height for glyph in glyphs if glyph.height > 0]
    if heights:
        return max(1.0, float(median(heights)))

    return fallback


def to_text_rows(glyphs, config):
    """Convert glyphs to text rows with proper spacing."""
    if not glyphs:
        return []

    row_map = {}
    max_row_index = 0
    for glyph in glyphs:
        if not glyph.text.strip():
            continue
        row_index = int(round(glyph.center_y * config.scale_y))
        row_map.setdefault(row_index, []).append(glyph)
        if row_index > max_row_index:
            max_row_index = row_index

    rows = []

    def ensure_length(line, target):
        if target > len(line):
            line.extend(' ' * (target - len(line)))

    for row_index in range(max_row_index + 1):
        glyphs_in_row = row_map.get(row_index)
        if not glyphs_in_row:
            rows.append('')
            continue

        glyphs_in_row.sort(key=lambda g: g.left)
        line_chars = []
        prev_end_col = 0
        prev_right_px = None
        prev_text = None

        for glyph in glyphs_in_row:
            text = glyph.text
            if not text:
                continue

            start_col = int(round(glyph.left * config.scale_x))
            width_cols = max(len(text), int(round(max(glyph.width * config.scale_x, 1.0))))

            if prev_right_px is not None:
                physical_gap = glyph.left - prev_right_px

                # Check if there's significant physical separation in the source document
                min_gap_threshold = 5.0  # pixels - adjust based on typical character spacing

                if physical_gap > min_gap_threshold:
                    # Significant gap exists - respect original position to maintain column alignment
                    start_col = max(0, start_col)
                    # Even with significant gaps, ensure proper spacing between words
                    needs_space = not should_join(prev_text, text)
                    if needs_space and start_col <= prev_end_col:
                        start_col = prev_end_col + 1
                else:
                    # Small or no gap - use relative positioning to avoid overlap
                    gap_cols = 0
                    if physical_gap > 0:
                        gap_cols = max(1, int(round(physical_gap * config.scale_x)))
                    desired_start = prev_end_col + gap_cols
                    if physical_gap <= 0:
                        desired_start = max(prev_end_col, start_col)
                    needs_space = not should_join(prev_text, text)
                    if needs_space:
                        desired_start = max(desired_start, prev_end_col + 1)
                    start_col = max(desired_start, start_col)
            else:
                start_col = max(0, start_col)

            end_required = start_col + width_cols + 1
            ensure_length(line_chars, end_required)

            # Place characters directly at calculated positions
            for i, ch in enumerate(text):
                target_col = start_col + i
                if target_col < len(line_chars):
                    line_chars[target_col] = ch

            prev_end_col = start_col + len(text)
            prev_right_px = glyph.right
            prev_text = text

        rows.append(''.join(line_chars).rstrip())

    return rows


def to_markdown_rows(glyphs, config):
    """Convert glyphs to markdown rows with minimal styling (h1-h4, bold, italic), preserving layout."""
    if not glyphs:
        return []

    row_map = {}
    max_row_index = 0
    for glyph in glyphs:
        if not glyph.text.strip():
            continue
        row_index = int(round(glyph.center_y * config.scale_y))
        row_map.setdefault(row_index, []).append(glyph)
        if row_index > max_row_index:
            max_row_index = row_index

    rows = []

    def ensure_length(line, target):
        if target > len(line):
            line.extend(' ' * (target - len(line)))

    for row_index in range(max_row_index + 1):
        glyphs_in_row = row_map.get(row_index)
        if not glyphs_in_row:
            rows.append('')
            continue

        glyphs_in_row.sort(key=lambda g: g.left)

        # Check if this row can be treated as a heading
        all_have_style = all(g.style for g in glyphs_in_row)
        all_bold = all_have_style and all(
            'font-weight' in g.style and 'bold' in g.style['font-weight'].lower()
            for g in glyphs_in_row
        )
        sizes = []
        is_potential_heading = all_have_style
        for g in glyphs_in_row:
            size_str = g.style.get('font-size', '8pt')
            size_match = re.search(r'(\d+(?:\.\d+)?)', size_str)
            size = float(size_match.group(1)) if size_match else 10.0
            sizes.append(size)
            if size <= 8.0:
                is_potential_heading = False

        if is_potential_heading and all_bold and sizes:
            max_size = max(sizes)
            heading_level = 0
            if max_size >= 14:
                heading_level = 1
            elif max_size >= 12:
                heading_level = 2
            # elif max_size >= 10:
            #     heading_level = 3
            # elif max_size >= 8:
            #     heading_level = 4
            if heading_level > 0:
                joined_text = ' '.join(g.text.strip() for g in glyphs_in_row if g.text.strip())
                if joined_text:
                    line = '#' * heading_level + ' ' + joined_text
                    rows.append(line)
                    continue

        # Fallback to positioned layout with inline markdown
        line_chars = []
        prev_end_col = 0
        prev_right_px = None
        prev_text = None

        for glyph in glyphs_in_row:
            orig_text = glyph.text
            if not orig_text:
                continue

            md_text = get_md_wrap(orig_text, glyph.style)

            start_col = int(round(glyph.left * config.scale_x))
            width_cols = max(len(md_text), int(round(max(glyph.width * config.scale_x, 1.0))))

            if prev_right_px is not None:
                physical_gap = glyph.left - prev_right_px

                # Check if there's significant physical separation in the source document
                min_gap_threshold = 5.0  # pixels - adjust based on typical character spacing

                if physical_gap > min_gap_threshold:
                    # Significant gap exists - respect original position to maintain column alignment
                    start_col = max(0, start_col)
                    # Even with significant gaps, ensure proper spacing between words
                    needs_space = not should_join(prev_text, orig_text)
                    if needs_space and start_col <= prev_end_col:
                        start_col = prev_end_col + 1
                else:
                    # Small or no gap - use relative positioning to avoid overlap
                    gap_cols = 0
                    if physical_gap > 0:
                        gap_cols = max(1, int(round(physical_gap * config.scale_x)))
                    desired_start = prev_end_col + gap_cols
                    if physical_gap <= 0:
                        desired_start = max(prev_end_col, start_col)
                    needs_space = not should_join(prev_text, orig_text)
                    if needs_space:
                        desired_start = max(desired_start, prev_end_col + 1)
                    start_col = max(desired_start, start_col)
            else:
                start_col = max(0, start_col)

            end_required = start_col + width_cols + 1
            ensure_length(line_chars, end_required)

            # Place markdown characters directly at calculated positions
            for i, ch in enumerate(md_text):
                target_col = start_col + i
                if target_col < len(line_chars):
                    # Overwrite if necessary, but positioning minimizes overlap
                    line_chars[target_col] = ch

            prev_end_col = start_col + len(md_text)
            prev_right_px = glyph.right
            prev_text = orig_text

        rows.append(''.join(line_chars).rstrip())

    # Remove leading empty rows at the end
    while rows and not rows[-1].strip():
        rows.pop()

    return rows


def parse_pos(pos):
    """Parse position string into left, top, right, bottom coordinates."""
    left_str, top_str, right_str, bottom_str = pos.split(',')
    return float(left_str), float(top_str), float(right_str), float(bottom_str)


def contains_email_file_pattern(text: str) -> bool:
    """
    Check if a given file path matches the email file pattern.

    Parameters
    ----------
    text : str
        The file path or file name to check.

    Returns
    -------
    bool
        True if the file name matches the pattern 'email_file' optionally followed 
        by an underscore and digits, ending with '.pdf'. Otherwise, False.
    """
    pattern = r'email_file(?:_\d+)?\.pdf'
    return re.search(pattern, text) is not None


def get_pages_from_json_data(data):
    all_pages = []
    for doc_obj in data.get("nodes", []):
        file_path = doc_obj.get("file_path", "")
        if contains_email_file_pattern(file_path):
            continue
        for page_dict in doc_obj.get("children", []):
            page_dict["file_path"] = file_path
            all_pages.append(page_dict)
    return all_pages

def load_words_from_page(page_node):
    """Extract words from a specific page node."""
    words = []

    # Parse styles
    styles_list = page_node.get('styles', [])
    parsed_styles = {}
    for st in styles_list:
        if 'id' not in st or 'v' not in st:
            continue
        try:
            sid = int(st['id'])
        except ValueError:
            continue
        props_str = st['v'].strip()
        if not props_str:
            continue
        props = {}
        for part in [p.strip() for p in props_str.split(';') if p.strip()]:
            if ':' in part:
                key, val = [p.strip() for p in part.split(':', 1)]
                if key and val:
                    props[key] = val
        parsed_styles[sid] = props

    def visit(node):
        children = node.get('children', [])
        if not children:
            return
        for child in children:
            node_type = child.get('type')
            if node_type == 'word':
                text = child.get('v', '')
                pos = child.get('pos', '')
                style_id = int(child.get('s', 0))
                confidence = float(child.get('cn', 0.0))
                left, top, right, bottom = parse_pos(pos)
                words.append(
                    Glyph(
                        text=text,
                        left=left,
                        right=right,
                        top=top,
                        bottom=bottom,
                        width=right - left,
                        height=bottom - top,
                        confidence=confidence,
                        style_id=style_id,
                        style=parsed_styles.get(style_id, {}),
                    )
                )
            else:
                visit(child)

    visit(page_node)
    return words


def render_page(page_node, page_num):
    """Render a single page to text rows."""
    glyphs = load_words_from_page(page_node)
    if not glyphs:
        return [f"# Page {page_num}: No content found"]

    px_per_char = estimate_px_per_char(glyphs)
    px_per_row = estimate_px_per_row(glyphs)
    config = TextLayoutConfig(px_per_char=px_per_char, px_per_row=px_per_row)
    rows = to_markdown_rows(glyphs, config)

    # Remove leading empty rows
    while rows and not rows[0].strip():
        rows.pop(0)

    # Add page header
    page_id = page_node.get('id', f'Page{page_num}')
    header = f"# Page {page_num} ({page_id})"
    return [header, ""] + rows


def render_from_json_data_multipage(data):
    """Render all pages from JSON data sequentially."""
    pages = get_pages_from_json_data(data)
    if not pages:
        return ["# No pages found in JSON"]

    all_rows = []
    for i, page in enumerate(pages, 1):
        page_rows = render_page(page, i)
        all_rows.extend(page_rows)

        # Add page separator (except after last page)
        if i < len(pages):
            all_rows.extend(["", "=" * 80, ""])

    return all_rows


def render_json_to_text_with_layout(data):
    """
    Render RA JSON data to text using layout-aware rendering.

    This function automatically detects whether the input is a single page or
    multi-page JSON structure and renders accordingly.

    Args:
        data: Either a single page dictionary or complete RA JSON data dictionary

    Returns:
        String containing the text representation of the page(s)
    """
    try:
        # Check if this is a single page or multi-page structure
        if 'type' in data and data.get('type') == 'page':
            # Single page data
            return _render_single_page_with_layout(data)
        elif 'nodes' in data:
            # Multi-page JSON structure (digital_transactions format)
            return _render_multipage_with_layout(data)
        elif 'pages' in data:
            # Multi-page JSON structure (bf_batches format)
            return _render_multipage_with_layout(data)
        else:
            # Assume it's a single page without explicit type
            return _render_single_page_with_layout(data)

    except Exception as e:
        return f"Error processing JSON: {str(e)}"


def _render_single_page_with_layout(page_data):
    """
    Internal function to render a single page with layout preservation.

    Args:
        page_data: A single page dictionary from RA JSON format

    Returns:
        String containing the text representation of the page
    """
    try:
        # Extract glyphs from the page
        glyphs = load_words_from_page(page_data)
        if not glyphs:
            return ""

        # Configure layout rendering
        px_per_char = estimate_px_per_char(glyphs)
        px_per_row = estimate_px_per_row(glyphs)
        config = TextLayoutConfig(px_per_char=px_per_char, px_per_row=px_per_row)

        # Render to markdown rows
        rows = to_markdown_rows(glyphs, config)

        # Remove leading empty rows
        while rows and not rows[0].strip():
            rows.pop(0)

        return '\n'.join(rows)

    except Exception:
        return ""

def _render_multipage_with_layout(json_data):
    """
    Internal function to render multi-page JSON data with layout preservation.

    Args:
        json_data: Complete RA JSON data dictionary with nodes structure

    Returns:
        String containing the text representation of all pages
    """
    try:
        pages = get_pages_from_json_data(json_data)
        if not pages:
            return "# No pages found in JSON"

        all_text_parts = []
        for i, page in enumerate(pages, 1):
            # Use layout-aware rendering for each page
            page_text = _render_single_page_with_layout(page)

            content = ""

            if page_text.strip():
                header = f"########################\nPAGE {i}\n########################\n"
                content = header + '\n' + page_text
            else:
                # If page processing fails, add a placeholder
                page_id = page.get('id', f'Page{i}')
                content = f"# Page {i} ({page_id}): No content found"

            # Add page separator (except after last page)
            if i < len(pages):
                content += '\n\n' + ('=' * 80) + '\n\n'

            all_text_parts.append(content)

        return all_text_parts

    except Exception as e:
        return f"Error processing multi-page JSON: {str(e)}"
    
def _render_multipage_with_layout_filewise(json_data):
    try:
        pages = get_pages_from_json_data(json_data)
        if not pages:
            return [["# No pages found in JSON"]]

        all_text_parts = []
        prev_file_path = None
        file_text_parts = []

        for page_num, page in enumerate(pages, 1):
            file_path = page.get('file_path', '')
            page_text = _render_single_page_with_layout(page)
            
            content = ""
            
            if not page_text.strip():
                header = f"########################\nPAGE {page_num} \n########################\n"
                content = header + '\n' + 'No content found'
                
            else:
                
                if prev_file_path == None:
                    header = f"########################\nPAGE {page_num} \n########################\n"
                    content = header + '\n' + page_text
                
                elif prev_file_path != file_path:
                    all_text_parts.append(file_text_parts)
                    
                    file_text_parts = []
                    
                    header = f"########################\nPAGE {page_num} \n########################\n"
                    content = header + '\n' + page_text
                
                else:
                    header = f"########################\nPAGE {page_num} \n########################\n"
                    content = header + '\n' + page_text
                    
            content += ("\n" + "=" * 80 + "\n")
            file_text_parts.append(content)        
                    
            prev_file_path = file_path
            
        if file_text_parts:
            all_text_parts.append(file_text_parts)
            
        return all_text_parts

    except Exception as e:
        return f"Error processing multi-page JSON: {str(e)}"