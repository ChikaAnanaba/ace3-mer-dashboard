"""
Targets loader — ACE3
Loads facility-level annual targets CSV/Excel, rolls up to state and programme level.
MER v2.8 comparison rules applied per indicator.
"""
import pandas as pd

# ── indicator catalogue ───────────────────────────────────────────────────────
# Keys must match exactly what ACE3Engine and prep_engine return
# frequency: quarterly | semiannual | annual
# has_target: False = analytics-only (TX_ML, TX_RTT, CxCa, AHD, EID)
# tx_curr_like: True = snapshot (not cumulative) for % calculation

INDICATOR_META = {
    # Treatment
    'TX_CURR':       {'label': 'Active on ART',                    'category': 'Treatment',  'code': 'TX_CURR',       'frequency': 'quarterly',   'has_target': True,  'snapshot': True,  'target_col': 'TX_CURR'},
    'TX_NEW':        {'label': 'New ART Initiations',              'category': 'Treatment',  'code': 'TX_NEW',        'frequency': 'quarterly',   'has_target': True,  'snapshot': False, 'target_col': 'TX_NEW'},
    'TX_ML':         {'label': 'Treatment Interruptions (IIT)',    'category': 'Retention',  'code': 'TX_ML',         'frequency': 'quarterly',   'has_target': False, 'snapshot': False, 'target_col': None},
    'TX_RTT':        {'label': 'Returned to Treatment',            'category': 'Retention',  'code': 'TX_RTT',        'frequency': 'quarterly',   'has_target': False, 'snapshot': False, 'target_col': None},
    # VL
    'TX_PVLS_D':     {'label': 'VL Test Results (Denominator)',    'category': 'Viral Load', 'code': 'TX_PVLS_D',     'frequency': 'quarterly',   'has_target': True,  'snapshot': False, 'target_col': 'TX_PVLS_D'},
    'TX_PVLS_N':     {'label': 'VL Suppressed (Numerator)',        'category': 'Viral Load', 'code': 'TX_PVLS_N',     'frequency': 'quarterly',   'has_target': True,  'snapshot': False, 'target_col': 'TX_PVLS_N'},
    'VL_COVERAGE':   {'label': 'VL Coverage %',                   'category': 'Viral Load', 'code': 'VL_COV',        'frequency': 'quarterly',   'has_target': False, 'snapshot': False, 'target_col': None},
    'VL_SUPPRESSION':{'label': 'VL Suppression %',                'category': 'Viral Load', 'code': 'VL_SUPP',       'frequency': 'quarterly',   'has_target': False, 'snapshot': False, 'target_col': None},
    # Testing
    'HTS_TST':       {'label': 'HIV Tests Conducted',              'category': 'Testing',    'code': 'HTS_TST',       'frequency': 'quarterly',   'has_target': True,  'snapshot': False, 'target_col': 'HTS_TST'},
    'HTS_TST_POS':   {'label': 'HIV Positive Results',             'category': 'Testing',    'code': 'HTS_TST_POS',   'frequency': 'quarterly',   'has_target': True,  'snapshot': False, 'target_col': 'HTS_TST_POS'},
    # PMTCT
    'PMTCT_STAT_N':  {'label': 'ANC Clients Tested',               'category': 'PMTCT',     'code': 'PMTCT_STAT',    'frequency': 'quarterly',   'has_target': True,  'snapshot': False, 'target_col': 'PMTCT_STAT_N'},
    'PMTCT_STAT_POS':{'label': 'ANC HIV Positive',                 'category': 'PMTCT',     'code': 'PMTCT_STAT_POS','frequency': 'quarterly',   'has_target': True,  'snapshot': False, 'target_col': 'PMTCT_STAT_POS'},
    'PMTCT_ART_D':   {'label': 'PMTCT on ART',                    'category': 'PMTCT',     'code': 'PMTCT_ART_D',   'frequency': 'quarterly',   'has_target': True,  'snapshot': False, 'target_col': 'PMTCT_ART_D'},
    'PMTCT_EID':     {'label': 'EID PCR Tests',                   'category': 'PMTCT',     'code': 'PMTCT_EID',     'frequency': 'quarterly',   'has_target': False, 'snapshot': False, 'target_col': None},
    # TB
    'TB_PREV_N':     {'label': 'TB Preventive Therapy (TPT)',      'category': 'TB/HIV',    'code': 'TB_PREV_N',     'frequency': 'semiannual',  'has_target': True,  'snapshot': False, 'target_col': 'TB_PREV_N'},
    'TX_TB_N':       {'label': 'TB/HIV Co-infected on ART',        'category': 'TB/HIV',    'code': 'TX_TB_N',       'frequency': 'semiannual',  'has_target': True,  'snapshot': False, 'target_col': 'TX_TB_N'},
    'TB_ART':        {'label': 'TB Patients on ART',               'category': 'TB/HIV',    'code': 'TB_ART',        'frequency': 'annual',      'has_target': True,  'snapshot': False, 'target_col': 'TB_ART'},
    'TB_SCREEN':     {'label': 'TB Screening (TX_CURR)',           'category': 'TB/HIV',    'code': 'TB_SCRN',       'frequency': 'quarterly',   'has_target': False, 'snapshot': False, 'target_col': None},
    # PrEP
    'PrEP_NEW':      {'label': 'New PrEP Initiations',             'category': 'PrEP',      'code': 'PrEP_NEW',      'frequency': 'quarterly',   'has_target': True,  'snapshot': False, 'target_col': 'PrEP_NEW'},
    'PrEP_CT':       {'label': 'PrEP Continuing (Follow-up)',      'category': 'PrEP',      'code': 'PrEP_CT',       'frequency': 'quarterly',   'has_target': False, 'snapshot': False, 'target_col': None},
    'PrEP_CURR':     {'label': 'Currently on PrEP (Snapshot)',     'category': 'PrEP',      'code': 'PrEP_CURR',     'frequency': 'quarterly',   'has_target': False, 'snapshot': True,  'target_col': None},
    # DSD
    'MMD_3P':        {'label': 'MMD ≥3 Months',                   'category': 'DSD',       'code': 'MMD_3P',        'frequency': 'quarterly',   'has_target': False, 'snapshot': False, 'target_col': None},
    'MMD_6P':        {'label': 'MMD 6+ Months',                   'category': 'DSD',       'code': 'MMD_6P',        'frequency': 'quarterly',   'has_target': False, 'snapshot': False, 'target_col': None},
    # Women's Health
    'CXCA_SCRN':     {'label': 'CxCa Eligible WLHIV',             'category': "Women's Health", 'code': 'CXCA_SCRN', 'frequency': 'semiannual',  'has_target': False, 'snapshot': False, 'target_col': None},
    'CXCA_TX':       {'label': 'CxCa Screened',                   'category': "Women's Health", 'code': 'CXCA_TX',   'frequency': 'semiannual',  'has_target': False, 'snapshot': False, 'target_col': None},
    # AHD
    'AHD_SCRN':      {'label': 'AHD Screened',                    'category': 'AHD',       'code': 'AHD_SCRN',      'frequency': 'quarterly',   'has_target': False, 'snapshot': False, 'target_col': None},
    'AHD_CONF':      {'label': 'AHD Confirmed',                   'category': 'AHD',       'code': 'AHD_CONF',      'frequency': 'quarterly',   'has_target': False, 'snapshot': False, 'target_col': None},
}

TARGET_FILE_COLS = [
    'HTS_TST','HTS_TST_POS','PMTCT_ART_D','PMTCT_STAT_N','PMTCT_STAT_POS',
    'PrEP_NEW','TB_ART','TB_PREV_N','TX_CURR','TX_NEW',
    'TX_PVLS_D','TX_PVLS_N','TX_TB_N'
]


def load_targets(src):
    """
    Load targets file. Returns (facility_df, state_tgts, prog_tgts).
    prog_tgts = {indicator_col: annual_total}
    state_tgts = {state: {indicator_col: annual_total}}
    """
    if isinstance(src, pd.DataFrame):
        df = src.copy()
    else:
        try:
            df = pd.read_csv(src)
        except Exception:
            try:
                if hasattr(src, 'seek'): src.seek(0)
                df = pd.read_excel(src)
            except Exception:
                raise ValueError("Cannot read targets file — must be .csv or .xlsx")

    df.columns = df.columns.str.strip()
    present = [c for c in TARGET_FILE_COLS if c in df.columns]

    for c in present:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    state_tgts = {}
    if 'State' in df.columns:
        for state, grp in df.groupby('State'):
            state_tgts[str(state)] = {c: int(grp[c].sum()) for c in present}

    prog_tgts = {c: int(df[c].sum()) for c in present}
    return df, state_tgts, prog_tgts


def get_annual_target(indicator_key, prog_tgts):
    """Return the annual target for an indicator key, or None if no target."""
    meta = INDICATOR_META.get(indicator_key, {})
    col  = meta.get('target_col')
    if not col or not meta.get('has_target'):
        return None
    return prog_tgts.get(col)


def pct_achieved(result, annual_target):
    """Safe percentage achieved."""
    if annual_target is None or annual_target == 0:
        return None
    return round(result / annual_target * 100, 1)


def status_flag(pct):
    """Return status label based on % of annual target achieved."""
    if pct is None:
        return '—'
    if pct >= 75:
        return '✓ On Track'
    if pct >= 50:
        return '⚠ Watch'
    return '✗ Behind'


def qoq_change(q1, q2):
    """Return (absolute_change, pct_change) or (None, None)."""
    if q1 is None or q2 is None:
        return None, None
    abs_chg = q2 - q1
    pct_chg = round(abs_chg / q1 * 100, 1) if q1 != 0 else None
    return abs_chg, pct_chg
