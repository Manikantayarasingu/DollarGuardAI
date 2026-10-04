"""
DollarGuard AI
Contract & PDF Intelligence Engine

Purpose:
    Extract commercially relevant information from supplier contracts
    and convert unstructured contract documents into structured data.

Supported documents:
    - PDF
    - TXT

Output:
    data/processed/contract_intelligence.csv
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

CONTRACTS_DIR = BASE_DIR / "documents" / "contracts"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "contract_intelligence.csv"


# ============================================================
# REGEX PATTERNS
# ============================================================

PATTERNS = {
    "contract_id": [
        r"\b(CON-\d{3,})\b",
        r"\b(CTR-\d{3,})\b",
        r"\b(CONTRACT-\d{3,})\b",
        r"contract\s*(?:id|number|no\.?)\s*[:\-]?\s*([A-Z0-9\-]+)",
    ],

    "vendor_id": [
        r"\b(VEN-\d{3,})\b",
        r"vendor\s*(?:id|number|no\.?)\s*[:\-]?\s*([A-Z0-9\-]+)",
    ],

    "unit_price": [
        r"(?:unit\s+price|price\s+per\s+unit)"
        r"\s*[:\-]?\s*(?:₹|INR|Rs\.?|USD|\$)?\s*([\d,]+(?:\.\d+)?)",

        r"(?:price|rate)"
        r"\s*[:\-]?\s*(?:₹|INR|Rs\.?|USD|\$)\s*([\d,]+(?:\.\d+)?)",
    ],

    "rebate_percentage": [
        r"(?:rebate|discount)\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*%",
        r"(\d+(?:\.\d+)?)\s*%\s*(?:rebate|discount)",
    ],

    "payment_terms": [
        r"\b(Net\s+\d+)\b",
        r"\b(Payment\s+terms?\s*[:\-]?\s*Net\s+\d+)\b",
        r"\b(\d+\s+days?)\s+(?:from|after)\s+(?:invoice|delivery|receipt)",
    ],

    "volume_commitment": [
        r"(?:minimum\s+purchase|minimum\s+volume|volume\s+commitment)"
        r"\s*[:\-]?\s*([\d,]+)\s*(?:units?|pieces?|pcs)?",

        r"(?:commit(?:ted)?\s+volume)"
        r"\s*[:\-]?\s*([\d,]+)\s*(?:units?|pieces?|pcs)?",
    ],

    "penalty_percentage": [
        r"(?:penalty|late\s+delivery\s+penalty)"
        r"\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*%",
    ],

    "penalty_amount": [
        r"(?:penalty|liquidated\s+damages)"
        r"\s*(?:of|:)?\s*(?:₹|INR|Rs\.?|USD|\$)\s*"
        r"([\d,]+(?:\.\d+)?)",
    ],

    "contract_start_date": [
        r"(?:effective\s+date|start\s+date|commencement\s+date)"
        r"\s*[:\-]?\s*"
        r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
    ],

    "contract_end_date": [
        r"(?:expiry\s+date|expiration\s+date|end\s+date|valid\s+until)"
        r"\s*[:\-]?\s*"
        r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
    ],

    "currency": [
        r"(₹|INR|Rs\.?)",
        r"(USD|\$)",
        r"(EUR|€)",
    ],
}


# ============================================================
# TEXT EXTRACTION
# ============================================================

def extract_pdf_text(file_path: Path) -> str:
    """
    Extract text from a PDF file.
    """

    if PdfReader is None:
        raise ImportError(
            "pypdf is not installed. "
            "Run: pip install pypdf"
        )

    reader = PdfReader(str(file_path))

    pages = []

    for page in reader.pages:
        try:
            page_text = page.extract_text()

            if page_text:
                pages.append(page_text)
        except Exception:
            continue

    return "\n".join(pages)


def extract_text(file_path: Path) -> str:
    """
    Extract text from supported document formats.
    """

    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(file_path)

    if extension == ".txt":
        return file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    raise ValueError(
        f"Unsupported document type: {extension}"
    )


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize extracted document text for easier matching.
    """

    text = text.replace("\xa0", " ")
    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "-")

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n+",
        "\n",
        text
    )

    return text.strip()


def clean_number(value: Optional[str]) -> Optional[float]:
    """
    Convert values such as:
        1,250
        1250.50
    into numeric values.
    """

    if not value:
        return None

    try:
        return float(
            value.replace(",", "").strip()
        )
    except ValueError:
        return None


# ============================================================
# FIELD EXTRACTION
# ============================================================

def find_first_match(
    text: str,
    patterns: List[str]
) -> Optional[str]:
    """
    Return the first matching capture group.
    """

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            if match.groups():
                return match.group(1).strip()

            return match.group(0).strip()

    return None


def extract_field(
    text: str,
    field_name: str
) -> Optional[str]:

    patterns = PATTERNS.get(
        field_name,
        []
    )

    return find_first_match(
        text,
        patterns
    )


# ============================================================
# CLAUSE DETECTION
# ============================================================

CLAUSE_KEYWORDS = {
    "rebate_clause": [
        "rebate",
        "volume rebate",
        "annual rebate",
        "discount",
    ],

    "payment_clause": [
        "payment terms",
        "payment terms",
        "net 30",
        "net 45",
        "net 60",
        "payment shall",
    ],

    "price_clause": [
        "unit price",
        "unit pricing",
        "price per unit",
        "pricing",
    ],

    "volume_clause": [
        "minimum purchase",
        "minimum volume",
        "volume commitment",
        "committed volume",
    ],

    "penalty_clause": [
        "penalty",
        "late delivery",
        "liquidated damages",
    ],

    "termination_clause": [
        "termination",
        "terminate",
        "termination notice",
    ],

    "renewal_clause": [
        "renewal",
        "auto-renew",
        "automatically renew",
    ],
}


def detect_clauses(text: str) -> Dict[str, bool]:
    """
    Detect whether important commercial clauses exist.
    """

    lowered = text.lower()

    result = {}

    for clause_name, keywords in CLAUSE_KEYWORDS.items():
        result[clause_name] = any(
            keyword.lower() in lowered
            for keyword in keywords
        )

    return result


# ============================================================
# EVIDENCE EXTRACTION
# ============================================================

def get_evidence(
    text: str,
    keywords: List[str],
    max_length: int = 300
) -> str:
    """
    Return a short text snippet around an important keyword.
    """

    lowered = text.lower()

    for keyword in keywords:
        position = lowered.find(
            keyword.lower()
        )

        if position == -1:
            continue

        start = max(
            0,
            position - 100
        )

        end = min(
            len(text),
            position + max_length
        )

        snippet = text[start:end]

        snippet = re.sub(
            r"\s+",
            " ",
            snippet
        )

        return snippet.strip()

    return ""


# ============================================================
# CONFIDENCE
# ============================================================

def calculate_confidence(
    extracted: Dict[str, object]
) -> float:
    """
    Calculate extraction confidence from the number
    of commercially important fields detected.
    """

    important_fields = [
        "contract_id",
        "vendor_id",
        "unit_price",
        "rebate_percentage",
        "payment_terms",
        "volume_commitment",
        "penalty_percentage",
        "contract_start_date",
        "contract_end_date",
    ]

    detected = 0

    for field in important_fields:
        value = extracted.get(field)

        if value not in (
            None,
            "",
            False,
        ):
            detected += 1

    confidence = (
        detected /
        len(important_fields)
    ) * 100

    return round(
        confidence,
        2
    )


# ============================================================
# SINGLE DOCUMENT PROCESSING
# ============================================================

def process_contract(
    file_path: Path
) -> Dict[str, object]:
    """
    Process a single contract document.
    """

    raw_text = extract_text(
        file_path
    )

    text = normalize_text(
        raw_text
    )

    contract_id = extract_field(
        text,
        "contract_id"
    )

    vendor_id = extract_field(
        text,
        "vendor_id"
    )

    unit_price_raw = extract_field(
        text,
        "unit_price"
    )

    rebate_raw = extract_field(
        text,
        "rebate_percentage"
    )

    volume_raw = extract_field(
        text,
        "volume_commitment"
    )

    penalty_percentage_raw = extract_field(
        text,
        "penalty_percentage"
    )

    penalty_amount_raw = extract_field(
        text,
        "penalty_amount"
    )

    currency = extract_field(
        text,
        "currency"
    )

    payment_terms = extract_field(
        text,
        "payment_terms"
    )

    start_date = extract_field(
        text,
        "contract_start_date"
    )

    end_date = extract_field(
        text,
        "contract_end_date"
    )

    clauses = detect_clauses(
        text
    )

    result = {
        "document_name": file_path.name,
        "document_path": str(file_path),

        "contract_id": contract_id,
        "vendor_id": vendor_id,

        "currency": currency,

        "unit_price": clean_number(
            unit_price_raw
        ),

        "rebate_percentage": clean_number(
            rebate_raw
        ),

        "payment_terms": payment_terms,

        "volume_commitment": clean_number(
            volume_raw
        ),

        "penalty_percentage": clean_number(
            penalty_percentage_raw
        ),

        "penalty_amount": clean_number(
            penalty_amount_raw
        ),

        "contract_start_date": start_date,
        "contract_end_date": end_date,

        "rebate_clause": clauses[
            "rebate_clause"
        ],

        "payment_clause": clauses[
            "payment_clause"
        ],

        "price_clause": clauses[
            "price_clause"
        ],

        "volume_clause": clauses[
            "volume_clause"
        ],

        "penalty_clause": clauses[
            "penalty_clause"
        ],

        "termination_clause": clauses[
            "termination_clause"
        ],

        "renewal_clause": clauses[
            "renewal_clause"
        ],

        "rebate_evidence": get_evidence(
            text,
            CLAUSE_KEYWORDS["rebate_clause"]
        ),

        "price_evidence": get_evidence(
            text,
            CLAUSE_KEYWORDS["price_clause"]
        ),

        "payment_evidence": get_evidence(
            text,
            CLAUSE_KEYWORDS["payment_clause"]
        ),

        "penalty_evidence": get_evidence(
            text,
            CLAUSE_KEYWORDS["penalty_clause"]
        ),

        "document_characters": len(text),
        "document_pages": None,
        "extraction_status": "SUCCESS",
        "processed_at": datetime.utcnow().isoformat(),
    }

    result["extraction_confidence"] = (
        calculate_confidence(result)
    )

    return result


# ============================================================
# DOCUMENT DISCOVERY
# ============================================================

def discover_contract_documents() -> List[Path]:
    """
    Find all supported contract documents.
    """

    CONTRACTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    documents = []

    for extension in (
        "*.pdf",
        "*.PDF",
        "*.txt",
        "*.TXT",
    ):
        documents.extend(
            CONTRACTS_DIR.glob(extension)
        )

    return sorted(
        set(documents)
    )


# ============================================================
# MAIN PROCESSOR
# ============================================================

def process_all_contracts() -> pd.DataFrame:
    """
    Process every contract document.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    documents = discover_contract_documents()

    if not documents:
        print()
        print("=" * 70)
        print("DOLLARGUARD AI - CONTRACT INTELLIGENCE")
        print("=" * 70)
        print()
        print(
            "No contract documents found."
        )
        print()
        print(
            f"Place PDF or TXT contracts inside:"
        )
        print(
            f"  {CONTRACTS_DIR}"
        )
        print()

        return pd.DataFrame()

    results = []

    print()
    print("=" * 70)
    print("DOLLARGUARD AI - CONTRACT INTELLIGENCE")
    print("=" * 70)
    print()

    print(
        f"Documents discovered : {len(documents)}"
    )
    print()

    for index, document in enumerate(
        documents,
        start=1
    ):

        print(
            f"[{index}/{len(documents)}] "
            f"Processing: {document.name}"
        )

        try:
            result = process_contract(
                document
            )

            results.append(
                result
            )

            print(
                f"    Contract ID       : "
                f"{result.get('contract_id')}"
            )

            print(
                f"    Vendor ID         : "
                f"{result.get('vendor_id')}"
            )

            print(
                f"    Unit Price        : "
                f"{result.get('unit_price')}"
            )

            print(
                f"    Rebate            : "
                f"{result.get('rebate_percentage')}%"
            )

            print(
                f"    Payment Terms     : "
                f"{result.get('payment_terms')}"
            )

            print(
                f"    Confidence        : "
                f"{result.get('extraction_confidence')}%"
            )

            print()

        except Exception as exc:

            print(
                f"    ERROR: {exc}"
            )

            results.append(
                {
                    "document_name": document.name,
                    "document_path": str(document),
                    "extraction_status": "FAILED",
                    "error": str(exc),
                    "processed_at": (
                        datetime.utcnow().isoformat()
                    ),
                }
            )

    dataframe = pd.DataFrame(
        results
    )

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("=" * 70)
    print("CONTRACT INTELLIGENCE COMPLETE")
    print("=" * 70)
    print()

    print(
        f"Documents processed : "
        f"{len(dataframe)}"
    )

    successful = (
        dataframe["extraction_status"]
        .eq("SUCCESS")
        .sum()
        if "extraction_status" in dataframe.columns
        else 0
    )

    failed = (
        dataframe["extraction_status"]
        .eq("FAILED")
        .sum()
        if "extraction_status" in dataframe.columns
        else 0
    )

    print(
        f"Successful          : {successful}"
    )

    print(
        f"Failed              : {failed}"
    )

    if (
        "extraction_confidence"
        in dataframe.columns
    ):

        confidence = pd.to_numeric(
            dataframe[
                "extraction_confidence"
            ],
            errors="coerce"
        ).dropna()

        if not confidence.empty:

            print(
                f"Average confidence : "
                f"{confidence.mean():.2f}%"
            )

    print()
    print(
        f"Output file:"
    )
    print(
        f"  {OUTPUT_FILE}"
    )

    print()

    return dataframe


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    process_all_contracts()