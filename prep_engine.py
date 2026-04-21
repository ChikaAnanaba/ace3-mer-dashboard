"""
PrEP Engine — computes PrEP_NEW, PrEP_CT, PrEP_CURR from PrEP line list.
MER v2.8: PrEP_NEW = new initiations in reporting period (quarterly)
"""
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

try:
    from ace3_engine import FY_START, Q1_START, Q1_END, Q2_START, Q2_END, Q3_START, Q3_END, Q4_START, Q4_END
except ImportError:
    from datetime import datetime
    today = pd.Timestamp.today()
    fy_year = today.year if today.month >= 10 else today.year - 1
    FY_START  = pd.Timestamp(f'{fy_year}-10-01')
    Q1_START  = FY_START
    Q1_END    = pd.Timestamp(f'{fy_year}-12-31')
    Q2_START  = pd.Timestamp(f'{fy_year+1}-01-01')
    Q2_END    = pd.Timestamp(f'{fy_year+1}-03-31')
    Q3_START  = pd.Timestamp(f'{fy_year+1}-04-01')
    Q3_END    = pd.Timestamp(f'{fy_year+1}-06-30')
    Q4_START  = pd.Timestamp(f'{fy_year+1}-07-01')
    Q4_END    = pd.Timestamp(f'{fy_year+1}-09-30')

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
            if 'prep' in s.lower():
                sheet = s
                break
        return pd.read_excel(xl, sheet_name=sheet)
    except Exception:
        if hasattr(src, 'seek'):
            src.seek(0)
        return pd.read_csv(src, encoding='latin-1', low_memory=False)


def compute_prep(src, quarter: str = 'Q1') -> dict:
    """Compute PrEP indicators from line list."""
    try:
        df = _read(src)
    except Exception as e:
        return {'error': str(e)}

    # Normalise columns
    df.columns = [str(c).strip() for c in df.columns]

    # Date of commencement
    date_col = None
    for c in ['Date Of Commencement', 'Date of Commencement', 'Date Of PrEP Commencement',
              'Commencement Date', 'Visit Date', 'Date']:
        if c in df.columns:
            date_col = c
            break

    if date_col:
        df['_dt'] = pd.to_datetime(df[date_col], errors='coerce')
    else:
        df['_dt'] = pd.NaT

    # Quarter boundaries
    if quarter == 'Q1':
        q_start, q_end = Q1_START, Q1_END
    elif quarter == 'Q2':
        q_start, q_end = Q2_START, Q2_END
    elif quarter == 'Q3':
        q_start, q_end = Q3_START, Q3_END
    elif quarter == 'Q4':
        q_start, q_end = Q4_START, Q4_END
    else:  # CUM
        q_start, q_end = FY_START, Q2_END

    # PrEP_NEW = new initiations in period
    new = df[df['_dt'].notna() & (df['_dt'] >= q_start) & (df['_dt'] <= q_end)]

    # State breakdown
    state_col = None
    for c in ['State', 'State Of Residence', 'state']:
        if c in df.columns:
            state_col = c
            break

    state_counts = {}
    if state_col:
        filtered = new[new[state_col].isin(STATES)] if state_col else new
        state_counts = filtered.groupby(state_col).size().to_dict()
        new = filtered

    # Population type breakdown
    pop_col = None
    for c in ['Population Type', 'Client Type', 'Target Population', 'PopulationType']:
        if c in df.columns:
            pop_col = c
            break

    pop_counts = {}
    if pop_col:
        pop_counts = new[pop_col].value_counts().head(8).to_dict()

    # PrEP_CT = continuing (visited in period, not new)
    visit_col = None
    for c in ['Visit Date', 'Last Visit Date', 'Date of Last Visit']:
        if c in df.columns:
            visit_col = c
            break

    prep_ct = 0
    if visit_col:
        df['_vdt'] = pd.to_datetime(df[visit_col], errors='coerce')
        ct = df[
            df['_vdt'].notna() &
            (df['_vdt'] >= q_start) & (df['_vdt'] <= q_end) &
            ~(df['_dt'].notna() & (df['_dt'] >= q_start) & (df['_dt'] <= q_end))
        ]
        prep_ct = len(ct)

    # PrEP_CURR = active snapshot (those still on PrEP at period end)
    curr_col = None
    for c in ['Current Status', 'PrEP Status', 'Status']:
        if c in df.columns:
            curr_col = c
            break

    prep_curr = 0
    if curr_col:
        prep_curr = int(df[df[curr_col].astype(str).str.lower().isin(
            ['active', 'on prep', 'current'])].shape[0])
    else:
        prep_curr = len(new)  # fallback

    return {
        'PrEP_NEW':       len(new),
        'PrEP_CT':        prep_ct,
        'PrEP_CURR':      prep_curr,
        'PrEP_NEW_STATE': {k: int(v) for k, v in state_counts.items()},
        'PrEP_NEW_POP':   {str(k): int(v) for k, v in pop_counts.items()},
    }
