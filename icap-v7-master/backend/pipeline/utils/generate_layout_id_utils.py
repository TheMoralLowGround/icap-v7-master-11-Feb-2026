import re
import uuid
import numpy as np
import pickle
from functools import lru_cache
from django.conf import settings
from core.models import Batch, BatchStatus, EmailBatch, TrainBatch, Definition

# Performance optimization: Database-stored embeddings
# Embeddings are stored directly in the Definition model for ultimate performance
# This eliminates the need for Redis cache and provides instant access

# Version tracking for automatic cache invalidation
# IMPORTANT: Increment MASKING_VERSION whenever you modify mask_variable_content() logic
# Example: Change from "v1.0" to "v1.1" after updating regex patterns
MASKING_VERSION = "v1.0"

def _get_model_version():
    """Get combined version string for cache invalidation
    
    Combines:
    - Sentence transformer model version/name
    - Masking function version (MASKING_VERSION)
    
    This ensures embeddings are invalidated when EITHER:
    - The embedding model changes, OR
    - The masking logic changes
    
    Returns:
        str: Combined version string like "all-MiniLM-L6-v2__mask_v1.0"
    """
    try:
        model = settings.SENTENCE_TRANSFORMERS_MODEL
        # Try to get model name/version
        if hasattr(model, '_model_name'):
            model_ver = model._model_name
        elif hasattr(model, 'model_card_data'):
            model_ver = str(model.model_card_data.get('model_id', 'unknown'))
        else:
            model_ver = 'default'
        
        # Combine model version with masking version
        return f"{model_ver}__mask_{MASKING_VERSION}"
    except:
        return f'default__mask_{MASKING_VERSION}'


def clear_layout_caches():
    """
    Clear all caches used for layout matching performance.
    With database-stored embeddings, this only clears the LRU cache for masked patterns.
    To refresh database embeddings, update the embedding_model_version field.
    """
    # Clear LRU cache for masked patterns
    mask_variable_content.cache_clear()
    print(f"Cleared layout pattern mask cache")


def get_cache_stats():
    """
    Get statistics about cache usage for performance monitoring.
    Returns dict with cache sizes and hit rates.
    """
    from core.models import Definition
    
    cache_info = mask_variable_content.cache_info()
    
    # Count definitions with stored embeddings
    total_definitions = Definition.objects.count()
    definitions_with_embeddings = Definition.objects.exclude(embedding__isnull=True).count()
    
    stats = {
        'storage_backend': 'Database (persistent)',
        'total_definitions': total_definitions,
        'definitions_with_embeddings': definitions_with_embeddings,
        'embedding_coverage': f"{(definitions_with_embeddings / total_definitions * 100) if total_definitions > 0 else 0:.1f}%",
        'mask_cache_hits': cache_info.hits,
        'mask_cache_misses': cache_info.misses,
        'mask_cache_size': cache_info.currsize,
        'mask_cache_maxsize': cache_info.maxsize,
        'mask_hit_rate': cache_info.hits / (cache_info.hits + cache_info.misses) if (cache_info.hits + cache_info.misses) > 0 else 0,
        'current_model_version': _get_model_version(),
        'masking_version': MASKING_VERSION
    }
    
    return stats


def _get_embedding_from_db(definition, current_model_version):
    """
    Retrieve embedding from database if available and model version matches.
    Returns None if not found or model version mismatch.
    """
    try:
        if definition.embedding and definition.embedding_model_version == current_model_version:
            return pickle.loads(definition.embedding)
    except Exception as e:
        print(f"Error loading embedding from database: {e}")
    return None


def _save_embedding_to_db(definition, embedding, current_model_version, save_now=True):
    """
    Store embedding in database for persistent storage.
    This eliminates the need for Redis cache and provides instant access across all pods.
    
    Args:
        definition: Definition model instance
        embedding: Numpy array embedding
        current_model_version: Model version string
        save_now: If True, saves immediately. If False, caller must save.
    """
    try:
        definition.embedding = pickle.dumps(embedding)
        definition.embedding_model_version = current_model_version
        if save_now:
            definition.save(update_fields=['embedding', 'embedding_model_version'])
    except Exception as e:
        print(f"Error saving embedding to database: {e}")


@lru_cache(maxsize=2000)
def mask_variable_content(text):
    """
    Masks variable content while preserving document structure for similarity matching.
    
    Strategy:
    1. Extract and normalize key structural phrases (headers, labels)
    2. Mask variable data (numbers, company names, addresses)
    3. Preserve document type indicators and layout structure
    
    This balances between:
    - Similar documents (same type) matching with high similarity
    - Different documents (different types/layouts) having low similarity
    
    Performance: Uses LRU cache to avoid re-computing masks for same text.
    """
    if not text:
        return ""
    
    # Step 1: Replace [AMOUNT] placeholders
    text = re.sub(r'\[AMOUNT\]', '', text)
    
    # Step 2: Normalize whitespace first
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = '\n'.join(line.strip() for line in text.split('\n'))
    text = re.sub(r'\n+', ' ', text)  # Convert to single line for processing
    
    # Step 3: Define key structural phrases to extract and normalize
    # These are the "anchors" that define document types
    key_phrases = [
        # Air Waybill phrases
        (r"Shipper'?s?\s+Name\s+and\s+Address", "[SHIPPER_ADDR]"),
        (r"Shipper'?s?\s+Account\s+Number", "[SHIPPER_ACCT]"),
        (r"Consignee'?s?\s+Name\s+and\s+Address", "[CONSIGNEE_ADDR]"),
        (r"Consignee'?s?\s+Account\s+Number", "[CONSIGNEE_ACCT]"),
        (r"Not\s+[Nn]egotiable", "[NOT_NEGOTIABLE]"),
        (r"Air\s+[Ww]aybill", "[AIR_WAYBILL]"),
        (r"Issued\s+[Bb]y", "[ISSUED_BY]"),
        (r"Carrier'?s?\s+Agent", "[CARRIER_AGENT]"),
        (r"Airport\s+of\s+Departure", "[AIRPORT_DEP]"),
        (r"Airport\s+of\s+Destination", "[AIRPORT_DEST]"),
        (r"Handling\s+Information", "[HANDLING_INFO]"),
        (r"Gross\s+Weight", "[GROSS_WEIGHT]"),
        (r"Chargeable\s+Weight", "[CHARGE_WEIGHT]"),
        (r"Nature\s+and\s+Quantity", "[NATURE_QTY]"),
        (r"Declared\s+Value", "[DECLARED_VAL]"),
        # Invoice phrases
        (r"EXPORT\s+INVOICE", "[EXPORT_INVOICE]"),
        (r"TAX\s+INVOICE", "[TAX_INVOICE]"),
        (r"COMMERCIAL\s+INVOICE", "[COMMERCIAL_INVOICE]"),
        (r"PROFORMA\s+INVOICE", "[PROFORMA_INVOICE]"),
        (r"Invoice\s+No\.?\s*(?:&\s*Date)?\s*:?", "[INVOICE_NO]"),
        (r"Invoice\s+Dt\.?\s*:?", "[INVOICE_DATE]"),
        (r"Exporter'?s?\s+Ref\.?\s*:?", "[EXPORTER_REF]"),
        (r"Buyer'?s?\s+Order\s*(?:No\.?)?\s*(?:&\s*Date)?\s*:?", "[BUYER_ORDER]"),
        (r"IEC\s+Code\s*:?", "[IEC_CODE]"),
        (r"REX\s+No\.?\s*:?", "[REX_NO]"),
        (r"U/?S\s*\d*\s*OF\s+CGST\s+ACT", "[CGST_ACT]"),
        (r"Exporter\s*:?", "[EXPORTER]"),
        # Bill of Lading phrases
        (r"Bill\s+of\s+Lading", "[BILL_OF_LADING]"),
        (r"Port\s+of\s+Loading", "[PORT_LOADING]"),
        (r"Port\s+of\s+Discharge", "[PORT_DISCHARGE]"),
        # Packing List phrases
        (r"Packing\s+List", "[PACKING_LIST]"),
        # Certificate phrases
        (r"Certificate\s+of\s+Origin", "[CERT_ORIGIN]"),
        # Common phrases
        (r"PREVIEW", "[PREVIEW]"),
        (r"Original", "[ORIGINAL]"),
        (r"Copy", "[COPY]"),
    ]
    
    # Extract found phrases
    found_phrases = []
    for pattern, token in key_phrases:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found_phrases.append(token)
            # Replace in text with token
            text = re.sub(pattern, token, text, flags=re.IGNORECASE)
    
    # Step 4: Mask variable content
    # Company names (ALL CAPS words, 2+ consecutive)
    text = re.sub(r'\b[A-Z][A-Z\s\.\,\&]{5,}(?:LTD|LIMITED|PVT|PRIVATE|INC|CORP|CO|LLC|B\.?V\.?|GMBH)?\b', '[COMPANY]', text)
    
    # Addresses (patterns with common address words)
    text = re.sub(r'\b(?:PLOT|SECTOR|ROAD|STREET|AVENUE|LANE|BUILDING|BLDG|FLOOR|SUITE|UNIT)\s*(?:No\.?)?\s*[A-Za-z0-9\-\,\s]+', '[ADDR]', text, flags=re.IGNORECASE)
    
    # Location codes (3-letter airport/port codes)
    text = re.sub(r'\b[A-Z]{3}\b', '[LOC]', text)
    
    # Numbers and codes
    text = re.sub(r'\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b', '[DATE]', text)
    text = re.sub(r'\b\d{3,}\b', '[NUM]', text)
    text = re.sub(r'\b[A-Z]{2,4}[\-]?\d{3,}\b', '[CODE]', text)
    
    # Step 5: Clean up and collapse tokens
    text = re.sub(r'(\[COMPANY\]\s*)+', '[COMPANY] ', text)
    text = re.sub(r'(\[ADDR\]\s*)+', '[ADDR] ', text)
    text = re.sub(r'(\[LOC\]\s*)+', '[LOC] ', text)
    text = re.sub(r'(\[NUM\]\s*)+', '[NUM] ', text)
    text = re.sub(r'(\[CODE\]\s*)+', '[CODE] ', text)
    text = re.sub(r'(\[DATE\]\s*)+', '[DATE] ', text)
    
    # Remove punctuation noise
    text = re.sub(r'[\,\.\:\;\-\_\*\#\&]+', ' ', text)
    
    # Final whitespace cleanup
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Step 6: If we found key phrases, prioritize them in output
    if found_phrases:
        # Create a structured output: key phrases first, then remaining text
        phrase_str = ' '.join(sorted(set(found_phrases)))
        # Limit remaining text to avoid noise
        remaining = text[:500] if len(text) > 500 else text
        return f"{phrase_str} | {remaining}"
    
    return text


def get_text_embedding(text, apply_mask=True):
    """
    Generate embedding for a single text. Use this to pre-compute embeddings.
    
    Args:
        text (str): Text to encode
        apply_mask (bool): Whether to apply mask_variable_content preprocessing
    
    Returns:
        numpy.ndarray: Embedding vector, or None if error
    """
    if not text:
        return None
    
    try:
        model = settings.SENTENCE_TRANSFORMERS_MODEL
        processed = mask_variable_content(text) if apply_mask else text
        return model.encode(processed, convert_to_numpy=True)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def calculate_embedding_similarity(embedding1, embedding2):
    """
    Calculate cosine similarity between two pre-computed embeddings.
    
    Args:
        embedding1 (numpy.ndarray): First embedding
        embedding2 (numpy.ndarray): Second embedding
    
    Returns:
        float: Similarity score between 0.0 and 1.0
    """
    if embedding1 is None or embedding2 is None:
        return 0.0
    
    try:
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cosine_similarity = dot_product / (norm1 * norm2)
        return max(0.0, min(1.0, float(cosine_similarity)))
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0


def calculate_text_similarity(text1, text2):
    """
    Calculate semantic similarity between two texts using cosine similarity with sentence embeddings.
    
    Args:
        text1 (str): First text to compare
        text2 (str): Second text to compare
    
    Returns:
        float: Similarity score between 0.0 and 1.0, where 1.0 is identical
    """
    if not text1 or not text2:
        return 0.0
    
    embedding1 = get_text_embedding(text1)
    embedding2 = get_text_embedding(text2)
    return calculate_embedding_similarity(embedding1, embedding2)



# Top parse positions (Left, Top, Right, Bottom)
def parse_pos(word_object):
    return [int(coordinate) for coordinate in word_object["pos"].split(",")]


def get_left_pos(word_object):
    return parse_pos(word_object)[0]


def get_right_pos(word_object):
    return parse_pos(word_object)[2]


def get_top_pos(word_object):
    return parse_pos(word_object)[1]


def get_bottom_pos(word_object):
    return parse_pos(word_object)[3]


def check_chunk(range_list, val1, val2, threshold, extra_space=0):
    """
    Check chunk threshold by using right and left pos of 2 object
    """
    val1_right_pos = val1["pos"].split(",")[2]
    val2_left_pos = val2["pos"].split(",")[0]

    val1_top_pos = val1["pos"].split(",")[1]
    val2_top_pos = val2["pos"].split(",")[1]

    difference = abs(int(val1_right_pos) - int(val2_left_pos))

    if threshold_check(int(val1_top_pos), int(val2_top_pos), int(threshold)):
        if int(difference) >= int(range_list[0]) and int(difference) <= (
            int(range_list[1]) + int(extra_space)
        ):
            return True
        else:
            return False
    else:
        return False


def threshold_check(num1, num2, check_threshold):
    """
    Check if the difference between 2 number is less than threshold
    """
    return abs(int(num1) - int(num2)) <= int(check_threshold)


def chunk_node_to_word(chunk_list):
    """
    Convert Chunks data(with POS) to Word only
    """
    words = []

    pos = [
        get_left_pos(chunk_list[0]),
        get_top_pos(chunk_list[0]),
        get_right_pos(chunk_list[-1]),
        get_bottom_pos(chunk_list[0]),
    ]

    pos = [str(x) for x in pos]

    for chunk in chunk_list:
        words.append(chunk["v"])

    page_id = chunk_list[0]["id"].split(".")[0]

    return [" ".join(words), ",".join(pos), page_id]


def construct_sentences(word_dict):
    space_unit = 10  # Pixels per space (adjustable)
    line_height = 25  # Average line height in pixels (adjustable)
    sentences = []
    lines = word_dict[0]

    # Collect all words with their positions
    words_info = []
    for line_key in lines:
        word_list = lines[line_key]
        for word_entry in word_list:
            word = word_entry[0]
            position = word_entry[1]
            left, top, right, bottom = map(int, position.split(","))
            words_info.append(
                {
                    "word": word,
                    "left": left,
                    "top": top,
                    "right": right,
                    "bottom": bottom,
                }
            )

    # Sort words by top position, then by left position
    words_info.sort(key=lambda x: (x["top"], x["left"]))

    # Initialize variables for tracking
    prev_line_num = None
    prev_bottom = None
    line_buffer = {}

    for word_info in words_info:
        # Calculate line number and character position
        line_num = int(word_info["top"] / line_height)
        char_pos = int(word_info["left"] / space_unit)

        # Handle vertical gaps
        if prev_line_num is not None and line_num > prev_line_num + 1:
            gap_lines = line_num - prev_line_num - 1
            for i in range(prev_line_num + 1, line_num):
                line_buffer[i] = ""  # Empty lines for gaps

        # Initialize line in buffer if not present
        if line_num not in line_buffer:
            line_buffer[line_num] = {}

        # Add word to line buffer at the calculated character position
        line_buffer[line_num][char_pos] = word_info["word"]

        prev_line_num = line_num
        prev_bottom = word_info["bottom"]

    # Build the final text lines
    max_line_num = max(line_buffer.keys())
    final_lines = []
    for i in range(max_line_num + 1):
        if i in line_buffer:
            line_content = line_buffer[i]
            # Build line string based on character positions
            if line_content:
                sorted_positions = sorted(line_content.keys())
                line_str = ""
                last_pos = 0
                for pos in sorted_positions:
                    spaces = pos - last_pos
                    line_str += " " * spaces + line_content[pos]
                    last_pos = pos + len(line_content[pos])
                final_lines.append(line_str.rstrip())
            else:
                final_lines.append("")
        else:
            final_lines.append("")  # Empty line

    # Remove leading and trailing empty lines
    while final_lines and not final_lines[0]:
        final_lines.pop(0)
    while final_lines and not final_lines[-1]:
        final_lines.pop()

    # Join lines into a single text
    return "\n".join(final_lines)


# Get Page Level Data
def chunk_process_level_page(
    PAGE, line_threshold=10, chunk_threshold=20, extra_chunk_space=10
):
    # Here we will hold data with chunking line also word only version
    data = dict()

    # Go through all the XML objects
    for PAGE_ID, PAGE in enumerate([PAGE]):

        # Extract all the W_nodes
        W_nodes = []

        def find_all_words(data):
            if isinstance(data, list):
                for elem1 in data:
                    find_all_words(elem1)
            elif isinstance(data, dict):
                for k, v in data.items():
                    if (k == "type") and (v == "word"):
                        W_nodes.append(data)
                    elif isinstance(v, list):
                        find_all_words(v)

        # Find All Word elements and put it into W_nodes
        find_all_words(PAGE["children"])

        # Turn All the Data into Lines with Chuncking
        word_space_list = []

        for index, W_node in enumerate(W_nodes):
            try:
                current_node_pos = W_node["pos"]
                current_node_right_pos = current_node_pos.split(",")[2]

                next_node_pos = W_nodes[index + 1]["pos"]
                next_node_left_pos = next_node_pos.split(",")[0]

                diffr = int(next_node_left_pos) - int(current_node_right_pos)

                if diffr < 0:
                    pass
                else:
                    word_space_list.append(diffr)

            except (IndexError, ValueError):
                pass

        if not W_nodes:
            continue

        # Only if there is only 1 word
        if (len(W_nodes) == 1) or word_space_list == []:
            word_space_list = [5]

        space_list = sorted(list(set(word_space_list)))

        space_range = [space_list[0], space_list[0] + 20]

        """
        Make Chunks
        """
        chunk_list = []

        start_idx = 0
        end_idx = len(W_nodes)

        while True:
            temp_chunk = []

            while True:
                try:
                    check = check_chunk(
                        space_range,
                        W_nodes[start_idx],
                        W_nodes[start_idx + 1],
                        chunk_threshold,
                        extra_chunk_space,
                    )
                #
                except IndexError:
                    start_idx = start_idx + 1
                    if start_idx >= end_idx:
                        temp_chunk.append(W_nodes[start_idx - 1])
                    break

                if check == True:
                    temp_chunk.append(W_nodes[start_idx])

                    start_idx = start_idx + 1
                else:
                    temp_chunk.append(W_nodes[start_idx])
                    start_idx = start_idx + 1
                    break

            if temp_chunk != []:
                chunk_list.append(temp_chunk)

            if start_idx >= end_idx:
                break

        chunk_data = []

        for chunk in chunk_list:
            chunk_data.append(chunk_node_to_word(chunk))

        """
        Turn Data into Proper Lines
        """

        left_pos_holder = []
        top_pos_holder = []

        for chunk in chunk_data:
            left_pos_holder.append(int(chunk[1].split(",")[0]))

            top_pos_holder.append(int(chunk[1].split(",")[1]))

        sorted_top_pos_holder = sorted(set(top_pos_holder))

        # Extra Check Threshold 5 times
        for _ in range(5):
            for index, i in enumerate(sorted_top_pos_holder):
                if index != 0:
                    check = threshold_check(
                        sorted_top_pos_holder[index],
                        sorted_top_pos_holder[index - 1],
                        line_threshold,
                    )
                    if check:
                        sorted_top_pos_holder.remove(i)

        unique_line_data = dict()

        for i in sorted_top_pos_holder:
            unique_line_data[str(i)] = []

        """
        for chunk in chunk_data:
            top_pos = int(chunk[1].split(",")[1])
            for key in unique_line_data.keys():
                check = threshold_check(int(key), top_pos, line_threshold)
                if check:
                    if chunk[0].strip() != "":
                        unique_line_data[key].append([chunk[0], chunk[1], chunk[2], int(chunk[1].split(",")[0])])
                        
        """
        prev_positions = set()
        for chunk in chunk_data:
            top_pos = int(chunk[1].split(",")[1])
            for key in unique_line_data.keys():
                check = threshold_check(int(key), top_pos, line_threshold)
                if prev_positions:
                    if chunk[1] in prev_positions:
                        check = False
                if check:
                    if chunk[0].strip() != "":
                        unique_line_data[key].append(
                            [chunk[0], chunk[1], chunk[2], int(chunk[1].split(",")[0])]
                        )
                        prev_positions.add(chunk[1])  # using add() for a set

        # Remove if the line is empty
        for i in sorted_top_pos_holder:
            try:
                if len(unique_line_data[str(i)]) == 0:
                    del unique_line_data[str(i)]

                # Remove if a line have only a chunk and chunk have only 1 char
                if len(unique_line_data[str(i)]) == 1:
                    if len(unique_line_data[str(i)][0][0].strip()) == 1:
                        del unique_line_data[str(i)]
            except:
                pass

        for i in sorted_top_pos_holder:
            try:
                unique_line_data[str(i)] = sorted(
                    unique_line_data[str(i)], key=lambda left_pos: left_pos[3]
                )
            except:
                pass

        for i in sorted_top_pos_holder:
            try:
                for j in unique_line_data[str(i)]:
                    j.pop()
            except:
                pass

        data[PAGE_ID] = unique_line_data

    return data


def get_ra_json_to_txt(page_data):
    try:
        # RAJSON = RAJson()
        # page_data = RAJSON.process_PAGE(path_to_xml)
        chunk_page_data = chunk_process_level_page(page_data)
        text_data = construct_sentences(chunk_page_data)
        return text_data
    except:
        return ""
        pass


def normalize_document_text(text: str) -> str:

    text = re.sub(r"[\$€£¥]?\s?\d{1,3}(?:[,.]\d{3})*(?:[.,]\d{2})?", "[AMOUNT]", text)
    text = re.sub(
        r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\w{3}\s\d{1,2},\s\d{4}", "[DATE]", text
    )
    text = re.sub(r"\b\d{5,}\b", "[NUMBER]", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def chunk_text(text, max_chars=1000):
    """Split text into chunks of approximately max_chars characters"""
    chunks = []
    for i in range(0, len(text), max_chars):
        chunks.append(text[i : i + max_chars])
    return chunks


def find_similar_document_and_get_params(new_document_text):
    
    normalized_query_text = normalize_document_text(new_document_text)

    if len(normalized_query_text) > 1000:
        search_text = normalized_query_text[:1000]
        print(f"Using first 1000 characters of normalized text for search")
    else:
        search_text = normalized_query_text

   
    return search_text


def get_exceptions(document):
    
    template_text = get_ra_json_to_txt(document["children"][0])
    print(f"Document text length: {len(template_text)} characters")

    retrieved_params = find_similar_document_and_get_params(template_text)
    return  retrieved_params



def get_layout_id(batch_instance, document):
    """
    Get or create layout_id based on document pattern matching.
    
    Logic:
    1. Extract and normalize the document pattern
    2. Search for existing definitions with similar patterns
    3. If match found (above similarity threshold), return existing layout_id
    4. If no match, create new definition with new layout_id and save pattern
    
    Performance optimizations:
    - Pre-compute embedding for new document once
    - Batch encode all stored patterns in single model call
    - Use vectorized similarity computation
    - LRU cache for masked patterns
    - In-memory cache for embeddings
    - Conditional debug logging
    
    Args:
        batch_instance: Batch instance with definition_id and other attributes
        document: Document to process
    """
    try:
        # Get current model version for cache invalidation
        current_model_version = _get_model_version()
        
        # Validate inputs
        if not batch_instance or not hasattr(batch_instance, 'definition_id'):
            print("Error: batch_instance is invalid or missing definition_id")
            return None
        
        if not document:
            print("Error: document is None or empty")
            return None
        
        # Extract batch attributes once
        definition_id = batch_instance.definition_id
        vendor = getattr(batch_instance, 'vendor', '') or ''
        doc_type = getattr(batch_instance, 'type', '') or ''
        name_matching_text = getattr(batch_instance, 'name_matching_text', '') or ''
        
        # Get the normalized text pattern from the document
        normalized_pattern = get_exceptions(document)
        
        # Validate that we got a pattern
        if not normalized_pattern or not normalized_pattern.strip():
            print("Warning: Normalized pattern is empty. Creating definition without pattern matching.")
            new_layout_id = str(uuid.uuid4())
            Definition.objects.create(
                definition_id=definition_id,
                layout_id=new_layout_id,
                hash_layout=[],
                vendor=vendor,
                type=doc_type,
                name_matching_text=name_matching_text
            )
            print(f"Created new definition (empty pattern) with layout_id: {new_layout_id}")
            return new_layout_id
        
        # Fetch existing definitions with valid hash_layout
        # Performance: Use exact match and fetch embedding data
        existing_definitions = list(Definition.objects.filter(
            definition_id=definition_id
        ).exclude(
            hash_layout=[]
        ).exclude(
            hash_layout__isnull=True
        ).only('id', 'layout_id', 'hash_layout', 'embedding', 'embedding_model_version'))
        
        # If no existing definitions, create new one directly
        if not existing_definitions:
            print("No existing definitions found. Creating new definition.")
            new_layout_id = str(uuid.uuid4())
            Definition.objects.create(
                definition_id=definition_id,
                layout_id=new_layout_id,
                hash_layout=[normalized_pattern],
                vendor=vendor,
                type=doc_type,
                name_matching_text=name_matching_text
            )
            print(f"Created new definition with layout_id: {new_layout_id}")
            return new_layout_id
        
        # Prepare texts for batch encoding with caching
        new_pattern_masked = mask_variable_content(normalized_pattern)
        layout_ids = []
        stored_embeddings_cached = []
        patterns_to_encode = [new_pattern_masked]
        
        # Load embeddings from database (much faster than encoding)
        # Only compute mask when embedding is NOT in database
        definitions_to_update = []  # Track definitions that need embedding updates
        valid_definitions_count = 0
        
        for definition in existing_definitions:
            if definition.hash_layout and definition.hash_layout[0]:
                valid_definitions_count += 1
                layout_ids.append(definition.layout_id)
                
                # Try to load embedding from database FIRST
                db_embedding = _get_embedding_from_db(definition, current_model_version)
                
                if db_embedding is not None:
                    # Embedding exists - no need to mask! (faster path)
                    stored_embeddings_cached.append(db_embedding)
                else:
                    # Embedding not in DB - need to mask and encode
                    pattern = definition.hash_layout[0]
                    masked = mask_variable_content(pattern)
                    patterns_to_encode.append(masked)
                    stored_embeddings_cached.append(None)
                    definitions_to_update.append(definition)
        
        if valid_definitions_count == 0:
            print("No valid stored patterns found. Creating new definition.")
            new_layout_id = str(uuid.uuid4())
            Definition.objects.create(
                definition_id=definition_id,
                layout_id=new_layout_id,
                hash_layout=[normalized_pattern],
                vendor=vendor,
                type=doc_type,
                name_matching_text=name_matching_text
            )
            print(f"Created new definition with layout_id: {new_layout_id}")
            return new_layout_id
        
        # Batch encode only texts that are not cached
        # MAJOR performance improvement: Skip encoding for cached embeddings
        model = settings.SENTENCE_TRANSFORMERS_MODEL
        
        if len(patterns_to_encode) > 1:
            # Some patterns need encoding (new doc + missing embeddings)
            encoded = model.encode(patterns_to_encode, convert_to_numpy=True, show_progress_bar=False)
            
            # First embedding is always the new document
            new_doc_embedding = encoded[0]
            
            # Fill in the stored embeddings and save to database
            encode_idx = 1
            stored_embeddings = []
            for i, cached_emb in enumerate(stored_embeddings_cached):
                if cached_emb is not None:
                    stored_embeddings.append(cached_emb)
                else:
                    emb = encoded[encode_idx]
                    stored_embeddings.append(emb)
                    # Save to database for persistent storage
                    if encode_idx - 1 < len(definitions_to_update):
                        definition_to_update = definitions_to_update[encode_idx - 1]
                        _save_embedding_to_db(definition_to_update, emb, current_model_version, save_now=True)
                    encode_idx += 1
            
            stored_embeddings = np.array(stored_embeddings)
        else:
            # All stored embeddings were loaded from database (fastest path!)
            # Only need to encode the new document pattern
            new_doc_embedding = model.encode([new_pattern_masked], convert_to_numpy=True, show_progress_bar=False)[0]
            stored_embeddings = np.array(stored_embeddings_cached)
        
        # Vectorized similarity computation using matrix operations
        # Normalize embeddings for cosine similarity
        new_norm = np.linalg.norm(new_doc_embedding)
        if new_norm == 0:
            print("Warning: New document embedding has zero norm. Creating new definition.")
            new_layout_id = str(uuid.uuid4())
            Definition.objects.create(
                definition_id=definition_id,
                layout_id=new_layout_id,
                hash_layout=[normalized_pattern],
                vendor=vendor,
                type=doc_type,
                name_matching_text=name_matching_text
            )
            return new_layout_id
        
        new_doc_normalized = new_doc_embedding / new_norm
        
        # Compute all similarities at once using dot product
        stored_norms = np.linalg.norm(stored_embeddings, axis=1, keepdims=True)
        stored_norms[stored_norms == 0] = 1  # Avoid division by zero
        stored_normalized = stored_embeddings / stored_norms
        similarities = np.dot(stored_normalized, new_doc_normalized)
        
        threshold = settings.LAYOUT_SIMILARITY_THRESHOLD
        
        # Find best match
        best_idx = np.argmax(similarities)
        best_score = float(similarities[best_idx])
        best_layout_id = layout_ids[best_idx]
        
        # Conditional debug logging (only when debug=True)
        if settings.DEBUG:
            for i, (layout_id, score) in enumerate(zip(layout_ids, similarities)):
                print(f"[DEBUG] Comparing with layout_id: {layout_id}, Similarity: {float(score):.4f}")
        
        # Check if best match exceeds threshold
        if best_score >= threshold:
            print(f"Match found! Using existing layout_id: {best_layout_id}")
            return best_layout_id
        
        # No match found - create new definition with embedding
        print(f"No match above threshold. Best was {best_layout_id} at {best_score:.4f}")
        print("Creating new definition with new layout_id.")
        
        new_layout_id = str(uuid.uuid4())
        new_definition = Definition.objects.create(
            definition_id=definition_id,
            layout_id=new_layout_id,
            hash_layout=[normalized_pattern],
            vendor=vendor,
            type=doc_type,
            name_matching_text=name_matching_text
        )
        
        # Save the embedding to the new definition
        _save_embedding_to_db(new_definition, new_doc_embedding, current_model_version, save_now=True)
        
        print(f"Created new definition with layout_id: {new_layout_id}")
        return new_layout_id
        
    except Exception as e:
        print(f"Error in get_layout_id: {str(e)}")
        import traceback
        traceback.print_exc()
        return None