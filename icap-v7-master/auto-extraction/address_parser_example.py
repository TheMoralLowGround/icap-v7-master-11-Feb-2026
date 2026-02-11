
address_example_dict = {"1":{"address_str":"OU1083 COVIDIEN LP 15 Hampshire St MANSFIELD MA 02048-1139 USA","example":"""**Input:** `OU1083 COVIDIEN LP 15 Hampshire St MANSFIELD MA 02048-1139 USA`

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
"""},

                        
"2":{"address_str":"3120 Covidien AG Victor von Bruns-Strasse 19 8212 NEUHAUSEN AM RHEINFALL SWITZERLAND EORI FRCH424062396","example":"""**Input:** `3120 Covidien AG Victor von Bruns-Strasse 19 8212 NEUHAUSEN AM RHEINFALL SWITZERLAND EORI FRCH424062396`

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
- `EORI FRCH424062396` is ignored as extra data""" },



"3":{"address_str":"C1680 Medtronic c/o CEVA Logistics HRL 3 | Inbound | 1680 HRL 3 Earl Bakkenstraat 7 6422 PJ HEERLEN NETHERLANDS","example":"""**Input:** `C1680 Medtronic c/o CEVA Logistics HRL 3 | Inbound | 1680 HRL 3 Earl Bakkenstraat 7 6422 PJ HEERLEN NETHERLANDS`

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
- `NETHERLANDS` → `NL` (country code conversion)"""},


                        "4":{"address_str":"MEDTRONIC C/O CEVA LOGISTICS HRL 3 |INBOUND | 1680 EARL BAKKENSTRAAT 7 6422 PJ HEERLEN NETHERLANDS","example":"""**Input:** `MEDTRONIC C/O CEVA LOGISTICS HRL 3 |INBOUND | 1680 EARL BAKKENSTRAAT 7 6422 PJ HEERLEN NETHERLANDS`

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
- `NETHERLANDS` → `NL` (country code conversion)"""},

                        "5":{"address_str":"LU1881 Covidien LP Central DC 3PL 5300 Airways Blvd MEMPHIS TN 38116 USA","example":"""**Input:** `LU1881 Covidien LP Central DC 3PL 5300 Airways Blvd MEMPHIS TN 38116 USA`

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
- `USA` → `US` (country code conversion)"""},

                        "6":{"address_str":"COVIDIEN LP CENTRAL DC 5300 AIRWAYS BLVD MEMPHIS TN 38116 UNITED STATES","example":"""**Input:** `COVIDIEN LP CENTRAL DC 5300 AIRWAYS BLVD MEMPHIS TN 38116 UNITED STATES`

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
- `UNITED STATES` → `US` (country code conversion)"""},

                        "7":{"address_str":"MEDTRONIC 1860 OUTER LOOP DOOR 434 LOUISVILLE KY 40219 US","example":"""**Input:** 'MEDTRONIC 1860 OUTER LOOP DOOR 434 LOUISVILLE KY 40219 US'

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
```"""},

                        "8":{"address_str":"Covidien LP Juarez (MMJ) MFG SPACEI BORDER LOGISTICS EL PASO TX 79927 USA","example":"""**Input:** `Covidien LP Juarez (MMJ) MFG SPACEI BORDER LOGISTICS EL PASO TX 79927 USA`

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
"""},

                        "9":{"address_str":"MEDTRONIC B.V. EARL BAKKENSTRAAT 10 SITE 1030 HEERLEN 6422 PJ NL TE +31455668000 MEDTRONIC COT TEAM EORI No. NL001686987","example":"""**Input:** `MEDTRONIC B.V. EARL BAKKENSTRAAT 10 SITE 1030 HEERLEN 6422 PJ NL TE +31455668000 MEDTRONIC COT TEAM EORI No. NL001686987`

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

- CRITICAL: "B.V." = Dutch legal entity marker (like "LTD" in English). Organization name MUST stop here!"""},

                        "10":{"address_str":"Medtronic c/o CEVA Logistics Earl Bakkenstraat 7-15 PJ HEERLEN 6422 NETHERLANDS 3 I Inbound 1680 HRL","example":"""**Input:** `Medtronic c/o CEVA Logistics Earl Bakkenstraat 7-15 PJ HEERLEN 6422 NETHERLANDS 3 I Inbound 1680 HRL`

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
- No contact information present"""},

                        "11":{"address_str":"Global Forwarding Israel Ltd. 2 Rakefet St. North Industrial Zoni Shoham, 6083706 Israel","example":"""Input: Global Forwarding Israel Ltd. 2 Rakefet St. North Industrial Zoni Shoham, 6083706 Israel
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
- No contact information present"""},

                        "12":{"address_str":"GIVEN IMAGING LTD. HERMON BUILDING ILIT YOKNEAM POB 258,NEW IND PARK, 3RD FLOOR","example":"""**Input:** `GIVEN IMAGING LTD. HERMON BUILDING ILIT YOKNEAM POB 258,NEW IND PARK, 3RD FLOOR`

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
-When multiple location elements exist, group logically: building/floor together, POB/area together"""},

                        "13":{"address_str":"COVIDIEN (ISRAEL)LTD NOTIFY NOVOLOG 55 HAMAAYAN ST MODIIN 71713 ISRAEL","example":"""**Input:** `COVIDIEN (ISRAEL)LTD NOTIFY NOVOLOG 55 HAMAAYAN ST MODIIN 71713 ISRAEL`

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
    Address = "NOTIFY NOVOLOG 55 HAMAAYAN ST"""},

                        "14":{"address_str":"GIVEN IMAGING LTD. HERMON BUILDING ILIT POB 258,NEW IND PARK, 3RD FLOOR YOKNEAM","example":"""**Input:** `GIVEN IMAGING LTD. HERMON BUILDING ILIT POB 258,NEW IND PARK, 3RD FLOOR YOKNEAM`

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
"""},

                        "15":{"address_str":"CEVA FREIGHT LLC 1333 South Mt. Prospect Rd Des Plaines IL 60018 US","example":"""**Input:** `CEVA FREIGHT LLC 1333 South Mt. Prospect Rd Des Plaines IL 60018 US`

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
"Des Plaines" is a two-word city name (keep together)"""},

                        "16":{"address_str":"MEDTRONIC 9560 JOE RODRIGUEZ EL PASO TX 79927 US","example":"""**Input:** `MEDTRONIC 9560 JOE RODRIGUEZ EL PASO TX 79927 US`

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
US is already the country code"""},

                        "17":{"address_str":"MEDTRONIC INTERNATIONAL C/O CEVA EARL BAKKENSTRAAT 7-15 HEERLEN 6422 PJ NL","example":"""Input: MEDTRONIC INTERNATIONAL C/O CEVA EARL BAKKENSTRAAT 7-15 HEERLEN 6422 PJ NL
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
Second example: No legal marker, but stops at street name (BAKKENSTRAAT)"""},

                        "18":{"address_str":"GIVEN IMAGING VIETNAM CO.,LTD 4A, 4TH FLR & 5A, 5&6TH FLR, S.F BLDG, ST. 14, TAN THUAN EPZ, TAN THUAN DONG, DIST 7 HO CHI MINH CITY VN TE +84974197720 VAT 0304602359","example":"""**Input:** `GIVEN IMAGING VIETNAM CO.,LTD 4A, 4TH FLR & 5A, 5&6TH FLR, S.F BLDG, ST. 14, TAN THUAN EPZ, TAN THUAN DONG, DIST 7 HO CHI MINH CITY VN TE +84974197720 VAT 0304602359`

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
"VAT 0304602359" → Ignore VAT numbers"""},
                        "19":{"address_str":"945352 Unit 5 & 6 Eden Business park Eden house drive, MALTON North Yorkshire YO17 6AE UNITED KINGDOM","example":""" Input: 945352 Unit 5 & 6 Eden Business park Eden house drive, MALTON North Yorkshire YO17 6AE UNITED KINGDOM
Output:
json{
  "name": "",
  "addressShortCode": "",
  "accountNumber": "945352",
  "address": {
    "addressLine1": "Unit 5 & 6 Eden Business park",
    "addressLine2": "Eden house drive",
    "postalCode": "YO17 6AE",
    "city": "MALTON",
    "stateProvince": "North Yorkshire",
    "countryCode": "GB"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}"""},
                        "20":{"address_str":"LU1887 MITG Central XDOC XDOCK 5300 Airways Blvd MEMPHIS TN 38116 USA","example":""" Input: LU1887 MITG Central XDOC XDOCK 5300 Airways Blvd MEMPHIS TN 38116 USA
Output:
json{
  "name": "MITG Central XDOC",
  "addressShortCode": "",
  "accountNumber": "LU1887",
  "address": {
    "addressLine1": "XDOCK 5300 Airways Blvd",
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
}"""},
             
             "21" : {"address_str":"DAVIS & GECK CARIBE, LTD. SAN ISIDRO MANUFACTORING ZONA FRANCA SAN ISIDRO SANTO DOMINGO, DOMINICAN REPUBLIC","example":"""Input: DAVIS & GECK CARIBE, LTD. SAN ISIDRO MANUFACTORING ZONA FRANCA SAN ISIDRO SANTO DOMINGO, DOMINICAN REPUBLIC
Output:
json{
  "name": "DAVIS & GECK CARIBE, LTD.",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "SAN ISIDRO MANUFACTORING ZONA FRANCA",
    "addressLine2": "SAN ISIDRO",
    "postalCode": "",
    "city": "SANTO DOMINGO",
    "stateProvince": "",
    "countryCode": "DO"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}RetryClaude can make mistakes. Please double-check responses. """} ,
             
             "22": {"address_str":"Davis & Geek Caribe LTD, XDOC XDOC Autopista de San Isidro km 17 11500 SANTO DOMINGO ESTE DOMINICAN REPUBJC","example":"""Input: Davis & Geek Caribe LTD, XDOC XDOC Autopista de San Isidro km 17 11500 SANTO DOMINGO ESTE DOMINICAN REPUBJC
Output:
json{
  "name": "Davis & Geek Caribe LTD",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": ", XDOC XDOC Autopista de San Isidro km 17",
    "addressLine2": "",
    "postalCode": "11500",
    "city": "SANTO DOMINGO ESTE",
    "stateProvince": "",
    "countryCode": "DO"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
} """},
             "23": {"address_str":"YOUSUF MAHMOOD HUSSAIN CO. W.L.L. P.O. BOX 23, MANAMA CENTER BUILDING 58 ROAD 381 MANAMA Bahrain","example":""" Input: YOUSUF MAHMOOD HUSSAIN CO. W.L.L. P.O. BOX 23, MANAMA CENTER BUILDING 58 ROAD 381 MANAMA Bahrain
Output:
json{
  "name": "YOUSUF MAHMOOD HUSSAIN CO. W.L.L.",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "P.O. BOX 23, MANAMA CENTER",
    "addressLine2": "BUILDING 58 ROAD 381",
    "postalCode": "",
    "city": "MANAMA",
    "stateProvince": "",
    "countryCode": "BH"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}"""},
             "24": {"address_str":"ETIHAD AIRWAYS ABU DHABI AE,TL0097125058000,FX0097125058111","example":""" Input: ETIHAD AIRWAYS ABU DHABI AE,TL0097125058000,FX0097125058111
Output:
json{
  "name": "ETIHAD AIRWAYS",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "",
    "addressLine2": "",
    "postalCode": "",
    "city": "ABU DHABI",
    "stateProvince": "",
    "countryCode": "AE"
  },
  "contact": {
    "name": "",
    "phone": "0097125058000",
    "email": ""
  }
}"""},
             "25": {"address_str":"Modem Pharmaceutical 71 Ishaaa Building Ibn Dubail Healthcare Citv Dubal, United Arab PO Box 1586","example":"""Input: Modem Pharmaceutical 71 Ishaaa Building Ibn Dubail Healthcare Citv Dubal, United Arab PO Box 1586
Output:
json{
  "name": "Modem Pharmaceutical",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "71 Ishaaa Building",
    "addressLine2": "Ibn Dubail Healthcare Citv",
    "postalCode": "1586",
    "city": "Dubal",
    "stateProvince": "",
    "countryCode": "AE"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
} """},
             "26": {"address_str":"LU1885 MDT Logistics Central XDOC 5414 Airways Blvd, Building D Gate Access 5570 Airways Blvd MEMPHIS TN 38116 USA","example":"""Input: LU1885 MDT Logistics Central XDOC 5414 Airways Blvd, Building D Gate Access 5570 Airways Blvd MEMPHIS TN 38116 USA
Output:
json{
  "name": "MDT Logistics Central XDOC",
  "addressShortCode": "",
  "accountNumber": "LU1885",
  "address": {
    "addressLine1": "5414 Airways Blvd, Building D",
    "addressLine2": "Gate Access 5570 Airways Blvd",
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
}"""},
             "27": {"address_str":"Bimed d.o.o. Banja Luka, Branka Morace 12 78000 Banja Luka, Bosnia and Herzegovina","example":"""Input: Bimed d.o.o. Banja Luka, Branka Morace 12 78000 Banja Luka, Bosnia and Herzegovina
Output:
json{
  "name": "Bimed d.o.o. Banja Luka",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "Branka Morace 12",
    "addressLine2": "",
    "postalCode": "78000",
    "city": "Banja Luka",
    "stateProvince": "",
    "countryCode": "BA"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
} """},
             "28": {"address_str":"DHL GLOBAL FORWARDING ABU DHABI - SOLE PROPRIETORS SKY CITY LOGISTICS PARK A8-4 ABU DHABI CITY LIMITS 27066 UNITED ARAB EMIRATES","example":""" Input: DHL GLOBAL FORWARDING ABU DHABI - SOLE PROPRIETORS SKY CITY LOGISTICS PARK A8-4 ABU DHABI CITY LIMITS 27066 UNITED ARAB EMIRATES
Output:
json{
  "name": "DHL GLOBAL FORWARDING ABU DHABI - SOLE PROPRIETORS",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "SKY CITY LOGISTICS PARK A8-4",
    "addressLine2": "ABU DHABI CITY LIMITS",
    "postalCode": "27066",
    "city": "ABU DHABI",
    "stateProvince": "",
    "countryCode": "AE"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}"""},
             "29": {"address_str":"100391 CSTC-CUSTOMER CARRIER","example":""" Input: 100391 CSTC-CUSTOMER CARRIER
Output:
json{
  "name": "CSTC-CUSTOMER CARRIER",
  "addressShortCode": "",
  "accountNumber": "100391",
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
}"""},
             "30": {"address_str":"SIFA TAHITI FARE UTE - BP 9011 98715 PAPEETE POLYNéSIE FRANçAISE","example":"""**Input:** `SIFA TAHITI FARE UTE - BP 9011 98715 PAPEETE POLYNéSIE FRANçAISE`

**Output:**
```json
{
  "name": "SIFA TAHITI",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "FARE UTE - BP 9011",
    "addressLine2": "",
    "postalCode": "98715",
    "city": "PAPEETE",
    "stateProvince": "",
    "countryCode": "PF"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}
```

**Detailed Parsing Rules:**

1. **Case Inconsistencies in OCR**:
   - "POLYNéSIE" - mixed case with lowercase é
   - "FRANçAISE" - uppercase with lowercase ç
   - Keep original casing in processing
   - Still map to correct country code despite case errors

2. **French Polynesia Recognition Patterns**:
   - "POLYNÉSIE FRANÇAISE" → PF
   - "POLYNESIE FRANCAISE" → PF  
   - "POLYNéSIE FRANçAISE" → PF
   - "POLYN\u00e9SIE FRAN\u00e7AISE" → PF
   - Handle all variations of accents/cases

3. **BP (Boîte Postale) Handling**:
   - "BP" = P.O. Box in French territories
   - Always followed by numbers
   - Include in address line, not as separate field
   - Format: "BP XXXX" or "BP XXXXX"

4. **French Territory Postal Codes**:
   - 5 digits (like mainland France)
   - 987XX series = French Polynesia
   - 971XX = Guadeloupe
   - 972XX = Martinique
   - No need to add country prefix

5. **Address Structure**:
   - Company: SIFA TAHITI (stop at first location indicator)
   - Location: FARE UTE (local area/building name)
   - Postal Box: BP 9011
   - The dash (-) separates location from postal box
"""},
             "31": {"address_str":"FARMONT M.P. D.O.O. KOSIC BB 81410 DANILOVGRAD MONTENEGRO","example":""" Input: FARMONT M.P. D.O.O. KOSIC BB 81410 DANILOVGRAD MONTENEGRO
Output:
json{
  "name": "FARMONT M.P. D.O.O.",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "KOSIC BB",
    "addressLine2": "",
    "postalCode": "81410",
    "city": "DANILOVGRAD",
    "stateProvince": "",
    "countryCode": "ME"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}"""},
             
            "32": {"address_str":"BYBOX NVC 301 HOLLYMOOR WAY BIRMINGHAM B31 5HE UNITED KINGDOM","example":"""Input: BYBOX NVC 301 HOLLYMOOR WAY BIRMINGHAM B31 5HE UNITED KINGDOM
Output:
json{
  "name": "BYBOX NVC",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "301 HOLLYMOOR WAY",
    "addressLine2": "",
    "postalCode": "B31 5HE",
    "city": "BIRMINGHAM",
    "stateProvince": "",
    "countryCode": "GB"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}"""},
            "33": {"address_str":"BRING WAREHOUSING AS ATT LARS TONNES TLF 90150920 TOMTEVEIEN 55 1618 FREDRIKSTAD NORWAY","example":""" Input: BRING WAREHOUSING AS ATT LARS TONNES TLF 90150920 TOMTEVEIEN 55 1618 FREDRIKSTAD NORWAY
Output:
json{
  "name": "BRING WAREHOUSING AS",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "TOMTEVEIEN 55",
    "addressLine2": "",
    "postalCode": "1618",
    "city": "FREDRIKSTAD",
    "stateProvince": "",
    "countryCode": "NO"
  },
  "contact": {
    "name": "LARS TONNES",
    "phone": "90150920",
    "email": ""
  }
}"""},
            "34": {"address_str":"Modern Pharmaceutical 71 Ibn Ishaaa Building Dubai Healthcare Citv Dubai. United Arab PO Box 1586","example":""" Input: Modern Pharmaceutical 71 Ibn Ishaaa Building Dubai Healthcare Citv Dubai. United Arab PO Box 1586
Output:
json{
  "name": "Modern Pharmaceutical",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "71 Ibn Ishaaa Building",
    "addressLine2": "Dubai Healthcare Citv",
    "postalCode": "1586",
    "city": "Dubai",
    "stateProvince": "",
    "countryCode": "AE"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}"""},
            "35":{"address_str":"ETIHAD AIRWAYS ABU DHABI","example":"""Input: ETIHAD AIRWAYS ABU DHABI
Output:
json{
  "name": "ETIHAD AIRWAYS",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "",
    "addressLine2": "",
    "postalCode": "",
    "city": "ABU DHABI",
    "stateProvince": "",
    "countryCode": "AE"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
} """},
            "36": {"address_str":"MEDTRONIC HEERLEN DISTRIBUTION CENTER EARL BAKKENSTRAAT 10 HEERLEN 6422 PJ NL TE +31455664920 MEDTRONIC COT TEAM EORI No. NL001686987","example":""" Input: MEDTRONIC HEERLEN DISTRIBUTION CENTER EARL BAKKENSTRAAT 10 HEERLEN 6422 PJ NL TE +31455664920 MEDTRONIC COT TEAM EORI No. NL001686987
Output:
json{
  "name": "MEDTRONIC HEERLEN DISTRIBUTION CENTER",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "EARL BAKKENSTRAAT 10",
    "addressLine2": "",
    "postalCode": "6422 PJ",
    "city": "HEERLEN",
    "stateProvince": "",
    "countryCode": "NL"
  },
  "contact": {
    "name": "MEDTRONIC COT TEAM",
    "phone": "+31455664920",
    "email": ""
  }
}"""},
            
            "37": {"address_str":"OU3102 Company Medtronic Europe Sarl Route du Molliau 31 1131 TOLOCHENAZ SWITZERLAND","example":"""Input: OU3102 Company Medtronic Europe Sarl Route du Molliau 31 1131 TOLOCHENAZ SWITZERLAND
Output:
json{
  "name": "Company Medtronic Europe Sarl",
  "addressShortCode": "",
  "accountNumber": "OU3102",
  "address": {
    "addressLine1": "Route du Molliau 31",
    "addressLine2": "",
    "postalCode": "1131",
    "city": "TOLOCHENAZ",
    "stateProvince": "",
    "countryCode": "CH"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}"""},
            "38":{"address_str":"COVIDIEN JAPAN INC. 2-70 KONAN 1-CHOME MINATO-KU TOKYO 1080075JP","example":"""Input: COVIDIEN JAPAN INC. 2-70 KONAN 1-CHOME MINATO-KU TOKYO 1080075JP
Output:
json{
  "name": "COVIDIEN JAPAN INC.",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "2-70 KONAN 1-CHOME",
    "addressLine2": "MINATO-KU",
    "postalCode": "108-0075",
    "city": "TOKYO",
    "stateProvince": "",
    "countryCode": "JP"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
} """},
            "39": {"address_str":"N I P P O N E X P R E S S S S NX GROUP BLD.,2-KANDAIZUMICHO -CHIYODA-KU, TOKYO, 101-8647,JAPAN.","example":""" Input: N I P P O N E X P R E S S S S NX GROUP BLD.,2-KANDAIZUMICHO -CHIYODA-KU, TOKYO, 101-8647,JAPAN.
Output:
json{
  "name": "N I P P O N E X P R E S S S S",
  "addressShortCode": "",
  "accountNumber": "",
  "address": {
    "addressLine1": "NX GROUP BLD., 2-KANDAIZUMICHO",
    "addressLine2": "CHIYODA-KU",
    "postalCode": "101-8647",
    "city": "TOKYO",
    "stateProvince": "",
    "countryCode": "JP"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
}"""},
            "40": {"address_str":"31623868547  Earl Bakkenstraat 7-15,Bjorn Insu Medtronic c/o FedEx Express QYLA Nijverheidsweg 20 HRL 3 - Inbound - 1711 HRL CEVA ELST, GL 6662 NL","example":"""Input: 31623868547  Earl Bakkenstraat 7-15,Bjorn Insu Medtronic c/o FedEx Express QYLA Nijverheidsweg 20 HRL 3 - Inbound - 1711 HRL CEVA ELST, GL 6662 NL
Output:
json{
  "name": "Medtronic c/o FedEx Express QYLA",
  "addressShortCode": "",
  "accountNumber": "31623868547",
  "address": {
    "addressLine1": "Earl Bakkenstraat 7-15,Bjorn Insu",
    "addressLine2": "Nijverheidsweg 20 HRL 3 - Inbound - 1711 HRL CEVA",
    "postalCode": "6662",
    "city": "ELST",
    "stateProvince": "GL",
    "countryCode": "NL"
  },
  "contact": {
    "name": "",
    "phone": "",
    "email": ""
  }
} """},

"41": {"address_str":"CHCOA012","example":""" Input: CHCOA012

Output:
{
  "name": "",
  "addressShortCode": "",
  "accountNumber": "CHCOA012",
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
} """}
              
               
                        
                        
}





#{"address_str":"","example":""" """}