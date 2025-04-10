# Plan: Refine QuanticsToolInput Validation and Make All Fields Required

**Objective:** Modify the `QuanticsToolInput` Pydantic model in `chat-agent/src/react_agent/tools.py` to enforce specific validation rules and ensure all fields are required.

**Asset Codes Allowed:**
`["ES", "NQ", "DOW", "RUSS", "VIX", "EURUSD", "BP", "AUD", "JY", "GC", "HG", "SI", "PL", "CL", "NG", "CORN", "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT"]`

**Validation Rules (Post-Change):**

The `QuanticsToolInput` Pydantic model will enforce the following rules on the input JSON object:

*   **`asset`:**
    *   **Type:** Must be a `string`.
    *   **Required:** Yes.
    *   **Constraint:** Must be one of the predefined `Asset Codes Allowed` (using `Literal`).
*   **`start_date`:**
    *   **Type:** Must be an `integer`.
    *   **Required:** Yes.
    *   **Constraint:** Must be between `20120101` and `20241231` (inclusive, using `ge=20120101, le=20241231`). Represents `YYYYMMDD`.
*   **`end_date`:**
    *   **Type:** Must be an `integer`.
    *   **Required:** Yes.
    *   **Constraint:** Must be between `20120101` and `20241231` (inclusive, using `ge=20120101, le=20241231`). Represents `YYYYMMDD`. Also, must be greater than or equal to `start_date` (enforced via custom validator).
*   **`bar_period`:**
    *   **Type:** Must be an `integer`.
    *   **Required:** Yes.
    *   **Constraint:** Must be greater than or equal to 1 (`ge=1`). Represents time frame in *minutes*.
*   **`time_filters`:**
    *   **Type:** Must be a `dictionary` mapping strings to lists of booleans (`Dict[str, List[bool]]`).
    *   **Required:** Yes (Planned change).
    *   **Constraint:** Pydantic enforces the basic type (`Dict[str, List[bool]]`). A custom validator will enforce required keys (`"months"`, `"daysOfWeek"`, `"daysOfMonth"`) and exact list lengths (12, 5, 31 respectively).
*   **`trading_hours`:**
    *   **Type:** Must be a `dictionary` mapping strings to integers (`Dict[str, int]`).
    *   **Required:** Yes (Planned change).
    *   **Constraint:** Pydantic enforces the basic type (`Dict[str, int]`). A custom validator will enforce required keys (`"startHour"`, `"startMin"`, `"endHour"`, `"endMin"`) and valid value ranges (Hour: 0-23, Minute: 0-59).

**Tasks:**

1.  **Define Asset Literal:**
    *   **Action:** Import `Literal` from `typing` and define a type alias using the allowed asset codes.
    *   **File:** `chat-agent/src/react_agent/tools.py`

2.  **Modify `asset` Field:**
    *   **Action:** Update the Pydantic model definition for `asset`.
    *   **Details:** Change type hint to the new `Literal` type. Update description.
    *   **File:** `chat-agent/src/react_agent/tools.py`

3.  **Modify `start_date` Field:**
    *   **Action:** Update the Pydantic model definition for `start_date`.
    *   **Details:** Add `ge=20120101, le=20241231` constraints. Update description.
    *   **File:** `chat-agent/src/react_agent/tools.py`

4.  **Modify `end_date` Field:**
    *   **Action:** Update the Pydantic model definition for `end_date`.
    *   **Details:** Add `ge=20120101, le=20241231` constraints. Update description.
    *   **File:** `chat-agent/src/react_agent/tools.py`

5.  **Add `end_date` Validator:**
    *   **Action:** Implement a Pydantic validator within the `QuanticsToolInput` model.
    *   **Details:** Ensure `end_date` is greater than or equal to `start_date`. Import necessary Pydantic components (`validator` or `model_validator`).
    *   **File:** `chat-agent/src/react_agent/tools.py`

9.  **Add `time_filters` Validator:**
    *   **Action:** Implement a Pydantic validator within the `QuanticsToolInput` model.
    *   **Details:** Ensure the dictionary contains exactly the keys `"months"`, `"daysOfWeek"`, `"daysOfMonth"`. Ensure the corresponding boolean lists have lengths 12, 5, and 31 respectively.
    *   **File:** `chat-agent/src/react_agent/tools.py`

10. **Add `trading_hours` Validator:**
    *   **Action:** Implement a Pydantic validator within the `QuanticsToolInput` model.
    *   **Details:** Ensure the dictionary contains exactly the keys `"startHour"`, `"startMin"`, `"endHour"`, `"endMin"`. Ensure hours are between 0-23 and minutes are between 0-59.
    *   **File:** `chat-agent/src/react_agent/tools.py`

6.  **Modify `bar_period` Field:**
    *   **Action:** Update the Pydantic model definition for `bar_period`.
    *   **Details:** Ensure `ge=1` constraint is present. Update description to specify *minutes*.
    *   **File:** `chat-agent/src/react_agent/tools.py`

7.  **Modify `time_filters` Field:**
    *   **Action:** Update the Pydantic model definition for `time_filters`.
    *   **Details:** Remove `Optional[...]` and `default=None`. Update description to indicate it's required and mention expected structure.
    *   **File:** `chat-agent/src/react_agent/tools.py`

8.  **Modify `trading_hours` Field:**
    *   **Action:** Update the Pydantic model definition for `trading_hours`.
    *   **Details:** Remove `Optional[...]` and `default=None`. Update description to indicate it's required and mention expected structure.
    *   **File:** `chat-agent/src/react_agent/tools.py`

**Implementation Steps (Code Mode):**

1.  Read `chat-agent/src/react_agent/tools.py`.
2.  Prepare an `apply_diff` patch incorporating all the modifications outlined in the tasks above (Literal definition, field updates, `end_date` validator addition, `time_filters` validator addition, `trading_hours` validator addition).
3.  Apply the diff to the file.
4.  Verify the changes.