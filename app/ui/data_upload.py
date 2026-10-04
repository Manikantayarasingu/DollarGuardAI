# ============================================================
# DOLLARGUARD AI
# REAL DATA UPLOAD & ANALYSIS PAGE
# ============================================================

from pathlib import Path

import pandas as pd
import streamlit as st

from app.data_ingestion.upload_manager import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_MB,
    apply_column_mapping,
    create_upload_workspace,
    detect_dataset_type,
    read_uploaded_file,
    save_dataframe,
    suggest_column_mapping,
    validate_dataset,
    validate_file,
)

from app.services.uploaded_data_engine import (
    run_uploaded_analysis,
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

USER_UPLOAD_DIR = (
    BASE_DIR
    / "data"
    / "user_uploads"
)


# ============================================================
# DATASET LABELS
# ============================================================

DATASET_LABELS = {
    "contracts": "Contracts",
    "purchase_orders": "Purchase Orders",
    "goods_receipts": "Goods Receipts",
    "invoices": "Invoices",
    "payments": "Payments",
    "rebates": "Rebates",
}


# ============================================================
# SESSION STATE
# ============================================================

def initialize_upload_state():
    """
    Initialize all upload-related Streamlit state.
    """

    defaults = {
        "data_mode": "Demo Data",

        # IMPORTANT:
        # This must remain a pathlib.Path object.
        "upload_workspace": None,

        "uploaded_datasets": {},

        "upload_validated": False,

        "uploaded_analysis_result": None,

        "uploaded_analysis_ready": False,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================
# CURRENCY FORMAT
# ============================================================

def money(value) -> str:
    """
    Safely format an amount as INR.
    """

    try:

        return f"₹{float(value):,.2f}"

    except (
        ValueError,
        TypeError,
    ):

        return "₹0.00"


# ============================================================
# SAFE NUMBER
# ============================================================

def safe_number(value) -> float:
    """
    Safely convert a value to float.
    """

    try:

        number = float(value)

        if pd.isna(number):
            return 0.0

        return number

    except (
        ValueError,
        TypeError,
    ):

        return 0.0


# ============================================================
# UPLOADED DATA STATUS
# ============================================================

def uploaded_data_is_ready() -> bool:
    """
    Check whether uploaded data has been prepared
    and is ready for analysis.
    """

    workspace = (
        st.session_state.get(
            "upload_workspace"
        )
    )

    datasets = (
        st.session_state.get(
            "uploaded_datasets",
            {},
        )
    )

    validated = (
        st.session_state.get(
            "upload_validated",
            False,
        )
    )

    return bool(
        validated
        and workspace
        and datasets
    )


# ============================================================
# GET UPLOADED WORKSPACE
# ============================================================

def get_uploaded_workspace():
    """
    Return the uploaded workspace as pathlib.Path.

    IMPORTANT:
    dashboard.py expects:
        uploaded_workspace.name

    Therefore this function must return Path,
    not str.
    """

    workspace = (
        st.session_state.get(
            "upload_workspace"
        )
    )

    if not workspace:
        return None

    if isinstance(
        workspace,
        Path,
    ):

        return workspace

    return Path(workspace)


# ============================================================
# GET UPLOADED DATASETS
# ============================================================

def get_uploaded_datasets():
    """
    Return uploaded dataset metadata.
    """

    return st.session_state.get(
        "uploaded_datasets",
        {},
    )


# ============================================================
# RESET ANALYSIS
# ============================================================

def reset_uploaded_analysis():

    st.session_state[
        "uploaded_analysis_result"
    ] = None

    st.session_state[
        "uploaded_analysis_ready"
    ] = False


# ============================================================
# RESET COMPLETE UPLOAD SESSION
# ============================================================

def reset_upload_session():

    st.session_state[
        "upload_workspace"
    ] = None

    st.session_state[
        "uploaded_datasets"
    ] = {}

    st.session_state[
        "upload_validated"
    ] = False

    st.session_state[
        "uploaded_analysis_result"
    ] = None

    st.session_state[
        "uploaded_analysis_ready"
    ] = False


# ============================================================
# DATASET DISPLAY NAME
# ============================================================

def get_dataset_label(
    dataset_type: str,
) -> str:

    return DATASET_LABELS.get(
        dataset_type,
        dataset_type.replace(
            "_",
            " ",
        ).title(),
    )


# ============================================================
# MAIN DATA UPLOAD PAGE
# ============================================================

def render_data_upload_page():

    initialize_upload_state()

    # ========================================================
    # HEADER
    # ========================================================

    st.header(
        "📂 Data Management"
    )

    st.markdown(
        """
Upload your own enterprise financial data and run
DollarGuard AI's revenue leakage detection engine.

DollarGuard supports:

- Invoices
- Purchase Orders
- Payments
- Contracts
- Rebates
- Goods Receipts
        """
    )

    st.divider()

    # ========================================================
    # DATA MODE
    # ========================================================

    st.subheader(
        "1️⃣ Choose Data Mode"
    )

    current_mode = st.session_state.get(
        "data_mode",
        "Demo Data",
    )

    data_mode = st.radio(
        "Data Source",
        [
            "Demo Data",
            "Upload My Data",
        ],
        index=(
            0
            if current_mode == "Demo Data"
            else 1
        ),
        horizontal=True,
    )

    if data_mode != current_mode:

        st.session_state[
            "data_mode"
        ] = data_mode

        if data_mode == "Demo Data":

            reset_uploaded_analysis()

    # ========================================================
    # DEMO DATA
    # ========================================================

    if data_mode == "Demo Data":

        st.info(
            """
**Demo Data Mode**

The existing DollarGuard synthetic enterprise
dataset will be used by the main dashboard.

Switch to **Upload My Data** to analyze your
own financial datasets.
            """
        )

        return

    # ========================================================
    # UPLOAD MODE
    # ========================================================

    st.subheader(
        "2️⃣ Upload Financial Datasets"
    )

    st.caption(
        f"Supported formats: CSV and XLSX | "
        f"Maximum file size: "
        f"{MAX_FILE_SIZE_MB} MB per file"
    )

    uploaded_files = st.file_uploader(
        "Upload your financial datasets",
        type=[
            extension.replace(
                ".",
                "",
            )
            for extension in ALLOWED_EXTENSIONS
        ],
        accept_multiple_files=True,
        help=(
            "Upload invoices, purchase orders, payments, "
            "contracts, rebates and goods receipts."
        ),
    )

    # ========================================================
    # NO NEW FILES
    # ========================================================

    if not uploaded_files:

        if uploaded_data_is_ready():

            uploaded_workspace = (
                get_uploaded_workspace()
            )

            st.success(
                "✓ Uploaded data is already prepared."
            )

            if uploaded_workspace:

                st.info(
                    f"Workspace: "
                    f"{uploaded_workspace.name}"
                )

                st.code(
                    str(uploaded_workspace),
                    language="text",
                )

        else:

            st.info(
                "Upload your CSV/XLSX files to begin."
            )

        # Existing prepared data can still be analyzed.
        if uploaded_data_is_ready():

            st.divider()

            st.subheader(
                "7️⃣ Run DollarGuard Analysis"
            )

            uploaded_workspace = (
                get_uploaded_workspace()
            )

            if st.button(
                "🚀 Run DollarGuard Analysis",
                type="primary",
                use_container_width=True,
            ):

                with st.spinner(
                    "DollarGuard AI is analyzing "
                    "your uploaded financial data..."
                ):

                    try:

                        result = (
                            run_uploaded_analysis(
                                uploaded_workspace
                            )
                        )

                        st.session_state[
                            "uploaded_analysis_result"
                        ] = result

                        st.session_state[
                            "uploaded_analysis_ready"
                        ] = (
                            result.get(
                                "status"
                            )
                            == "completed"
                        )

                        if st.session_state[
                            "uploaded_analysis_ready"
                        ]:

                            st.success(
                                "✅ Analysis completed successfully."
                            )

                        else:

                            st.warning(
                                "Analysis finished with "
                                "a non-completed status."
                            )

                    except Exception as exc:

                        st.session_state[
                            "uploaded_analysis_ready"
                        ] = False

                        st.error(
                            f"Analysis failed: {exc}"
                        )

        # Show existing results if available.
        render_existing_analysis_results()

        return

    # ========================================================
    # VALIDATION
    # ========================================================

    st.subheader(
        "3️⃣ Dataset Detection & Validation"
    )

    prepared_datasets = {}

    validation_rows = []

    has_errors = False

    detected_dataset_types = set()

    # ========================================================
    # PROCESS EACH FILE
    # ========================================================

    for uploaded_file in uploaded_files:

        st.markdown(
            f"### 📄 {uploaded_file.name}"
        )

        # ----------------------------------------------------
        # File validation
        # ----------------------------------------------------

        file_validation = validate_file(
            uploaded_file.name,
            uploaded_file.size,
        )

        if not file_validation.get(
            "valid",
            False,
        ):

            has_errors = True

            st.error(
                f"{uploaded_file.name}: "
                f"{file_validation.get('message', 'Invalid file.')}"
            )

            continue

        # ----------------------------------------------------
        # Read file
        # ----------------------------------------------------

        try:

            dataframe = read_uploaded_file(
                uploaded_file
            )

        except Exception as exc:

            has_errors = True

            st.error(
                f"{uploaded_file.name}: "
                f"Unable to read file: {exc}"
            )

            continue

        if (
            dataframe is None
            or dataframe.empty
        ):

            has_errors = True

            st.error(
                f"{uploaded_file.name}: "
                "The file contains no usable rows."
            )

            continue

        # ----------------------------------------------------
        # Original columns
        # ----------------------------------------------------

        with st.expander(
            f"View uploaded columns — "
            f"{uploaded_file.name}"
        ):

            st.write(
                list(dataframe.columns)
            )

            st.dataframe(
                dataframe.head(10),
                use_container_width=True,
                hide_index=True,
            )

        # ----------------------------------------------------
        # Detect dataset
        # ----------------------------------------------------

        detection = detect_dataset_type(
            dataframe,
            uploaded_file.name,
        )

        dataset_type = detection.get(
            "dataset_type"
        )

        confidence = safe_number(
            detection.get(
                "confidence",
                0,
            )
        )

        if not dataset_type:

            has_errors = True

            st.error(
                f"{uploaded_file.name}: "
                "Unable to identify this dataset."
            )

            continue

        st.success(
            f"✓ Detected dataset: "
            f"**{get_dataset_label(dataset_type)}**"
        )

        st.caption(
            f"Detection confidence: "
            f"{confidence:.1f}%"
        )

        # ----------------------------------------------------
        # Duplicate dataset protection
        # ----------------------------------------------------

        if dataset_type in detected_dataset_types:

            has_errors = True

            existing = prepared_datasets[
                dataset_type
            ][
                "filename"
            ]

            st.warning(
                f"{get_dataset_label(dataset_type)} "
                f"has already been supplied by "
                f"`{existing}`. "
                f"This file will not replace the "
                f"first uploaded dataset."
            )

            continue

        detected_dataset_types.add(
            dataset_type
        )

        # ----------------------------------------------------
        # Column mapping
        # ----------------------------------------------------

        mapping = suggest_column_mapping(
            dataframe,
            dataset_type,
        )

        if mapping:

            st.write(
                "**Column mapping:**"
            )

            mapping_rows = []

            for (
                canonical,
                uploaded_column,
            ) in mapping.items():

                mapping_rows.append(
                    {
                        "DollarGuard Column":
                            canonical,

                        "Uploaded Column":
                            uploaded_column,
                    }
                )

            st.dataframe(
                pd.DataFrame(
                    mapping_rows
                ),
                use_container_width=True,
                hide_index=True,
            )

        # ----------------------------------------------------
        # Apply mapping
        # ----------------------------------------------------

        normalized_dataframe = (
            apply_column_mapping(
                dataframe,
                mapping,
                dataset_type,
            )
        )

        # ----------------------------------------------------
        # Validate normalized dataset
        # ----------------------------------------------------

        validation = validate_dataset(
            normalized_dataframe,
            dataset_type,
        )

        valid = validation.get(
            "valid",
            False,
        )

        if not valid:

            has_errors = True

            st.error(
                f"✗ {get_dataset_label(dataset_type)}: "
                f"{validation.get('message', 'Validation failed.')}"
            )

            missing = validation.get(
                "missing_columns",
                [],
            )

            if missing:

                st.write(
                    "**Missing required columns:**"
                )

                st.code(
                    "\n".join(missing)
                )

        else:

            st.success(
                f"✓ {get_dataset_label(dataset_type)}: "
                f"{len(normalized_dataframe)} rows "
                f"passed structural validation."
            )

        # ----------------------------------------------------
        # Warnings
        # ----------------------------------------------------

        for warning in validation.get(
            "warnings",
            [],
        ):

            st.warning(
                f"⚠️ {warning}"
            )

        # ----------------------------------------------------
        # Save in memory
        # ----------------------------------------------------

        prepared_datasets[
            dataset_type
        ] = {

            "filename":
                uploaded_file.name,

            "dataframe":
                normalized_dataframe,

            "dataset_type":
                dataset_type,

            "confidence":
                confidence,

            "validation":
                validation,

            "mapping":
                mapping,
        }

        validation_rows.append(
            {
                "File":
                    uploaded_file.name,

                "Detected Dataset":
                    get_dataset_label(
                        dataset_type
                    ),

                "Rows":
                    len(
                        normalized_dataframe
                    ),

                "Detection Confidence":
                    f"{confidence:.1f}%",

                "Validation":
                    (
                        "PASS"
                        if valid
                        else "REVIEW"
                    ),
            }
        )

        # ----------------------------------------------------
        # Normalized preview
        # ----------------------------------------------------

        with st.expander(
            f"Preview normalized "
            f"{get_dataset_label(dataset_type)}"
        ):

            st.dataframe(
                normalized_dataframe.head(20),
                use_container_width=True,
                hide_index=True,
            )

    # ========================================================
    # VALIDATION SUMMARY
    # ========================================================

    if validation_rows:

        st.divider()

        st.subheader(
            "📋 Upload Validation Summary"
        )

        validation_df = pd.DataFrame(
            validation_rows
        )

        st.dataframe(
            validation_df,
            use_container_width=True,
            hide_index=True,
        )

    # ========================================================
    # PREPARE WORKSPACE
    # ========================================================

    st.divider()

    st.subheader(
        "4️⃣ Prepare Uploaded Workspace"
    )

    all_valid = (
        bool(prepared_datasets)
        and not has_errors
        and all(
            info[
                "validation"
            ].get(
                "valid",
                False,
            )
            for info in prepared_datasets.values()
        )
    )

    if not all_valid:

        st.warning(
            "Resolve the validation issues above "
            "before preparing the uploaded workspace."
        )

    if st.button(
        "📦 Prepare Uploaded Data",
        type="primary",
        use_container_width=True,
        disabled=not all_valid,
    ):

        try:

            # IMPORTANT:
            # Keep this as Path.
            workspace = (
                create_upload_workspace()
            )

            saved_datasets = {}

            for (
                dataset_type,
                dataset_info,
            ) in prepared_datasets.items():

                dataframe = dataset_info[
                    "dataframe"
                ]

                saved_path = save_dataframe(
                    dataframe,
                    workspace,
                    dataset_type,
                )

                saved_datasets[
                    dataset_type
                ] = str(
                    saved_path
                )

            # IMPORTANT:
            # DO NOT use str(workspace).
            # Dashboard expects Path.name.
            st.session_state[
                "upload_workspace"
            ] = workspace

            st.session_state[
                "uploaded_datasets"
            ] = saved_datasets

            st.session_state[
                "upload_validated"
            ] = True

            reset_uploaded_analysis()

            st.success(
                "✓ Uploaded datasets prepared successfully."
            )

            st.info(
                f"Workspace: "
                f"{workspace.name}"
            )

            st.code(
                str(workspace),
                language="text",
            )

        except Exception as exc:

            st.error(
                f"Unable to prepare uploaded data: {exc}"
            )

    # ========================================================
    # RUN ANALYSIS
    # ========================================================

    st.divider()

    st.subheader(
        "5️⃣ Run DollarGuard Analysis"
    )

    if uploaded_data_is_ready():

        uploaded_workspace = (
            get_uploaded_workspace()
        )

        st.success(
            "✓ Uploaded datasets are ready "
            "for DollarGuard analysis."
        )

        if uploaded_workspace:

            st.info(
                f"Workspace: "
                f"{uploaded_workspace.name}"
            )

            st.code(
                str(uploaded_workspace),
                language="text",
            )

        if st.button(
            "🚀 Run DollarGuard Analysis",
            type="primary",
            use_container_width=True,
        ):

            with st.spinner(
                "DollarGuard AI is analyzing "
                "your uploaded financial data..."
            ):

                try:

                    result = (
                        run_uploaded_analysis(
                            uploaded_workspace
                        )
                    )

                    st.session_state[
                        "uploaded_analysis_result"
                    ] = result

                    st.session_state[
                        "uploaded_analysis_ready"
                    ] = (
                        result.get(
                            "status"
                        )
                        == "completed"
                    )

                    if st.session_state[
                        "uploaded_analysis_ready"
                    ]:

                        st.success(
                            "✅ DollarGuard analysis "
                            "completed successfully."
                        )

                    else:

                        st.warning(
                            "Analysis completed with "
                            "a non-completed status."
                        )

                except Exception as exc:

                    st.session_state[
                        "uploaded_analysis_ready"
                    ] = False

                    st.error(
                        f"Analysis failed: {exc}"
                    )

    else:

        st.info(
            "Prepare the uploaded workspace first."
        )

    # ========================================================
    # RESULTS
    # ========================================================

    render_existing_analysis_results()

    # ========================================================
    # RESET
    # ========================================================

    if (
        st.session_state.get(
            "upload_workspace"
        )
        or st.session_state.get(
            "uploaded_datasets"
        )
    ):

        st.divider()

        if st.button(
            "🔄 Start New Upload Session",
            use_container_width=True,
        ):

            reset_upload_session()

            st.rerun()


# ============================================================
# ANALYSIS RESULTS
# ============================================================

def render_existing_analysis_results():

    if not st.session_state.get(
        "uploaded_analysis_ready",
        False,
    ):

        return

    result = (
        st.session_state.get(
            "uploaded_analysis_result",
            {},
        )
    )

    if not result:

        return

    st.divider()

    st.header(
        "📊 Uploaded Data Analysis Results"
    )

    total_claims = int(
        safe_number(
            result.get(
                "total_claims",
                0,
            )
        )
    )

    potential_leakage = safe_number(
        result.get(
            "potential_leakage",
            0,
        )
    )

    datasets_found = result.get(
        "datasets_found",
        [],
    )

    leakage_by_type = result.get(
        "leakage_by_type",
        {},
    )

    risk_distribution = result.get(
        "risk_distribution",
        {},
    )

    # ========================================================
    # KPI CARDS
    # ========================================================

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Claims Detected",
            f"{total_claims:,}",
        )

    with col2:

        st.metric(
            "Potential Leakage",
            money(
                potential_leakage
            ),
        )

    with col3:

        st.metric(
            "Datasets Analyzed",
            f"{len(datasets_found):,}",
        )

    with col4:

        st.metric(
            "Leakage Categories",
            f"{len(leakage_by_type):,}",
        )

    # ========================================================
    # LEAKAGE BY TYPE
    # ========================================================

    st.subheader(
        "💰 Leakage by Type"
    )

    if leakage_by_type:

        leakage_rows = []

        for (
            leakage_type,
            amount,
        ) in leakage_by_type.items():

            leakage_rows.append(
                {
                    "Leakage Type":
                        leakage_type,

                    "Potential Leakage":
                        safe_number(
                            amount
                        ),
                }
            )

        leakage_df = pd.DataFrame(
            leakage_rows
        )

        display_df = (
            leakage_df.copy()
        )

        display_df[
            "Potential Leakage"
        ] = display_df[
            "Potential Leakage"
        ].map(
            money
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )

        st.bar_chart(
            leakage_df.set_index(
                "Leakage Type"
            )[
                "Potential Leakage"
            ]
        )

    else:

        st.info(
            "No leakage categories detected."
        )

    # ========================================================
    # RISK DISTRIBUTION
    # ========================================================

    st.subheader(
        "⚠️ Risk Distribution"
    )

    if risk_distribution:

        risk_rows = []

        for (
            risk_level,
            count,
        ) in risk_distribution.items():

            risk_rows.append(
                {
                    "Risk Level":
                        risk_level,

                    "Claims":
                        count,
                }
            )

        risk_df = pd.DataFrame(
            risk_rows
        )

        st.dataframe(
            risk_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No risk distribution available."
        )

    # ========================================================
    # DATASETS USED
    # ========================================================

    st.subheader(
        "📁 Datasets Used"
    )

    if datasets_found:

        st.write(
            ", ".join(
                get_dataset_label(
                    dataset
                )
                for dataset in datasets_found
            )
        )

    # ========================================================
    # CLAIM FILE
    # ========================================================

    workspace = (
        get_uploaded_workspace()
    )

    if workspace:

        claims_file = (
            workspace
            / "results"
            / "uploaded_unified_claims.csv"
        )

        if claims_file.exists():

            try:

                claims_df = pd.read_csv(
                    claims_file
                )

            except Exception as exc:

                st.error(
                    f"Unable to load claims: {exc}"
                )

                claims_df = pd.DataFrame()

            if not claims_df.empty:

                st.subheader(
                    "🔎 Detected Leakage Claims"
                )

                filtered_claims = (
                    claims_df.copy()
                )

                col1, col2 = (
                    st.columns(2)
                )

                # ------------------------------------------------
                # Leakage filter
                # ------------------------------------------------

                with col1:

                    if (
                        "leakage_type"
                        in filtered_claims.columns
                    ):

                        leakage_options = [
                            "All"
                        ] + sorted(
                            filtered_claims[
                                "leakage_type"
                            ]
                            .dropna()
                            .astype(str)
                            .unique()
                            .tolist()
                        )

                        selected_leakage = (
                            st.selectbox(
                                "Leakage Type",
                                leakage_options,
                            )
                        )

                        if (
                            selected_leakage
                            != "All"
                        ):

                            filtered_claims = (
                                filtered_claims[
                                    filtered_claims[
                                        "leakage_type"
                                    ].astype(str)
                                    == selected_leakage
                                ]
                            )

                # ------------------------------------------------
                # Risk filter
                # ------------------------------------------------

                with col2:

                    if (
                        "risk_level"
                        in filtered_claims.columns
                    ):

                        risk_options = [
                            "All"
                        ] + sorted(
                            filtered_claims[
                                "risk_level"
                            ]
                            .dropna()
                            .astype(str)
                            .unique()
                            .tolist()
                        )

                        selected_risk = (
                            st.selectbox(
                                "Risk Level",
                                risk_options,
                            )
                        )

                        if (
                            selected_risk
                            != "All"
                        ):

                            filtered_claims = (
                                filtered_claims[
                                    filtered_claims[
                                        "risk_level"
                                    ].astype(str)
                                    == selected_risk
                                ]
                            )

                st.write(
                    f"Showing "
                    f"**{len(filtered_claims):,}** "
                    f"claims."
                )

                display_claims = (
                    filtered_claims.copy()
                )

                if (
                    "potential_leakage"
                    in display_claims.columns
                ):

                    display_claims[
                        "potential_leakage"
                    ] = pd.to_numeric(
                        display_claims[
                            "potential_leakage"
                        ],
                        errors="coerce",
                    ).fillna(0)

                    display_claims[
                        "potential_leakage"
                    ] = display_claims[
                        "potential_leakage"
                    ].map(
                        money
                    )

                st.dataframe(
                    display_claims,
                    use_container_width=True,
                    hide_index=True,
                )

                # ------------------------------------------------
                # Download
                # ------------------------------------------------

                st.download_button(
                    "⬇️ Download Filtered Claims",
                    data=filtered_claims.to_csv(
                        index=False
                    ),
                    file_name=(
                        "dollarguard_uploaded_claims.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                )

    # ========================================================
    # RAW RESULT
    # ========================================================

    with st.expander(
        "View Analysis Summary"
    ):

        st.json(
            result
        )


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def render_upload_page():

    render_data_upload_page()


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    st.set_page_config(
        page_title=(
            "DollarGuard AI - Data Upload"
        ),
        page_icon="📂",
        layout="wide",
    )

    render_data_upload_page()