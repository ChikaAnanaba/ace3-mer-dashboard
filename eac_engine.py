"""
EAC Engine — Enhanced Adherence Counselling indicators.
Computes EAC caseload, sessions, post-EAC VL and re-suppression.
"""
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

STATES = ['Kebbi', 'Sokoto', 'Zamfara']


def _read(src):
    if isinstance(src, pd.DataFrame):
        return src
    if hasattr(src, 'seek'):
        src.seek(0)
    try:
        xl = pd.ExcelFile(src)
        sheet = xl.sheet_names[0]
        for s in xl.sheet_names:
            if 'eac' in s.lower():
                sheet = s
                break
        return pd.read_excel(xl, sheet_name=sheet)
    except Exception:
        if hasattr(src, 'seek'):
            src.seek(0)
        return pd.read_csv(src, encoding='latin-1', low_memory=False)


def compute_eac(src, quarter: str = 'Q1') -> dict:
    """Compute EAC indicators from EAC line list."""
    try:
        df = _read(src)
    except Exception as e:
        return {'error': str(e)}

    df.columns = [str(c).strip() for c in df.columns]

    # State breakdown
    state_col = next((c for c in ['State', 'State Of Residence'] if c in df.columns), None)
    if state_col:
        df = df[df[state_col].isin(STATES)]

    state_counts = {}
    if state_col:
        state_counts = df.groupby(state_col).size().to_dict()

    # EAC Caseload = total unsuppressed patients with EAC initiated
    caseload = len(df)

    # Sessions
    sess1_col = next((c for c in df.columns if '1st' in c.lower() or 'session 1' in c.lower()
                      or 'eac1' in c.lower() or '1st eac' in c.lower()), None)
    sess2_col = next((c for c in df.columns if '2nd' in c.lower() or 'session 2' in c.lower()
                      or 'eac2' in c.lower() or '2nd eac' in c.lower()), None)
    sess3_col = next((c for c in df.columns if '3rd' in c.lower() or 'session 3' in c.lower()
                      or 'eac3' in c.lower() or '3rd eac' in c.lower()), None)
    ext_col   = next((c for c in df.columns if 'extend' in c.lower()), None)

    def _count_done(col):
        if col is None or col not in df.columns:
            return 0
        return int(df[col].notna().sum())

    sess1 = _count_done(sess1_col)
    sess2 = _count_done(sess2_col)
    sess3 = _count_done(sess3_col)
    ext   = _count_done(ext_col)

    # Post-EAC VL
    post_vl_col = next((c for c in df.columns if 'post' in c.lower() and 'vl' in c.lower()
                        and 'date' in c.lower()), None)
    post_vl_n = int(df[post_vl_col].notna().sum()) if post_vl_col else 0

    # Post-EAC suppression
    post_supp_col = next((c for c in df.columns if 'suppress' in c.lower()
                          or ('post' in c.lower() and 'result' in c.lower())), None)
    post_supp_n = 0
    if post_supp_col:
        vl_vals = pd.to_numeric(df[post_supp_col], errors='coerce')
        post_supp_n = int((vl_vals < 1000).sum())

    post_supp_r = round(post_supp_n / post_vl_n * 100, 1) if post_vl_n > 0 else 0

    return {
        'EAC_CASELOAD':      caseload,
        'EAC_SESS1':         sess1,
        'EAC_SESS2':         sess2,
        'EAC_SESS3':         sess3,
        'EAC_EXT':           ext,
        'EAC_POST_VL_N':     post_vl_n,
        'EAC_POST_SUPP_N':   post_supp_n,
        'EAC_POST_SUPP_R':   post_supp_r,
        'EAC_STATE':         {k: int(v) for k, v in state_counts.items()},
    }
