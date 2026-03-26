"""
ACE3 EAC Engine
Computes Enhanced Adherence Counselling indicators from the EAC line list.

Key metrics:
  - Total unsuppressed clients in EAC caseload
  - EAC sessions completed (1st / 2nd / 3rd / Extended)
  - Clients with post-EAC VL collected
  - Post-EAC re-suppression rate
  - VL indication breakdown
  - State breakdown
  - Clients eligible/referred for switch
"""
import pandas as pd
import numpy as np

Q1_START = pd.Timestamp('2025-10-01')
Q1_END   = pd.Timestamp('2025-12-31')
Q2_START = pd.Timestamp('2026-01-01')
Q2_END   = pd.Timestamp('2026-03-31')
FY_START = pd.Timestamp('2025-10-01')


def _safe_date(df, col):
    if col not in df.columns:
        return pd.Series(pd.NaT, index=df.index)
    s = pd.to_datetime(df[col], errors='coerce')
    # clip sentinel dates
    s = s.where(s >= pd.Timestamp('2000-01-01'), other=pd.NaT)
    return s


def _by_state(df):
    if 'State' not in df.columns:
        return {}
    return dict(df.groupby('State').size().sort_index())


def compute_eac(src, quarter='Q1'):
    """
    Load and compute EAC indicators.

    Parameters
    ----------
    src     : file path, BytesIO, or DataFrame
    quarter : 'Q1' | 'Q2' | 'CUM'

    Returns
    -------
    dict with all EAC metrics
    """
    # ── load ────────────────────────────────────────────────────────────────
    if isinstance(src, pd.DataFrame):
        df = src.copy()
    else:
        try:
            df = pd.read_excel(src, sheet_name='eac')
        except Exception:
            try:
                if hasattr(src, 'seek'): src.seek(0)
                df = pd.read_excel(src)
            except Exception:
                if hasattr(src, 'seek'): src.seek(0)
                df = pd.read_csv(src, encoding='latin-1', low_memory=False)

    df.columns = df.columns.str.strip()

    # ── parse dates ──────────────────────────────────────────────────────────
    eac1_start  = _safe_date(df, 'Date of commencement of 1st EAC (yyyy-mm-dd)')
    eac1_done   = _safe_date(df, 'Date of  1st EAC Session Completed')
    eac2_done   = _safe_date(df, 'Date of  2nd EAC Session Completed')
    eac3_done   = _safe_date(df, 'Date of  3rd EAC Session Completed')
    ext_done    = _safe_date(df, 'Date of  Extended EAC Session Completed')
    post_vl_dt  = _safe_date(df, 'Date of Repeat Viral Load - Post EAC VL Sample collected (yyyy-mm-dd)')
    unsup_dt    = _safe_date(df, 'Date of Unsuppressed Viral Load Result')

    # ── quarter filter on unsuppressed VL date ───────────────────────────────
    if quarter == 'Q1':
        q_start, q_end = Q1_START, Q1_END
    elif quarter == 'Q2':
        q_start, q_end = Q2_START, Q2_END
    else:  # CUM
        q_start, q_end = FY_START, Q2_END

    # Active EAC caseload = those with unsuppressed VL date within or before period
    # (still in care / not yet re-suppressed)
    in_period = df[
        unsup_dt.notna() & (unsup_dt <= q_end)
    ].copy()

    # ── sessions ─────────────────────────────────────────────────────────────
    sessions_col = 'Number of EAC Sessions Completed'
    if sessions_col in df.columns:
        sess = pd.to_numeric(df[sessions_col], errors='coerce').fillna(0)
    else:
        sess = pd.Series(0, index=df.index)

    total_caseload = len(in_period)

    # sessions completed within period
    eac1_n   = int(eac1_done.notna().sum())
    eac2_n   = int(eac2_done.notna().sum())
    eac3_n   = int(eac3_done.notna().sum())
    ext_n    = int(ext_done.notna().sum())
    no_sess  = int((sess == 0).sum())
    sess_ge2 = int((sess >= 2).sum())

    # ── post-EAC VL ──────────────────────────────────────────────────────────
    post_vl_n   = int(post_vl_dt.notna().sum())
    post_vl_res = pd.to_numeric(
        df.get('Repeat Viral load result (c/ml)- POST EAC',
               pd.Series(dtype=float)), errors='coerce').dropna()
    post_supp_n = int((post_vl_res < 1000).sum())
    post_supp_r = round(post_supp_n / len(post_vl_res) * 100, 1) if len(post_vl_res) > 0 else 0

    # ── VL indication ────────────────────────────────────────────────────────
    ind_col = 'Unsuppressed Viral Load Result Indication'
    indication = {}
    if ind_col in df.columns:
        indication = df[ind_col].value_counts().to_dict()

    # ── recent VL results (unsuppressed) ─────────────────────────────────────
    recent_vl = pd.to_numeric(
        df.get('Recent Unsuppressed Viral Load Result', pd.Series(dtype=float)),
        errors='coerce').dropna()
    # categorise by level
    vl_1000_9999 = int(((recent_vl >= 1000) & (recent_vl < 10000)).sum())
    vl_ge10000   = int((recent_vl >= 10000).sum())

    # ── switch pathway ───────────────────────────────────────────────────────
    switch_col = 'Eligible for Switch?'
    switched_n = 0
    if switch_col in df.columns:
        switched_n = int((df[switch_col].astype(str).str.lower() == 'yes').sum())

    # ── state breakdown ──────────────────────────────────────────────────────
    state_breakdown = _by_state(in_period)

    return {
        'total_caseload':   total_caseload,
        'eac1_completed':   eac1_n,
        'eac2_completed':   eac2_n,
        'eac3_completed':   eac3_n,
        'extended':         ext_n,
        'no_session_yet':   no_sess,
        'sessions_ge2':     sess_ge2,
        'post_vl_collected':post_vl_n,
        'post_vl_resulted': len(post_vl_res),
        'post_supp_n':      post_supp_n,
        'post_supp_rate':   post_supp_r,
        'indication':       indication,
        'vl_1000_9999':     vl_1000_9999,
        'vl_ge10000':       vl_ge10000,
        'switched':         switched_n,
        'state':            state_breakdown,
        'quarter':          quarter,
    }
