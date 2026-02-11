# Freight Extraction - Testing Tracker

**Purpose:** Track testing progress, document test cases, and record extraction accuracy
**Last Updated:** 2026-02-11

---

## Test Document Inventory

### Documents Collected

| Doc ID | Document Type | Origin Country | Dest Country | Has DG | Has Special Services | Status | Notes |
|--------|---------------|----------------|--------------|--------|---------------------|--------|-------|
| FT-001 | [Type] | [Country] | [Country] | ☐ | ☐ | ⬜ Not tested | |
| FT-002 |  |  |  | ☐ | ☐ | ⬜ Not tested | |
| FT-003 |  |  |  | ☐ | ☐ | ⬜ Not tested | |

**Status Legend:** ⬜ Not tested | 🟡 In progress | 🟢 Passed | 🔴 Failed | ⚠️ Partial

---

## Test Case Template

### TC-[Number]: [Test Case Name]

**Test ID:** TC-001
**Document ID:** FT-001
**Tester:** [Name]
**Test Date:** [YYYY-MM-DD]
**Priority:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low

**Test Objective:**
[What are you testing]

**Preconditions:**
- [ ] Document uploaded to system
- [ ] Profile selected: [Profile name]
- [ ] Processing completed without errors

**Test Steps:**
1. Upload document FT-001
2. Run extraction pipeline
3. Review extracted data
4. Compare against manual ground truth
5. Submit to DHL sandbox API (if available)

**Expected Results:**
- All required fields extracted
- Field values match ground truth
- API accepts submission without errors

**Actual Results:**
[Fill in after testing]

**Field Extraction Results:**

| Field Category | Total Fields | Correctly Extracted | Partially Correct | Missing | Accuracy % |
|----------------|--------------|---------------------|-------------------|---------|------------|
| Shipment Basic | 13 | - | - | - | - |
| Parties | 6 parties × 12 fields | - | - | - | - |
| Pieces | X pieces × 13 fields | - | - | - | - |
| Dangerous Goods | X DG × 21 fields | - | - | - | - |
| Additional Services | 20 fields | - | - | - | - |
| References | X refs × 2 fields | - | - | - | - |
| Additional Info | X info × 4 fields | - | - | - | - |
| **TOTAL** | **X** | **X** | **X** | **X** | **X%** |

**Detailed Field Comparison:**

| Field Path | Expected Value | Extracted Value | Match? | Issue |
|------------|----------------|-----------------|--------|-------|
| id | [value] | [value] | ✅ / ❌ | |
| productCode | [value] | [value] | ✅ / ❌ | |
| parties[0].name | [value] | [value] | ✅ / ❌ | |
| ... | ... | ... | ... | |

**Issues Found:**
1. [Issue description] - Severity: [Critical/High/Medium/Low]
2. [Issue description] - Severity: [Critical/High/Medium/Low]

**Test Result:** 🟢 PASS | 🔴 FAIL | ⚠️ PARTIAL
**Overall Accuracy:** [X]%
**Recommendation:** [Approve for production / Needs fixes / Major rework required]

---

## Test Execution Log

### Week 2026-W07 (Feb 10-16)

| Date | Test ID | Document ID | Tester | Result | Accuracy | Notes |
|------|---------|-------------|--------|--------|----------|-------|
| 2026-02-11 | Setup | - | [You] | ⚙️ | - | Created test framework |
|  |  |  |  |  |  |  |

---

## Accuracy Benchmarks by Document Type

### Standard Freight Waybill

| Field Category | Target Accuracy | Current Accuracy | Status | Priority Fixes |
|----------------|-----------------|------------------|--------|---------------|
| Shipment Basic | ≥95% | [Not tested] | ⬜ | - |
| Parties | ≥90% | [Not tested] | ⬜ | - |
| Pieces | ≥90% | [Not tested] | ⬜ | - |
| Dangerous Goods | ≥85% | [Not tested] | ⬜ | - |
| Additional Services | ≥80% | [Not tested] | ⬜ | - |
| References | ≥85% | [Not tested] | ⬜ | - |
| **Overall Target** | **≥90%** | **[TBD]** | ⬜ | - |

**Status Legend:** 🟢 Meeting target | 🟡 Close (within 5%) | 🔴 Below target | ⬜ Not tested

---

## API Validation Testing

### DHL Freight API Sandbox Tests

**Sandbox Endpoint:** https://api-sandbox.dhl.com/freight/shipping/orders/v1

| Test ID | Document ID | Submission Date | Response Code | Status | Error Messages |
|---------|-------------|-----------------|---------------|--------|---------------|
| API-001 | [Doc ID] | [Date] | [200/400] | [Success/Fail] | [If 400, list validation errors] |
|  |  |  |  |  |  |

**Common Validation Errors:**
1. [Error code] - [Field] - [Message] - Frequency: [X times]
2. [Error code] - [Field] - [Message] - Frequency: [X times]

---

## Regression Testing

After code changes, re-run these test cases to ensure no regressions:

| Change Description | Date | Affected Module | Regression Tests | Result |
|-------------------|------|-----------------|------------------|--------|
| [Change description] | [Date] | [Module] | TC-001, TC-003, TC-005 | [Pass/Fail] |
|  |  |  |  |  |

---

## Test Data Management

### Ground Truth Data

For each test document, maintain ground truth in JSON format:

**Location:** `icap-v7-master/tests/freight/ground_truth/`

**Naming:** `FT-[DocID]_ground_truth.json`

**Example:**
```json
{
  "document_id": "FT-001",
  "document_type": "DHL_Freight_Waybill",
  "ground_truth": {
    "id": "",
    "productCode": "ECI",
    "pickupDate": "2026-02-15",
    "parties": [
      {
        "type": "Consignor",
        "name": "ABC Manufacturing GmbH",
        "address": {
          "street": "Industriestrasse 45",
          "cityName": "Munich",
          "postalCode": "80939",
          "countryCode": "DE"
        }
      }
    ],
    "pieces": [...],
    ...
  }
}
```

### Test Scripts

**Location:** `icap-v7-master/tests/freight/`

**Scripts to create:**
1. `test_extraction_accuracy.py` - Compare extracted vs ground truth
2. `test_api_validation.py` - Submit to DHL sandbox and check responses
3. `test_field_constraints.py` - Validate length, numeric bounds, enums
4. `generate_test_report.py` - Generate HTML test report

---

## User Acceptance Testing (UAT)

### UAT Session Template

**Session:** UAT-[Number]
**Date:** [YYYY-MM-DD]
**Participants:** [User names]
**Documents Tested:** [Doc IDs]

**Feedback:**
1. [User feedback point]
2. [User feedback point]

**User Satisfaction Score:** [1-10]
**Would recommend to others:** ☐ Yes ☐ No

**Issues Reported:**
- [Issue]
- [Issue]

**Feature Requests:**
- [Request]
- [Request]

---

## Testing Milestones

- [ ] **Milestone 1:** Collect 10 diverse test documents
- [ ] **Milestone 2:** Achieve 80% overall extraction accuracy
- [ ] **Milestone 3:** Pass 5 consecutive DHL sandbox API submissions
- [ ] **Milestone 4:** User acceptance testing with 3+ users
- [ ] **Milestone 5:** Achieve 90% overall extraction accuracy
- [ ] **Milestone 6:** Production deployment approval

---

**Note:** Update this document after every test session. Accurate testing data is critical for making informed decisions about production readiness.
