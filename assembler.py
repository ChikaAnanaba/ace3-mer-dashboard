"""
ACE3 Assembler — builds semi-annual and annual results from quarter dicts.

_build_semi rules (MER v2.8):
  SNAPSHOT keys  → take Q2 value (not sum)
  CUMULATIVE keys → sum Q1 + Q2
"""
import pandas as pd
from targets import load_targets


# ── Keys that are SNAPSHOTS (period-end point-in-time, must NOT be summed) ────
SNAPSHOT_KEYS = {
    # Treatment snapshots
    'TX_CURR', 'TX_CURR_F', 'TX_CURR_M', 'TX_CURR_LT15', 'TX_CURR_BIO',
    'TX_CURR_STATE', 'TX_CURR_DISAGG',
    # VL snapshots
    'TX_PVLS_D', 'TX_PVLS_N', 'VL_COVERAGE', 'VL_SUPPRESSION',
    'VL_UNSUPP', 'VL_GAP', 'VL_ELIGIBLE',
    # VL Preg/BF snapshots
    'PVLS_PREG_ELIG', 'PVLS_PREG_D', 'PVLS_PREG_N', 'PVLS_BY_CAT',
    # MMD snapshots
    'MMD_3P', 'MMD_6P', 'MMD_LT3',
    # PrEP snapshot
    'PrEP_CURR',
    # EAC snapshots
    'EAC_CASELOAD', 'EAC_POST_VL_N', 'EAC_POST_SUPP_N', 'EAC_POST_SUPP_R',
    'EAC_STATE',
    # TB programme snapshots (no date filter in DAX)
    'TB_PREV_D', 'TB_PREV_N',
    # CxCa snapshots
    'CXCA_SCRN', 'CXCA_TX', 'CXCA_RESULTS',
    # AHD snapshots
    'AHD_SCRN', 'AHD_CONF', 'AHD_CD4', 'AHD_TBLAM_POS', 'AHD_CRAG_POS',
    # TX_TB_D is a placeholder — use Q2 value
    'TX_TB_D',
}


def _int(v):
    """Safely convert to int."""
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _int_dict(d):
    """Convert dict values to int."""
    if not isinstance(d, dict):
        return {}
    return {k: _int(v) for k, v in d.items()}


def _flatten(r: dict, prep: dict, eac: dict, prog_tgts: dict, quarter: str) -> dict:
    """
    Flatten engine output + prep + eac into a single flat dict for the app.
    All values are plain Python ints/floats — no numpy types.
    """
    txc  = r.get('TX_CURR', {})
    txn  = r.get('TX_NEW', {})
    pv   = r.get('TX_PVLS', {})
    ml   = r.get('TX_ML', {})
    rtt  = r.get('TX_RTT', {})
    hts  = r.get('HTS_TST', {})
    pm   = r.get('PMTCT_STAT', {})
    pa   = r.get('PMTCT_ART', {})
    tbs  = r.get('TB_SCREEN', {})
    tpt  = r.get('TPT', {})
    tx_tb= r.get('TX_TB', {})
    cx   = r.get('CXCA', {})
    ahd  = r.get('AHD', {})
    vle  = r.get('VL_ELIGIBLE', {})
    prog = r.get('PROGRAMMATIC', {})

    txc_n = _int(txc.get('value', 0))
    pvls_d = _int(pv.get('d', 0))
    pvls_n = _int(pv.get('n', 0))

    flat = {
        # TX_CURR
        'TX_CURR':          txc_n,
        'TX_CURR_F':        _int(txc.get('disagg', {}).get('Female', 0)),
        'TX_CURR_M':        _int(txc.get('disagg', {}).get('Male', 0)),
        'TX_CURR_LT15':     _int(txc.get('disagg', {}).get('<15', 0)),
        'TX_CURR_BIO':      _int(txc.get('biometric', 0)),
        'TX_CURR_STATE':    _int_dict(txc.get('state', {})),
        'TX_CURR_DISAGG':   txc.get('disagg', {}),

        # TX_NEW
        'TX_NEW':           _int(txn.get('value', 0)),
        'TX_NEW_STATE':     _int_dict(txn.get('state', {})),

        # TX_ML
        'TX_ML':            _int(ml.get('value', 0)),
        'TX_ML_OUTCOMES':   _int_dict(ml.get('outcomes', {})),
        'TX_ML_STATE':      _int_dict(ml.get('state', {})),

        # TX_RTT
        'TX_RTT':           _int(rtt.get('value', 0)),

        # TX_PVLS
        'TX_PVLS_D':        pvls_d,
        'TX_PVLS_N':        pvls_n,
        'VL_SUPPRESSION':   float(pv.get('suppression', 0)),
        'VL_COVERAGE':      float(pv.get('coverage', 0)),
        'VL_UNSUPP':        _int(pv.get('unsuppressed', 0)),
        'VL_GAP':           _int(vle.get('gap', 0)),
        'VL_ELIGIBLE':      _int(vle.get('eligible', 0)),
        # PVLS Preg/BF/PP
        'PVLS_PREG_ELIG':   _int(pv.get('preg_elig', 0)),
        'PVLS_PREG_D':      _int(pv.get('preg_d', 0)),
        'PVLS_PREG_N':      _int(pv.get('preg_n', 0)),
        'PVLS_BY_CAT':      pv.get('preg_by_cat', {}),

        # MMD
        'MMD_3P':           _int(txc.get('mmd', {}).get('3-5mo', 0)) + _int(txc.get('mmd', {}).get('6+mo', 0)),
        'MMD_6P':           _int(txc.get('mmd', {}).get('6+mo', 0)),
        'MMD_LT3':          _int(txc.get('mmd', {}).get('<3mo', 0)),

        # HTS
        'HTS_TST':          _int(hts.get('value', 0)),
        'HTS_TST_POS':      _int(hts.get('pos', 0)),
        'HTS_YIELD':        float(hts.get('yield', 0)),
        'HTS_STATE':        _int_dict(hts.get('state', {})),
        'HTS_MODALITY':     hts.get('modality', {}),

        # PMTCT
        'PMTCT_STAT_N':     _int(pm.get('n', 0)),
        'PMTCT_STAT_POS':   _int(pm.get('pos', 0)),
        'PMTCT_ART_D':      _int(pa.get('art_fy', 0)),
        'PMTCT_EID':        _int(pa.get('eid_pcr', 0)),
        'PMTCT_DELIVERED':  _int(pa.get('delivered', 0)),
        'PMTCT_ANC1':       _int(pm.get('anc1', 0)),
        'PMTCT_POSTANC':    _int(pm.get('post_anc', 0)),
        'PMTCT_BF':         _int(pm.get('breastfeeding', 0)),

        # TB
        'TB_SCREEN':        _int(tbs.get('screened', 0)),
        'TB_SCREEN_POS':    _int(tbs.get('positive', 0)),
        'TB_PREV_D':        _int(tpt.get('TB_PREV_D', 0)),
        'TB_PREV_N':        _int(tpt.get('TB_PREV_N', 0)),
        'TX_TB_D':          _int(tx_tb.get('D', 0)),   # placeholder — manual entry
        'TX_TB_N':          _int(tx_tb.get('N', 0)),
        'TX_TB_PLACEHOLDER': tx_tb.get('placeholder', False),

        # CxCa
        'CXCA_SCRN':        _int(cx.get('eligible', 0)),
        'CXCA_TX':          _int(cx.get('screened', 0)),
        'CXCA_RESULTS':     cx.get('results', {}),

        # AHD
        'AHD_SCRN':         _int(ahd.get('total', 0)),
        'AHD_CONF':         _int(ahd.get('ahd_yes', 0)),
        'AHD_CD4':          _int(ahd.get('cd4_done', 0)),
        'AHD_TBLAM_POS':    _int(ahd.get('tblam_pos', 0)),
        'AHD_CRAG_POS':     _int(ahd.get('crag_pos', 0)),

        # PrEP
        'PrEP_NEW':         _int(prep.get('PrEP_NEW', 0)),
        'PrEP_CT':          _int(prep.get('PrEP_CT', 0)),
        'PrEP_CURR':        _int(prep.get('PrEP_CURR', 0)),
        'PrEP_NEW_STATE':   _int_dict(prep.get('PrEP_NEW_STATE', {})),
        'PrEP_NEW_POP':     prep.get('PrEP_NEW_POP', {}),

        # EAC
        'EAC_CASELOAD':     _int(eac.get('EAC_CASELOAD', 0)),
        'EAC_SESS1':        _int(eac.get('EAC_SESS1', 0)),
        'EAC_SESS2':        _int(eac.get('EAC_SESS2', 0)),
        'EAC_SESS3':        _int(eac.get('EAC_SESS3', 0)),
        'EAC_EXT':          _int(eac.get('EAC_EXT', 0)),
        'EAC_POST_VL_N':    _int(eac.get('EAC_POST_VL_N', 0)),
        'EAC_POST_SUPP_N':  _int(eac.get('EAC_POST_SUPP_N', 0)),
        'EAC_POST_SUPP_R':  float(eac.get('EAC_POST_SUPP_R', 0)),
        'EAC_STATE':        _int_dict(eac.get('EAC_STATE', {})),

        # Targets
        'TARGETS':          prog_tgts,

        # Quarter label
        'quarter': quarter,
    }
    return flat


def _build_semi(q1: dict, q2: dict, prog_tgts: dict) -> dict:
    """
    Build semi-annual totals from Q1 + Q2 flat dicts.

    Rules per MER v2.8:
    - SNAPSHOT_KEYS → use Q2 value (period-end snapshot)
    - All other numeric keys → sum Q1 + Q2
    - Dict values (state breakdowns, outcomes) → sum values within dict
    - Non-numeric / metadata keys → use Q2 value
    """
    if not q1 and not q2:
        return {}
    if not q2:
        return dict(q1)
    if not q1:
        return dict(q2)

    semi = {'quarter': 'SEMI', 'TARGETS': prog_tgts}
    all_keys = set(list(q1.keys()) + list(q2.keys()))

    for key in all_keys:
        if key in ('quarter', 'TARGETS'):
            continue

        v1 = q1.get(key)
        v2 = q2.get(key)

        # Snapshot → always use Q2
        if key in SNAPSHOT_KEYS:
            semi[key] = v2 if v2 is not None else v1
            continue

        # Both missing
        if v1 is None and v2 is None:
            semi[key] = None
            continue

        # One missing → use the other
        if v1 is None:
            semi[key] = v2
            continue
        if v2 is None:
            semi[key] = v1
            continue

        # Dict → sum inner values (state breakdowns, outcome breakdowns)
        if isinstance(v1, dict) and isinstance(v2, dict):
            merged = dict(v1)
            for k, val in v2.items():
                if isinstance(val, (int, float)) and isinstance(merged.get(k), (int, float)):
                    merged[k] = merged[k] + val
                else:
                    merged[k] = val
            semi[key] = merged
            continue

        # Numeric → sum
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            semi[key] = v1 + v2
            continue

        # Boolean / placeholder → use Q2
        if isinstance(v1, bool) or isinstance(v2, bool):
            semi[key] = v2
            continue

        # Default → use Q2
        semi[key] = v2

    return semi


def assemble(files_q1: dict, files_q2: dict = None,
             files_q3: dict = None, files_q4: dict = None,
             targets_src=None, quarter_mode: str = 'Q1') -> dict:
    """
    Run engine(s) and return unified results dict.
    quarter_mode: 'Q1' | 'Q2' | 'Q3' | 'Q4' | 'CUM' | 'ANNUAL'
    """
    from ace3_engine import ACE3Engine
    from prep_engine import compute_prep
    from eac_engine import compute_eac

    out = {
        'q1': {}, 'q2': {}, 'q3': {}, 'q4': {},
        'semi': {}, 'targets': {}, 'errors': []
    }

    # ── Load targets ──────────────────────────────────────────────────────────
    prog_tgts = {}
    if targets_src is not None:
        try:
            _, _, prog_tgts = load_targets(targets_src)
        except Exception as e:
            out['errors'].append(f'Targets load error: {e}')
    out['targets'] = prog_tgts

    def _run_quarter(files: dict, qname: str) -> dict:
        if not files or not files.get('radet'):
            return {}
        try:
            eng = ACE3Engine()
            eng.load_radet(files['radet'])
            if files.get('hts'):
                eng.load_hts(files['hts'])
            if files.get('pmtct_hts'):
                eng.load_pmtct_hts(files['pmtct_hts'])
            if files.get('pmtct_mat'):
                eng.load_pmtct_mat(files['pmtct_mat'])
            if files.get('tb'):
                eng.load_tb(files['tb'])
            if files.get('ahd'):
                eng.load_ahd(files['ahd'])
            if files.get('vl_eligible'):
                eng.load_vl_eligible(files['vl_eligible'])

            r = eng.compute(quarter=qname)

            prep = {}
            if files.get('prep'):
                try:
                    prep = compute_prep(files['prep'], quarter=qname)
                except Exception as e:
                    out['errors'].append(f'{qname} PrEP error: {e}')

            eac = {}
            if files.get('eac'):
                try:
                    eac = compute_eac(files['eac'], quarter=qname)
                except Exception as e:
                    out['errors'].append(f'{qname} EAC error: {e}')

            return _flatten(r, prep, eac, prog_tgts, qname)
        except Exception as e:
            out['errors'].append(f'{qname} engine error: {e}')
            import traceback
            out['errors'].append(traceback.format_exc())
            return {}

    # ── Run each quarter ──────────────────────────────────────────────────────
    out['q1'] = _run_quarter(files_q1, 'Q1')

    if files_q2 and files_q2.get('radet'):
        out['q2'] = _run_quarter(files_q2, 'Q2')

    if files_q3 and files_q3.get('radet'):
        out['q3'] = _run_quarter(files_q3, 'Q3')

    if files_q4 and files_q4.get('radet'):
        out['q4'] = _run_quarter(files_q4, 'Q4')

    # ── Build semi-annual ─────────────────────────────────────────────────────
    if out['q1'] and out['q2']:
        out['semi'] = _build_semi(out['q1'], out['q2'], prog_tgts)

    return out
