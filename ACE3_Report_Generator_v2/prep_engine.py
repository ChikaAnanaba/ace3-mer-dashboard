"""
PrEP indicator engine for ACE3.
Computes PrEP_NEW, PrEP_CT, PrEP_CURR from the Combined PrEP line list.

MER v2.8 definitions:
  PrEP_NEW  – individuals who initiated PrEP for the first time (Visit Type = Initiation,
               Date Of Commencement within the reporting period)
  PrEP_CT   – individuals who returned for a follow-up visit (Refill/Re-Injection,
               Restart, Method Switch) with Date Of Last Pickup within reporting period
  PrEP_CURR – snapshot of active clients (Current Status == Active) at period end
"""
import pandas as pd

Q1_START = pd.Timestamp('2025-10-01')
Q1_END   = pd.Timestamp('2025-12-31')
Q2_START = pd.Timestamp('2026-01-01')
Q2_END   = pd.Timestamp('2026-03-31')
FY_START = pd.Timestamp('2025-10-01')

NEW_VISIT_TYPES = ['Initiation', 'Second Initiation']
CT_VISIT_TYPES  = ['Refill/Re-Injection', 'Restart', 'Method Switch']


def _date_col(df, name):
    """Return a parsed datetime Series, coercing errors."""
    if name not in df.columns:
        return pd.Series(pd.NaT, index=df.index)
    s = pd.to_datetime(df[name], errors='coerce')
    # clip obviously wrong sentinel dates (e.g. 1900-01-01, 1970-01-01)
    s = s.where(s >= pd.Timestamp('2000-01-01'), other=pd.NaT)
    return s


def _disagg(df):
    sex = df['Sex'] if 'Sex' in df.columns else pd.Series(dtype=str)
    age = pd.to_numeric(df.get('Age', pd.Series(dtype=float)), errors='coerce')
    return {
        'Female': int((sex == 'Female').sum()),
        'Male':   int((sex == 'Male').sum()),
        '<15':    int((age < 15).sum()),
        '15+':    int((age >= 15).sum()),
        'Total':  len(df),
    }


def _by_state(df):
    if 'State' not in df.columns:
        return {}
    return dict(df.groupby('State').size().sort_index())


def _pop_type(df):
    if 'Population Type' not in df.columns:
        return {}
    return df['Population Type'].value_counts().to_dict()


def _prep_type(df):
    if 'Prep Type' not in df.columns:
        return {}
    return df['Prep Type'].value_counts().to_dict()


def compute_prep(src, quarter='Q1'):
    """
    Load and compute all PrEP indicators.

    Parameters
    ----------
    src     : file path, BytesIO, or DataFrame
    quarter : 'Q1' | 'Q2' | 'CUM'  (CUM = semi-annual Q1+Q2)

    Returns
    -------
    dict with keys: PrEP_NEW, PrEP_CT, PrEP_CURR
    each containing value, q1, q2, cum, disagg, state, pop_type, prep_type
    """
    # ── load ────────────────────────────────────────────────────────────────
    if isinstance(src, pd.DataFrame):
        df = src.copy()
    else:
        try:
            df = pd.read_excel(src, sheet_name='prep')
        except Exception:
            try:
                if hasattr(src, 'seek'):
                    src.seek(0)
                df = pd.read_excel(src)
            except Exception:
                if hasattr(src, 'seek'):
                    src.seek(0)
                df = pd.read_csv(src, encoding='latin-1', low_memory=False)

    df.columns = df.columns.str.strip()

    # ── parse key date columns ───────────────────────────────────────────────
    comm_dt   = _date_col(df, 'Date Of Commencement (yyyy-mm-dd)')
    pickup_dt = _date_col(df, 'Date Of Last Pickup (yyyy-mm-dd)')
    status_dt = _date_col(df, 'Date Of Current Status (yyyy-mm-dd)')

    visit_type = df['Visit Type'].astype(str).str.strip() if 'Visit Type' in df.columns \
                 else pd.Series('', index=df.index)
    curr_status = df['Current Status'].astype(str).str.strip() if 'Current Status' in df.columns \
                  else pd.Series('', index=df.index)

    # ── PrEP_NEW ─────────────────────────────────────────────────────────────
    # New initiation: Visit Type in NEW_VISIT_TYPES AND commencement date in period
    new_mask_q1 = (visit_type.isin(NEW_VISIT_TYPES)) & (comm_dt >= Q1_START) & (comm_dt <= Q1_END)
    new_mask_q2 = (visit_type.isin(NEW_VISIT_TYPES)) & (comm_dt >= Q2_START) & (comm_dt <= Q2_END)
    new_q1 = df[new_mask_q1]
    new_q2 = df[new_mask_q2]
    new_cum = df[new_mask_q1 | new_mask_q2]

    # ── PrEP_CT ──────────────────────────────────────────────────────────────
    # Continuing: Visit Type in CT_VISIT_TYPES AND last pickup in period
    ct_mask_q1 = (visit_type.isin(CT_VISIT_TYPES)) & (pickup_dt >= Q1_START) & (pickup_dt <= Q1_END)
    ct_mask_q2 = (visit_type.isin(CT_VISIT_TYPES)) & (pickup_dt >= Q2_START) & (pickup_dt <= Q2_END)
    ct_q1 = df[ct_mask_q1]
    ct_q2 = df[ct_mask_q2]
    ct_cum = df[ct_mask_q1 | ct_mask_q2]

    # ── PrEP_CURR ────────────────────────────────────────────────────────────
    # Active snapshot at period end
    curr_active = df[curr_status == 'Active']

    # ── select by quarter ────────────────────────────────────────────────────
    def _sel(q1_df, q2_df, cum_df):
        if quarter == 'Q1':   return q1_df
        if quarter == 'Q2':   return q2_df
        return cum_df  # CUM

    new_sel = _sel(new_q1, new_q2, new_cum)
    ct_sel  = _sel(ct_q1,  ct_q2,  ct_cum)

    return {
        'PrEP_NEW': {
            'value':     len(new_sel),
            'q1':        len(new_q1),
            'q2':        len(new_q2),
            'cum':       len(new_cum),
            'disagg':    _disagg(new_sel),
            'state':     _by_state(new_sel),
            'pop_type':  _pop_type(new_sel),
            'prep_type': _prep_type(new_sel),
        },
        'PrEP_CT': {
            'value':     len(ct_sel),
            'q1':        len(ct_q1),
            'q2':        len(ct_q2),
            'cum':       len(ct_cum),
            'disagg':    _disagg(ct_sel),
            'state':     _by_state(ct_sel),
            'pop_type':  _pop_type(ct_sel),
            'prep_type': _prep_type(ct_sel),
        },
        'PrEP_CURR': {
            'value':  len(curr_active),
            'disagg': _disagg(curr_active),
            'state':  _by_state(curr_active),
        },
    }
