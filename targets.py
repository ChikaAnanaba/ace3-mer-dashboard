"""
Targets loader for ACE3 programme.
Reads facility-level annual targets from CSV or Excel.
"""
import pandas as pd


def load_targets(src):
    """
    Load targets file and return (df_raw, site_targets_dict, programme_targets_dict).
    programme_targets_dict maps indicator name -> annual target total.
    """
    try:
        if hasattr(src, 'read'):
            # Try Excel first, then CSV
            try:
                src.seek(0)
                df = pd.read_excel(src)
            except Exception:
                src.seek(0)
                df = pd.read_csv(src)
        elif str(src).endswith('.csv'):
            df = pd.read_csv(src)
        else:
            df = pd.read_excel(src)
    except Exception as e:
        raise ValueError(f'Cannot read targets file: {e}')

    # Standardise column names
    df.columns = [str(c).strip() for c in df.columns]

    # Build programme-level totals
    prog_tgts = {}
    indicator_cols = [
        'TX_CURR', 'TX_NEW', 'HTS_TST', 'HTS_TST_POS',
        'TX_PVLS_D', 'TX_PVLS_N', 'PMTCT_STAT_N', 'PMTCT_ART_D',
        'PrEP_NEW', 'TB_PREV_N', 'TX_TB_N', 'TB_ART',
    ]
    for col in indicator_cols:
        if col in df.columns:
            try:
                prog_tgts[col] = int(pd.to_numeric(df[col], errors='coerce').sum())
            except Exception:
                pass

    return df, {}, prog_tgts

# INDICATOR_META — used by app.py for targets display
INDICATOR_META = {
    'TX_CURR':      {'label': 'Active on ART',          'freq': 'Quarterly',    'snapshot': True},
    'TX_NEW':       {'label': 'New ART Initiations',     'freq': 'Quarterly',    'snapshot': False},
    'HTS_TST':      {'label': 'HIV Tests',               'freq': 'Quarterly',    'snapshot': False},
    'HTS_TST_POS':  {'label': 'HIV Positive Results',    'freq': 'Quarterly',    'snapshot': False},
    'TX_PVLS_D':    {'label': 'VL Tests Resulted',       'freq': 'Quarterly',    'snapshot': False},
    'TX_PVLS_N':    {'label': 'VL Suppressed',           'freq': 'Quarterly',    'snapshot': False},
    'PMTCT_STAT_N': {'label': 'ANC Clients Tested',      'freq': 'Quarterly',    'snapshot': False},
    'PMTCT_ART_D':  {'label': 'PMTCT on ART',            'freq': 'Quarterly',    'snapshot': False},
    'PrEP_NEW':     {'label': 'PrEP New Initiations',    'freq': 'Quarterly',    'snapshot': False},
    'TB_PREV_N':    {'label': 'TPT Completed',           'freq': 'Semi-Annual',  'snapshot': False},
    'TX_TB_N':      {'label': 'TB/HIV on ART',           'freq': 'Semi-Annual',  'snapshot': False},
    'TB_ART':       {'label': 'TB Patients on ART',      'freq': 'Annual',       'snapshot': False},
}
