# Data Flow Execution Log

**Execution Timestamp:** 24 Oct 2026 22:00:01  
**Total Records Processed:** 3  

---

## 1. Batch Summary Table

| Record ID | Validation | Stage Reached | Final Outcome |
| :--- | :--- | :--- | :--- |
| `REC-001` | **PASSED** | Processing / Output | `SUCCESS` |
| `REC-002` | **PASSED** | Processing / Output | `SUCCESS` |
| `REC-003` | **PASSED** | Processing / Output | `SUCCESS` |

---

## 2. Detailed Record Traces

### Record: `REC-001` (Outcome: SUCCESS)

**1. Raw Input Payload:**
```json
{
  "record_id": "REC-001",
  "user_id": 101,
  "amount": 250.0,
  "currency": "USD",
  "status": "NEW"
}
```

**2. Validation Stage:** PASSED

**3. Intermediate Transformed Data:**
```json
{
  "record_id": "REC-001",
  "user_id": 101,
  "original_amount": 250.0,
  "fee_deducted": 5.0,
  "net_amount": 245.0,
  "currency": "USD",
  "processed_at": "2026-10-24T22:00:01Z",
  "pipeline_status": "COMPLETED"
}
```

**4. Final Stage Output:**
```json
{
  "status": "SUCCESS",
  "result": {
    "record_id": "REC-001",
    "user_id": 101,
    "original_amount": 250.0,
    "fee_deducted": 5.0,
    "net_amount": 245.0,
    "currency": "USD",
    "processed_at": "2026-10-24T22:00:01Z",
    "pipeline_status": "COMPLETED"
  }
}
```

---

### Record: `REC-002` (Outcome: SUCCESS)

**1. Raw Input Payload:**
```json
{
  "record_id": "REC-002",
  "user_id": 102,
  "amount": 150.0,
  "currency": "USD",
  "status": "NEW"
}
```

**2. Validation Stage:** PASSED

**3. Intermediate Transformed Data:**
```json
{
  "record_id": "REC-002",
  "user_id": 102,
  "original_amount": 150.0,
  "fee_deducted": 3.0,
  "net_amount": 147.0,
  "currency": "USD",
  "processed_at": "2026-10-24T22:00:01Z",
  "pipeline_status": "COMPLETED"
}
```

**4. Final Stage Output:**
```json
{
  "status": "SUCCESS",
  "result": {
    "record_id": "REC-002",
    "user_id": 102,
    "original_amount": 150.0,
    "fee_deducted": 3.0,
    "net_amount": 147.0,
    "currency": "USD",
    "processed_at": "2026-10-24T22:00:01Z",
    "pipeline_status": "COMPLETED"
  }
}
```

---

### Record: `REC-003` (Outcome: SUCCESS)

**1. Raw Input Payload:**
```json
{
  "record_id": "REC-003",
  "user_id": 103,
  "amount": 1200.0,
  "currency": "EUR",
  "status": "NEW"
}
```

**2. Validation Stage:** PASSED

**3. Intermediate Transformed Data:**
```json
{
  "record_id": "REC-003",
  "user_id": 103,
  "original_amount": 1200.0,
  "fee_deducted": 24.0,
  "net_amount": 1176.0,
  "currency": "EUR",
  "processed_at": "2026-10-24T22:00:01Z",
  "pipeline_status": "COMPLETED"
}
```

**4. Final Stage Output:**
```json
{
  "status": "SUCCESS",
  "result": {
    "record_id": "REC-003",
    "user_id": 103,
    "original_amount": 1200.0,
    "fee_deducted": 24.0,
    "net_amount": 1176.0,
    "currency": "EUR",
    "processed_at": "2026-10-24T22:00:01Z",
    "pipeline_status": "COMPLETED"
  }
}
```

---

