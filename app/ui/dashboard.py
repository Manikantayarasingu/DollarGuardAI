
"""
DollarGuard AI
Executive Revenue Leakage Dashboard

Step 35:
    Real Data Upload & Analysis

Features:
    - Executive overview
    - Leakage claims
    - AI investigations
    - Recovery claims
    - Recovery Command Center
    - Executive Recovery Analytics
    - Vendor Intelligence
    - Contract Intelligence
    - Investigation Center
    - ML anomalies
    - Real CSV/XLSX data upload
    - Data validation and column mapping
    - Demo Data / Upload My Data mode
"""

from pathlib import Path
import json

import pandas as pd
import plotly.express as px
import streamlit as st

from app.ui.data_upload import (
    render_data_upload_page,
    uploaded_data_is_ready,
    get_uploaded_workspace,
    get_uploaded_datasets,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed"

CLAIMS_FILE = PROCESSED_DIR / "unified_claims.csv"

ANOMALIES_FILE = (
    PROCESSED_DIR / "ml_anomalies.csv"
)

INVESTIGATIONS_FILE = (
    PROCESSED_DIR / "investigation_reports.csv"
)

RECOVERY_FILE = (
    PROCESSED_DIR / "recovery_claims.csv"
)

CONTRACT_INTELLIGENCE_FILE = (
    PROCESSED_DIR / "contract_intelligence.csv"
)

CONTRACT_COMPLIANCE_FILE = (
    PROCESSED_DIR / "contract_compliance.csv"
)

VENDOR_ANALYTICS_FILE = (
    PROCESSED_DIR / "vendor_analytics.csv"
)

INVESTIGATION_PACKETS_FILE = (
    PROCESSED_DIR / "investigation_packets.csv"
)

RECOVERY_COMMAND_CENTER_FILE = (
    PROCESSED_DIR / "recovery_command_center.csv"
)

RECOVERY_ANALYTICS_FILE = (
    PROCESSED_DIR / "recovery_analytics.csv"
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="DollarGuard AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# HELPERS
# ============================================================

def load_csv(path: Path) -> pd.DataFrame:

    if not path.exists():
        return pd.DataFrame()

    try:

        dataframe = pd.read_csv(path)

        dataframe.columns = [
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            for column in dataframe.columns
        ]

        return dataframe

    except Exception as exc:

        st.error(
            f"Unable to load {path.name}: {exc}"
        )

        return pd.DataFrame()


def safe_number(series):

    return pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0)


def money(value) -> str:

    try:

        return f"₹{float(value):,.2f}"

    except (ValueError, TypeError):

        return "₹0.00"


def save_recovery_data(
    dataframe: pd.DataFrame
) -> bool:

    try:

        dataframe.to_csv(
            RECOVERY_FILE,
            index=False
        )

        return True

    except Exception as exc:

        st.error(
            f"Unable to save recovery claims: {exc}"
        )

        return False


# ============================================================
# LOAD PROCESSED DATA
# ============================================================

claims_df = load_csv(
    CLAIMS_FILE
)

anomalies_df = load_csv(
    ANOMALIES_FILE
)

investigations_df = load_csv(
    INVESTIGATIONS_FILE
)

recovery_df = load_csv(
    RECOVERY_FILE
)

contract_intelligence_df = load_csv(
    CONTRACT_INTELLIGENCE_FILE
)

contract_compliance_df = load_csv(
    CONTRACT_COMPLIANCE_FILE
)

vendor_df = load_csv(
    VENDOR_ANALYTICS_FILE
)

investigation_packets_df = load_csv(
    INVESTIGATION_PACKETS_FILE
)

recovery_command_df = load_csv(
    RECOVERY_COMMAND_CENTER_FILE
)

recovery_analytics_df = load_csv(
    RECOVERY_ANALYTICS_FILE
)


# ============================================================
# PREPARE RECOVERY DATA
# ============================================================

if not recovery_df.empty:

    for column in [
        "potential_leakage",
        "claimed_amount",
        "recovered_amount",
        "outstanding_amount",
        "confidence_score",
    ]:

        if column in recovery_df.columns:

            recovery_df[column] = safe_number(
                recovery_df[column]
            )

    if "claim_status" in recovery_df.columns:

        recovery_df["claim_status"] = (
            recovery_df["claim_status"]
            .astype(str)
            .str.upper()
        )

    if "recovery_priority" in recovery_df.columns:

        recovery_df["recovery_priority"] = (
            recovery_df["recovery_priority"]
            .astype(str)
            .str.upper()
        )


# ============================================================
# HEADER
# ============================================================

st.title("💰 DollarGuard AI")

st.markdown(
    """
### AI-Powered Revenue Leakage Detection & Recovery Platform

Detect financial leakage, investigate root causes, and manage
supplier recovery claims across enterprise financial data.
"""
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("DollarGuard AI")

st.sidebar.markdown(
    "### Navigation"
)

page = st.sidebar.radio(
    "Select View",
    [
        "Executive Overview",
        "📂 Data Management",
        "Claims",
        "AI Investigator",
        "Recovery Claims",
        "Recovery Command Center",
        "Executive Recovery Analytics",
        "Vendor Intelligence",
        "Contract Intelligence",
        "Investigation Center",
        "ML Anomalies",
    ],
)


# ============================================================
# DATA MODE STATUS
# ============================================================

uploaded_ready = uploaded_data_is_ready()

if uploaded_ready:

    uploaded_workspace = get_uploaded_workspace()
    uploaded_datasets = get_uploaded_datasets()

    st.sidebar.success(
        "📂 Uploaded Data Ready"
    )

    if uploaded_workspace:

        st.sidebar.caption(
            f"Workspace: {uploaded_workspace.name}"
        )

    if uploaded_datasets:

        st.sidebar.caption(
            f"{len(uploaded_datasets)} dataset(s) prepared"
        )

else:

    st.sidebar.info(
        "🧪 Demo Data Mode"
    )


# ============================================================
# EXECUTIVE RECOVERY METRICS
# ============================================================

if not recovery_df.empty:

    total_claimed = safe_number(
        recovery_df["claimed_amount"]
    ).sum()

    total_recovered = safe_number(
        recovery_df["recovered_amount"]
    ).sum()

    total_outstanding = safe_number(
        recovery_df["outstanding_amount"]
    ).sum()

    recovery_rate = (
        total_recovered / total_claimed * 100
        if total_claimed > 0
        else 0
    )

else:

    total_claimed = 0
    total_recovered = 0
    total_outstanding = 0
    recovery_rate = 0


# ============================================================
# DATA MANAGEMENT
# ============================================================

if page == "📂 Data Management":

    render_data_upload_page()


# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================

elif page == "Executive Overview":

    st.header("📊 Executive Overview")

    if uploaded_ready:

        st.success(
            "📂 Uploaded enterprise data is prepared and ready for analysis."
        )

        st.caption(
            "The current dashboard continues to display the processed "
            "DollarGuard pipeline. Uploaded files are stored in a dedicated "
            "workspace and are ready for the next pipeline execution step."
        )

    # --------------------------------------------------------
    # Main KPIs
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Detected Claims",
            f"{len(claims_df):,}"
        )

    with col2:

        st.metric(
            "Potential Leakage",
            money(
                safe_number(
                    claims_df["potential_leakage"]
                ).sum()
                if (
                    not claims_df.empty
                    and "potential_leakage"
                    in claims_df.columns
                )
                else 0
            )
        )

    with col3:

        st.metric(
            "Claimed for Recovery",
            money(total_claimed)
        )

    with col4:

        st.metric(
            "Recovered",
            money(total_recovered)
        )

    st.divider()

    # --------------------------------------------------------
    # Recovery KPIs
    # --------------------------------------------------------

    st.subheader(
        "💰 Recovery Performance"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Outstanding",
            money(total_outstanding)
        )

    with col2:

        st.metric(
            "Recovery Rate",
            f"{recovery_rate:.2f}%"
        )

    with col3:

        if not recovery_df.empty:

            urgent_count = int(
                (
                    recovery_df[
                        "recovery_priority"
                    ]
                    == "URGENT"
                ).sum()
            )

        else:

            urgent_count = 0

        st.metric(
            "Urgent Recoveries",
            f"{urgent_count:,}"
        )

    with col4:

        if not recovery_df.empty:

            recovered_claims = int(
                (
                    recovery_df[
                        "claim_status"
                    ]
                    == "RECOVERED"
                ).sum()
            )

        else:

            recovered_claims = 0

        st.metric(
            "Recovered Claims",
            f"{recovered_claims:,}"
        )

    st.divider()

    # --------------------------------------------------------
    # Charts
    # --------------------------------------------------------

    left, right = st.columns(2)

    with left:

        st.subheader(
            "Leakage by Type"
        )

        if (
            not claims_df.empty
            and "leakage_type" in claims_df.columns
        ):

            leakage_data = (
                claims_df
                .groupby(
                    "leakage_type"
                )["potential_leakage"]
                .sum()
                .reset_index()
                .sort_values(
                    "potential_leakage",
                    ascending=False
                )
            )

            fig = px.bar(
                leakage_data,
                x="leakage_type",
                y="potential_leakage",
                title="Potential Leakage by Type",
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info(
                "Leakage data unavailable."
            )

    with right:

        st.subheader(
            "Recovery Status"
        )

        if (
            not recovery_df.empty
            and "claim_status"
            in recovery_df.columns
        ):

            status_data = (
                recovery_df[
                    "claim_status"
                ]
                .value_counts()
                .reset_index()
            )

            status_data.columns = [
                "status",
                "count"
            ]

            fig = px.pie(
                status_data,
                names="status",
                values="count",
                title="Recovery Claim Status",
                hole=0.45,
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info(
                "Recovery data unavailable."
            )

    # --------------------------------------------------------
    # Recovery Priority
    # --------------------------------------------------------

    st.subheader(
        "Recovery Priority"
    )

    if not recovery_df.empty:

        priority_data = (
            recovery_df[
                "recovery_priority"
            ]
            .value_counts()
            .reset_index()
        )

        priority_data.columns = [
            "priority",
            "count"
        ]

        fig = px.bar(
            priority_data,
            x="priority",
            y="count",
            title="Recovery Priority Distribution",
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# CLAIMS
# ============================================================

elif page == "Claims":

    st.header(
        "🚨 Revenue Leakage Claims"
    )

    if claims_df.empty:

        st.info(
            "No leakage claims available."
        )

    else:

        dataframe = claims_df.copy()

        # ----------------------------------------------------
        # Filters
        # ----------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            if "risk_level" in dataframe.columns:

                options = sorted(
                    dataframe[
                        "risk_level"
                    ]
                    .dropna()
                    .astype(str)
                    .unique()
                )

                selected = st.multiselect(
                    "Risk Level",
                    options,
                    default=list(options),
                )

                dataframe = dataframe[
                    dataframe["risk_level"]
                    .astype(str)
                    .isin(selected)
                ]

        with col2:

            if "leakage_type" in dataframe.columns:

                options = sorted(
                    dataframe[
                        "leakage_type"
                    ]
                    .dropna()
                    .astype(str)
                    .unique()
                )

                selected = st.multiselect(
                    "Leakage Type",
                    options,
                    default=list(options),
                )

                dataframe = dataframe[
                    dataframe["leakage_type"]
                    .astype(str)
                    .isin(selected)
                ]

        with col3:

            search = st.text_input(
                "Search Claim / Vendor / Invoice"
            )

            if search:

                search = search.lower()

                columns = [
                    column
                    for column in [
                        "claim_id",
                        "vendor_id",
                        "invoice_id",
                        "po_id",
                        "sku",
                    ]
                    if column in dataframe.columns
                ]

                mask = pd.Series(
                    False,
                    index=dataframe.index
                )

                for column in columns:

                    mask = mask | (
                        dataframe[column]
                        .astype(str)
                        .str.lower()
                        .str.contains(
                            search,
                            na=False
                        )
                    )

                dataframe = dataframe[
                    mask
                ]

        st.write(
            f"Showing **{len(dataframe):,}** claims"
        )

        display_columns = [
            "claim_id",
            "leakage_type",
            "vendor_id",
            "invoice_id",
            "potential_leakage",
            "confidence_score",
            "risk_level",
            "status",
        ]

        display_columns = [
            column
            for column in display_columns
            if column in dataframe.columns
        ]

        st.dataframe(
            dataframe[
                display_columns
            ],
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# AI INVESTIGATOR
# ============================================================

elif page == "AI Investigator":

    st.header(
        "🧠 AI Investigator"
    )

    if investigations_df.empty:

        st.warning(
            "Investigation reports are not available."
        )

        st.code(
            "python -m app.services.ai_investigator",
            language="powershell"
        )

    else:

        dataframe = investigations_df.copy()

        dataframe[
            "potential_leakage"
        ] = safe_number(
            dataframe["potential_leakage"]
        )

        dataframe[
            "confidence_score"
        ] = safe_number(
            dataframe["confidence_score"]
        )

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Investigations",
                f"{len(dataframe):,}"
            )

        with col2:

            p1 = int(
                (
                    dataframe[
                        "investigation_priority"
                    ]
                    .astype(str)
                    .str.upper()
                    == "P1"
                ).sum()
            )

            st.metric(
                "P1 Investigations",
                f"{p1:,}"
            )

        with col3:

            strong = int(
                (
                    dataframe[
                        "evidence_quality"
                    ]
                    .astype(str)
                    .str.upper()
                    == "STRONG"
                ).sum()
            )

            st.metric(
                "Strong Evidence",
                f"{strong:,}"
            )

        with col4:

            st.metric(
                "Potential Exposure",
                money(
                    dataframe[
                        "potential_leakage"
                    ].sum()
                )
            )

        st.divider()

        # ----------------------------------------------------
        # Investigation Selector
        # ----------------------------------------------------

        search = st.text_input(
            "Search Investigation / Claim / Vendor / Invoice"
        )

        filtered = dataframe.copy()

        if search:

            search = search.lower()

            searchable = [
                column
                for column in [
                    "investigation_id",
                    "claim_id",
                    "vendor_id",
                    "invoice_id",
                ]
                if column in filtered.columns
            ]

            mask = pd.Series(
                False,
                index=filtered.index
            )

            for column in searchable:

                mask = mask | (
                    filtered[column]
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        search,
                        na=False
                    )
                )

            filtered = filtered[
                mask
            ]

        if not filtered.empty:

            investigation_ids = (
                filtered[
                    "investigation_id"
                ]
                .astype(str)
                .tolist()
            )

            selected_id = st.selectbox(
                "Select Investigation",
                investigation_ids,
            )

            report = filtered[
                filtered[
                    "investigation_id"
                ].astype(str)
                == selected_id
            ].iloc[0]

            col1, col2, col3, col4 = st.columns(4)

            with col1:

                st.metric(
                    "Potential Leakage",
                    money(
                        report.get(
                            "potential_leakage",
                            0
                        )
                    )
                )

            with col2:

                st.metric(
                    "Priority",
                    report.get(
                        "investigation_priority",
                        "N/A"
                    )
                )

            with col3:

                st.metric(
                    "Risk",
                    report.get(
                        "risk_level",
                        "N/A"
                    )
                )

            with col4:

                st.metric(
                    "Evidence",
                    report.get(
                        "evidence_quality",
                        "N/A"
                    )
                )

            st.divider()

            st.subheader(
                "🧠 Root Cause"
            )

            st.warning(
                report.get(
                    "root_cause",
                    "Unavailable"
                )
            )

            st.subheader(
                "📑 Evidence"
            )

            st.info(
                report.get(
                    "evidence",
                    "Unavailable"
                )
            )

            st.subheader(
                "🔎 Investigation Summary"
            )

            st.write(
                report.get(
                    "investigation_summary",
                    "Unavailable"
                )
            )

            st.subheader(
                "💰 Recommended Recovery Action"
            )

            st.success(
                report.get(
                    "recommended_recovery_action",
                    "Unavailable"
                )
            )

        else:

            st.info(
                "No investigations match your search."
            )


# ============================================================
# RECOVERY COMMAND CENTER
# ============================================================

elif page == "Recovery Command Center":

    st.header("🎯 Recovery Command Center")

    st.caption(
        "Operational queue connecting investigation evidence to recovery claims. "
        "Amounts shown are synthetic claim/exposure values from this portfolio dataset."
    )

    if recovery_command_df.empty:

        st.warning(
            "Recovery Command Center data is not available yet."
        )

        st.code(
            "python -m app.services.recovery_command_center",
            language="powershell"
        )

    else:

        dataframe = recovery_command_df.copy()

        for column in [
            "claimed_amount",
            "recovered_amount",
            "outstanding_amount",
            "recovery_rate",
            "confidence_score",
            "evidence_coverage",
        ]:
            if column in dataframe.columns:
                dataframe[column] = safe_number(dataframe[column])

        claimed = safe_number(
            dataframe["claimed_amount"]
        ).sum()

        recovered = safe_number(
            dataframe["recovered_amount"]
        ).sum()

        outstanding = safe_number(
            dataframe["outstanding_amount"]
        ).sum()

        urgent_open = int(
            (
                dataframe.get(
                    "recovery_priority",
                    pd.Series(
                        dtype=str
                    )
                )
                .astype(str)
                .str.upper()
                .eq("URGENT")
                &
                ~dataframe.get(
                    "claim_status",
                    pd.Series(
                        dtype=str
                    )
                )
                .astype(str)
                .str.upper()
                .isin(
                    [
                        "RECOVERED",
                        "CLOSED",
                        "REJECTED"
                    ]
                )
            ).sum()
        )

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "Recovery Queue",
                f"{len(dataframe):,}"
            )

        with col2:
            st.metric(
                "Claimed",
                money(claimed)
            )

        with col3:
            st.metric(
                "Recovered",
                money(recovered)
            )

        with col4:
            st.metric(
                "Outstanding",
                money(outstanding)
            )

        with col5:
            st.metric(
                "Urgent Open",
                f"{urgent_open:,}"
            )

        st.divider()

        # ----------------------------------------------------
        # Filters
        # ----------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            priorities = [
                "URGENT",
                "HIGH",
                "MEDIUM",
                "NORMAL"
            ]

            available = [
                value
                for value in priorities
                if value in set(
                    dataframe[
                        "recovery_priority"
                    ]
                    .astype(str)
                    .str.upper()
                )
            ]

            selected_priorities = st.multiselect(
                "Priority",
                available,
                default=available,
            )

        with col2:

            statuses = sorted(
                dataframe[
                    "claim_status"
                ]
                .astype(str)
                .str.upper()
                .unique()
                .tolist()
            )

            selected_statuses = st.multiselect(
                "Status",
                statuses,
                default=statuses,
            )

        with col3:

            leakage_types = sorted(
                dataframe.get(
                    "leakage_type",
                    pd.Series(
                        dtype=str
                    )
                )
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            selected_leakage = st.multiselect(
                "Leakage Type",
                leakage_types,
                default=leakage_types,
            )

        with col4:

            search = st.text_input(
                "Search claim / investigation / vendor / invoice"
            )

        filtered = dataframe.copy()

        filtered = filtered[
            filtered[
                "recovery_priority"
            ]
            .astype(str)
            .str.upper()
            .isin(
                selected_priorities
            )
        ]

        filtered = filtered[
            filtered[
                "claim_status"
            ]
            .astype(str)
            .str.upper()
            .isin(
                selected_statuses
            )
        ]

        if leakage_types:

            filtered = filtered[
                filtered.get(
                    "leakage_type",
                    pd.Series(
                        "",
                        index=filtered.index
                    )
                )
                .astype(str)
                .isin(
                    selected_leakage
                )
            ]

        if search:

            term = search.lower().strip()

            searchable = [
                column
                for column in [
                    "recovery_claim_id",
                    "investigation_id",
                    "investigation_packet_id",
                    "original_claim_id",
                    "vendor_id",
                    "invoice_id",
                    "po_id",
                    "contract_id",
                ]
                if column in filtered.columns
            ]

            mask = pd.Series(
                False,
                index=filtered.index
            )

            for column in searchable:

                mask = mask | (
                    filtered[
                        column
                    ]
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        term,
                        na=False,
                        regex=False
                    )
                )

            filtered = filtered[
                mask
            ]

        st.write(
            f"Showing **{len(filtered):,}** recovery queue items"
        )

        queue_columns = [
            "recovery_claim_id",
            "investigation_packet_id",
            "vendor_id",
            "invoice_id",
            "leakage_type",
            "recovery_priority",
            "claim_status",
            "claimed_amount",
            "recovered_amount",
            "outstanding_amount",
            "evidence_coverage",
            "aging_days",
            "next_action",
        ]

        queue_columns = [
            column
            for column in queue_columns
            if column in filtered.columns
        ]

        st.dataframe(
            filtered[
                queue_columns
            ],
            use_container_width=True,
            hide_index=True,
        )

        if not filtered.empty:

            st.divider()

            st.subheader(
                "🔎 Recovery Work Item"
            )

            claim_ids = (
                filtered[
                    "recovery_claim_id"
                ]
                .astype(str)
                .tolist()
            )

            selected_claim = st.selectbox(
                "Select Recovery Claim",
                claim_ids,
            )

            selected_row = filtered[
                filtered[
                    "recovery_claim_id"
                ].astype(str)
                == selected_claim
            ].iloc[0]

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "Claimed",
                    money(
                        selected_row.get(
                            "claimed_amount",
                            0
                        )
                    )
                )

            with c2:
                st.metric(
                    "Recovered",
                    money(
                        selected_row.get(
                            "recovered_amount",
                            0
                        )
                    )
                )

            with c3:
                st.metric(
                    "Outstanding",
                    money(
                        selected_row.get(
                            "outstanding_amount",
                            0
                        )
                    )
                )

            with c4:
                st.metric(
                    "Evidence Coverage",
                    f"{float(selected_row.get('evidence_coverage', 0)):.1f}%"
                )

            left, right = st.columns(2)

            with left:

                st.markdown(
                    f"**Recovery Claim:** "
                    f"{selected_row.get('recovery_claim_id', 'N/A')}"
                )

                st.markdown(
                    f"**Investigation:** "
                    f"{selected_row.get('investigation_id', 'N/A')}"
                )

                st.markdown(
                    f"**Investigation Packet:** "
                    f"{selected_row.get('investigation_packet_id', 'N/A')}"
                )

                st.markdown(
                    f"**Original Claim:** "
                    f"{selected_row.get('original_claim_id', 'N/A')}"
                )

                st.markdown(
                    f"**Vendor:** "
                    f"{selected_row.get('vendor_id', 'N/A')}"
                )

                st.markdown(
                    f"**Invoice:** "
                    f"{selected_row.get('invoice_id', 'N/A')}"
                )

                st.markdown(
                    f"**PO:** "
                    f"{selected_row.get('po_id', 'N/A')}"
                )

                st.markdown(
                    f"**Contract:** "
                    f"{selected_row.get('contract_id', 'N/A')}"
                )

            with right:

                st.markdown(
                    f"**Leakage Type:** "
                    f"{selected_row.get('leakage_type', 'N/A')}"
                )

                st.markdown(
                    f"**Risk Level:** "
                    f"{selected_row.get('risk_level', 'N/A')}"
                )

                st.markdown(
                    f"**Recovery Priority:** "
                    f"{selected_row.get('recovery_priority', 'N/A')}"
                )

                st.markdown(
                    f"**Claim Status:** "
                    f"{selected_row.get('claim_status', 'N/A')}"
                )

                st.markdown(
                    f"**Supplier Response:** "
                    f"{selected_row.get('supplier_response', 'N/A')}"
                )

                st.markdown(
                    f"**Aging:** "
                    f"{int(float(selected_row.get('aging_days', 0)))} days"
                )

                st.markdown(
                    f"**Next Action:** "
                    f"{selected_row.get('next_action', 'N/A')}"
                )

            st.divider()

            st.subheader(
                "🧾 Investigation Evidence"
            )

            conclusion = selected_row.get(
                "investigation_conclusion",
                ""
            )

            recommended = selected_row.get(
                "recommended_recovery_action",
                ""
            )

            if conclusion and not pd.isna(conclusion):
                st.info(str(conclusion))
            else:
                st.info(
                    "Investigation conclusion is not available."
                )

            if recommended and not pd.isna(recommended):
                st.success(str(recommended))
            else:
                st.warning(
                    "Recommended recovery action is not available."
                )

            if "evidence_chain" in selected_row.index:

                evidence_value = selected_row.get(
                    "evidence_chain",
                    ""
                )

                if (
                    evidence_value
                    and not pd.isna(evidence_value)
                ):

                    try:

                        evidence = json.loads(
                            str(evidence_value)
                        )

                        st.json(evidence)

                    except Exception:

                        st.code(
                            str(evidence_value),
                            language="text"
                        )

            st.caption(
                "Evidence coverage measures how much expected evidence "
                "is available in the synthetic dataset; it is not a "
                "fraud probability or a finding of intentional wrongdoing."
            )

            st.info(
                "Use the Recovery Claims page to edit claim status, "
                "supplier response, recovered amount, and notes."
            )


# ============================================================
# EXECUTIVE RECOVERY ANALYTICS
# ============================================================

elif page == "Executive Recovery Analytics":

    st.header(
        "📈 Executive Recovery Analytics"
    )

    st.caption(
        "Management view of the synthetic recovery pipeline: exposure, "
        "recovery progress, priority, aging, leakage/recovery categories, "
        "and vendor-level recovery performance."
    )

    if recovery_df.empty:

        st.warning(
            "Recovery claims data is not available yet."
        )

        st.stop()

    claimed = safe_number(
        recovery_df.get(
            "claimed_amount",
            pd.Series(
                dtype=float
            )
        )
    ).sum()

    recovered = safe_number(
        recovery_df.get(
            "recovered_amount",
            pd.Series(
                dtype=float
            )
        )
    ).sum()

    outstanding = safe_number(
        recovery_df.get(
            "outstanding_amount",
            pd.Series(
                dtype=float
            )
        )
    ).sum()

    overall_rate = (
        recovered / claimed * 100
        if claimed
        else 0
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Recovery Claims",
        f"{len(recovery_df):,}"
    )

    c2.metric(
        "Claimed Exposure",
        money(claimed)
    )

    c3.metric(
        "Recovered",
        money(recovered)
    )

    c4.metric(
        "Outstanding",
        money(outstanding)
    )

    c5.metric(
        "Recovery Rate",
        f"{overall_rate:.2f}%"
    )

    st.divider()

    st.subheader(
        "Recovery Funnel"
    )

    funnel = pd.DataFrame(
        {
            "Stage": [
                "Claimed",
                "Recovered",
                "Outstanding"
            ],
            "Amount": [
                claimed,
                recovered,
                outstanding
            ],
        }
    )

    fig = px.bar(
        funnel,
        x="Stage",
        y="Amount",
        text_auto=".2s",
        title="Claimed vs Recovered vs Outstanding",
    )

    fig.update_layout(
        yaxis_title="Amount (INR)",
        xaxis_title=""
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    left, right = st.columns(2)

    with left:

        st.subheader(
            "Recovery Status"
        )

        status_df = recovery_df.copy()

        if "claim_status" in status_df.columns:

            status_summary = (
                status_df
                .groupby(
                    "claim_status",
                    dropna=False
                )
                .agg(
                    Claims=(
                        "recovery_claim_id",
                        "count"
                    ),
                    Claimed=(
                        "claimed_amount",
                        "sum"
                    ),
                    Recovered=(
                        "recovered_amount",
                        "sum"
                    ),
                    Outstanding=(
                        "outstanding_amount",
                        "sum"
                    ),
                )
                .reset_index()
            )

            fig_status = px.bar(
                status_summary,
                x="claim_status",
                y="Claims",
                text_auto=True,
                title="Claims by Status",
            )

            st.plotly_chart(
                fig_status,
                use_container_width=True
            )

            st.dataframe(
                status_summary,
                use_container_width=True,
                hide_index=True
            )

    with right:

        st.subheader(
            "Recovery Priority"
        )

        priority_df = recovery_df.copy()

        if "recovery_priority" in priority_df.columns:

            priority_summary = (
                priority_df
                .groupby(
                    "recovery_priority",
                    dropna=False
                )
                .agg(
                    Claims=(
                        "recovery_claim_id",
                        "count"
                    ),
                    Claimed=(
                        "claimed_amount",
                        "sum"
                    ),
                    Recovered=(
                        "recovered_amount",
                        "sum"
                    ),
                    Outstanding=(
                        "outstanding_amount",
                        "sum"
                    ),
                )
                .reset_index()
            )

            priority_order = [
                "URGENT",
                "HIGH",
                "MEDIUM",
                "NORMAL"
            ]

            priority_summary[
                "sort_order"
            ] = (
                priority_summary[
                    "recovery_priority"
                ]
                .map(
                    {
                        value: index
                        for index, value
                        in enumerate(
                            priority_order
                        )
                    }
                )
                .fillna(99)
            )

            priority_summary = (
                priority_summary
                .sort_values(
                    "sort_order"
                )
                .drop(
                    columns="sort_order"
                )
            )

            fig_priority = px.bar(
                priority_summary,
                x="recovery_priority",
                y="Claims",
                text_auto=True,
                title="Claims by Recovery Priority",
            )

            st.plotly_chart(
                fig_priority,
                use_container_width=True
            )

            st.dataframe(
                priority_summary,
                use_container_width=True,
                hide_index=True
            )

    st.divider()

    st.subheader(
        "Recovery Aging"
    )

    aging_df = recovery_df.copy()

    if "created_at" in aging_df.columns:

        aging_df["created_at"] = pd.to_datetime(
            aging_df["created_at"],
            errors="coerce"
        )

        now = pd.Timestamp.now()

        aging_df[
            "claim_age_days"
        ] = (
            now
            - aging_df["created_at"]
        ).dt.total_seconds().div(
            86400
        ).fillna(0).clip(
            lower=0
        )

        aging_df[
            "aging_bucket"
        ] = pd.cut(
            aging_df["claim_age_days"],
            bins=[
                -1,
                7,
                30,
                60,
                90,
                float("inf")
            ],
            labels=[
                "0-7 days",
                "8-30 days",
                "31-60 days",
                "61-90 days",
                "90+ days"
            ],
        )

        aging_summary = (
            aging_df
            .groupby(
                "aging_bucket",
                observed=False
            )
            .agg(
                Claims=(
                    "recovery_claim_id",
                    "count"
                ),
                Claimed=(
                    "claimed_amount",
                    "sum"
                ),
                Recovered=(
                    "recovered_amount",
                    "sum"
                ),
                Outstanding=(
                    "outstanding_amount",
                    "sum"
                ),
            )
            .reset_index()
        )

        fig_aging = px.bar(
            aging_summary,
            x="aging_bucket",
            y="Outstanding",
            text_auto=".2s",
            title="Outstanding Exposure by Claim Age",
        )

        st.plotly_chart(
            fig_aging,
            use_container_width=True
        )

        st.dataframe(
            aging_summary,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    st.subheader(
        "Recovery by Category"
    )

    if "recovery_category" in recovery_df.columns:

        category_summary = (
            recovery_df
            .groupby(
                "recovery_category",
                dropna=False
            )
            .agg(
                Claims=(
                    "recovery_claim_id",
                    "count"
                ),
                Claimed=(
                    "claimed_amount",
                    "sum"
                ),
                Recovered=(
                    "recovered_amount",
                    "sum"
                ),
                Outstanding=(
                    "outstanding_amount",
                    "sum"
                ),
            )
            .reset_index()
        )

        category_summary[
            "Recovery Rate %"
        ] = (
            category_summary[
                "Recovered"
            ]
            /
            category_summary[
                "Claimed"
            ].replace(
                0,
                pd.NA
            )
            * 100
        ).fillna(0)

        fig_category = px.bar(
            category_summary,
            x="recovery_category",
            y="Outstanding",
            text_auto=".2s",
            title="Outstanding Exposure by Recovery Category",
        )

        st.plotly_chart(
            fig_category,
            use_container_width=True
        )

        st.dataframe(
            category_summary,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    st.subheader(
        "Vendor Recovery Performance"
    )

    vendor_summary = (
        recovery_df
        .groupby(
            "vendor_id",
            dropna=False
        )
        .agg(
            Claims=(
                "recovery_claim_id",
                "count"
            ),
            Claimed=(
                "claimed_amount",
                "sum"
            ),
            Recovered=(
                "recovered_amount",
                "sum"
            ),
            Outstanding=(
                "outstanding_amount",
                "sum"
            ),
        )
        .reset_index()
    )

    vendor_summary[
        "Recovery Rate %"
    ] = (
        vendor_summary[
            "Recovered"
        ]
        /
        vendor_summary[
            "Claimed"
        ].replace(
            0,
            pd.NA
        )
        * 100
    ).fillna(0)

    if (
        not vendor_df.empty
        and "vendor_risk_tier"
        in vendor_df.columns
    ):

        risk_cols = [
            "vendor_id",
            "vendor_risk_tier",
            "vendor_risk_score"
        ]

        risk_cols = [
            column
            for column in risk_cols
            if column in vendor_df.columns
        ]

        vendor_summary = vendor_summary.merge(
            vendor_df[
                risk_cols
            ].drop_duplicates(
                "vendor_id"
            ),
            on="vendor_id",
            how="left",
        )

    top_vendors = (
        vendor_summary
        .sort_values(
            "Outstanding",
            ascending=False
        )
        .head(15)
    )

    fig_vendor = px.bar(
        top_vendors.sort_values(
            "Outstanding"
        ),
        x="Outstanding",
        y="vendor_id",
        orientation="h",
        text_auto=".2s",
        title="Top 15 Vendors by Outstanding Recovery",
    )

    st.plotly_chart(
        fig_vendor,
        use_container_width=True
    )

    st.dataframe(
        vendor_summary.sort_values(
            "Outstanding",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "All financial exposure in this project is synthetic. "
        "These analytics describe generated claims and recovery "
        "workflow data and should not be interpreted as verified "
        "real-world loss."
    )


# ============================================================
# RECOVERY CLAIMS
# ============================================================

elif page == "Recovery Claims":

    st.header(
        "💰 Recovery Claim Management"
    )

    if recovery_df.empty:

        st.warning(
            "Recovery claims are not available."
        )

        st.code(
            "python -m app.services.claim_management",
            language="powershell"
        )

    else:

        claimed = safe_number(
            recovery_df["claimed_amount"]
        ).sum()

        recovered = safe_number(
            recovery_df["recovered_amount"]
        ).sum()

        outstanding = safe_number(
            recovery_df["outstanding_amount"]
        ).sum()

        rate = (
            recovered / claimed * 100
            if claimed > 0
            else 0
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Claims",
                f"{len(recovery_df):,}"
            )

        with col2:

            st.metric(
                "Claimed",
                money(claimed)
            )

        with col3:

            st.metric(
                "Recovered",
                money(recovered)
            )

        with col4:

            st.metric(
                "Recovery Rate",
                f"{rate:.2f}%"
            )

        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:

            statuses = sorted(
                recovery_df[
                    "claim_status"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            selected_status = st.multiselect(
                "Claim Status",
                statuses,
                default=statuses,
            )

        with col2:

            priorities = [
                "URGENT",
                "HIGH",
                "MEDIUM",
                "NORMAL",
            ]

            available_priorities = [
                priority
                for priority in priorities
                if priority in set(
                    recovery_df[
                        "recovery_priority"
                    ]
                    .astype(str)
                )
            ]

            selected_priority = st.multiselect(
                "Recovery Priority",
                available_priorities,
                default=available_priorities,
            )

        with col3:

            search = st.text_input(
                "Search Recovery Claim / Vendor / Invoice"
            )

        filtered = recovery_df.copy()

        filtered = filtered[
            filtered[
                "claim_status"
            ].isin(
                selected_status
            )
        ]

        filtered = filtered[
            filtered[
                "recovery_priority"
            ].isin(
                selected_priority
            )
        ]

        if search:

            search = search.lower()

            searchable = [
                column
                for column in [
                    "recovery_claim_id",
                    "original_claim_id",
                    "vendor_id",
                    "invoice_id",
                ]
                if column in filtered.columns
            ]

            mask = pd.Series(
                False,
                index=filtered.index
            )

            for column in searchable:

                mask = mask | (
                    filtered[
                        column
                    ]
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        search,
                        na=False
                    )
                )

            filtered = filtered[
                mask
            ]

        st.write(
            f"Showing **{len(filtered):,}** recovery claims"
        )

        table_columns = [
            "recovery_claim_id",
            "vendor_id",
            "invoice_id",
            "recovery_category",
            "claimed_amount",
            "recovered_amount",
            "outstanding_amount",
            "recovery_priority",
            "claim_status",
        ]

        table_columns = [
            column
            for column in table_columns
            if column in filtered.columns
        ]

        st.dataframe(
            filtered[
                table_columns
            ],
            use_container_width=True,
            hide_index=True,
        )

        if not filtered.empty:

            st.divider()

            st.subheader(
                "🔎 Manage Recovery Claim"
            )

            claim_ids = (
                filtered[
                    "recovery_claim_id"
                ]
                .astype(str)
                .tolist()
            )

            selected_claim = st.selectbox(
                "Select Recovery Claim",
                claim_ids,
            )

            row_index = filtered[
                filtered[
                    "recovery_claim_id"
                ].astype(str)
                == selected_claim
            ].index[0]

            claim = recovery_df.loc[
                row_index
            ]

            col1, col2, col3, col4 = st.columns(4)

            with col1:

                st.metric(
                    "Claimed",
                    money(
                        claim[
                            "claimed_amount"
                        ]
                    )
                )

            with col2:

                st.metric(
                    "Recovered",
                    money(
                        claim[
                            "recovered_amount"
                        ]
                    )
                )

            with col3:

                st.metric(
                    "Outstanding",
                    money(
                        claim[
                            "outstanding_amount"
                        ]
                    )
                )

            with col4:

                st.metric(
                    "Priority",
                    claim[
                        "recovery_priority"
                    ]
                )

            st.divider()

            left, right = st.columns(2)

            with left:

                st.markdown(
                    f"**Recovery Claim:** "
                    f"{claim['recovery_claim_id']}"
                )

                st.markdown(
                    f"**Original Claim:** "
                    f"{claim['original_claim_id']}"
                )

                st.markdown(
                    f"**Vendor:** "
                    f"{claim['vendor_id']}"
                )

                st.markdown(
                    f"**Invoice:** "
                    f"{claim['invoice_id']}"
                )

                st.markdown(
                    f"**Recovery Category:** "
                    f"{claim['recovery_category']}"
                )

            with right:

                st.markdown(
                    f"**Recovery Method:** "
                    f"{claim['recovery_method']}"
                )

                st.markdown(
                    f"**Risk Level:** "
                    f"{claim['risk_level']}"
                )

                st.markdown(
                    f"**Confidence:** "
                    f"{float(claim['confidence_score']):.1f}%"
                )

                st.markdown(
                    f"**Investigation Priority:** "
                    f"{claim['investigation_priority']}"
                )

            st.divider()

            st.subheader(
                "✏️ Update Recovery Claim"
            )

            edit_col1, edit_col2 = st.columns(2)

            with edit_col1:

                status_options = [
                    "NEW",
                    "UNDER_REVIEW",
                    "CLAIM_RAISED",
                    "RECOVERY_IN_PROGRESS",
                    "RECOVERED",
                    "REJECTED",
                    "CLOSED",
                ]

                current_status = str(
                    claim[
                        "claim_status"
                    ]
                )

                if current_status not in status_options:
                    current_status = "NEW"

                new_status = st.selectbox(
                    "Claim Status",
                    status_options,
                    index=status_options.index(
                        current_status
                    ),
                )

            with edit_col2:

                response_options = [
                    "PENDING",
                    "ACKNOWLEDGED",
                    "DISPUTED",
                    "ACCEPTED",
                    "PARTIALLY_ACCEPTED",
                    "REJECTED",
                ]

                current_response = str(
                    claim[
                        "supplier_response"
                    ]
                )

                if current_response not in response_options:
                    current_response = "PENDING"

                new_response = st.selectbox(
                    "Supplier Response",
                    response_options,
                    index=response_options.index(
                        current_response
                    ),
                )

            current_recovered = float(
                claim[
                    "recovered_amount"
                ]
            )

            new_recovered = st.number_input(
                "Recovered Amount (₹)",
                min_value=0.0,
                value=current_recovered,
                step=1000.0,
            )

            notes_default = (
                ""
                if pd.isna(
                    claim[
                        "recovery_notes"
                    ]
                )
                else str(
                    claim[
                        "recovery_notes"
                    ]
                )
            )

            new_notes = st.text_area(
                "Recovery Notes",
                value=notes_default,
                height=120,
            )

            if st.button(
                "💾 Save Recovery Update",
                type="primary",
            ):

                recovered_amount = min(
                    float(new_recovered),
                    float(
                        claim[
                            "claimed_amount"
                        ]
                    )
                )

                recovery_df.loc[
                    row_index,
                    "claim_status"
                ] = new_status

                recovery_df.loc[
                    row_index,
                    "supplier_response"
                ] = new_response

                recovery_df.loc[
                    row_index,
                    "recovered_amount"
                ] = recovered_amount

                recovery_df.loc[
                    row_index,
                    "outstanding_amount"
                ] = max(
                    float(
                        claim[
                            "claimed_amount"
                        ]
                    ) - recovered_amount,
                    0,
                )

                recovery_df.loc[
                    row_index,
                    "recovery_notes"
                ] = new_notes

                recovery_df.loc[
                    row_index,
                    "updated_at"
                ] = pd.Timestamp.utcnow().isoformat()

                if (
                    recovered_amount
                    >= float(
                        claim[
                            "claimed_amount"
                        ]
                    )
                    and recovered_amount > 0
                ):

                    recovery_df.loc[
                        row_index,
                        "claim_status"
                    ] = "RECOVERED"

                    recovery_df.loc[
                        row_index,
                        "outstanding_amount"
                    ] = 0.0

                if save_recovery_data(
                    recovery_df
                ):

                    st.success(
                        "Recovery claim updated successfully."
                    )

                    st.rerun()


# ============================================================
# VENDOR INTELLIGENCE
# ============================================================

elif page == "Vendor Intelligence":

    st.header(
        "🏢 Vendor Intelligence"
    )

    if vendor_df.empty:

        st.warning(
            "Vendor analytics are not available."
        )

        st.code(
            "python -m app.services.vendor_analytics",
            language="powershell"
        )

    else:

        dataframe = vendor_df.copy()

        for column in [
            "potential_leakage",
            "claimed_amount",
            "recovered_amount",
            "outstanding_amount",
            "recovery_rate",
            "average_confidence",
            "vendor_risk_score",
        ]:

            if column in dataframe.columns:

                dataframe[column] = safe_number(
                    dataframe[column]
                )

        if "vendor_risk_tier" in dataframe.columns:

            dataframe[
                "vendor_risk_tier"
            ] = (
                dataframe[
                    "vendor_risk_tier"
                ]
                .astype(str)
                .str.upper()
            )

        total_vendors = len(dataframe)

        total_leakage = (
            dataframe[
                "potential_leakage"
            ].sum()
        )

        total_outstanding_vendor = (
            dataframe[
                "outstanding_amount"
            ].sum()
        )

        vendor_recovery_rate = (
            dataframe[
                "recovered_amount"
            ].sum()
            /
            dataframe[
                "claimed_amount"
            ].sum()
            * 100
            if dataframe[
                "claimed_amount"
            ].sum() > 0
            else 0
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Vendors Analyzed",
                f"{total_vendors:,}"
            )

        with col2:
            st.metric(
                "Potential Leakage",
                money(total_leakage)
            )

        with col3:
            st.metric(
                "Outstanding Recovery",
                money(total_outstanding_vendor)
            )

        with col4:
            st.metric(
                "Recovery Rate",
                f"{vendor_recovery_rate:.2f}%"
            )

        st.caption(
            "Vendor risk score is an internal synthetic analytics score "
            "generated from this project's simulated financial data. "
            "It is not a real-world supplier rating or external credit assessment."
        )

        st.divider()

        left, right = st.columns(2)

        with left:

            st.subheader(
                "Vendor Risk Tier Distribution"
            )

            tier_data = (
                dataframe[
                    "vendor_risk_tier"
                ]
                .value_counts()
                .reindex(
                    [
                        "CRITICAL",
                        "HIGH",
                        "MEDIUM",
                        "LOW"
                    ],
                    fill_value=0
                )
                .reset_index()
            )

            tier_data.columns = [
                "risk_tier",
                "vendor_count"
            ]

            fig = px.bar(
                tier_data,
                x="risk_tier",
                y="vendor_count",
                title="Internal Vendor Risk Tiers",
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with right:

            st.subheader(
                "Top Vendors by Potential Leakage"
            )

            top_leakage = (
                dataframe
                .nlargest(
                    10,
                    "potential_leakage"
                )
                .copy()
                .sort_values(
                    "potential_leakage"
                )
            )

            fig = px.bar(
                top_leakage,
                x="potential_leakage",
                y="vendor_id",
                orientation="h",
                title="Top 10 Vendors by Potential Leakage",
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        st.divider()

        st.subheader(
            "🔎 Vendor Search & Analysis"
        )

        col1, col2 = st.columns(2)

        with col1:

            risk_options = [
                "CRITICAL",
                "HIGH",
                "MEDIUM",
                "LOW"
            ]

            available_risks = [
                risk
                for risk in risk_options
                if risk in set(
                    dataframe[
                        "vendor_risk_tier"
                    ].astype(str)
                )
            ]

            selected_risks = st.multiselect(
                "Risk Tier",
                available_risks,
                default=available_risks,
            )

        with col2:

            vendor_search = st.text_input(
                "Search Vendor ID",
                placeholder="Example: VEN-0108",
            )

        filtered = dataframe[
            dataframe[
                "vendor_risk_tier"
            ].isin(
                selected_risks
            )
        ].copy()

        if vendor_search:

            filtered = filtered[
                filtered[
                    "vendor_id"
                ]
                .astype(str)
                .str.contains(
                    vendor_search,
                    case=False,
                    na=False
                )
            ]

        st.write(
            f"Showing **{len(filtered):,}** vendors"
        )

        table_columns = [
            "vendor_id",
            "claim_count",
            "potential_leakage",
            "critical_claims",
            "high_claims",
            "p1_investigations",
            "claimed_amount",
            "recovered_amount",
            "outstanding_amount",
            "recovery_rate",
            "dominant_leakage_type",
            "vendor_risk_score",
            "vendor_risk_tier",
        ]

        table_columns = [
            column
            for column in table_columns
            if column in filtered.columns
        ]

        st.dataframe(
            filtered[
                table_columns
            ],
            use_container_width=True,
            hide_index=True,
        )

        if not filtered.empty:

            st.divider()

            st.subheader(
                "📋 Vendor Detail"
            )

            selected_vendor = st.selectbox(
                "Select Vendor",
                filtered[
                    "vendor_id"
                ].astype(str).tolist(),
            )

            vendor = filtered[
                filtered[
                    "vendor_id"
                ].astype(str)
                == selected_vendor
            ].iloc[0]

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Risk Score",
                    f"{float(vendor.get('vendor_risk_score', 0)):.1f}/100",
                )

            with col2:
                st.metric(
                    "Risk Tier",
                    str(
                        vendor.get(
                            "vendor_risk_tier",
                            "N/A"
                        )
                    ),
                )

            with col3:
                st.metric(
                    "Claims",
                    f"{int(float(vendor.get('claim_count', 0))):,}",
                )

            with col4:
                st.metric(
                    "P1 Investigations",
                    f"{int(float(vendor.get('p1_investigations', 0))):,}",
                )

            left, right = st.columns(2)

            with left:

                st.markdown(
                    f"**Vendor:** {selected_vendor}"
                )

                st.markdown(
                    f"**Potential Leakage:** "
                    f"{money(vendor.get('potential_leakage', 0))}"
                )

                st.markdown(
                    f"**Claimed Amount:** "
                    f"{money(vendor.get('claimed_amount', 0))}"
                )

                st.markdown(
                    f"**Recovered Amount:** "
                    f"{money(vendor.get('recovered_amount', 0))}"
                )

                st.markdown(
                    f"**Outstanding Recovery:** "
                    f"{money(vendor.get('outstanding_amount', 0))}"
                )

            with right:

                st.markdown(
                    f"**Recovery Rate:** "
                    f"{float(vendor.get('recovery_rate', 0)):.2f}%"
                )

                st.markdown(
                    f"**Critical Claims:** "
                    f"{int(float(vendor.get('critical_claims', 0))):,}"
                )

                st.markdown(
                    f"**High Claims:** "
                    f"{int(float(vendor.get('high_claims', 0))):,}"
                )

                st.markdown(
                    f"**Average Confidence:** "
                    f"{float(vendor.get('average_confidence', 0)):.2f}%"
                )

                st.markdown(
                    f"**Dominant Leakage Type:** "
                    f"{vendor.get('dominant_leakage_type', 'N/A')}"
                )

            st.info(
                f"Leakage types detected for {selected_vendor}: "
                f"{vendor.get('leakage_types', 'N/A')}"
            )

        else:

            st.info(
                "No vendors match the selected filters."
            )


# ============================================================
# CONTRACT INTELLIGENCE
# ============================================================

elif page == "Contract Intelligence":

    st.header(
        "📄 Contract Intelligence & Compliance"
    )

    if (
        contract_intelligence_df.empty
        and contract_compliance_df.empty
    ):

        st.warning(
            "Contract intelligence data is not available."
        )

        st.code(
            "python -m app.services.contract_intelligence\n"
            "python -m app.services.contract_compliance",
            language="powershell",
        )

    else:

        ci = contract_intelligence_df.copy()
        cc = contract_compliance_df.copy()

        for dataframe in [
            ci,
            cc
        ]:

            for column in dataframe.columns:

                if column in {
                    "unit_price",
                    "rebate_percentage",
                    "penalty_percentage",
                    "penalty_amount",
                    "volume_commitment",
                    "confidence",
                    "extraction_confidence",
                    "potential_leakage",
                    "leakage_amount",
                    "expected_amount",
                    "invoice_amount",
                    "contract_unit_price",
                    "invoice_unit_price",
                }:

                    dataframe[column] = safe_number(
                        dataframe[column]
                    )

        contract_count = len(ci)

        compliance_findings = len(cc)

        compliance_leakage = 0.0

        if not cc.empty:

            for col in [
                "potential_leakage",
                "leakage_amount"
            ]:

                if col in cc.columns:

                    compliance_leakage = (
                        safe_number(
                            cc[col]
                        ).sum()
                    )

                    break

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Contracts Analyzed",
                f"{contract_count:,}"
            )

        with col2:
            st.metric(
                "Compliance Findings",
                f"{compliance_findings:,}"
            )

        with col3:
            st.metric(
                "Compliance Exposure",
                money(compliance_leakage)
            )

        with col4:

            if "extraction_confidence" in ci.columns:

                avg_conf = safe_number(
                    ci[
                        "extraction_confidence"
                    ]
                ).mean()

            elif "confidence" in ci.columns:

                avg_conf = safe_number(
                    ci[
                        "confidence"
                    ]
                ).mean()

            else:

                avg_conf = 0

            st.metric(
                "Avg Extraction Confidence",
                f"{avg_conf:.1f}%"
            )

        st.divider()

        if not cc.empty:

            st.subheader(
                "⚠️ Compliance Findings"
            )

            type_col = next(
                (
                    column
                    for column in [
                        "violation_type",
                        "compliance_type",
                        "finding_type",
                        "leakage_type",
                        "category"
                    ]
                    if column in cc.columns
                ),
                None
            )

            if type_col:

                type_data = (
                    cc[
                        type_col
                    ]
                    .astype(str)
                    .value_counts()
                    .reset_index()
                )

                type_data.columns = [
                    "finding_type",
                    "count"
                ]

                fig = px.bar(
                    type_data,
                    x="finding_type",
                    y="count",
                    title="Contract Compliance Findings by Type",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            display_cols = [
                column
                for column in [
                    "claim_id",
                    "contract_id",
                    "vendor_id",
                    "invoice_id",
                    "violation_type",
                    "compliance_type",
                    "finding_type",
                    "potential_leakage",
                    "leakage_amount",
                    "risk_level",
                    "evidence",
                    "status"
                ]
                if column in cc.columns
            ]

            st.dataframe(
                cc[
                    display_cols
                ],
                use_container_width=True,
                hide_index=True
            )

        st.divider()

        st.subheader(
            "📑 Extracted Contract Terms"
        )

        if not ci.empty:

            search_contract = st.text_input(
                "Search Contract / Vendor"
            )

            filtered_ci = ci.copy()

            if search_contract:

                mask = pd.Series(
                    False,
                    index=filtered_ci.index
                )

                for column in [
                    "contract_id",
                    "vendor_id"
                ]:

                    if column in filtered_ci.columns:

                        mask |= (
                            filtered_ci[
                                column
                            ]
                            .astype(str)
                            .str.contains(
                                search_contract,
                                case=False,
                                na=False
                            )
                        )

                filtered_ci = filtered_ci[
                    mask
                ]

            preferred_cols = [
                "contract_id",
                "vendor_id",
                "unit_price",
                "rebate_percentage",
                "payment_terms",
                "volume_commitment",
                "penalty_percentage",
                "contract_start_date",
                "contract_end_date",
                "currency",
                "extraction_confidence"
            ]

            display_cols = [
                column
                for column in preferred_cols
                if column in filtered_ci.columns
            ]

            if display_cols:

                st.dataframe(
                    filtered_ci[
                        display_cols
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.dataframe(
                    filtered_ci,
                    use_container_width=True,
                    hide_index=True
                )

        st.info(
            "Contract Intelligence extracts structured commercial terms "
            "from synthetic contract documents and compares selected terms "
            "against transaction data. Compliance exposure shown here is synthetic."
        )


# ============================================================
# INVESTIGATION CENTER
# ============================================================

elif page == "Investigation Center":

    st.header(
        "🔎 Investigation Center"
    )

    st.caption(
        "End-to-end evidence chain for revenue leakage investigations"
    )

    if investigation_packets_df.empty:

        st.warning(
            "Investigation packets are not available."
        )

        st.code(
            "python -m app.services.investigation_engine",
            language="powershell"
        )

    else:

        dataframe = investigation_packets_df.copy()

        numeric_columns = [
            "potential_leakage",
            "contract_unit_price",
            "po_unit_price",
            "invoice_unit_price",
            "po_quantity",
            "invoice_quantity",
            "invoice_amount",
            "total_paid",
            "payment_overage",
            "price_variance",
            "quantity_variance",
            "contract_rebate_percentage",
            "expected_rebate",
            "credited_rebate",
            "missing_rebate",
            "evidence_coverage",
        ]

        for column in numeric_columns:

            if column in dataframe.columns:

                dataframe[column] = safe_number(
                    dataframe[column]
                )

        total_packets = len(dataframe)

        total_exposure = (
            dataframe[
                "potential_leakage"
            ].sum()
            if "potential_leakage"
            in dataframe.columns
            else 0
        )

        average_evidence = (
            dataframe[
                "evidence_coverage"
            ].mean()
            if "evidence_coverage"
            in dataframe.columns
            else 0
        )

        ready_packets = (
            (
                dataframe[
                    "packet_status"
                ]
                .astype(str)
                .str.upper()
                == "READY_FOR_REVIEW"
            ).sum()
            if "packet_status"
            in dataframe.columns
            else 0
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Investigation Packets",
                f"{total_packets:,}"
            )

        with col2:

            st.metric(
                "Potential Exposure",
                money(total_exposure)
            )

        with col3:

            st.metric(
                "Avg Evidence Coverage",
                f"{average_evidence:.1f}%"
            )

        with col4:

            st.metric(
                "Ready for Review",
                f"{ready_packets:,}"
            )

        st.divider()

        st.subheader(
            "🔎 Search Investigation"
        )

        search = st.text_input(
            "Search by Investigation ID, Claim ID, Vendor ID, Invoice ID or PO ID",
            placeholder="Example: INVEST-0000001 or VEN-0108"
        )

        filtered = dataframe.copy()

        if search:

            search_value = search.strip().lower()

            searchable_columns = [
                "investigation_packet_id",
                "investigation_id",
                "claim_id",
                "vendor_id",
                "invoice_id",
                "po_id",
                "contract_id",
            ]

            mask = pd.Series(
                False,
                index=filtered.index
            )

            for column in searchable_columns:

                if column in filtered.columns:

                    mask = mask | (
                        filtered[
                            column
                        ]
                        .astype(str)
                        .str.lower()
                        .str.contains(
                            search_value,
                            na=False,
                            regex=False
                        )
                    )

            filtered = filtered[
                mask
            ]

        st.write(
            f"Matching investigations: **{len(filtered):,}**"
        )

        if filtered.empty:

            st.warning(
                "No matching investigation found."
            )

        else:

            packet_column = (
                "investigation_packet_id"
            )

            if packet_column in filtered.columns:

                packet_options = (
                    filtered[
                        packet_column
                    ]
                    .astype(str)
                    .tolist()
                )

                selected_packet = st.selectbox(
                    "Select Investigation Packet",
                    packet_options
                )

                selected = filtered[
                    filtered[
                        packet_column
                    ].astype(str)
                    == selected_packet
                ].iloc[0]

            else:

                selected = filtered.iloc[0]

            st.divider()

            st.subheader(
                "Investigation Summary"
            )

            col1, col2, col3, col4 = st.columns(4)

            with col1:

                st.metric(
                    "Leakage Type",
                    str(
                        selected.get(
                            "leakage_type",
                            "N/A"
                        )
                    )
                )

            with col2:

                st.metric(
                    "Risk Level",
                    str(
                        selected.get(
                            "risk_level",
                            "N/A"
                        )
                    )
                )

            with col3:

                st.metric(
                    "Priority",
                    str(
                        selected.get(
                            "investigation_priority",
                            "N/A"
                        )
                    )
                )

            with col4:

                st.metric(
                    "Evidence Coverage",
                    f"{float(selected.get('evidence_coverage', 0)):.1f}%"
                )

            st.write(
                f"**Investigation ID:** "
                f"`{selected.get('investigation_id', 'N/A')}`"
            )

            st.write(
                f"**Claim ID:** "
                f"`{selected.get('claim_id', 'N/A')}`"
            )

            st.write(
                f"**Vendor:** "
                f"`{selected.get('vendor_id', 'N/A')}`"
            )

            st.write(
                f"**Invoice:** "
                f"`{selected.get('invoice_id', 'N/A')}`"
            )

            st.write(
                f"**Purchase Order:** "
                f"`{selected.get('po_id', 'N/A')}`"
            )

            st.write(
                f"**Contract:** "
                f"`{selected.get('contract_id', 'N/A')}`"
            )

            st.divider()

            st.subheader(
                "🔗 Evidence Chain"
            )

            evidence_chain = []

            raw_chain = selected.get(
                "evidence_chain",
                ""
            )

            try:

                if pd.notna(raw_chain):

                    evidence_chain = json.loads(
                        str(raw_chain)
                    )

            except Exception:

                evidence_chain = []

            if evidence_chain:

                for item in evidence_chain:

                    status = str(
                        item.get(
                            "status",
                            "UNKNOWN"
                        )
                    ).upper()

                    stage = item.get(
                        "stage",
                        "UNKNOWN"
                    )

                    reference = item.get(
                        "reference",
                        "N/A"
                    )

                    description = item.get(
                        "description",
                        ""
                    )

                    if status == "AVAILABLE":

                        icon = "✅"

                    else:

                        icon = "⚠️"

                    st.markdown(
                        f"""
                        <div style="
                            border:1px solid #444;
                            border-radius:10px;
                            padding:14px;
                            margin-bottom:8px;
                        ">
                            <b>{icon} {stage}</b><br>
                            <span>{description}</span><br>
                            <code>{reference}</code>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            else:

                st.info(
                    "Structured evidence-chain details are not available "
                    "for this investigation packet."
                )

            st.divider()

            st.subheader(
                "📊 Transaction Evidence"
            )

            evidence_rows = [
                (
                    "Contract Unit Price",
                    "contract_unit_price"
                ),
                (
                    "PO Unit Price",
                    "po_unit_price"
                ),
                (
                    "Invoice Unit Price",
                    "invoice_unit_price"
                ),
                (
                    "PO Quantity",
                    "po_quantity"
                ),
                (
                    "Invoice Quantity",
                    "invoice_quantity"
                ),
                (
                    "Invoice Amount",
                    "invoice_amount"
                ),
                (
                    "Total Paid",
                    "total_paid"
                ),
                (
                    "Payment Overage",
                    "payment_overage"
                ),
                (
                    "Price Variance",
                    "price_variance"
                ),
                (
                    "Quantity Variance",
                    "quantity_variance"
                ),
                (
                    "Contract Rebate %",
                    "contract_rebate_percentage"
                ),
                (
                    "Expected Rebate",
                    "expected_rebate"
                ),
                (
                    "Credited Rebate",
                    "credited_rebate"
                ),
                (
                    "Missing Rebate",
                    "missing_rebate"
                ),
            ]

            evidence_data = []

            for label, column in evidence_rows:

                if column in selected.index:

                    value = selected[
                        column
                    ]

                    if column == "contract_rebate_percentage":

                        display_value = (
                            f"{float(value):,.2f}%"
                        )

                    elif column in {
                        "po_quantity",
                        "invoice_quantity"
                    }:

                        display_value = (
                            f"{float(value):,.2f}"
                        )

                    else:

                        display_value = money(
                            value
                        )

                    evidence_data.append(
                        {
                            "Metric": label,
                            "Value": display_value
                        }
                    )

            if evidence_data:

                st.dataframe(
                    pd.DataFrame(
                        evidence_data
                    ),
                    use_container_width=True,
                    hide_index=True
                )

            st.divider()

            st.subheader(
                "🧠 Investigation Conclusion"
            )

            conclusion = selected.get(
                "investigation_conclusion",
                "Unavailable"
            )

            st.info(
                str(conclusion)
            )

            st.subheader(
                "💰 Recommended Recovery Action"
            )

            recovery_action = selected.get(
                "recommended_recovery_action",
                "Unavailable"
            )

            st.success(
                str(recovery_action)
            )

            st.divider()

            st.subheader(
                "Investigation Packet Status"
            )

            st.write(
                f"**Status:** "
                f"`{selected.get('packet_status', 'N/A')}`"
            )

            st.caption(
                "Evidence coverage measures the availability of linked "
                "records. It is not a fraud probability or a conclusion "
                "of intentional wrongdoing."
            )

            with st.expander(
                "View Structured Evidence Chain"
            ):

                if evidence_chain:

                    st.json(
                        evidence_chain
                    )

                else:

                    st.write(
                        selected.get(
                            "evidence_chain",
                            "Unavailable"
                        )
                    )


# ============================================================
# ML ANOMALIES
# ============================================================

elif page == "ML Anomalies":

    st.header(
        "🤖 Machine Learning Anomalies"
    )

    if anomalies_df.empty:

        st.warning(
            "ML anomaly data is not available."
        )

        st.code(
            "python -m app.services.ml_anomaly_detector",
            language="powershell"
        )

    else:

        dataframe = anomalies_df.copy()

        st.write(
            f"Detected **{len(dataframe):,}** "
            "potential anomalous transactions."
        )

        display_columns = [
            "invoice_id",
            "vendor_id",
            "anomaly_score",
            "invoice_amount",
            "invoice_unit_price",
            "po_unit_price",
            "invoice_quantity",
            "po_quantity",
        ]

        display_columns = [
            column
            for column in display_columns
            if column in dataframe.columns
        ]

        st.dataframe(
            dataframe[
                display_columns
            ],
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "DollarGuard AI | Enterprise financial analytics | "
    "Leakage Detection + ML Anomaly Detection + Contract Intelligence "
    "+ AI Investigation + Recovery Management + Real Data Upload"
)
