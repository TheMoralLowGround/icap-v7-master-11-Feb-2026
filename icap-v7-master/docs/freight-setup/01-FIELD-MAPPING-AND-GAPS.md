# DHL Freight API - Field Mapping & Gap Analysis

**Last Updated:** 2026-02-11
**API Version:** 1.7 (2025/R06)
**Status:** In Progress

---

## Overview

This document tracks the mapping between extracted document fields and the DHL Freight Shipment Booking API, identifies gaps, and documents validation requirements that users will face.

---

## ✅ FULLY IMPLEMENTED FIELDS

### Shipment Level - Basic Fields

| Extracted Field | API Field | Type | Status | Notes |
|----------------|-----------|------|--------|-------|
| `id` | `id` | string(13) | ✅ Mapped | Tracking ID - auto-assigned if empty |
| `productCode` | `productCode` | string(3) | ✅ Mapped | e.g., 'ECI' - see Product Manual |
| `pickupDate` | `pickupDate` | date | ✅ Mapped | Used with DHL Eurapid/EuroConnect |
| `requestedDeliveryDate` | `requestedDeliveryDate` | date | ✅ Mapped | Required with Eurapid + CDD |
| `pickupInstruction` | `pickupInstruction` | string(512) | ✅ Mapped | |
| `deliveryInstruction` | `deliveryInstruction` | string(512) | ✅ Mapped | |
| `totalNumberOfPieces` | `totalNumberOfPieces` | int(999) | ✅ Mapped | |
| `totalWeight` | `totalWeight` | number | ✅ Mapped | Weight in kg |
| `totalVolume` | `totalVolume` | number | ✅ Mapped | Volume in m³ |
| `totalLoadingMeters` | `totalLoadingMeters` | number | ✅ Mapped | LDM - full truck height |
| `totalPalletPlaces` | `totalPalletPlaces` | number | ✅ Mapped | PPL - 120x80cm EUR pallet |
| `goodsDescription` | `goodsDescription` | string(70) | ✅ Mapped | Shipment-level description |
| `goodsValue` | `goodsValue` | number | ✅ Mapped | Monetary value |
| `goodsValueCurrency` | `goodsValueCurrency` | string(3) | ✅ Mapped | ISO 4217 currency code |

### References

| Extracted Field | API Field | Type | Status | Notes |
|----------------|-----------|------|--------|-------|
| `references` array | `references[]` | array | ✅ Mapped | Max 99 items |
| - `qualifier` | `qualifier` | enum | ✅ Mapped | CNR/CNZ/INV |
| - `value` | `value` | string(35) | ✅ Mapped | Reference value |

### Payer Code

| Extracted Field | API Field | Type | Status | Notes |
|----------------|-----------|------|--------|-------|
| `payerCodeCode` → `code` | `payerCode.code` | string(3) | ✅ Mapped | **REQUIRED** - DAP/DDP/EXW/CIP |
| `payerCodeLocation` → `location` | `payerCode.location` | string(17) | ✅ Mapped | |

### Parties (Consignor, Pickup, Consignee, Delivery)

| Extracted Field | API Field | Type | Status | Notes |
|----------------|-----------|------|--------|-------|
| `{party}.type` | `parties[].type` | enum | ✅ Mapped | **REQUIRED** |
| `{party}.id` | `parties[].id` | string(15) | ✅ Mapped | Account number - mandatory for freight payer |
| `{party}.name` | `parties[].name` | string(70) | ✅ Mapped | **REQUIRED** |
| `{party}.contactName` | `parties[].contactName` | string(40) | ✅ Mapped | |
| `{party}.phone` | `parties[].phone` | string(64) | ✅ Mapped | |
| `{party}.email` | `parties[].email` | string(64) | ✅ Mapped | |
| `{party}.vatEoriSocialSecurityNumber` | `parties[].vatEoriSocialSecurityNumber` | string(20) | ✅ Mapped | EORI for customs |
| `{party}.address` | `parties[].address` | object | ✅ Mapped | **REQUIRED** |
| `{party}.addressLine1` → `street` | `parties[].address.street` | string(40) | ✅ Mapped | **REQUIRED** - includes house number |
| `{party}.addressLine2` → `additionalAddressInfo` | `parties[].address.additionalAddressInfo` | string(40) | ✅ Mapped | |
| `{party}.city` → `cityName` | `parties[].address.cityName` | string(40) | ✅ Mapped | **REQUIRED** |
| `{party}.postalCode` | `parties[].address.postalCode` | string(12) | ✅ Mapped | **REQUIRED** - IE uses COUNTY NAME |
| `{party}.countryCode` | `parties[].address.countryCode` | string(2) | ✅ Mapped | **REQUIRED** - ISO 3166-1 |
| `{party}.vatCountryCode` → `countryCode` | `parties[].vat.countryCode` | string(3) | ✅ Mapped | VAT country prefix |
| `{party}.vatNumber` → `number` | `parties[].vat.number` | string(11) | ✅ Mapped | VAT number |

### Pieces (Cargo Details)

| Extracted Field | API Field | Type | Status | Notes |
|----------------|-----------|------|--------|-------|
| `piecesId` → `id[]` | `pieces[].id[]` | string(35) | ✅ Mapped | SSCC codes - auto-assigned if empty |
| `goodsType` | `pieces[].goodsType` | string(70) | ✅ Mapped | Piece-level description |
| `packageType` | `pieces[].packageType` | string(4) | ✅ Mapped | **REQUIRED** - e.g., 'PAL' |
| `marksAndNumbers` | `pieces[].marksAndNumbers` | string(45) | ✅ Mapped | |
| `numberOfPieces` | `pieces[].numberOfPieces` | int(999) | ✅ Mapped | **REQUIRED** - min 1 |
| `weight` | `pieces[].weight` | number | ✅ Mapped | **REQUIRED** - kg |
| `volume` | `pieces[].volume` | number | ✅ Mapped | m³ |
| `loadingMeters` | `pieces[].loadingMeters` | number | ✅ Mapped | |
| `palletPlaces` | `pieces[].palletPlaces` | number | ✅ Mapped | |
| `width` | `pieces[].width` | number | ✅ Mapped | cm |
| `height` | `pieces[].height` | number | ✅ Mapped | cm |
| `length` | `pieces[].length` | number | ✅ Mapped | cm |
| `stackable` | `pieces[].stackable` | boolean | ✅ Mapped | |

### Dangerous Goods (within Pieces)

| Extracted Field | API Field | Type | Status | Notes |
|----------------|-----------|------|--------|-------|
| `dangerousGoodsDgmId` | `pieces[].dangerousGoods[].dgmId` | int | ✅ Mapped | DG Office ADR ID |
| `dangerousGoodsAdrClass` | `pieces[].dangerousGoods[].adrClass` | string(7) | ✅ Mapped | **REQUIRED** - e.g., "4.2" |
| `dangerousGoodsUnNumber` | `pieces[].dangerousGoods[].unNumber` | int | ✅ Mapped | **REQUIRED** - e.g., 1380 |
| `dangerousGoodsProperShippingName` | `pieces[].dangerousGoods[].properShippingName` | string(45) | ✅ Mapped | **REQUIRED** - PSN |
| `dangerousGoodsFlashpointValue` | `pieces[].dangerousGoods[].flashpointValue` | number | ✅ Mapped | Celsius |
| `dangerousGoodsPackageGroup` | `pieces[].dangerousGoods[].packageGroup` | string(3) | ✅ Mapped | I, II, III |
| `dangerousGoodsTunnelCode` | `pieces[].dangerousGoods[].tunnelCode` | string(6) | ✅ Mapped | **REQUIRED** - e.g., "B/E" |
| `dangerousGoodsGrossWeight` | `pieces[].dangerousGoods[].grossWeight` | number | ✅ Mapped | **REQUIRED** |
| `dangerousGoodsQuantityMeasurementUnitQualifier` | `pieces[].dangerousGoods[].quantityMeasurementUnitQualifier` | enum | ✅ Mapped | KG or LTR |
| `dangerousGoodsQuantityMeasurementValue` | `pieces[].dangerousGoods[].quantityMeasurementValue` | number | ✅ Mapped | |
| `dangerousGoodsNumberOfPieces` | `pieces[].dangerousGoods[].numberOfPieces` | int | ✅ Mapped | **REQUIRED** |
| `dangerousGoodsPackageType` | `pieces[].dangerousGoods[].packageType` | string(5) | ✅ Mapped | **REQUIRED** - ADR code |
| `dangerousGoodsOfficialNameTechDescription` | `pieces[].dangerousGoods[].officialNameTechDescription` | string(256) | ✅ Mapped | For N.O.S. UN numbers |
| `dangerousGoodsMarinePollutant` | `pieces[].dangerousGoods[].marinePollutant` | boolean | ✅ Mapped | |
| `dangerousGoodsMarinePollutantName` | `pieces[].dangerousGoods[].marinePollutantName` | string(45) | ✅ Mapped | |
| `dangerousGoodsExceptedQuantity` | `pieces[].dangerousGoods[].exceptedQuantity` | boolean | ✅ Mapped | |
| `dangerousGoodsLimitedQuantity` | `pieces[].dangerousGoods[].limitedQuantity` | boolean | ✅ Mapped | |
| `dangerousGoodsEmptyContainer` | `pieces[].dangerousGoods[].emptyContainer` | boolean | ✅ Mapped | |
| `dangerousGoodsEnvironmentHazardous` | `pieces[].dangerousGoods[].environmentHazardous` | boolean | ✅ Mapped | |
| `dangerousGoodsWaste` | `pieces[].dangerousGoods[].waste` | boolean | ✅ Mapped | |

### Additional Services

| Extracted Field | API Field | Type | Status | Notes |
|----------------|-----------|------|--------|-------|
| `additionalServicesCashOnDeliveryAmount` | `additionalServices.cashOnDelivery.amount` | int | ✅ Mapped | **REQUIRED** if present |
| `additionalServicesCashOnDeliveryCurrency` | `additionalServices.cashOnDelivery.currency` | string(3) | ✅ Mapped | **REQUIRED** if present |
| `additionalServicesDangerousGoods` | `additionalServices.dangerousGoods` | boolean | ✅ Mapped | |
| `additionalServicesInsuranceValue` | `additionalServices.insurance.value` | number | ✅ Mapped | **REQUIRED** if present |
| `additionalServicesInsuranceCurrency` | `additionalServices.insurance.currency` | string(3) | ✅ Mapped | **REQUIRED** if present |
| `additionalServicesHighValueShipmentValue` | `additionalServices.highValueShipment.value` | number | ✅ Mapped | **REQUIRED** if present |
| `additionalServicesHighValueShipmentCurrency` | `additionalServices.highValueShipment.currency` | string(3) | ✅ Mapped | **REQUIRED** if present |
| `additionalServicesPreAdvice` | `additionalServices.preAdvice` | boolean | ✅ Mapped | |
| `additionalServicesTailLiftLoading` | `additionalServices.tailLiftLoading` | boolean | ✅ Mapped | |
| `additionalServicesTailLiftUnloading` | `additionalServices.tailLiftUnloading` | boolean | ✅ Mapped | |
| `additionalServicesSideLoadingPickup` | `additionalServices.sideLoadingPickup` | boolean | ✅ Mapped | |
| `additionalServicesSideUnloadingDelivery` | `additionalServices.sideUnloadingDelivery` | boolean | ✅ Mapped | |
| `additionalServicesThermoColdMin` | `additionalServices.thermoCold.min` | number | ✅ Mapped | Temperature range |
| `additionalServicesThermoColdMax` | `additionalServices.thermoCold.max` | number | ✅ Mapped | Temperature range |
| `additionalServicesTimeSlotBookingPickup` | `additionalServices.timeSlotBookingPickup` | boolean | ✅ Mapped | |
| `additionalServicesTimeSlotBookingDelivery` | `additionalServices.timeSlotBookingDelivery` | boolean | ✅ Mapped | |
| `additionalServicesFixedDeliveryDateDate` | `additionalServices.fixedDeliveryDate.date` | date | ✅ Mapped | **REQUIRED** if present |
| `additionalServicesPriorityServiceP10` | `additionalServices.priorityServiceP10` | boolean | ✅ Mapped | |
| `additionalServicesPriorityServiceP12` | `additionalServices.priorityServiceP12` | boolean | ✅ Mapped | |
| `additionalServicesDropOffByConsignor` | `additionalServices.dropOffByConsignor` | boolean | ✅ Mapped | |
| `additionalServicesAfter12Delivery` | `additionalServices.after12Delivery` | boolean | ✅ Mapped | |
| `additionalServicesAvailablePickupTimeFromTime` | `additionalServices.availablePickupTime.fromTime` | time | ✅ Mapped | e.g., '09:30' |
| `additionalServicesAvailablePickupTimeToTime` | `additionalServices.availablePickupTime.toTime` | time | ✅ Mapped | e.g., '14:30' |
| `additionalServicesAvailableDeliveryTimeFromTime` | `additionalServices.availableDeliveryTime.fromTime` | time | ✅ Mapped | e.g., '09:30' |
| `additionalServicesAvailableDeliveryTimeToTime` | `additionalServices.availableDeliveryTime.toTime` | time | ✅ Mapped | e.g., '14:30' |

### Additional Information (Country-Specific)

| Extracted Field | API Field | Type | Status | Notes |
|----------------|-----------|------|--------|-------|
| `additionalInformationCode` | `additionalInformation[].code` | enum | ✅ Mapped | EKAER_FREE, EKAER_NUMBER, SENT_REF, etc. |
| `additionalInformationStringValue` | `additionalInformation[].stringValue` | string | ✅ Mapped | |
| `additionalInformationDateValue` | `additionalInformation[].dateValue` | datetime | ✅ Mapped | |
| `additionalInformationNumericValue` | `additionalInformation[].numericValue` | number | ✅ Mapped | |

---

## 🟡 VALIDATION & CONSTRAINT GAPS

### Critical API Requirements Not Yet Validated

1. **Required Field Validation**
   - ❌ Missing validation: `parties` (min 2, max 6 items)
   - ❌ Missing validation: `payerCode.code` is REQUIRED
   - ❌ Missing validation: `productCode` is REQUIRED
   - ❌ Missing validation: `pieces` is REQUIRED (max 999 items)
   - ❌ Missing validation: Party with freight payer role MUST have `id` (account number)

2. **String Length Constraints**
   - ❌ No length validation on most fields (API has strict max lengths)
   - Examples:
     - `id`: max 13 chars
     - `productCode`: max 3 chars
     - `goodsDescription`: max 70 chars
     - `parties[].name`: max 70 chars
     - `parties[].address.street`: max 40 chars

3. **Numeric Constraints**
   - ❌ No max value validation:
     - `totalNumberOfPieces`: max 999
     - `totalWeight`: max 99999
     - `totalVolume`: max 999
     - `pieces[].numberOfPieces`: min 1, max 999

4. **Enum Validation**
   - ❌ No validation for enum fields:
     - `references[].qualifier`: must be CNR, CNZ, or INV
     - `payerCode.code`: must be DAP, DDP, EXW, or CIP
     - `parties[].type`: must be Consignor, Pickup, Consignee, or Delivery
     - `dangerousGoods[].quantityMeasurementUnitQualifier`: KG or LTR

5. **Conditional Requirements**
   - ❌ `requestedDeliveryDate` required with DHL Eurapid + CDD (product-dependent)
   - ❌ `additionalServices.fixedDeliveryDate.date` required if fixedDeliveryDate present
   - ❌ Ireland postal codes: must use COUNTY NAME instead of EirCode

6. **Data Type Validation**
   - ❌ Date format validation (ISO date format)
   - ❌ Time format validation (HH:mm format for availablePickupTime/deliveryTime)
   - ❌ Currency code validation (ISO 4217)
   - ❌ Country code validation (ISO 3166-1)

---

## 🔴 POTENTIAL USER HURDLES

### Extraction Challenges

1. **Multiple Party Types**
   - **Issue:** Documents may not clearly distinguish between Consignor/Pickup or Consignee/Delivery addresses
   - **Impact:** Users need to manually assign correct party types
   - **Solution Needed:** Intelligent address classification or user prompt

2. **Dangerous Goods Complex Fields**
   - **Issue:** DG data requires precise ADR codes (UN numbers, class, tunnel codes, package types)
   - **Impact:** High probability of extraction errors or missing data
   - **Solution Needed:** Validation against ADR master data, user-friendly DG form

3. **Product Code Selection**
   - **Issue:** Documents don't contain DHL-specific product codes (ECI, DHL Eurapid, etc.)
   - **Impact:** Users must manually select from Product Manual
   - **Solution Needed:** Smart suggestion based on route, weight, timing requirements

4. **Payer Code & Account Numbers**
   - **Issue:** Freight payer identification requires business logic (DAP/DDP/EXW/CIP)
   - **Impact:** Users must understand Incoterms and map to correct party account number
   - **Solution Needed:** Incoterms guidance, account number lookup by party name

5. **Reference Qualifiers**
   - **Issue:** Generic reference numbers need classification (Consignor ref vs Invoice vs Consignee ref)
   - **Impact:** Manual review required to assign correct qualifier
   - **Solution Needed:** Pattern recognition for invoice numbers, PO numbers, etc.

6. **Measurement Unit Conversions**
   - **Issue:** Documents may use lbs, inches, cubic feet instead of kg, cm, m³
   - **Impact:** Conversion errors or missing conversions
   - **Solution Needed:** Auto-detect units and convert, flag for review

7. **Country-Specific Additional Information**
   - **Issue:** Hungarian EKAER, Polish SENT, Romanian UIT are rarely on standard documents
   - **Impact:** Users from these countries will always need to add manually
   - **Solution Needed:** Country-based pre-fill prompts

8. **Time Format Extraction**
   - **Issue:** Available pickup/delivery times may be written as "9:30 AM - 2:30 PM" instead of 24hr format
   - **Impact:** Format conversion errors
   - **Solution Needed:** Time parser with 12hr/24hr support

### Data Quality Issues

9. **Incomplete Address Data**
   - **Issue:** Scanned documents may have incomplete addresses
   - **Impact:** Missing required fields (postalCode, countryCode)
   - **Solution Needed:** Address validation API, geocoding fallback

10. **Package Type Codes**
    - **Issue:** Documents say "Pallet" but API needs specific code "PAL"
    - **Impact:** Need package type mapping dictionary
    - **Solution Needed:** Fuzzy matching to standardized codes

11. **Total Calculations**
    - **Issue:** Mismatch between sum of pieces and totalWeight/totalNumberOfPieces
    - **Impact:** API validation errors
    - **Solution Needed:** Auto-calculate totals, flag discrepancies

12. **VAT/EORI Numbers**
    - **Issue:** May be present but in non-standard formats or mixed with other IDs
    - **Impact:** Field extraction errors
    - **Solution Needed:** Regex validation per country format

---

## 📋 REQUIRED API FIELDS CHECKLIST

When creating a freight shipment, users MUST provide:

### Mandatory Root Fields
- [ ] `productCode` (3 chars) - DHL product code
- [ ] `payerCode.code` (3 chars) - DAP/DDP/EXW/CIP
- [ ] `parties[]` (min 2, max 6) - Party array

### Mandatory Party Fields (for each party)
- [ ] `type` - Consignor/Pickup/Consignee/Delivery
- [ ] `name` (max 70 chars)
- [ ] `address.street` (max 40 chars) - includes house number
- [ ] `address.cityName` (max 40 chars)
- [ ] `address.postalCode` (max 12 chars) - use COUNTY for Ireland
- [ ] `address.countryCode` (2 chars) - ISO 3166-1
- [ ] `id` (account number) - **REQUIRED for the party paying freight** (determined by payerCode)

### Mandatory Pieces Fields (at least 1 piece)
- [ ] `packageType` (4 chars) - e.g., 'PAL'
- [ ] `numberOfPieces` (1-999)
- [ ] `weight` (kg, max 99999)

### Mandatory Dangerous Goods Fields (if DG present)
- [ ] `unNumber` (int)
- [ ] `properShippingName` (max 45 chars)
- [ ] `adrClass` (max 7 chars) - can be empty for LQ/EQ
- [ ] `tunnelCode` (max 6 chars)
- [ ] `grossWeight` (number)
- [ ] `numberOfPieces` (int)
- [ ] `packageType` (max 5 chars) - ADR code

### Conditional Required Fields
- [ ] `requestedDeliveryDate` - Required with DHL Eurapid + Committed Delivery Date
- [ ] `additionalServices.fixedDeliveryDate.date` - Required if using fixedDeliveryDate
- [ ] `additionalServices.cashOnDelivery.amount` + `currency` - Both required if COD used
- [ ] `additionalServices.insurance.value` + `currency` - Both required if insurance used

---

## 🔧 RECOMMENDED ENHANCEMENTS

### 1. Field Validation Module
**Priority:** HIGH
**Description:** Add pre-submission validation against DHL API constraints
**Benefit:** Catch errors before API submission, reduce user frustration

### 2. Product Code Recommendation Engine
**Priority:** HIGH
**Description:** Suggest appropriate productCode based on route, weight, dates
**Benefit:** Reduce manual product selection errors

### 3. Payer Code / Account Number Mapper
**Priority:** HIGH
**Description:** Map Incoterms to payer codes, lookup account numbers by party name
**Benefit:** Automate complex business logic

### 4. Address Validation & Geocoding
**Priority:** MEDIUM
**Description:** Validate addresses, fill missing postal codes via geocoding API
**Benefit:** Improve address data quality

### 5. Package Type Dictionary
**Priority:** MEDIUM
**Description:** Map common package descriptions to DHL codes (fuzzy matching)
**Benefit:** Reduce manual code lookup

### 6. Unit Conversion Helper
**Priority:** MEDIUM
**Description:** Auto-detect and convert lbs/inches/ft³ to kg/cm/m³
**Benefit:** Support US-formatted documents

### 7. Dangerous Goods Wizard
**Priority:** MEDIUM
**Description:** User-friendly DG entry form with ADR code lookup
**Benefit:** Improve DG data accuracy

### 8. Country-Specific Prompts
**Priority:** LOW
**Description:** Auto-prompt for EKAER (Hungary), SENT (Poland), UIT (Romania) based on country
**Benefit:** Reduce missing country-specific data

### 9. Total Calculation Validator
**Priority:** LOW
**Description:** Auto-calculate and validate totalWeight/totalNumberOfPieces vs. pieces sum
**Benefit:** Catch arithmetic errors

### 10. Time Format Normalizer
**Priority:** LOW
**Description:** Parse 12hr/24hr time formats, convert to HH:mm
**Benefit:** Support varied document formats

---

## 📊 FIELD EXTRACTION ACCURACY TRACKING

Use this section to track extraction accuracy as you test with real documents:

| Field Category | Extraction Accuracy | Common Issues | Priority |
|----------------|---------------------|---------------|----------|
| Shipment Basic Fields | ⬜ Not tested yet | | |
| Parties (Addresses) | ⬜ Not tested yet | | |
| Pieces (Cargo) | ⬜ Not tested yet | | |
| Dangerous Goods | ⬜ Not tested yet | | |
| Additional Services | ⬜ Not tested yet | | |
| References | ⬜ Not tested yet | | |
| Country-Specific | ⬜ Not tested yet | | |

**Legend:** 🟢 >90% accurate | 🟡 70-90% | 🟠 50-70% | 🔴 <50% | ⬜ Not tested

---

## 📝 NEXT STEPS

1. **Validation Implementation**
   - Add field length validation
   - Add enum validation
   - Add required field checks
   - Add numeric constraint validation

2. **User Testing**
   - Test with sample freight documents
   - Identify most common extraction errors
   - Prioritize fixes based on frequency

3. **Enhancement Prioritization**
   - Review recommended enhancements
   - Assign priorities based on user needs
   - Create implementation roadmap

4. **Documentation**
   - User guide for manual field entry
   - Product code selection guide
   - Dangerous goods quick reference

---

**Maintained by:** [Your Team]
**For questions:** Contact DEV team or see meeting notes in `02-MEETING-NOTES.md`
