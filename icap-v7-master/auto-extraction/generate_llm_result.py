
import os
import requests
import json
import copy
from xml_or_ra_json_to_text import get_xml_to_text, get_ra_json_to_txt_kvv, get_ra_json_to_txt_table_old, get_ra_json_to_txt_table_new
from llm_clients import run_llm

LLM_SERVICE_API_URL = os.getenv("LLM_SERVICE_API_URL")

PROMPT_TEMPLATE = """<|begin_of_text|>
<|start_header_id|>system<|end_header_id|>
{system_prompt}
<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{prompt}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""

SYSTEM_PROMPT_KVV = """You are an AI language model designed to extract Vendor and Key-Value pairs from documents.The given text has appropiate spacing between word and sentence so that you can understand the document layout very appropiately. Given the following text data from a page, perform the following tasks:

### Tasks:
    
    1.Vendor Identification:
        -Extract the Vendor, which is the company that created the document.
        -Note: The vendor field should contain only a single value (e.g., the name of the company).
    
    2.Key-Value Pair Extraction:
        -Extract all Key-Value Pairs.
        -Keys are labels or headings.
        -Values are the associated data, which may span one or multiple lines.
        -Must analysis for multi line values to combine them
        -Must combine multiline address given below a company name with the company
        -Do not Add Key value those are in any table (You can first identify table area then for excluding the table keys from the result)
        -Many different key can have same values. so do not exclude those key value pairs
        
### Output Format:
Provide the extracted data in the following consistent JSON format:
 {
    "vendor": "Vendor data",
    "key-value": [
        {
            "key": "Key name",
            "value": "key associated value"
        },
        // Repeat for all key-value pairs, strictly maintain format that one set key value pairs should be in one dictionary.
        ]
 }
    
### Importants
 - DO NOT ADD EXTRA WORDS or SENTENCES FROM YOU WHEN YOU GENERATE THE OUTPUT, ONLY GENERATE THE JSON WITH APPROPIATE STRUCTURE MENTIONED in output format without any extra data.
 - Very Deeply analysis the document to extract all the key-value pair correctly.    
 - DO NOT ADD TABLE KEY VALUE PAIRS in key value list of your output THAT IS THE KEY VALUES, THOSE STAY IN A TABLE  
"""





SYSTEM_PROMPT_KVV_AGENT = """You are an AI language model specialized in extracting structured information from documents. You must analyze the provided text thoroughly and extract ALL vendor information and key-value pairs with high accuracy and consistency.

## Input Understanding
The provided text maintains appropriate spacing between words and sentences to preserve document layout. Use this spatial information to understand the document structure.

## Task 1: Vendor Identification
- **Definition**: The vendor is the company/organization that created or issued the document
- **Location hints**: Look for company names in headers, logos area, letterhead, "From:" fields, or signature blocks
- **Output**: Single company name only (not addresses or other details)

## Task 2: Key-Value Pair Extraction

### Extraction Rules:
1. **Comprehensive Coverage**: Extract EVERY key-value pair visible in the document
2. **Key Definition**: Any label, heading, or field name followed by associated data
3. **Value Definition**: The data associated with a key, which may be:
   - Single line (e.g., "Date: 01/15/2024")
   - Multi-line (e.g., addresses, descriptions)
   - Empty/blank (still include with empty string value)

### Critical Instructions:
- **Multi-line Values**: MUST combine all lines belonging to the same value
- **Company Addresses**: When an address appears below a company name, combine them as a single key-value pair
- **Duplicate Values**: Multiple keys CAN have the same value - include all instances
- **Tables**: EXCLUDE any key-value pairs that appear within table structures
- **Empty Values**: Include keys even if their values are blank/empty

### Table Identification:
Before extraction, identify table regions by looking for:
- Grid-like structures with rows and columns
- Repeated column headers
- Aligned data in columnar format
Mark these regions and exclude their content from key-value extraction.

## Output Requirements

### Format:
{
    "vendor": "Company Name Here",
    "key-value": [
        {
            "key": "Exact key text",
            "value": "Complete value text"
        }
    ]
}

### Strict Rules:
1. Output ONLY the JSON structure - no explanations or additional text
2. Each key-value pair MUST be a separate dictionary object
3. Preserve exact text from the document (no paraphrasing)
4. Include ALL key-value pairs found (except those in tables)
5. Maintain consistent extraction across similar documents

## Quality Checklist:
Before finalizing output, verify:
- [ ] All visible key-value pairs extracted (except tables)
- [ ] Multi-line values properly combined
- [ ] No table data included
- [ ] Vendor correctly identified
- [ ] JSON format is valid
- [ ] No missing or partial extractions

## Remember: Consistency is critical. If you extract 20 key-value pairs from one document, similar documents should yield similar counts."""




LIGHT_PROMPT_KVV_AGENT = """
You are an AI that extracts structured data from OCR documents.

1. Identify the vendor (company/organization issuing the document).
2. Extract all key-value pairs outside of tables. Tables contain rows/columns and should be ignored.
3. Combine multi-line values.
4. Output only JSON format like:
{
  "vendor": "Vendor Name",
  "key-value": [
    {"key": "Key1", "value": "Value1"},
    {"key": "Key2", "value": "Value2"}
  ]
}
"""




SYSTEM_PROMPT_TABLE = """You are an AI language model designed to extract all table data from given text documents.The given text has appropiate spacing between word and sentence and contains multiple pages so that you can understand the document layout very appropiately.

## Tasks
    - Extract all Tables from the document, including any that appear at the beginning.
    - For each table, capture all column headers of the table and Each row's data, where values can span one or multiple lines.
    - Assign appropriate labels from the headers to each value.
    - Include All Tables: Ensure that no tables are omitted.
    - Extract any summary information (totals, subtotals, VAT/tax) into a separate summary_table.
    - Handle Multiple Tables across Multiple Pages appropriately.
    - If a table continues in multiple pages handle it appropiately.
    
### Output Format:
{
    'Table 1': {
        'row1': [['value 1 from row 1', 'column label for value 1'], ['value 2 from row 1', 'column label for value 2'], //Other Values ],
        'row2': [['value 1 from row 2', 'column label for value 1'], ['value 2 from row 2', 'column label for value 2'], //Other Values ],
        //Other rows
    },
    ...  # Repeat for other tables
    'Summary Table 1': {
        'row1': [['summary value 1', 'summary label 1 of value 1'],['summary value 2', 'summary label 2 of value 2'], //Other Values]  # Include all summary data if presents
    }
}

## Importants
 - DO NOT ADD EXTRA WORDS or SENTENCES FROM YOU WHEN YOU GENERATE THE OUTPUT, ONLY GENERATE THE JSON WITH APPROPIATE STRUCTURE MENTIONED in output format without any extra data.
 - Very Deeply analysis the document to extract all the tables correctly.   
"""







#########################


SYSTEM_PROMPT_ADDRESS_PARSER = """
# YOU ARE AN ULTRA-STRICT ADDRESS PARSING SYSTEM

This system extracts address, organization, and contact details from free-form input strings. It must follow these rules strictly and output only the parsed extraction in the JSON format specified below. **Do not include any example data, sample outputs, or additional text in the final result. Only output the final JSON extraction.**

## FIELD CONSTRAINTS TABLE

| JSON Path                | Type   | Max Length | Validation Rules                                                                                                                                                                                                                                             |
|--------------------------|--------|------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| name                     | string | 100        | Extract the organization name from the start of the input up to the first **clear address marker** (e.g., "HRL", "3PL", street names, etc.). **Ensure that no address components are included.** Only retain the organization name. |               
| addressShortCode         | string | 25         | Internal code format: **exactly 2–5 letters immediately followed by 1–3 digits (regex: `^[A-Za-z]{2,5}[0-9]{1,3}$`)**. Extract if found anywhere in the input. If no matching pattern exists, set to empty string.    |
| accountNumber            | string | 25         | Extract the first token if it appears to be an account code (letters + digits OR just digits at the beginning). If no clear code pattern exists at the start, set to empty string.    |
| address.addressLine1     | string | 50         | Extract the **core street address** (e.g., "Earl Bakkenstraat 7", "5300 Airways Blvd"). This should be the actual physical street address. |
| address.addressLine2     | string | 50         | Extract **secondary logistics/facility information** (e.g., "HRL 3 | Inbound | 1680", "3PL"). This is for warehouse locations, building identifiers, or other non-street address details. |
| address.postalCode       | string | 10         | Extract postal code with **country-specific formatting**. US: keep hyphens (e.g., "02048-1139"). Netherlands: keep space and letters (e.g., "6422 PJ"). |
| address.city             | string | 50         | Extract the city name. **Ensure that the city name does not contain numbers or country names.** |
| address.stateProvince    | string | 25         | Extract state/province code for countries that use them (e.g., US states). **Leave empty for countries without states/provinces** (e.g., Switzerland, Netherlands). |
| address.countryCode      | string | 2          | Extract from an explicit country name (e.g., "USA", "SWITZERLAND") and convert it to a **two-letter ISO code**. |
| contact.name             | string | 256        | Extract text **following the "Contact:" marker**. **Ensure that organization names are NOT included.** |
| contact.phone            | string | 20         | Extract phone number, ensuring it includes the country code. Convert "ext" to "x". |
| contact.email            | string | 254        | Extract a valid email format, ensuring the domain part is in lowercase. |

## PARSING SEQUENCE AND LOGIC

1. **Extract Account Number:**
   - Check if the first token is a potential account code (can be letters+digits OR just digits)
   - If it looks like an account code, extract it; otherwise, set to empty string

2. **Extract Address Short Code:**
   - Search for pattern matching exactly 2-5 letters followed by 1-3 digits (e.g., "ABC12", "DEFGH123")
   - Can appear anywhere in the input string
   - If no matching pattern found, set to empty string

3. **Extract Organization Name:**
   - Identify the organization name after any account number
   - Stop at clear address markers like "HRL", "3PL", street names, or street numbers

4. **Separate Address Components:**
   - **addressLine1:** Extract the actual street address (street name and number)
   - **addressLine2:** Extract facility/warehouse identifiers, logistics information
   - Key rule: Street addresses go to line1, logistics/facility info goes to line2

5. **Extract Location Identifiers:**
   - **Postal Code:** Keep country-specific formatting (US with hyphens, Dutch with space and letters)
   - **City:** Text that clearly represents a city name
   - **State/Province:** Only for countries that use them (e.g., US states). Leave empty for others
   - **Country:** Convert country names to ISO codes

6. **Handle Country-Specific Patterns:**
   - US addresses: Include state codes, postal codes with hyphens
   - Dutch addresses: Postal codes with format "NNNN AA", no state/province
   - Swiss addresses: Simple numeric postal codes, no state/province

## EXAMPLE PARSING

### Example 1
**Input:** `OU1083 COVIDIEN LP 15 Hampshire St MANSFIELD MA 02048-1139 USA`

**Output:**
```json
{
  "name": "COVIDIEN LP",
  "addressShortCode": "",
  "accountNumber": "OU1083",
  "address": {
    "addressLine1": "15 Hampshire St",
    "addressLine2": "",
    "postalCode": "02048-1139",
    "city": "MANSFIELD",
    "stateProvince": "MA",
    "countryCode": "US"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```

**Parsing Logic:**
- `OU1083` is extracted as accountNumber (letters + digits at start)
- addressShortCode is empty (no pattern matching 2-5 letters + 1-3 digits found)
- `COVIDIEN LP` is the organization name (after account number, before street number "15")
- `15 Hampshire St` is the street address → addressLine1
- No secondary/logistics info → addressLine2 is empty
- `02048-1139` is the US postal code (keep hyphen)
- `MANSFIELD` is the city
- `MA` is the state code (US uses states)
- `USA` → `US` (country code conversion)


### Example 2
**Input:** `3120 Covidien AG Victor von Bruns-Strasse 19 8212 NEUHAUSEN AM RHEINFALL SWITZERLAND EORI FRCH424062396`

**Output:**
```json
{
  "name": "Covidien AG",
  "addressShortCode": "",
  "accountNumber": "3120",
  "address": {
    "addressLine1": "Victor von Bruns-Strasse 19",
    "addressLine2": "",
    "postalCode": "8212",
    "city": "NEUHAUSEN AM RHEINFALL",
    "stateProvince": "",
    "countryCode": "CH"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```

**Parsing Logic:**
- `3120` is extracted as accountNumber (pure digits at start)
- addressShortCode is empty (no pattern matching 2-5 letters + 1-3 digits found)
- `Covidien AG` is the organization name (after account number, before street name)
- `Victor von Bruns-Strasse 19` is the street address → addressLine1
- No secondary/logistics info → addressLine2 is empty
- `8212` is the Swiss postal code (simple numeric format)
- `NEUHAUSEN AM RHEINFALL` is the city
- stateProvince is empty (Switzerland doesn't use states)
- `SWITZERLAND` → `CH` (country code conversion)
- `EORI FRCH424062396` is ignored as extra data

### Example 3
**Input:** `C1680 Medtronic c/o CEVA Logistics HRL 3 | Inbound | 1680 HRL 3 Earl Bakkenstraat 7 6422 PJ HEERLEN NETHERLANDS`

**Output:**
```json
{
  "name": "Medtronic c/o CEVA Logistics",
  "addressShortCode": "",
  "accountNumber": "C1680",
  "address": {
    "addressLine1": "Earl Bakkenstraat 7",
    "addressLine2": "HRL 3 | Inbound | 1680 HRL 3",
    "postalCode": "6422 PJ",
    "city": "HEERLEN",
    "stateProvince": "",
    "countryCode": "NL"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```

**Parsing Logic:**
- `C1680` is extracted as accountNumber (letter + digits pattern)
- addressShortCode is empty (C1680 has 1 letter + 4 digits, doesn't match required 2-5 letters + 1-3 digits)
- `Medtronic c/o CEVA Logistics` is the organization name (stops at "HRL" marker)
- `Earl Bakkenstraat 7` is the street address → addressLine1
- `HRL 3 | Inbound | 1680 HRL 3` is logistics/facility info → addressLine2
- `6422 PJ` is the Dutch postal code (keep space and letters - format NNNN AA)
- `HEERLEN` is the city
- stateProvince is empty (Netherlands doesn't use states)
- `NETHERLANDS` → `NL` (country code conversion)

### Example 4
**Input:** `MEDTRONIC C/O CEVA LOGISTICS HRL 3 |INBOUND | 1680 EARL BAKKENSTRAAT 7 6422 PJ HEERLEN NETHERLANDS`

**Output:**
```json
{
  "name": "MEDTRONIC C/O CEVA LOGISTICS",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "EARL BAKKENSTRAAT 7",
    "addressLine2": "HRL 3 |INBOUND | 1680",
    "postalCode": "6422 PJ",
    "city": "HEERLEN",
    "stateProvince": "",
    "countryCode": "NL"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```

**Parsing Logic:**
- No account number at the beginning → accountNumber is empty
- addressShortCode is empty (no pattern matching 2-5 letters + 1-3 digits found)
- `MEDTRONIC C/O CEVA LOGISTICS` is the organization name (stops at "HRL" marker)
- `EARL BAKKENSTRAAT 7` is the street address → addressLine1
- `HRL 3 |INBOUND | 1680` is logistics/facility info → addressLine2
- `6422 PJ` is the Dutch postal code (format NNNN AA)
- `HEERLEN` is the city
- stateProvince is empty (Netherlands doesn't use states)
- `NETHERLANDS` → `NL` (country code conversion)

### Example 5
**Input:** `LU1881 Covidien LP Central DC 3PL 5300 Airways Blvd MEMPHIS TN 38116 USA`

**Output:**
```json
{
  "name": "Covidien LP Central DC",
  "addressShortCode": "",
  "accountNumber": "LU1881",
  "address": {
    "addressLine1": "3PL 5300 Airways Blvd",
    "addressLine2": "",
    "postalCode": "38116",
    "city": "MEMPHIS",
    "stateProvince": "TN",
    "countryCode": "US"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```

**Parsing Logic:**
- `LU1881` is extracted as accountNumber (letters + digits pattern)
- addressShortCode is empty (LU1881 has 2 letters + 4 digits, doesn't match required 2-5 letters + 1-3 digits)
- `Covidien LP Central DC` is the organization name (stops at "3PL" marker)
- `3PL 5300 Airways Blvd` includes facility marker + street → all goes to addressLine1
- No additional logistics info → addressLine2 is empty
- `38116` is the US postal code
- `MEMPHIS` is the city
- `TN` is the state code (US uses states)
- `USA` → `US` (country code conversion)

### Example 6
**Input:** `COVIDIEN LP CENTRAL DC 5300 AIRWAYS BLVD MEMPHIS TN 38116 UNITED STATES`

**Output:**
```json
{
  "name": "COVIDIEN LP CENTRAL DC",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "5300 AIRWAYS BLVD",
    "addressLine2": "",
    "postalCode": "38116",
    "city": "MEMPHIS",
    "stateProvince": "TN",
    "countryCode": "US"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```

**Parsing Logic:**
- No account number at the beginning → accountNumber is empty
- addressShortCode is empty (no pattern matching 2-5 letters + 1-3 digits found)
- `COVIDIEN LP CENTRAL DC` is the organization name (before street number "5300")
- `5300 AIRWAYS BLVD` is the street address → addressLine1
- No secondary/logistics info → addressLine2 is empty
- `38116` is the US postal code
- `MEMPHIS` is the city
- `TN` is the state code
- `UNITED STATES` → `US` (country code conversion)


### Example 7
**Input:** 'MEDTRONIC 1860 OUTER LOOP DOOR 434 LOUISVILLE KY 40219 US'

**Output:**
```json
{
  "name": "MEDTRONIC",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "1860 OUTER LOOP DOOR 434",
    "addressLine2": "",
    "postalCode": "40219",
    "city": "LOUISVILLE",
    "stateProvince": "KY",
    "countryCode": "US"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```

## Example 8
**Input:** `Covidien LP Juarez (MMJ) MFG SPACEI BORDER LOGISTICS EL PASO TX 79927 USA`

**Output:**
```json
{
  "name": "Covidien LP Juarez (MMJ) MFG",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "SPACEI BORDER LOGISTICS",
    "addressLine2": "",
    "postalCode": "79927",
    "city": "EL PASO",
    "stateProvince": "TX",
    "countryCode": "US"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```

Parsing Logic:
- No account number at start → accountNumber = ""
- addressShortCode is empty (no pattern matching 2-5 letters + 1-3 digits found)
- Covidien LP Juarez (MMJ) MFG is the organization name - includes "(MMJ)" parenthetical info and stops after "MFG"
- Why stop at MFG? "SPACEI BORDER LOGISTICS" is clearly a facility/location name, not part of company name
- SPACEI BORDER LOGISTICS is the facility/address name → addressLine1
- No secondary address info → addressLine2 = ""
- 79927 is the US postal code (5 digits)
- EL PASO is the city
- TX is the state code (Texas)
- USA → US (country code conversion)
- No contact information present

- KEY POINT: When organization name includes location (Juarez) and type (MFG), the actual facility/logistics center name (SPACEI BORDER LOGISTICS) becomes the address

## Example 9
**Input:** `MEDTRONIC B.V. EARL BAKKENSTRAAT 10 SITE 1030 HEERLEN 6422 PJ NL TE +31455668000 MEDTRONIC COT TEAM EORI No. NL001686987`

**Output:**
```json
{
  "name": "MEDTRONIC B.V.",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "EARL BAKKENSTRAAT 10",
    "addressLine2": "SITE 1030",
    "postalCode": "6422 PJ",
    "city": "HEERLEN",
    "stateProvince": "",
    "countryCode": "NL"
  },
  "contact": {
    "name": "MEDTRONIC COT TEAM",
    "phone": "+31455668000",
    "email": ""
  }
}
```

Parsing Logic:
- No account number at start → accountNumber = ""
- addressShortCode is empty (no pattern matching 2-5 letters + 1-3 digits found)
- MEDTRONIC B.V. is the organization name - STOPS at "B.V." because it's a legal entity marker
- "BAKKENSTRAAT" contains "STRAAT" (Dutch for "street") → This confirms it's an address, not company name
- EARL BAKKENSTRAAT 10 is the street address → addressLine1
- SITE 1030 is the facility/site identifier → addressLine2
- 6422 PJ is the Dutch postal code (format: NNNN AA with space)
- HEERLEN is the city
- No state/province (Netherlands doesn't use states) → stateProvince = ""
- NL is already the country code for Netherlands
- TE +31455668000 → "TE" marks the phone number
- MEDTRONIC COT TEAM is the contact name (appears after phone)
- EORI No. NL001686987 is ignored (tax/customs registration number)

- CRITICAL: "B.V." = Dutch legal entity marker (like "LTD" in English). Organization name MUST stop here!


## Example 10
**Input:** `Medtronic c/o CEVA Logistics Earl Bakkenstraat 7-15 PJ HEERLEN 6422 NETHERLANDS 3 I Inbound 1680 HRL`

**Output:**
```json
{
  "name": "Medtronic c/o CEVA Logistics",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "Earl Bakkenstraat 7-15",
    "addressLine2": "3 I Inbound 1680 HRL",
    "postalCode": "6422 PJ",
    "city": "HEERLEN",
    "stateProvince": "",
    "countryCode": "NL"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```
Parsing Logic:
- No account number at start → accountNumber = ""
- Medtronic c/o CEVA Logistics is the organization name - STOPS at "Earl" because "BAKKENSTRAAT" contains "STRAAT" (street)
- Earl Bakkenstraat 7-15 is the street address → addressLine1
- 3 I Inbound 1680 HRL is facility/warehouse info (appears after country) → addressLine2
- TRICKY: Postal code "6422 PJ" is split in input - "PJ" appears after street, "6422" appears after city
- HEERLEN is the city
- NETHERLANDS → NL (country code conversion)
- No contact information present

## Example 11:
Input: Global Forwarding Israel Ltd. 2 Rakefet St. North Industrial Zoni Shoham, 6083706 Israel
Output:
```json
{
  "name": "Global Forwarding Israel Ltd.",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "2 Rakefet St.",
    "addressLine2": "North Industrial Zoni",
    "postalCode": "6083706",
    "city": "Shoham",
    "stateProvince": "",
    "countryCode": "IL"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```
Parsing Logic:
- No account number at start → accountNumber = ""
- Global Forwarding Israel Ltd. is the organization name - STOPS at "Ltd." (legal entity marker)
- 2 Rakefet St. is the street address → addressLine1
- North Industrial Zoni is the zone/area info → addressLine2
- 6083706 is the Israeli postal code (7 digits)
- Shoham is the city (appears before comma)
- No state/province (Israel doesn't use states) → stateProvince = ""
- Israel → IL (country code conversion)
- No contact information present


## Example 12:
**Input:** `GIVEN IMAGING LTD. HERMON BUILDING ILIT YOKNEAM POB 258,NEW IND PARK, 3RD FLOOR`

**Output:**
```json
{
  "name": "GIVEN IMAGING LTD.",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "HERMON BUILDING, 3RD FLOOR",
    "addressLine2": "ILIT, POB 258, NEW IND PARK",
    "postalCode": "",
    "city": "YOKNEAM",
    "stateProvince": "",
    "countryCode": ""
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```
Parsing Logic:
- No account number at start → accountNumber = ""
- addressShortCode is empty (no pattern matching 2-5 letters + 1-3 digits found)
- GIVEN IMAGING LTD. is the organization name - STOPS at "LTD." (legal entity marker)
- HERMON BUILDING is a building name, not part of company → goes to address
- 3RD FLOOR is floor info → combined with building in addressLine1
- ILIT appears to be area/street name → addressLine2
- POB 258 (Post Office Box 258) → addressLine2
- NEW IND PARK (New Industrial Park) → addressLine2
- YOKNEAM is the city
- No postal code visible → postalCode = ""
- No state/province → stateProvince = ""
- No country mentioned → countryCode = ""
- No contact information present

- KEY POINTS:
-Building names (HERMON BUILDING) come after legal entity markers, so they're part of address
-POB = Post Office Box
-IND = Industrial (abbreviated)
-When multiple location elements exist, group logically: building/floor together, POB/area together

## Example 13:
**Input:** `COVIDIEN (ISRAEL)LTD NOTIFY NOVOLOG 55 HAMAAYAN ST MODIIN 71713 ISRAEL`

**Output:**
```json
{
  "name": "COVIDIEN (ISRAEL) LTD",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "NOTIFY NOVOLOG 55 HAMAAYAN ST",
    "addressLine2": "",
    "postalCode": "71713",
    "city": "MODIIN",
    "stateProvince": "",
    "countryCode": "IL"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```
- EXTREME PARSING CLARITY:

 - FIND "LTD" IN THE INPUT → "(ISRAEL)LTD" contains "LTD"
 - FIX SPACING → "(ISRAEL)LTD" becomes "(ISRAEL) LTD"
 - EVERYTHING BEFORE AND INCLUDING "LTD" = COMPANY NAME

 - Company name = "COVIDIEN (ISRAEL) LTD"
 - STOP HERE. FULL STOP. DO NOT CONTINUE.

- EVERYTHING AFTER "LTD" = ADDRESS

 - "NOTIFY" is NOT part of company name
 - "NOVOLOG" is NOT part of company name
 - These are delivery instructions

- STEP BY STEP:
    Read: "COVIDIEN" → part of name
    Read: "(ISRAEL)LTD" → contains "LTD" → name ends here
    Fix: "(ISRAEL)LTD" → "(ISRAEL) LTD"
    Name = "COVIDIEN (ISRAEL) LTD"
    Next word "NOTIFY" → This is AFTER "LTD" so it's ADDRESS
    Address = "NOTIFY NOVOLOG 55 HAMAAYAN ST"


## Example 14
**Input:** `GIVEN IMAGING LTD. HERMON BUILDING ILIT POB 258,NEW IND PARK, 3RD FLOOR YOKNEAM`

**Output:**
```json
{
  "name": "GIVEN IMAGING LTD.",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "HERMON BUILDING ILIT",
    "addressLine2": "POB 258, NEW IND PARK, 3RD FLOOR",
    "postalCode": "",
    "city": "YOKNEAM",
    "stateProvince": "",
    "countryCode": ""
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```
CRITICAL PARSING RULES FOR THIS EXAMPLE:
- Organization name = "GIVEN IMAGING LTD." → MUST STOP after "LTD."
- "HERMON BUILDING" is NOT part of company name → It's the building name in the address
- WHY? After legal entity markers (LTD., INC., CORP., etc.), EVERYTHING is address
- Even if next word is "BUILDING", "TOWER", "PLAZA" → These are address components

Step-by-step parsing:

- See "LTD." → Organization name ENDS HERE
- "HERMON BUILDING" → First part of address (building name)
- "ILIT" → Area/location name, continues address
- "YOKNEAM" → This is the CITY
- "POB 258,NEW IND PARK, 3RD FLOOR" → Additional address details

- RULE: After LTD./INC./CORP., even words like BUILDING, TOWER, CENTER, PLAZA are part of the address, NOT the company name
- Alternative acceptable parsing:

- addressLine1: "HERMON BUILDING, 3RD FLOOR"
- addressLine2: "ILIT, POB 258, NEW IND PARK"
- city: "YOKNEAM" 


## Example 15 
**Input:** `CEVA FREIGHT LLC 1333 South Mt. Prospect Rd Des Plaines IL 60018 US`

**Output:**
```json
{
  "name": "CEVA FREIGHT LLC",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "1333 South Mt. Prospect Rd",
    "addressLine2": "",
    "postalCode": "60018",
    "city": "Des Plaines",
    "stateProvince": "IL",
    "countryCode": "US"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```
- Parsing Logic:

 - No account number at start → accountNumber = ""
 - addressShortCode is empty (no pattern matching 2-5 letters + 1-3 digits found)
 - CEVA FREIGHT LLC is the organization name - STOPS at "LLC" (legal entity marker)
 - 1333 is a street number → marks start of address
 - 1333 South Mt. Prospect Rd is the street address → addressLine1
 - No secondary address info → addressLine2 = ""
 - 60018 is the US postal code (5 digits)
 - Des Plaines is the city (note: two-word city name)
 - IL is the state code (Illinois)
 - US is already the country code
 - No contact information present

KEY POINTS:
"LLC" = Limited Liability Company (legal entity marker like LTD, INC, CORP)
After "LLC", the number "1333" clearly starts the address
"Mt. Prospect" is part of street name, not separate
"Des Plaines" is a two-word city name (keep together)

## Example 16

**Input:** `MEDTRONIC 9560 JOE RODRIGUEZ EL PASO TX 79927 US`

**Output:**
```json
{
  "name": "MEDTRONIC",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "9560 JOE RODRIGUEZ",
    "addressLine2": "",
    "postalCode": "79927",
    "city": "EL PASO",
    "stateProvince": "TX",
    "countryCode": "US"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```
Parsing Logic:

No account number at start → accountNumber = ""
MEDTRONIC is the organization name - STOPS at "9560" because it's a street number
No legal entity marker (no LLC, INC, etc.) but number indicates address start
9560 JOE RODRIGUEZ is the street address (number + street name) → addressLine1
No secondary address info → addressLine2 = ""
79927 is the US postal code
EL PASO is the city (two-word city name)
TX is the state code (Texas)
US is already the country code

## Example 17

Input: MEDTRONIC INTERNATIONAL C/O CEVA EARL BAKKENSTRAAT 7-15 HEERLEN 6422 PJ NL
Output:
json{
  "name": "MEDTRONIC INTERNATIONAL C/O CEVA",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "EARL BAKKENSTRAAT 7-15",
    "addressLine2": "",
    "postalCode": "6422 PJ",
    "city": "HEERLEN",
    "stateProvince": "",
    "countryCode": "NL"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```
Parsing Logic:

No account number at start → accountNumber = ""
MEDTRONIC INTERNATIONAL C/O CEVA is the organization name (includes "c/o" relationship)
STOPS at "EARL" because "BAKKENSTRAAT" contains "STRAAT" (Dutch for street)
EARL BAKKENSTRAAT 7-15 is the street address → addressLine1
No secondary address info → addressLine2 = ""
6422 PJ is the Dutch postal code (NNNN AA format)
HEERLEN is the city
No state/province (Netherlands doesn't use states) → stateProvince = ""
NL is already the country code for Netherlands

KEY DIFFERENCE:

First example: No legal marker, but stops at street number
Second example: No legal marker, but stops at street name (BAKKENSTRAAT)


## Example 18
**Input:** `GIVEN IMAGING VIETNAM CO.,LTD 4A, 4TH FLR & 5A, 5&6TH FLR, S.F BLDG, ST. 14, TAN THUAN EPZ, TAN THUAN DONG, DIST 7 HO CHI MINH CITY VN TE +84974197720 VAT 0304602359`

**Output:**
```json
{
  "name": "GIVEN IMAGING VIETNAM CO.,LTD",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "4A, 4TH FLR & 5A, 5&6TH FLR, S.F BLDG, ST. 14,",
    "addressLine2": "TAN THUAN EPZ, TAN THUAN DONG, DIST 7",
    "postalCode": "",
    "city": "HO CHI MINH CITY",
    "stateProvince": "",
    "countryCode": "VN"
  },
  "contact": {
    "name": "",
    "phone": "+84974197720",
    "email": ""
  }
}
ULTRA-CLEAR PARSING INSTRUCTIONS:

SCAN FOR "LTD" → Found in "CO.,LTD"
ORGANIZATION NAME ENDS AT "LTD" → name = "GIVEN IMAGING VIETNAM CO.,LTD"
EVERYTHING AFTER "LTD" IS ADDRESS → Starting with "4A,"

WHY "4A," IS NOT PART OF COMPANY NAME:

"4A," comes AFTER "LTD"
RULE: After "LTD", EVERYTHING is address
"4A" is a unit/suite number (like "Suite 4A" or "Unit 4A")
Even though it starts with a letter, it's still an address component

PARSING BREAKDOWN:

"GIVEN IMAGING VIETNAM CO.,LTD" ← Organization name STOPS HERE
"4A," ← Unit number (part of address)
"4TH FLR & 5A, 5&6TH FLR" ← Floor information
"S.F BLDG" ← Building name
"ST. 14" ← Street 14 (ST. = abbreviation for Street)
"TAN THUAN EPZ, TAN THUAN DONG, DIST 7" ← Zone and district info

ADDRESS COMPONENTS THAT MIGHT LOOK LIKE COMPANY PARTS:

"4A" → It's a unit number, not company name
"S.F BLDG" → It's a building name, not company name
"ST." → It's abbreviation for "Street", not company name

PHONE PARSING:

"TE +84974197720" → "TE" marks the phone number
Phone = "+84974197720"
"VAT 0304602359" → Ignore VAT numbers


## OUTPUT REQUIREMENTS

- **Strictly output only the final JSON extraction in the format below.**
- **No additional text, commentary, or example outputs.**

## AUTOMATIC CONVERSIONS
- **Country Name to ISO Code:** e.g., "India" → "IN", "Finland" → "FI", "USA" → "US", "UNITED STATES" → "US", "SWITZERLAND" → "CH", "NETHERLANDS" → "NL".
- **Email Domain Normalization:** Convert the domain part of email addresses to lowercase.
- **Phone Number Formatting:** Replace "ext" with "x".

## COUNTRY-SPECIFIC POSTAL CODE HANDLING
- **US:** Keep hyphens (e.g., "02048-1139")
- **Netherlands:** Keep space and letters, format NNNN AA (e.g., "6422 PJ")
- **Switzerland:** Simple numeric format (e.g., "8212")
- **Other countries:** Preserve original formatting


## OUTPUT JSON STRUCTURE

{
  "name": "",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "",
    "addressLine2": "",
    "postalCode": "",
    "city": "",
    "stateProvince": "",
    "countryCode": ""
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}


### Very Important: There must be address line in address data, dont skip them for any input.
"""



###########################












SAMPLING_PARAM_KVV_LLM = {
                          "temperature":0,
                          "max_tokens":20000,
                          "type" : "normal"
                          }

SAMPLING_PARAM_TABLE_LLM = {
                          "temperature":0,
                          "max_tokens":25000,
                          "type" : "normal"
                          }

SAMPLING_PARAM_GENERAL_LLM = {
                            "temperature":0,
                            "max_tokens":10000,
                            "stop" : ["<|eot_id|>"],
                            "top_k" : 100,
                            "top_p" : 0.9,
                          }


SAMPLING_PARAM_KVV_LLM_FOR_GREEDY = {
                                "temperature":0.8,
                                "max_tokens":20000,
                                "num_of_generation" : 10,
                                "type" : "greedy"
                                }


SAMPLING_PARAM_KVV_LLM_FOR_MISSING_KEY = {
                                        "temperature":1,
                                        "max_tokens":20000,
                                        "stop" : ["<|eot_id|>"],
                                        "top_k" : 150,
                                        "top_p" : 0.9,
                                        "type" : "normal"
                                        }

SAMPLING_PARAM_TABLE_LLM_FOR_MISSING_TABLE = {
                                        "temperature":1,
                                        "max_tokens":25000,
                                        "stop" : ["<|eot_id|>"],
                                        "top_k" : 150,
                                        "top_p" : 0.9,
                                        "type" : "creative"
                                        }








def get_llm_result_kvv(layout_paths,ra_json,is_ra_json_available, no_key_found = False, is_greedy = False,custom_param = {}):


    page_ids = []
    llm_result = {}
    prompts_general = []
    prompts_agent = []
    prompts_greedy = []

    if is_ra_json_available:

        for  page_idx, page in enumerate(ra_json["children"]):
            page_id = page["id"]
            page_wise_paragraph = get_ra_json_to_txt_kvv(page)
            if page_wise_paragraph == "":
                continue
            page_ids.append(page_id)
            prompt_general = PROMPT_TEMPLATE.format(system_prompt = SYSTEM_PROMPT_KVV , prompt =  page_wise_paragraph)
            #+ "\n" + page_wise_paragraph + "\n" + SYSTEM_PROMPT_KVV
            prompts_general.append(prompt_general)

            prompt_agent = PROMPT_TEMPLATE.format(system_prompt = SYSTEM_PROMPT_KVV_AGENT , prompt =  page_wise_paragraph )
            prompts_agent.append(prompt_agent)
            
            prompt_greedy = PROMPT_TEMPLATE.format(system_prompt = SYSTEM_PROMPT_KVV_AGENT , prompt =  page_wise_paragraph.replace(" ","")+ "\n"+SYSTEM_PROMPT_KVV_AGENT)
            prompts_greedy.append(prompt_greedy)
    else:
        for layout_path in layout_paths:

            page_id = layout_path.replace("_layout.xml", "")[-8:] 
            
            page_wise_paragraph = get_xml_to_text(layout_path)
            if page_wise_paragraph == "":
                continue
            page_ids.append(page_id)
            prompt_general = PROMPT_TEMPLATE.format(system_prompt = SYSTEM_PROMPT_KVV , prompt =  page_wise_paragraph )
            prompts_general.append(prompt_general)

            prompt_agent = PROMPT_TEMPLATE.format(system_prompt = SYSTEM_PROMPT_KVV_AGENT , prompt =  page_wise_paragraph)
            prompts_agent.append(prompt_agent)
            
            prompt_greedy = PROMPT_TEMPLATE.format(system_prompt = SYSTEM_PROMPT_KVV , prompt =  page_wise_paragraph + "\n"+ SYSTEM_PROMPT_KVV + "\n" + page_wise_paragraph + "\n" + SYSTEM_PROMPT_KVV)
            prompts_greedy.append(prompt_greedy)
    
    if not no_key_found and not is_greedy:
        outputs = requests.post(f"{LLM_SERVICE_API_URL}/llm_service_kvv",json = {"prompts":prompts_general,"sampling_param":SAMPLING_PARAM_KVV_LLM})
    elif is_greedy:
        #SAMPLING_PARAM_KVV_LLM_FOR_GREEDY["temperature"] = custom_param["temperature"]
        #SAMPLING_PARAM_KVV_LLM_FOR_GREEDY["num_of_generation"] = custom_param["num_of_generation"]
        outputs = requests.post(f"{LLM_SERVICE_API_URL}/llm_service_kvv",json = {"prompts":prompts_greedy,"sampling_param":SAMPLING_PARAM_KVV_LLM_FOR_MISSING_KEY})
    else:
        outputs = requests.post(f"{LLM_SERVICE_API_URL}/llm_service_kvv",json = {"prompts":prompts_agent,"sampling_param":SAMPLING_PARAM_KVV_LLM_FOR_MISSING_KEY})
    
    outputs = outputs.json()
    outputs = outputs["llm_result_kvv"]
    

    for idx, output in enumerate(outputs):
        llm_result[page_ids[idx]] = output
    
    return llm_result


def get_llm_result_table_new(layout_paths,ra_json,is_ra_json_available, no_table_found = False):

    page_ids = []
    llm_result = []
    prompts = []
    prompt_hub = []
    sampling_rate = 15
    
    if is_ra_json_available:
        
        sampling_rate = len(ra_json["children"])

        if len(ra_json["children"])> 50:
            sampling_rate = 7
        elif len(ra_json["children"])> 15:
            sampling_rate = 15
        
        batch_text = ""
        
        
        for  page_idx, page in enumerate(ra_json["children"]):
            page_wise_paragraph_table = get_ra_json_to_txt_table_new(page)
            if page_wise_paragraph_table == "":
                continue
            if batch_text == "":
                batch_text = page_wise_paragraph_table
            else:
                batch_text = f"{batch_text}\n\n\n{page_wise_paragraph_table}"
            if (page_idx+1)%sampling_rate == 0:
                prompt = PROMPT_TEMPLATE.format(system_prompt = SYSTEM_PROMPT_TABLE, prompt = batch_text)
                prompts.append(prompt)
                batch_text = ""
            elif page_idx+1 == len(ra_json["children"]):
                prompt = PROMPT_TEMPLATE.format(system_prompt = SYSTEM_PROMPT_TABLE, prompt = batch_text)
                prompts.append(prompt)
                batch_text = ""
    else:
        sampling_rate = len(layout_paths)

        if len(layout_paths)> 50:
            sampling_rate = 7
        elif len(layout_paths)> 15:
            sampling_rate = 15
            
        batch_text = ""
        for page_idx, layout_path in enumerate(layout_paths):
            page_wise_paragraph_table = get_xml_to_text(layout_path)
            if page_wise_paragraph_table == "":
                continue
            if batch_text == "":
                batch_text = page_wise_paragraph_table
            else:
                batch_text = f"{batch_text}\n\n\n{page_wise_paragraph_table}"
                
            if (page_idx+1)%sampling_rate == 0:
                prompt = PROMPT_TEMPLATE.format(system_prompt = SYSTEM_PROMPT_TABLE, prompt= batch_text)
                prompts.append(prompt)
                batch_text = "" 
            elif page_idx+1 == len(layout_paths):
                prompt = PROMPT_TEMPLATE.format(system_prompt = SYSTEM_PROMPT_TABLE, prompt= batch_text)
                prompts.append(prompt)
                batch_text = ""

    sub_prompt_hub = []
    
    for p_idx, p in enumerate(prompts):
        sub_prompt_hub.append(p)

        if (p_idx+1)%6 == 0:
            prompt_hub.append(sub_prompt_hub)
            sub_prompt_hub = []
        elif p_idx+1 == len(prompts):
            prompt_hub.append(sub_prompt_hub)
            sub_prompt_hub = []
            
        
    for prompt_list in prompt_hub:
        if not no_table_found:
            outputs = requests.post(f"{LLM_SERVICE_API_URL}/llm_service_table",json = {"prompts":prompt_list, "sampling_param":SAMPLING_PARAM_TABLE_LLM})
        else:
            outputs = requests.post(f"{LLM_SERVICE_API_URL}/llm_service_table",json = {"prompts":prompt_list, "sampling_param":SAMPLING_PARAM_TABLE_LLM_FOR_MISSING_TABLE})
        outputs = outputs.json()
        outputs = outputs["llm_result_table"]

        for out in outputs:
            llm_result.append(out)
            
    return llm_result






def get_llm_result_table_old(layout_paths,ra_json,is_ra_json_available, no_table_found = False):

    page_ids = []
    llm_result = []
    prompts = []
    prompt_hub = []
    sampling_rate = 15
    
    if is_ra_json_available:
        
        sampling_rate = len(ra_json["children"])

        if len(ra_json["children"])> 50:
            sampling_rate = 7
        elif len(ra_json["children"])> 15:
            sampling_rate = 15
        
        batch_text = ""
        
        
        for  page_idx, page in enumerate(ra_json["children"]):
            page_wise_paragraph_table = get_ra_json_to_txt_table_old(page)
            if page_wise_paragraph_table == "":
                continue
            if batch_text == "":
                batch_text = page_wise_paragraph_table
            else:
                batch_text = f"{batch_text}\n\n\n{page_wise_paragraph_table}"
            if (page_idx+1)%sampling_rate == 0:
                prompt = PROMPT_TEMPLATE.format(system_prompt = SYSTEM_PROMPT_TABLE, prompt = batch_text)
                prompts.append(prompt)
                batch_text = ""
            elif page_idx+1 == len(ra_json["children"]):
                prompt = PROMPT_TEMPLATE.format(system_prompt = SYSTEM_PROMPT_TABLE, prompt = batch_text)
                prompts.append(prompt)
                batch_text = ""
    else:
        sampling_rate = len(layout_paths)

        if len(layout_paths)> 50:
            sampling_rate = 7
        elif len(layout_paths)> 15:
            sampling_rate = 15
            
        batch_text = ""
        for page_idx, layout_path in enumerate(layout_paths):
            page_wise_paragraph_table = get_xml_to_text(layout_path)
            if page_wise_paragraph_table == "":
                continue
            if batch_text == "":
                batch_text = page_wise_paragraph_table
            else:
                batch_text = f"{batch_text}\n\n\n{page_wise_paragraph_table}"
                
            if (page_idx+1)%sampling_rate == 0:
                prompt = PROMPT_TEMPLATE.format(system_prompt = SYSTEM_PROMPT_TABLE, prompt= batch_text)
                prompts.append(prompt)
                batch_text = "" 
            elif page_idx+1 == len(layout_paths):
                prompt = PROMPT_TEMPLATE.format(system_prompt = SYSTEM_PROMPT_TABLE, prompt= batch_text)
                prompts.append(prompt)
                batch_text = ""

    sub_prompt_hub = []
    
    for p_idx, p in enumerate(prompts):
        sub_prompt_hub.append(p)

        if (p_idx+1)%6 == 0:
            prompt_hub.append(sub_prompt_hub)
            sub_prompt_hub = []
        elif p_idx+1 == len(prompts):
            prompt_hub.append(sub_prompt_hub)
            sub_prompt_hub = []
            
        
    for prompt_list in prompt_hub:
        if not no_table_found:
            outputs = requests.post(f"{LLM_SERVICE_API_URL}/llm_service_table",json = {"prompts":prompt_list, "sampling_param":SAMPLING_PARAM_TABLE_LLM})
        else:
            outputs = requests.post(f"{LLM_SERVICE_API_URL}/llm_service_table",json = {"prompts":prompt_list, "sampling_param":SAMPLING_PARAM_TABLE_LLM_FOR_MISSING_TABLE})
        outputs = outputs.json()
        outputs = outputs["llm_result_table"]

        for out in outputs:
            llm_result.append(out)
            
    return llm_result









"""
def get_llm_result_table(layout_paths,ra_json_path,is_ra_json_available):

    page_ids = []
    llm_result = {}
    prompts = []
    batch_text = ""

    if is_ra_json_available:

        with open(ra_json_path, 'r') as file:
            ra_json = json.load(file)

        for  page_idx, page in enumerate(ra_json["pages"]):
            page_wise_paragraph_table = get_ra_json_to_txt(page)
            if page_wise_paragraph_table == "":
                continue
            if batch_text == "":
                batch_text = page_wise_paragraph_table
            else:
                batch_text = f"{batch_text}\n\n\n{page_wise_paragraph_table}"
    else:
        for layout_path in layout_paths:
            page_wise_paragraph_table = get_xml_to_text(layout_path)
            if page_wise_paragraph_table== "":
                continue
            if batch_text == "":
                batch_text = page_wise_paragraph_table
            else:
                batch_text = f"{batch_text}\n\n\n{page_wise_paragraph_table}"

    prompt = PROMPT_TEMPLATE.format(system_prompt=system_prompt_table, prompt=batch_text)
    output = requests.post(f"{LLM_SERVICE_API_URL}/llm_service_table",json = {"prompt":prompt})
    
    output = output.json()
    output = output["llm_result_table"]
    
    return output


def remove_kv_data(key_value_list, page_data, page_id):
        
    for idx, kv in enumerate(key_value_list):
        page_id_from_kv = kv["page_id"]
        if page_id != page_id_from_kv:
            continue
        
        keys = kv["key"].split(" ")
        values = kv["value"].split(" ")

        for k in keys:
            page_data = page_data.replace(k.strip(),"",1)
        for v in values:
            page_data = page_data.replace(v.strip(),"",1)

    return page_data


def get_llm_result_table(layout_paths,ra_json_path,is_ra_json_available, key_value_list):

    page_ids = []
    llm_result = {}
    prompts = []
    batch_text = ""

    if is_ra_json_available:

        with open(ra_json_path, 'r') as file:
            ra_json = json.load(file)

        for  page_idx, page in enumerate(ra_json["pages"]):
            page_id = page["id"]
            page_wise_paragraph_table = get_ra_json_to_txt(page)
            page_wise_paragraph_table = remove_kv_data(key_value_list, page_wise_paragraph_table, page_id)
            if page_wise_paragraph_table == "":
                continue
            if batch_text == "":
                batch_text = page_wise_paragraph_table
            else:
                batch_text = f"{batch_text}\n\n\n{page_wise_paragraph_table}"
    else:
        for layout_path in layout_paths:
            page_wise_paragraph_table = get_xml_to_text(layout_path)
            page_id = layout_path.replace("_layout.xml", "")[-8:]
            page_wise_paragraph_table = remove_kv_data(key_value_list, page_wise_paragraph_table, page_id)
            if page_wise_paragraph_table== "":
                continue
            if batch_text == "":
                batch_text = page_wise_paragraph_table
            else:
                batch_text = f"{batch_text}\n\n\n{page_wise_paragraph_table}"

    prompt = PROMPT_TEMPLATE.format(system_prompt=system_prompt_table, prompt=batch_text)
    output = requests.post(f"{LLM_SERVICE_API_URL}/llm_service_table",json = {"prompt":prompt})
    
    output = output.json()
    output = output["llm_result_table"]
    
    return output
"""





######## new address parsers prompt strategy

from address_parser_example import address_example_dict
from rapidfuzz import fuzz
import copy

CONVERSION_RULES = {
    **{char: "X" for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
    **{char: "X" for char in "abcdefghijklmnopqrstuvwxyz"},
    **{char: "D" for char in "0123456789"},
    ".": "",
    ",": "",
    ":": "",
    "-":""
}

def compress_x(input_string):
    result = [] 
    x_count = 0

    for char in input_string:
        if char == 'X':
            if x_count < 3: 
                result.append('X')
            x_count += 1  
        else:
            if char in 'Dbyc ': 
                x_count = 0
            result.append(char) 

    return ''.join(result) 

def str_to_shape(string):
    """
    Converts string into Shape
    """
    return compress_x("".join([CONVERSION_RULES.get(char, char) for char in string]))


def get_matched_address_example(inp_str,address_example_dict):
    best_score = 0
    best_match_example = {}
    for k,v in address_example_dict.items():
        inp_pattern = str_to_shape(inp_str)
        example_pattern = str_to_shape(v["address_str"])
        score = fuzz.ratio(inp_pattern,example_pattern)
        if score >= best_score:
            best_score = score
            best_match_example = copy.deepcopy(v["example"])
    return best_match_example


SYSTEM_PROMPT_ADDRESS_PARSER_p1 = """
# YOU ARE AN ULTRA-STRICT ADDRESS PARSING SYSTEM

This system extracts address, organization, and contact details from free-form input strings. It must follow these rules strictly and output only the parsed extraction in the JSON format specified below. **Do not include any example data, sample outputs, or additional text in the final result. Only output the final JSON extraction.**

## FIELD CONSTRAINTS TABLE

| JSON Path                | Type   | Max Length | Validation Rules                                                                                                                                                                                                                                             |
|--------------------------|--------|------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| name                     | string | 100        | Extract the organization name from the start of the input up to the first **clear address marker** (e.g., "HRL", "3PL", street names, etc.). **Ensure that no address components are included.** Only retain the organization name. |               
| address.addressLine1     | string | 50         | Extract the **core street address** (e.g., "Earl Bakkenstraat 7", "5300 Airways Blvd"). This should be the actual physical street address. |
| address.addressLine2     | string | 50         | Extract **secondary logistics/facility information** (e.g., "HRL 3 | Inbound | 1680", "3PL"). This is for warehouse locations, building identifiers, or other non-street address details. |
| address.postalCode       | string | 10         | Extract postal code with **country-specific formatting**. US: keep hyphens (e.g., "02048-1139"). Netherlands: keep space and letters (e.g., "6422 PJ"). |
| address.city             | string | 50         | Extract the city name. **Ensure that the city name does not contain numbers or country names.** |
| address.stateProvince    | string | 25         | Extract state/province code for countries that use them (e.g., US states). **Leave empty for countries without states/provinces** (e.g., Switzerland, Netherlands). |
| address.countryCode      | string | 2          | Extract from an explicit country name (e.g., "USA", "SWITZERLAND") and convert it to a **two-letter ISO code**. |
| contact.name             | string | 256        | Extract text **following the "Contact:" marker**. **Ensure that organization names are NOT included.** |
| contact.phone            | string | 20         | Extract phone number, ensuring it includes the country code. Convert "ext" to "x". |
| contact.email            | string | 254        | Extract a valid email format, ensuring the domain part is in lowercase. |

## PARSING SEQUENCE AND LOGIC


1. **Extract Organization Name:**
   - Identify the organization name after any account number
   - Stop at clear address markers like "HRL", "3PL", street names, or street numbers

2. **Separate Address Components:**
   - **addressLine1:** Extract the actual street address (street name and number)
   - **addressLine2:** Extract facility/warehouse identifiers, logistics information
   - Key rule: Street addresses go to line1, logistics/facility info goes to line2

3. **Extract Location Identifiers:**
   - **Postal Code:** Keep country-specific formatting (US with hyphens, Dutch with space and letters)
   - **City:** Text that clearly represents a city name
   - **State/Province:** Only for countries that use them (e.g., US states). Leave empty for others
   - **Country:** Convert country names to ISO codes

4. **Handle Country-Specific Patterns:**
   - US addresses: Include state codes, postal codes with hyphens
   - Dutch addresses: Postal codes with format "NNNN AA", no state/province
   - Swiss addresses: Simple numeric postal codes, no state/province

## EXAMPLE PARSING
"""




SYSTEM_PROMPT_ADDRESS_PARSER_p2 = """## OUTPUT REQUIREMENTS

- **Strictly output only the final JSON extraction in the format below.**
- **No additional text, commentary, or example outputs.**

## AUTOMATIC CONVERSIONS
- **Country Name to ISO Code:** e.g., "India" → "IN", "Finland" → "FI", "USA" → "US", "UNITED STATES" → "US", "SWITZERLAND" → "CH", "NETHERLANDS" → "NL".
- **Email Domain Normalization:** Convert the domain part of email addresses to lowercase.
- **Phone Number Formatting:** Replace "ext" with "x".

## COUNTRY-SPECIFIC POSTAL CODE HANDLING
- **US:** Keep hyphens (e.g., "02048-1139")
- **Netherlands:** Keep space and letters, format NNNN AA (e.g., "6422 PJ")
- **Switzerland:** Simple numeric format (e.g., "8212")
- **Other countries:** Preserve original formatting


## OUTPUT JSON STRUCTURE

{
  "name": "",
  "address": {
    "addressLine1": "",
    "addressLine2": "",
    "postalCode": "",
    "city": "",
    "stateProvince": "",
    "countryCode": ""
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}

### Important: Always maintain output json format strictly for every case.
"""


SYSTEM_PROMPT_ADDRESS_PARSER_p1_prealert = """
# YOU ARE AN ULTRA-STRICT ADDRESS PARSING SYSTEM

This system extracts address, organization, and contact details from free-form input strings. It must follow these rules strictly and output only the parsed extraction in the JSON format specified below. **Do not include any example data, sample outputs, or additional text in the final result. Only output the final JSON extraction.**

## FIELD CONSTRAINTS TABLE

| JSON Path                | Type   | Max Length | Validation Rules                                                                                                                                                                                                                                             |
|--------------------------|--------|------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| name                     | string | 100        | Extract the organization name from the start of the input up to the first **clear address marker** (e.g., "HRL", "3PL", street names, etc.). **Ensure that no address components are included.** Only retain the organization name. |               
| accountNumber            | string | 25         | Extract the first token if it appears to be an account code (letters + digits OR just digits at the beginning). If no clear code pattern exists at the start, set to empty string.    |
| address.addressLine1     | string | 50         | Extract the **core street address** (e.g., "Earl Bakkenstraat 7", "5300 Airways Blvd"). This should be the actual physical street address. |
| address.addressLine2     | string | 50         | Extract **secondary logistics/facility information** (e.g., "HRL 3 | Inbound | 1680", "3PL"). This is for warehouse locations, building identifiers, or other non-street address details. |
| address.postalCode       | string | 10         | Extract postal code with **country-specific formatting**. US: keep hyphens (e.g., "02048-1139"). Netherlands: keep space and letters (e.g., "6422 PJ"). |
| address.city             | string | 50         | Extract the city name. **Ensure that the city name does not contain numbers or country names.** |
| address.stateProvince    | string | 25         | Extract state/province code for countries that use them (e.g., US states). **Leave empty for countries without states/provinces** (e.g., Switzerland, Netherlands). |
| address.countryCode      | string | 2          | Extract from an explicit country name (e.g., "USA", "SWITZERLAND") and convert it to a **two-letter ISO code**. |
| contact.name             | string | 256        | Extract text **following the "Contact:" marker**. **Ensure that organization names are NOT included.** |
| contact.phone            | string | 20         | Extract phone number, ensuring it includes the country code. Convert "ext" to "x". |
| contact.email            | string | 254        | Extract a valid email format, ensuring the domain part is in lowercase. |

## PARSING SEQUENCE AND LOGIC

1. **Extract Account Number:**
   - Check if the first token is a potential account code
   - If it looks like an account code, extract it; otherwise, set to empty string

2. **Extract Organization Name:**
   - Identify the organization name after any account number
   - Stop at clear address markers like "HRL", "3PL", street names, or street numbers

3. **Separate Address Components:**
   - **addressLine1:** Extract the actual street address (street name and number)
   - **addressLine2:** Extract facility/warehouse identifiers, logistics information
   - Key rule: Street addresses go to line1, logistics/facility info goes to line2

4. **Extract Location Identifiers:**
   - **Postal Code:** Keep country-specific formatting (US with hyphens, Dutch with space and letters)
   - **City:** Text that clearly represents a city name
   - **State/Province:** Only for countries that use them (e.g., US states). Leave empty for others
   - **Country:** Convert country names to ISO codes

5. **Handle Country-Specific Patterns:**
   - US addresses: Include state codes, postal codes with hyphens
   - Dutch addresses: Postal codes with format "NNNN AA", no state/province
   - Swiss addresses: Simple numeric postal codes, no state/province

## EXAMPLE PARSING
"""




SYSTEM_PROMPT_ADDRESS_PARSER_p2_prealert = """## OUTPUT REQUIREMENTS

- **Strictly output only the final JSON extraction in the format below.**
- **No additional text, commentary, or example outputs.**

## AUTOMATIC CONVERSIONS
- **Country Name to ISO Code:** e.g., "India" → "IN", "Finland" → "FI", "USA" → "US", "UNITED STATES" → "US", "SWITZERLAND" → "CH", "NETHERLANDS" → "NL".
- **Email Domain Normalization:** Convert the domain part of email addresses to lowercase.
- **Phone Number Formatting:** Replace "ext" with "x".

## COUNTRY-SPECIFIC POSTAL CODE HANDLING
- **US:** Keep hyphens (e.g., "02048-1139")
- **Netherlands:** Keep space and letters, format NNNN AA (e.g., "6422 PJ")
- **Switzerland:** Simple numeric format (e.g., "8212")
- **Other countries:** Preserve original formatting


## OUTPUT JSON STRUCTURE

{
  "name": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "",
    "addressLine2": "",
    "postalCode": "",
    "city": "",
    "stateProvince": "",
    "countryCode": ""
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}

### Important: Always maintain output json format strictly for every case.
"""



def get_address_parser_prompt(inp_str, address_parser_example_from_backend, doc_type):

  if address_parser_example_from_backend != {}:
    address_example_all = address_parser_example_from_backend
  else:
    address_example_all = address_example_dict

  example = get_matched_address_example(inp_str,address_example_all)

  if doc_type.lower().replace(" ","").strip() == "prealert":
    return SYSTEM_PROMPT_ADDRESS_PARSER_p1_prealert + "\n" + example + "\n\n\n" +SYSTEM_PROMPT_ADDRESS_PARSER_p2_prealert

  return SYSTEM_PROMPT_ADDRESS_PARSER_p1 + "\n" + example + "\n\n\n" +SYSTEM_PROMPT_ADDRESS_PARSER_p2
  
    

            

def get_llm_result_address_parser(address_data_dict, address_parser_example_from_backend, doc_type):


  prompts = []
  outputs = []
  
  for address_data in address_data_dict.values():

      SYSTEM_PROMPT_ADDRESS_PARSER = get_address_parser_prompt(address_data, address_parser_example_from_backend, doc_type)
      parsed_address,_ = run_llm(SYSTEM_PROMPT_ADDRESS_PARSER,address_data)
      outputs.append(parsed_address)

  return outputs







################################## for autoextraction v2

import json
import re
from typing import Dict, Any, Union

def convert_data_to_json(vendor,key_table_data,page_map):

  try:
    page_id_vendor = page_map["1"]
  except:
    page_id_vendor = ""
    pass
    
  tmp_data_json = {"vendor":{"vendor": vendor,
                              "vendor_position": "0,0,0,0",
                              "page_id": page_id_vendor},
                              
                              "key_data":[],
                              "table_data":[]
                              }
  
  for item in key_table_data["key"]:
    key_string = list(item.keys())[0]
    value_string = list(item.values())[0]

    try:
      if list(item.values())[-1]:
        page_id = page_map[str(list(item.values())[-1])]
      else:
        page_id = page_map["1"]
    except:
      page_id = ""
      pass

    if value_string == None:
      value_string = ""
    tmp_data_json["key_data"].append({
                                "key": key_string,
                                "key_position": "0,0,0,0",
                                "value": str(value_string),
                                "value_position": "0,0,0,0",
                                "page_id": page_id, 
                                "original_key":key_string,
                                "is_label_mapped":False,
                                "is_profile_key_found":True,
                                "is_data_exception_done": False,
                                "is_pure_autoextraction" : True,
                                "original_key_label" :key_string,
                                "key_value":key_string
                                })
  single_table =  {"table_id":1,"table_name":"Main Table","table_data":{"rows":[]}}
  for row_id, row_items in enumerate(key_table_data["item_value"]):
    single_row = {"row_id":row_id,"row_data":[]}
    for col_id, col_data in enumerate(row_items):
        value = col_data["value"]
        if col_data["value"] == None:
          value = ""
        single_row["row_data"].append({
          "value":str(value),
          "label":col_data["label"],
          "is_label_mapped":False,
          "is_profile_key_found":True,
          "is_pure_autoextraction":True,  
          "is_data_exception_done": False,
          "original_key_label" : col_data["label"],
          "pos" : "0,0,0,0",
          "position":  "0,0,0,0", 
          "is_column_mapped_to_key":False,
          "key_value":col_data["label"]})

    single_table["table_data"]["rows"].append(single_row)  
  tmp_data_json["table_data"].append(single_table)
  return tmp_data_json





def llm_json_to_dict(llm_response: str) -> Dict[str, Any]:

    cleaned = llm_response.strip()
    
  
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```(?:json)?\s*\n', '', cleaned)
        cleaned = re.sub(r'\n```$', '', cleaned)
    
   
    json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', cleaned)
    if json_match:
        cleaned = json_match.group(1)
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Attempted to parse: {cleaned[:200]}...") 
        return {}

def safe_extract_dict(text: str) -> Union[Dict[str, Any], None]:
    
    patterns = [
        r'\{[^{}]*\{[^{}]*\}[^{}]*\}', 
        r'\{[^{}]*\}', 
        r'\[[^\[\]]*\]', 
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                result = json.loads(match)
                if isinstance(result, (dict, list)):
                    return result
            except:
                continue
    
    
    try:
        return json.loads(text.strip())
    except:
        return None
    




def generate_system_prompt_kv_table(field_need_to_extract):
    
    keys = []
    table_columns = []
    
    for item in field_need_to_extract:
        if item.get("type") == "key" or item.get("type") == "addressBlock" or item.get("type") == "addressBlockPartial":
            if item.get("type") == "addressBlockPartial" and item.get("field_description", "").strip() == "Field_Name" and item.get("rules_description", "").strip() == "":
              continue
              
            keys.append({
                "key": item.get("keyValue", ""),
                "description": item.get("field_description", ""),
                "rule" : item.get("rules_description", "")
            })
        elif item.get("type") == "table":
            table_columns.append({
                "column": item.get("keyValue", ""),
                "description": item.get("field_description", ""),
                "rule" : item.get("rules_description", "")
            })
    
    
    key_section = ""
    if keys:
        key_section = "  key:\n"
        for key_item in keys:
            key_section += f'    - {{ "key": "{key_item["key"]}", "description": "{key_item["description"]}", "value_conversion_rule": "{key_item["rule"]}"}}\n'
    
    
    table_section = ""
    if table_columns:
        table_section = "  table:\n"
        for col_item in table_columns:
            table_section += f'    - {{ "column": "{col_item["column"]}", "description": "{col_item["description"]}", "value_conversion_rule": "{col_item["rule"]}"}}\n'
    
    
    # key_output_example = ""
    # if keys:
    #     key_output_example = '    "key": [\n'
    #     for i, key_item in enumerate(keys):
    #         comma = "," if i < len(keys) - 1 else ""
    #         key_output_example += f'      "{key_item["key"]}": value or null{comma}\n'
    #     key_output_example += '    ],\n'
    
    
    # table_output_example = ""
    # if table_columns:
    #     column_examples = ""
    #     for i, col_item in enumerate(table_columns):
    #         comma = "," if i < len(table_columns) - 1 else ""
    #         column_examples += f'        {{"label":"{col_item["column"]}", "value": value or null}}{comma}\n'
        
    #     table_output_example = f'    "item_value": [\n'
    #     table_output_example += f'      [\n{column_examples}      ],\n'
    #     table_output_example += f'      [\n{column_examples}      ]\n'
    #     table_output_example += '    ]\n'
    
    
    system_prompt_kv_table = f"""You are an Adaptive Field & Table Extractor.
    Task
    Given document_text (plain text) and an extraction spec (keys + table columns with descriptions and rule), 
    extract values that match—even if expressed via synonyms/abbreviations/paraphrase— and apply key/column wise value conversion rule accordingly then return only the JSON in the required shape. 
    Do not calculate any amount value, quantity if not specifically mentioned in the description. 
    Extract all possible keys and tables data if it's present on the document or based on the data in the document, intelligently figure out other fields by making intelligent connections, always give detemenistic solution. 
    Verify what you are extracting too. Note: There might be some OCR error in the document that you need to account for and intelligently figure out.
    For keys, if it says that you need to first extract or find the table then figure out it's value. Firstly process the table and based on that determine or calculate it's value. 
    Input Payload (fill this template)

    {key_section}
    {table_section}
    
    
    Output (strict shape, no extra text)
    {{
      "key": [
        {{"KEY_NAME_1": value or null, "page_no": page no mentioned at top or null}},
        {{"KEY_NAME_2": value or null, "page_no": page no mentioned at top or null}},
        {{"KEY_NAME_N": value or null, "page_no": page no mentioned at top or null}}
      ],
      "item_value": [
        [
          {{"label":"COLUMN_NAME_1", "value": value or null, "page_no": page no mentioned at top or null}},
          {{"label":"COLUMN_NAME_2", "value": value or null, "page_no": page no mentioned at top or null}},
          {{"label":"COLUMN_NAME_M", "value": value or null, "page_no": page no mentioned at top or null}}
        ],
        [
          {{"label":"COLUMN_NAME_1", "value": value or null, "page_no": page no mentioned at top or null}},
          {{"label":"COLUMN_NAME_2", "value": value or null, "page_no": page no mentioned at top or null}},
          {{"label":"COLUMN_NAME_M", "value": value or null, "page_no": page no mentioned at top or null}}
        ]
      ]
    }}
    Rules
    Preserve each provided key/column name exactly in output.
    Use descriptions to resolve aliases/short forms; prefer label–value lines, titles, and repeated cues.
    Normalize whitespace; keep original units/text unless the description demands a specific format.
    Apply key/column wise value conversion rule correctly if theres any.
    If a key isn't confidently present → null.
    If the description defines a static value for any key or column, you must set that exact value—do not skip it.
    Build table rows from the document's line-item sections; if a row lacks some columns, include the row with null for missing cells.
    Always return all the keys and table even if it's empty
    For table, firstly check how many rows are there before extracting. Double check to verify how many rows are present in the document. To distinguish the row, if there are multiple, you will see pattern repeating.
    For table, there will be cases where column data is not present in a table but it will be present in another table connected by HS Code or some code.
    Extract all the items from table even if it's huge, no questions asked. You can't extract only some. You need to extract all the items/rows, MUST
    Return only the JSON object, no explanations.
    """
    
    return system_prompt_kv_table




def generate_system_prompt_vendor():
    system_prompt_vendor = """You are a Vendor Name extractor.
 
    Task
    From the first page’s plain text only, output one line with the vendor name (the entity that created/issued the document). A name must be returned.
    
    Heuristics (in priority order)
    
    Labeled issuer fields: Issued by, Vendor, Supplier, Seller, Exporter, Shipper, Consignor, From:, Bill From.
    
    Company header/letterhead/title block at the very top (logo line, registered name).
    
    Signature/issuer block (e.g., “For and on behalf of …”).
    
    If multiple candidates, pick the earliest high-confidence issuer and exclude recipient roles: Buyer, Customer, Bill To, Ship To, Consignee, Importer, Deliver To.
    
    If unlabeled, prefer the earliest company-like string (contains org suffix: Ltd, Limited, LLC, Inc., GmbH, BV, SAS, PLC, Co., Pvt, Sdn Bhd, KK, Oy, AB, Sp. z o.o., SA, PTY, LLP, LP) or a line matching the email/web domain owner near contact details.
    
    Output (strict)
    
    Return only the vendor name (trim whitespace/punctuation).
    
    No placeholders, no NONE, no extra text."""

    return system_prompt_vendor



def get_merged_chunk_wise_data_json(llm_result_hub):

  combined_data_json = {}
  already_added_key_list = []

  for chunk_wise_data_json in llm_result_hub:
    if combined_data_json == {}:
      combined_data_json = chunk_wise_data_json
      for kv_item in combined_data_json["key_data"]:
        already_added_key_list.append(kv_item["key"].lower().strip())  
    else:
      for kv_item in chunk_wise_data_json["key_data"]:
        if kv_item["key"].lower().strip() not in already_added_key_list:
          chunk_wise_data_json["key_data"].append(copy.deepcopy(kv_item))
      
      try:
        continued_row_id = combined_data_json["table_data"][0]["table_data"]["rows"][-1]["row_id"]+1
      except:
        continued_row_id = 0 

      for new_row_idx, new_row_data in enumerate(chunk_wise_data_json["table_data"][0]["table_data"]["rows"]):
        new_row_data["id"] = continued_row_id
        combined_data_json["table_data"][0]["table_data"]["rows"].append(copy.deepcopy(new_row_data))
        continued_row_id += 1

  return combined_data_json











def get_llm_result(ra_json,field_need_to_extract, page_sampling_rate = 10):


    user_prompt_hub = []
    llm_result_hub = []
    all_reasoning = ""

    user_content_kv_table = ""
    user_content_vendor = ""
    page_map = {}

    
    for  page_idx, page in enumerate(ra_json["children"]):

      page_map[f"{page_idx+1}"] = page["id"]
      page_wise_paragraph = get_ra_json_to_txt_table_new(page)
        
      if user_content_kv_table == "":
        if user_content_vendor == "":
          user_content_vendor = page_wise_paragraph
        user_content_kv_table =f"########################\nPAGE {page_idx+1}\n########################\n{page_wise_paragraph}"
      else:
        user_content_kv_table = f"{user_content_kv_table}\n########################\nPAGE {page_idx+1}\n########################\n{page_wise_paragraph}"


      if (page_idx + 1) % page_sampling_rate == 0:
        user_prompt_hub.append(user_content_kv_table)
        user_content_kv_table = ""

    user_prompt_hub.append(user_content_kv_table)

    system_prompt_vendor = generate_system_prompt_vendor()
    system_prompt_kv_table = generate_system_prompt_kv_table(field_need_to_extract)

    extracted_vendor, _ = run_llm(system_prompt_vendor , user_content_vendor)

    for cwuc_idx, chunk_wise_user_content in enumerate(user_prompt_hub):
      response, reasoning = run_llm(system_prompt_kv_table, chunk_wise_user_content)

      if all_reasoning == "":
        all_reasoning = f"Current chunk size = {page_sampling_rate} pages \n For chunk {cwuc_idx+1}\n{reasoning}"
      else:
        all_reasoning = f"{all_reasoning}\nFor chunk {cwuc_idx+1}\n{reasoning}"

      extracted_kv_table = llm_json_to_dict(response)
      data_json = convert_data_to_json(extracted_vendor,extracted_kv_table,page_map)

      llm_result_hub.append(data_json)

    merged_data_json = get_merged_chunk_wise_data_json(llm_result_hub)

    return merged_data_json, all_reasoning