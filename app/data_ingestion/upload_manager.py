# ============================================================
# DOLLARGUARD AI - UPLOAD MANAGER
# Real Data Upload, Detection, Mapping & Validation
# ============================================================

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

USER_UPLOADS_DIR = PROJECT_ROOT / "data" / "user_uploads"

ALLOWED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
}

MAX_FILE_SIZE_MB = 25


# ============================================================
# DATASET SCHEMAS
# ============================================================

DATASET_SCHEMAS: Dict[str, Dict[str, Any]] = {

    "invoices": {
        "display_name": "Invoices",

        "required": [
            "invoice_id",
            "vendor_id",
            "po_id",
            "sku",
            "unit_price",
            "quantity",
            "invoice_amount",
        ],

        "aliases": {
            "invoice_id": [
                "invoice_id",
                "invoice",
                "invoice_number",
                "invoice_no",
                "invoice_num",
            ],
            "vendor_id": [
                "vendor_id",
                "vendor",
                "vendor_code",
                "supplier_id",
                "supplier_code",
            ],
            "po_id": [
                "po_id",
                "po",
                "po_number",
                "po_no",
                "purchase_order_id",
            ],
            "sku": [
                "sku",
                "sku_id",
                "product_id",
                "item_id",
                "item_code",
            ],
            "unit_price": [
                "unit_price",
                "unit_cost",
                "price",
                "invoice_unit_price",
                "item_price",
            ],
            "quantity": [
                "quantity",
                "qty",
                "invoice_quantity",
                "invoice_qty",
            ],
            "invoice_amount": [
                "invoice_amount",
                "invoice_total",
                "total_amount",
                "amount",
                "invoice_value",
                "total",
            ],
        },
    },

    "purchase_orders": {
        "display_name": "Purchase Orders",

        "required": [
            "po_id",
            "vendor_id",
            "sku",
            "unit_price",
            "quantity",
        ],

        "aliases": {
            "po_id": [
                "po_id",
                "po",
                "po_number",
                "po_no",
                "purchase_order_id",
            ],
            "vendor_id": [
                "vendor_id",
                "vendor",
                "vendor_code",
                "supplier_id",
                "supplier_code",
            ],
            "sku": [
                "sku",
                "sku_id",
                "product_id",
                "item_id",
                "item_code",
            ],
            "unit_price": [
                "unit_price",
                "unit_cost",
                "price",
                "po_unit_price",
                "item_price",
            ],
            "quantity": [
                "quantity",
                "qty",
                "ordered_quantity",
                "ordered_qty",
                "po_quantity",
            ],
        },
    },

    "payments": {
        "display_name": "Payments",

        "required": [
            "payment_id",
            "invoice_id",
            "paid_amount",
        ],

        "aliases": {
            "payment_id": [
                "payment_id",
                "payment",
                "payment_number",
                "payment_no",
                "transaction_id",
                "transaction_number",
            ],
            "invoice_id": [
                "invoice_id",
                "invoice",
                "invoice_number",
                "invoice_no",
            ],
            "paid_amount": [
                "paid_amount",
                "payment_amount",
                "amount_paid",
                "amount",
                "paid",
                "payment_value",
            ],
        },
    },

    "contracts": {
        "display_name": "Contracts",

        "required": [
            "contract_id",
            "vendor_id",
            "unit_price",
            "rebate_percentage",
        ],

        "aliases": {
            "contract_id": [
                "contract_id",
                "contract",
                "contract_number",
                "contract_no",
            ],
            "vendor_id": [
                "vendor_id",
                "vendor",
                "vendor_code",
                "supplier_id",
                "supplier_code",
            ],
            "unit_price": [
                "unit_price",
                "contract_unit_price",
                "agreed_price",
                "contract_price",
                "price",
            ],
            "rebate_percentage": [
                "rebate_percentage",
                "rebate_percent",
                "rebate_pct",
                "rebate",
                "discount_percentage",
                "discount_percent",
            ],
        },
    },

    "rebates": {
        "display_name": "Rebates",

        "required": [
            "rebate_id",
            "vendor_id",
            "contract_id",
            "invoice_id",
            "base_amount",
            "credited_rebate",
        ],

        "aliases": {
            "rebate_id": [
                "rebate_id",
                "rebate",
                "rebate_number",
                "rebate_no",
            ],
            "vendor_id": [
                "vendor_id",
                "vendor",
                "vendor_code",
                "supplier_id",
                "supplier_code",
            ],
            "contract_id": [
                "contract_id",
                "contract",
                "contract_number",
                "contract_no",
            ],
            "invoice_id": [
                "invoice_id",
                "invoice",
                "invoice_number",
                "invoice_no",
            ],
            "base_amount": [
                "base_amount",
                "rebate_base_amount",
                "eligible_amount",
                "base_value",
                "rebate_base",
            ],
            "credited_rebate": [
                "credited_rebate",
                "rebate_amount",
                "credited_amount",
                "credit_amount",
                "rebate_credited",
            ],
        },
    },

    "goods_receipts": {
        "display_name": "Goods Receipts",

        "required": [
            "goods_receipt_id",
            "po_id",
            "invoice_id",
            "vendor_id",
            "sku",
            "received_quantity",
        ],

        "aliases": {
            "goods_receipt_id": [
                "goods_receipt_id",
                "goods_receipt",
                "gr_id",
                "gr_number",
                "gr_no",
                "receipt_id",
            ],
            "po_id": [
                "po_id",
                "po",
                "po_number",
                "po_no",
                "purchase_order_id",
            ],
            "invoice_id": [
                "invoice_id",
                "invoice",
                "invoice_number",
                "invoice_no",
            ],
            "vendor_id": [
                "vendor_id",
                "vendor",
                "vendor_code",
                "supplier_id",
                "supplier_code",
            ],
            "sku": [
                "sku",
                "sku_id",
                "product_id",
                "item_id",
                "item_code",
            ],
            "received_quantity": [
                "received_quantity",
                "received_qty",
                "receipt_quantity",
                "receipt_qty",
                "goods_received_quantity",
                "gr_quantity",
            ],
        },
    },
}


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _normalize_column_name(column: Any) -> str:
    """
    Convert a raw column name into a normalized comparison form.
    """
    value = str(column).strip().lower()

    for char in [" ", "-", "/", "\\", ".", "(", ")", "[", "]"]:
        value = value.replace(char, "_")

    while "__" in value:
        value = value.replace("__", "_")

    return value.strip("_")


def _normalized_columns(df: pd.DataFrame) -> Dict[str, str]:
    """
    Return:
        normalized_name -> original_name
    """
    result: Dict[str, str] = {}

    for column in df.columns:
        normalized = _normalize_column_name(column)
        result[normalized] = str(column)

    return result


def _find_alias_match(
    normalized_columns: Dict[str, str],
    aliases: list[str],
) -> Optional[str]:
    """
    Find the first matching alias.
    """

    normalized_aliases = [
        _normalize_column_name(alias)
        for alias in aliases
    ]

    for alias in normalized_aliases:
        if alias in normalized_columns:
            return normalized_columns[alias]

    return None


# ============================================================
# FILE VALIDATION
# ============================================================

def validate_file(
    filename: str,
    file_size: int,
) -> Dict[str, Any]:
    """
    Validate uploaded file extension and size.
    """

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return {
            "valid": False,
            "message": (
                f"Unsupported file type: {extension}. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        }

    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024

    if file_size > max_bytes:
        return {
            "valid": False,
            "message": (
                f"File exceeds the maximum size of "
                f"{MAX_FILE_SIZE_MB} MB."
            ),
        }

    return {
        "valid": True,
        "message": "File is valid.",
    }


# ============================================================
# READ UPLOADED FILE
# ============================================================

def read_uploaded_file(
    uploaded_file: Any,
) -> pd.DataFrame:
    """
    Read a Streamlit UploadedFile, file path, or file-like object.
    """

    filename = getattr(uploaded_file, "name", "")

    if not filename:
        raise ValueError("Uploaded file does not have a filename.")

    extension = Path(filename).suffix.lower()

    if extension == ".csv":
        df = pd.read_csv(uploaded_file)

    elif extension in {".xlsx", ".xls"}:
        df = pd.read_excel(uploaded_file)

    else:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    if df.empty:
        raise ValueError(
            f"{filename} contains no data."
        )

    # Clean completely empty rows/columns.
    df = df.dropna(
        axis=0,
        how="all",
    )

    df = df.dropna(
        axis=1,
        how="all",
    )

    # Normalize whitespace in string cells.
    for column in df.columns:
        if df[column].dtype == "object":
            df[column] = (
                df[column]
                .astype(str)
                .str.strip()
            )

    return df


# ============================================================
# DATASET DETECTION
# ============================================================

def _score_dataset(
    df: pd.DataFrame,
    dataset_type: str,
) -> Dict[str, Any]:
    """
    Strictly score a dataframe against one dataset schema.

    Important:
    Only required-field aliases are used.

    This prevents:
        goods_receipts -> payments
        invoices -> payments
        etc.
    """

    schema = DATASET_SCHEMAS[dataset_type]

    normalized_columns = _normalized_columns(df)

    matched: Dict[str, str] = {}
    missing: list[str] = []

    for required_field in schema["required"]:

        aliases = schema["aliases"].get(
            required_field,
            [required_field],
        )

        match = _find_alias_match(
            normalized_columns,
            aliases,
        )

        if match:
            matched[required_field] = match
        else:
            missing.append(required_field)

    required_count = len(
        schema["required"]
    )

    matched_count = len(matched)

    confidence = (
        matched_count / required_count * 100
        if required_count
        else 0
    )

    # Never allow confidence above 100%.
    confidence = min(
        100.0,
        round(confidence, 1),
    )

    return {
        "dataset_type": dataset_type,
        "display_name": schema["display_name"],
        "matched": matched,
        "missing": missing,
        "matched_count": matched_count,
        "required_count": required_count,
        "confidence": confidence,
    }


def detect_dataset_type(
    df: pd.DataFrame,
    filename: str = "",
) -> Dict[str, Any]:
    """
    Detect the most likely dataset type.

    Detection is intentionally strict.

    Filename is used only as a tie-breaker after
    structural column matching.
    """

    filename_lower = (
        Path(filename).stem.lower()
        if filename
        else ""
    )

    scores = []

    for dataset_type in DATASET_SCHEMAS:

        score = _score_dataset(
            df,
            dataset_type,
        )

        scores.append(score)

    # --------------------------------------------------------
    # Special protection for Payments.
    # Payments must contain all three:
    #
    # payment_id
    # invoice_id
    # paid_amount
    # --------------------------------------------------------

    payment_score = next(
        (
            item
            for item in scores
            if item["dataset_type"] == "payments"
        ),
        None,
    )

    if payment_score:
        payment_required = {
            "payment_id",
            "invoice_id",
            "paid_amount",
        }

        payment_matched = set(
            payment_score["matched"].keys()
        )

        payment_score["is_valid_signature"] = (
            payment_required.issubset(
                payment_matched
            )
        )
    else:
        payment_score = None

    # --------------------------------------------------------
    # Sort by:
    #
    # 1. Number of required fields matched
    # 2. Confidence
    # --------------------------------------------------------

    scores.sort(
        key=lambda item: (
            item["matched_count"],
            item["confidence"],
        ),
        reverse=True,
    )

    best = scores[0]

    # --------------------------------------------------------
    # Filename tie-breaker
    # --------------------------------------------------------

    filename_hints = {
        "invoices": [
            "invoice",
            "invoices",
        ],
        "purchase_orders": [
            "purchase_order",
            "purchase_orders",
            "purchaseorder",
            "purchaseorders",
            "po",
        ],
        "payments": [
            "payment",
            "payments",
        ],
        "contracts": [
            "contract",
            "contracts",
        ],
        "rebates": [
            "rebate",
            "rebates",
        ],
        "goods_receipts": [
            "goods_receipt",
            "goods_receipts",
            "goodsreceipt",
            "goodsreceipts",
            "receipt",
            "receipts",
            "gr",
        ],
    }

    for candidate in scores:

        if candidate["matched_count"] != best["matched_count"]:
            continue

        if candidate["confidence"] != best["confidence"]:
            continue

        hints = filename_hints.get(
            candidate["dataset_type"],
            [],
        )

        if any(
            hint in filename_lower
            for hint in hints
        ):
            best = candidate
            break

    # --------------------------------------------------------
    # Require at least one meaningful match.
    # --------------------------------------------------------

    if best["matched_count"] == 0:

        return {
            "dataset_type": None,
            "display_name": "Unknown",
            "confidence": 0.0,
            "matched": {},
            "missing": [],
            "matched_count": 0,
            "required_count": 0,
            "is_valid": False,
            "message": (
                "Unable to identify the dataset "
                "from its columns."
            ),
        }

    # --------------------------------------------------------
    # If only a weak partial match exists, do not confidently
    # classify it.
    # --------------------------------------------------------

    if best["confidence"] < 50:

        return {
            **best,
            "dataset_type": None,
            "display_name": "Unknown",
            "is_valid": False,
            "message": (
                "Dataset confidence is too low. "
                "Please check the column names."
            ),
        }

    return {
        **best,
        "is_valid": True,
        "message": (
            f"Detected dataset: "
            f"{best['display_name']}"
        ),
    }


# ============================================================
# COLUMN MAPPING
# ============================================================

def suggest_column_mapping(
    df: pd.DataFrame,
    dataset_type: str,
) -> Dict[str, str]:
    """
    Suggest:
        canonical_column -> uploaded_column
    """

    if dataset_type not in DATASET_SCHEMAS:
        raise ValueError(
            f"Unknown dataset type: {dataset_type}"
        )

    schema = DATASET_SCHEMAS[
        dataset_type
    ]

    normalized_columns = _normalized_columns(df)

    mapping: Dict[str, str] = {}

    for canonical_field in schema["required"]:

        aliases = schema["aliases"].get(
            canonical_field,
            [canonical_field],
        )

        match = _find_alias_match(
            normalized_columns,
            aliases,
        )

        if match:
            mapping[
                canonical_field
            ] = match

    return mapping


# ============================================================
# APPLY COLUMN MAPPING
# ============================================================

def apply_column_mapping(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    dataset_type: str,
) -> pd.DataFrame:
    """
    Rename uploaded columns to DollarGuard canonical names.
    """

    if dataset_type not in DATASET_SCHEMAS:
        raise ValueError(
            f"Unknown dataset type: {dataset_type}"
        )

    reverse_mapping = {}

    for canonical, uploaded in mapping.items():

        if uploaded in df.columns:
            reverse_mapping[
                uploaded
            ] = canonical

    normalized_df = df.rename(
        columns=reverse_mapping
    ).copy()

    # --------------------------------------------------------
    # Calculate invoice_amount when missing.
    # --------------------------------------------------------

    if dataset_type == "invoices":

        if (
            "invoice_amount"
            not in normalized_df.columns
            and "unit_price"
            in normalized_df.columns
            and "quantity"
            in normalized_df.columns
        ):

            normalized_df[
                "invoice_amount"
            ] = (
                pd.to_numeric(
                    normalized_df["unit_price"],
                    errors="coerce",
                )
                *
                pd.to_numeric(
                    normalized_df["quantity"],
                    errors="coerce",
                )
            )

    return normalized_df


# ============================================================
# DATASET VALIDATION
# ============================================================

def validate_dataset(
    df: pd.DataFrame,
    dataset_type: str,
) -> Dict[str, Any]:
    """
    Validate a normalized dataframe.
    """

    if dataset_type not in DATASET_SCHEMAS:
        return {
            "valid": False,
            "dataset_type": dataset_type,
            "missing_columns": [],
            "message": (
                f"Unknown dataset type: "
                f"{dataset_type}"
            ),
        }

    schema = DATASET_SCHEMAS[
        dataset_type
    ]

    missing_columns = [
        column
        for column in schema["required"]
        if column not in df.columns
    ]

    if missing_columns:

        return {
            "valid": False,
            "dataset_type": dataset_type,
            "missing_columns": missing_columns,
            "row_count": len(df),
            "message": (
                "Required columns are missing: "
                + ", ".join(missing_columns)
            ),
        }

    # --------------------------------------------------------
    # Numeric validation
    # --------------------------------------------------------

    numeric_columns = []

    if dataset_type == "invoices":
        numeric_columns = [
            "unit_price",
            "quantity",
            "invoice_amount",
        ]

    elif dataset_type == "purchase_orders":
        numeric_columns = [
            "unit_price",
            "quantity",
        ]

    elif dataset_type == "payments":
        numeric_columns = [
            "paid_amount",
        ]

    elif dataset_type == "contracts":
        numeric_columns = [
            "unit_price",
            "rebate_percentage",
        ]

    elif dataset_type == "rebates":
        numeric_columns = [
            "base_amount",
            "credited_rebate",
        ]

    elif dataset_type == "goods_receipts":
        numeric_columns = [
            "received_quantity",
        ]

    numeric_issues = []

    for column in numeric_columns:

        if column not in df.columns:
            continue

        converted = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        invalid_count = int(
            converted.isna().sum()
        )

        if invalid_count > 0:

            numeric_issues.append(
                {
                    "column": column,
                    "invalid_values": invalid_count,
                }
            )

    # --------------------------------------------------------
    # Duplicate primary IDs
    # --------------------------------------------------------

    primary_key_map = {
        "invoices": "invoice_id",
        "purchase_orders": "po_id",
        "payments": "payment_id",
        "contracts": "contract_id",
        "rebates": "rebate_id",
        "goods_receipts": "goods_receipt_id",
    }

    primary_key = primary_key_map[
        dataset_type
    ]

    duplicate_count = int(
        df[primary_key]
        .duplicated()
        .sum()
    )

    # Duplicates are warnings, not structural failures.
    warnings = []

    if duplicate_count > 0:
        warnings.append(
            f"{duplicate_count} duplicate "
            f"{primary_key} values detected."
        )

    if numeric_issues:
        warnings.append(
            "Some numeric columns contain "
            "non-numeric or missing values."
        )

    return {
        "valid": True,
        "dataset_type": dataset_type,
        "row_count": len(df),
        "column_count": len(df.columns),
        "missing_columns": [],
        "numeric_issues": numeric_issues,
        "duplicate_count": duplicate_count,
        "warnings": warnings,
        "message": (
            f"{schema['display_name']}: "
            f"{len(df)} rows passed "
            f"structural validation."
        ),
    }


# ============================================================
# CREATE UPLOAD WORKSPACE
# ============================================================

def create_upload_workspace() -> Path:
    """
    Create a unique workspace for one upload session.
    """

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    workspace = (
        USER_UPLOADS_DIR
        / f"session_{timestamp}"
    )

    workspace.mkdir(
        parents=True,
        exist_ok=True,
    )

    return workspace


# ============================================================
# SAVE DATAFRAME
# ============================================================

def save_dataframe(
    df: pd.DataFrame,
    workspace: Path,
    dataset_type: str,
) -> Path:
    """
    Save normalized dataframe to workspace.
    """

    if dataset_type not in DATASET_SCHEMAS:
        raise ValueError(
            f"Unknown dataset type: {dataset_type}"
        )

    filename = (
        f"{dataset_type}.csv"
    )

    output_path = (
        workspace / filename
    )

    df.to_csv(
        output_path,
        index=False,
    )

    return output_path


# ============================================================
# LOAD NORMALIZED DATASET
# ============================================================

def load_normalized_dataset(
    workspace: Path,
    dataset_type: str,
) -> Optional[pd.DataFrame]:
    """
    Load a normalized dataset from an upload workspace.
    """

    file_path = (
        workspace
        / f"{dataset_type}.csv"
    )

    if not file_path.exists():
        return None

    return pd.read_csv(file_path)


# ============================================================
# GET AVAILABLE DATASETS
# ============================================================

def get_available_datasets(
    workspace: Path,
) -> list[str]:
    """
    Return normalized datasets available in workspace.
    """

    datasets = []

    for dataset_type in DATASET_SCHEMAS:

        path = (
            workspace
            / f"{dataset_type}.csv"
        )

        if path.exists():
            datasets.append(
                dataset_type
            )

    return datasets


# ============================================================
# TEST / CLI
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print(
        "DOLLARGUARD AI - UPLOAD MANAGER TEST"
    )
    print("=" * 60)

    print(
        f"Project root: "
        f"{PROJECT_ROOT}"
    )

    print(
        f"Allowed extensions: "
        f"{sorted(ALLOWED_EXTENSIONS)}"
    )

    print(
        f"Maximum file size: "
        f"{MAX_FILE_SIZE_MB} MB"
    )

    print()
    print("Dataset schemas:")

    for dataset_type, schema in (
        DATASET_SCHEMAS.items()
    ):

        print(
            f"  - "
            f"{schema['display_name']}: "
            f"{len(schema['required'])} "
            f"required columns"
        )

    print("=" * 60)