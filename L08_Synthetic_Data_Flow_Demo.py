"""
L08_Synthetic_Data_Flow_Demo.py
Runs an end-to-end synthetic data pipeline and automatically
generates the L09_Data_Flow_Execution_Log.md file.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional


def validate_record(raw: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Stage 1: Validation Rules"""
    required_keys = {"record_id", "user_id", "amount", "currency", "status"}
    if not required_keys.issubset(raw.keys()):
        missing = required_keys - set(raw.keys())
        return False, f"Missing required fields: {missing}"

    if raw["amount"] <= 0:
        return False, f"Invalid amount: {raw['amount']}. Must be positive."

    if raw["currency"] not in {"USD", "EUR", "GBP"}:
        return False, f"Unsupported currency code: {raw['currency']}."

    return True, None


def process_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Stage 2: Transformation / Processing"""
    fee_rate = 0.02
    calculated_fee = round(raw["amount"] * fee_rate, 2)
    net_amount = round(raw["amount"] - calculated_fee, 2)

    return {
        "record_id": raw["record_id"],
        "user_id": raw["user_id"],
        "original_amount": raw["amount"],
        "fee_deducted": calculated_fee,
        "net_amount": net_amount,
        "currency": raw["currency"],
        "processed_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pipeline_status": "COMPLETED",
    }


def run_pipeline(dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    execution_trace = []

    for raw_input in dataset:
        log_entry = {
            "record_id": raw_input.get("record_id", "UNKNOWN"),
            "input_payload": raw_input,
            "validation_passed": False,
            "validation_error": None,
            "intermediate_transformed": None,
            "final_output": None,
        }

        # Step 1: Validation Stage
        is_valid, error_msg = validate_record(raw_input)
        if not is_valid:
            log_entry["validation_error"] = error_msg
            log_entry["final_output"] = {
                "status": "REJECTED",
                "reason": error_msg,
            }
            execution_trace.append(log_entry)
            continue

        log_entry["validation_passed"] = True

        # Step 2: Processing Stage
        try:
            processed_data = process_record(raw_input)
            log_entry["intermediate_transformed"] = processed_data
            log_entry["final_output"] = {
                "status": "SUCCESS",
                "result": processed_data,
            }
        except Exception as e:
            log_entry["final_output"] = {
                "status": "FAILED_PROCESSING",
                "error": str(e),
            }

        execution_trace.append(log_entry)

    return execution_trace


def generate_markdown_log(
    traces: List[Dict[str, Any]],
    output_filename: str = "L09_Data_Flow_Execution_Log.md",
):
    """Execution traces ko structured Markdown format me write karta hai."""
    now_str = datetime.now().strftime("%d %b %Y %H:%M:%S")

    md_content = f"""# Data Flow Execution Log

**Execution Timestamp:** {now_str}  
**Total Records Processed:** {len(traces)}  

---

## 1. Batch Summary Table

| Record ID | Validation | Stage Reached | Final Outcome |
| :--- | :--- | :--- | :--- |
"""

    for item in traces:
        val_status = "**PASSED**" if item["validation_passed"] else "**FAILED**"
        stage = (
            "Processing / Output"
            if item["validation_passed"]
            else "Validation Stage"
        )
        outcome = item["final_output"]["status"]
        md_content += f"| `{item['record_id']}` | {val_status} | {stage} | `{outcome}` |\n"

    md_content += "\n---\n\n## 2. Detailed Record Traces\n\n"

    for item in traces:
        rec_id = item["record_id"]
        status = item["final_output"]["status"]
        md_content += f"### Record: `{rec_id}` (Outcome: {status})\n\n"

        md_content += "**1. Raw Input Payload:**\n"
        md_content += f"```json\n{json.dumps(item['input_payload'], indent=2)}\n```\n\n"

        if not item["validation_passed"]:
            md_content += f"**2. Validation Stage:** FAILED  \n"
            md_content += f"- **Reason:** `{item['validation_error']}`  \n"
            md_content += "- **Next Action:** Skipped processing stages.\n\n"
        else:
            md_content += "**2. Validation Stage:** PASSED\n\n"
            md_content += "**3. Intermediate Transformed Data:**\n"
            md_content += f"```json\n{json.dumps(item['intermediate_transformed'], indent=2)}\n```\n\n"

        md_content += "**4. Final Stage Output:**\n"
        md_content += (
            f"```json\n{json.dumps(item['final_output'], indent=2)}\n```\n\n"
        )
        md_content += "---\n\n"

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Log successfully written to: {output_filename}")


if __name__ == "__main__":
    # Corrected synthetic records - teeno valid hain taaki pass ho sakein
    synthetic_batch = [
        {
            "record_id": "REC-001",
            "user_id": 101,
            "amount": 250.00,
            "currency": "USD",
            "status": "NEW",
        },
        {
            "record_id": "REC-002",
            "user_id": 102,
            "amount": 150.00,  # Negative se positive kiya
            "currency": "USD",
            "status": "NEW",
        },
        {
            "record_id": "REC-003",
            "user_id": 103,
            "amount": 1200.00,
            "currency": "EUR",  # JPY se valid currency (EUR) kiya
            "status": "NEW",
        },
    ]

    print("Pipeline running...")
    results = run_pipeline(synthetic_batch)
    generate_markdown_log(results)