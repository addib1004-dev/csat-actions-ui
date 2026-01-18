import pandas as pd
import streamlit as st

st.set_page_config(page_title="CSAT Approved SMART Actions", layout="wide")

st.title("✅ CSAT Approved SMART Actions")
st.caption("Data source: Google Sheets (Published CSV) → ApprovalQueue")

# ---- CONFIG ----
PUBLISHED_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vScHlqnqFOunJNbSGHE2a9PRQgy-Lcgummq14rnn1HxkydyDeZ0sSHdW5BFb1Cg3qNaZ4gxtk5ycUJS/pub?gid=304505671&single=true&output=csv"

# ---- LOAD ----
@st.cache_data(ttl=60)
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    # normalize common columns
    if "ApprovalStatus" in df.columns:
        df["ApprovalStatus"] = df["ApprovalStatus"].astype(str).str.strip()
    if "Priority" in df.columns:
        df["Priority"] = df["Priority"].astype(str).str.strip().str.upper()
    return df

df = load_data(PUBLISHED_CSV_URL)

if df.empty:
    st.warning("No data found in the sheet.")
    st.stop()

# ---- FILTER: Approved only ----
if "ApprovalStatus" not in df.columns:
    st.error("Column 'ApprovalStatus' not found. Please ensure ApprovalQueue has ApprovalStatus.")
    st.stop()

approved = df[df["ApprovalStatus"].str.lower() == "approved"].copy()

# ---- SIDEBAR FILTERS ----
st.sidebar.header("Filters")

acct_col = "Account" if "Account" in approved.columns else None
theme_col = "Theme" if "Theme" in approved.columns else ("theme" if "theme" in approved.columns else None)
pm_col = "Project Manager" if "Project Manager" in approved.columns else None
prio_col = "Priority" if "Priority" in approved.columns else None

if acct_col:
    accounts = ["All"] + sorted([a for a in approved[acct_col].dropna().unique()])
    sel_account = st.sidebar.selectbox("Account", accounts, index=0)
    if sel_account != "All":
        approved = approved[approved[acct_col] == sel_account]

if theme_col:
    themes = ["All"] + sorted([t for t in approved[theme_col].dropna().unique()])
    sel_theme = st.sidebar.selectbox("Theme", themes, index=0)
    if sel_theme != "All":
        approved = approved[approved[theme_col] == sel_theme]

if pm_col:
    pms = ["All"] + sorted([p for p in approved[pm_col].dropna().unique()])
    sel_pm = st.sidebar.selectbox("Project Manager", pms, index=0)
    if sel_pm != "All":
        approved = approved[approved[pm_col] == sel_pm]

if prio_col:
    prios = ["All"] + sorted([p for p in approved[prio_col].dropna().unique()])
    sel_prio = st.sidebar.selectbox("Priority", prios, index=0)
    if sel_prio != "All":
        approved = approved[approved[prio_col] == sel_prio]

search = st.sidebar.text_input("Search in SMART Action / Feedback", "")

text_cols = []
if "SMART Action" in approved.columns:
    text_cols.append("SMART Action")
if "Feedback" in approved.columns:
    text_cols.append("Feedback")
if "FinalFeedback" in approved.columns:
    text_cols.append("FinalFeedback")

if search.strip() and text_cols:
    s = search.strip().lower()
    mask = False
    for c in text_cols:
        mask = mask | approved[c].astype(str).str.lower().str.contains(s, na=False)
    approved = approved[mask]

# ---- METRICS ----
c1, c2, c3 = st.columns(3)
c1.metric("Approved Actions", len(approved))
c2.metric("Total Rows in Sheet", len(df))
if prio_col:
    c3.metric("P1 Approved", int((approved[prio_col] == "P1").sum()))
else:
    c3.metric("Last Refreshed", "live")

st.divider()

# ---- DISPLAY ----
# Choose display columns (only if present)
preferred_cols = [
    "Account",
    "Stakeholder (Responder)",
    "Project Manager",
    "PM Email",
    "Theme",
    "Priority",
    "Target Date",
    "Status",
    "SMART Action",
    "KPI Impact",
    "Evidence",
    "SentryStatus",
    "SentryReason",
    "SentryEscalationTo",
    "SentryMessage",
    "Last Update"
]
display_cols = [c for c in preferred_cols if c in approved.columns]

# If none match, show all
if not display_cols:
    display_cols = approved.columns.tolist()

st.dataframe(approved[display_cols], use_container_width=True, height=520)

# ---- DOWNLOAD ----
st.download_button(
    "⬇️ Download Approved Actions (CSV)",
    approved.to_csv(index=False).encode("utf-8"),
    file_name="approved_actions.csv",
    mime="text/csv"
)
