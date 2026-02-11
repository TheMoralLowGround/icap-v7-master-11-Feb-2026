# User Hurdles & Solutions - DHL Freight Extraction

**Purpose:** Track actual problems users encounter and document solutions
**Last Updated:** 2026-02-11

---

## How to Use This Document

1. **When a user reports an issue**, add it under "Active Hurdles"
2. **Document the solution** once resolved
3. **Move to "Resolved Hurdles"** after testing confirms fix
4. **Update FAQ** for common questions

---

## 🔴 ACTIVE HURDLES

### Hurdle Template
```markdown
### H-[Number]: [Short Title]

**Reported By:** [User name]
**Date:** [YYYY-MM-DD]
**Severity:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low
**Frequency:** [How often this occurs]

**Problem Description:**
[What happened]

**User Impact:**
[How this affects the user's workflow]

**Steps to Reproduce:**
1.
2.
3.

**Current Workaround:**
[If any]

**Proposed Solution:**
[What needs to be fixed]

**Status:** ⬜ Not Started | 🟡 In Progress | 🟢 Resolved | 🔴 Blocked

**Assignee:** [DEV team member]
**Target Date:** [YYYY-MM-DD]

**Resolution Notes:**
[Details once resolved]
```

---

### H-001: Product Code Selection Confusion

**Reported By:** [User]
**Date:** [To be filled]
**Severity:** 🟠 High
**Frequency:** Every shipment

**Problem Description:**
Users don't know which DHL product code to select (ECI, Eurapid, EuroConnect, etc.) because the freight document doesn't contain this information.

**User Impact:**
- Must manually research product codes in DHL Product Manual
- Slows down processing time
- Risk of selecting wrong product leading to booking errors

**Steps to Reproduce:**
1. Extract data from standard freight waybill
2. Reach productCode field
3. Field is empty or contains non-DHL code
4. User must stop and look up correct code

**Current Workaround:**
- Keep DHL Product Manual open in separate window
- Manually determine product based on route and requirements

**Proposed Solution:**
- Build product recommendation engine based on:
  - Origin/destination countries
  - Weight and volume
  - Pickup/delivery dates (time-sensitive?)
  - Special services (dangerous goods, tail lift, etc.)
- Integrate with DHL GET /products API to validate
- Provide top 3 suggestions with explanations

**Status:** ⬜ Not Started

**Assignee:** [To be assigned]
**Target Date:** [TBD]

---

### H-002: Party Type Assignment Ambiguity

**Reported By:** [User]
**Date:** [To be filled]
**Severity:** 🟡 Medium
**Frequency:** ~30% of documents

**Problem Description:**
Freight documents often show only "Shipper" and "Receiver" addresses, but DHL API requires distinguishing between:
- Consignor (goods owner) vs Pickup (physical pickup location)
- Consignee (goods recipient) vs Delivery (physical delivery location)

**User Impact:**
- Must manually determine if addresses are same or different
- Risk of assigning wrong party type
- Could cause pickup/delivery failures if locations are incorrect

**Steps to Reproduce:**
1. Extract document with "Shipper" and "Receiver" labels
2. System extracts as single Consignor and single Consignee
3. User must manually check if pickup/delivery locations differ
4. Must manually add separate Pickup/Delivery parties if different

**Current Workaround:**
- Users manually review every shipment
- Add Pickup or Delivery parties manually when needed

**Proposed Solution:**
- Add clarifying questions during extraction:
  - "Is pickup location same as consignor address?"
  - "Is delivery location same as consignee address?"
- Store common business patterns (e.g., "Always different for Customer X")
- Highlight when addresses appear similar but not identical

**Status:** ⬜ Not Started

**Assignee:** [To be assigned]
**Target Date:** [TBD]

---

### H-003: Missing Account Numbers for Freight Payer

**Reported By:** [User]
**Date:** [To be filled]
**Severity:** 🔴 Critical
**Frequency:** ~50% of documents

**Problem Description:**
DHL API requires the party paying freight (determined by payerCode: DAP/DDP/EXW/CIP) to have an account number (id field). Documents rarely contain DHL account numbers.

**User Impact:**
- Shipment booking fails at API submission
- Must look up account numbers in separate system
- Major workflow blocker

**Steps to Reproduce:**
1. Extract document with parties
2. Determine payerCode (e.g., DAP = consignee pays)
3. Consignee party has no account number
4. API rejects submission

**Current Workaround:**
- Maintain manual lookup table of company names to account numbers
- Users search by company name before submitting

**Proposed Solution:**
- Build account number lookup service
  - Search by exact company name
  - Fuzzy matching for variations (ABC Corp vs ABC Corporation)
  - Store recent lookups for faster access
- Integrate with DHL customer database if available
- Auto-populate account number when party name matches known customer

**Status:** ⬜ Not Started

**Assignee:** [To be assigned]
**Target Date:** [TBD]

---

## 🟢 RESOLVED HURDLES

### HR-001: [Example - Delete this once you have real resolved hurdles]

**Reported By:** Example User
**Date:** 2026-02-10
**Severity:** 🟡 Medium
**Resolution Date:** 2026-02-11

**Problem Description:**
Weight field was extracted in lbs but API requires kg.

**Solution Implemented:**
Added automatic unit detection and conversion in dimension_parser_agent.py. System now recognizes "lbs", "lb", "pounds" and converts to kg.

**Validation:**
- Tested with 50 sample documents
- 100% conversion accuracy
- Users confirmed fix works

**Code Changes:**
- `auto-extraction/intelligent_parsers_module/dimension_parser_agent.py:145-167`

---

## 📚 USER FAQ

### Q: Why do I need to select a product code manually?
**A:** Freight documents don't include DHL-specific product codes. The code determines pricing, transit time, and available services. We're building a recommendation engine to help (see H-001).

### Q: What's the difference between Consignor and Pickup?
**A:**
- **Consignor:** The party who owns the goods (seller/shipper)
- **Pickup:** The physical location where DHL collects the goods
- Usually the same, but can differ (e.g., goods stored at warehouse, but owned by manufacturer)

### Q: How do I know which Incoterm/payer code to use?
**A:** Check your sales contract:
- **EXW** (Ex Works): Consignor pays for nothing, consignee pays all transport
- **DAP** (Delivered At Place): Consignor pays transport, consignee pays import duties
- **DDP** (Delivered Duty Paid): Consignor pays everything including duties
- **CIP** (Carriage and Insurance Paid): Consignor pays transport + insurance

### Q: What if the document doesn't have all required fields?
**A:** You'll need to fill them manually based on your business knowledge:
- **productCode:** Choose based on route and urgency
- **Account numbers:** Look up in your customer database
- **Package types:** Use standardized codes (PAL for pallet, etc.)

### Q: How accurate is the dangerous goods extraction?
**A:** Dangerous goods require highly precise data (UN numbers, ADR classes, tunnel codes). We recommend:
1. Review all extracted DG data
2. Validate against ADR/IMDG code books
3. Use DG Office software if available for complex shipments

---

## 📊 HURDLE METRICS

Track how many hurdles users face over time:

| Week | Total Issues | Critical | High | Medium | Low | Resolution Rate |
|------|--------------|----------|------|--------|-----|-----------------|
| 2026-W07 | 0 | 0 | 0 | 0 | 0 | - |
|  |  |  |  |  |  |  |

---

## 🎯 PRIORITIZATION CRITERIA

When deciding which hurdles to solve first, consider:

1. **Frequency:** How many users hit this issue?
2. **Severity:** Does it block workflow or just slow it down?
3. **Workaround Difficulty:** Is the manual fix easy or complex?
4. **Development Effort:** Quick fix or major feature?
5. **User Impact:** High-value users affected?

**Priority Score Formula:**
```
Priority = (Frequency × Severity × Workaround_Difficulty) / Development_Effort
```

---

**Note:** Keep this document updated as users report issues. This is your living guide to improving the freight extraction system.
