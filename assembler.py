"""
ACE3 Results Assembler
Runs ACE3Engine for Q1 and/or Q2, merges PrEP, merges targets,
returns a clean results dict used by the dashboard and Excel export.
"""
import pandas as pd
from ace3_engine import ACE3Engine
from prep_engine import compute_prep
from eac_engine import compute_eac
from targets import (load_targets, get_annual_target, pct_achieved,
                     status_flag, qoq_change, INDICATOR_META)


def _safe(d, *keys, default=0):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d if d is not None else default


def _pct(n, d, dec=1):
    return round(n / d * 100, dec) if d else 0


def build_engine(files: dict) -> ACE3Engine:
    """Load all uploaded files into the engine."""
    eng = ACE3Engine()
    if files.get('radet'):
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
    return eng


def assemble(files_q1: dict, files_q2: dict = None,
             targets_src=None, quarter_mode='Q1') -> dict:
    """
    Run engine(s), merge PrEP and targets, return unified results dict.

    Parameters
    ----------
    files_q1     : dict of uploaded file objects for Q1
    files_q2     : dict of uploaded file objects for Q2 (optional)
    targets_src  : targets file path/object (optional)
    quarter_mode : 'Q1' | 'Q2' | 'SEMI'

    Returns
    -------
    dict with keys: q1, q2, semi, targets, meta
    Each quarter dict contains all indicator values.
    """
    out = {'q1': {}, 'q2': {}, 'semi': {}, 'targets': {}, 'errors': []}

    # ── targets ──────────────────────────────────────────────────────────────
    prog_tgts = {}
    state_tgts = {}
    if targets_src:
        try:
            _, state_tgts, prog_tgts = load_targets(targets_src)
            out['targets'] = prog_tgts
            out['state_targets'] = state_tgts
        except Exception as e:
            out['errors'].append(f'Targets load error: {e}')

    # ── Q1 engine ────────────────────────────────────────────────────────────
    if files_q1.get('radet'):
        try:
            eng1 = build_engine(files_q1)
            # map quarter_mode to engine quarter key
            eng_q = quarter_mode if quarter_mode in ['Q1','Q2','Q3','Q4','ANNUAL'] else 'Q1'
            r1   = eng1.compute(quarter=eng_q)
            prep1 = {}
            if files_q1.get('prep'):
                prep1 = compute_prep(files_q1['prep'], quarter=eng_q)
            eac1 = {}
            if files_q1.get('eac'):
                eac1 = compute_eac(files_q1['eac'], quarter=eng_q)
            out['q1'] = _flatten(r1, prep1, eac1, prog_tgts, eng_q)
        except Exception as e:
            out['errors'].append(f'Q1 engine error: {e}')

    # ── Q2 engine (only for semi-annual) ─────────────────────────────────────
    if files_q2 and files_q2.get('radet') and quarter_mode == 'CUM':
        try:
            eng2 = build_engine(files_q2)
            r2   = eng2.compute(quarter='Q2')
            prep2 = {}
            if files_q2.get('prep'):
                prep2 = compute_prep(files_q2['prep'], quarter='Q2')
            eac2 = {}
            if files_q2.get('eac'):
                eac2 = compute_eac(files_q2['eac'], quarter='Q2')
            out['q2'] = _flatten(r2, prep2, eac2, prog_tgts, 'Q2')
        except Exception as e:
            out['errors'].append(f'Q2 engine error: {e}')

    # ── semi-annual (re-run engine on Q1 files with CUM, then Q2 files) ─────
    if out['q1'] and out['q2']:
        out['semi'] = _build_semi(out['q1'], out['q2'], prog_tgts)

    return out


def _flatten(r: dict, prep: dict, eac: dict, prog_tgts: dict, quarter: str) -> dict:
    """Flatten raw engine output into a clean indicator dict."""
    txc  = r.get('TX_CURR', {})
    txn  = r.get('TX_NEW', {})
    pvls = r.get('TX_PVLS', {})
    vle  = r.get('VL_ELIGIBLE', {})
    txml = r.get('TX_ML', {})
    rtt  = r.get('TX_RTT', {})
    hts  = r.get('HTS_TST', {})
    pmts = r.get('PMTCT_STAT', {})
    pmta = r.get('PMTCT_ART', {})
    tb   = r.get('TB_SCREEN', {})
    tpt  = r.get('TPT', {})
    cxca = r.get('CXCA', {})
    ahd  = r.get('AHD', {})
    mmd  = txc.get('mmd', {})

    txc_total = txc.get('value', 0)
    pvls_d    = pvls.get('d', 0)
    pvls_n    = pvls.get('n', 0)

    # Derived
    vl_cov_pct  = _pct(pvls_d, txc_total)
    vl_supp_pct = _pct(pvls_n, pvls_d)
    mmd_3p      = mmd.get('3-5mo', 0) + mmd.get('6+mo', 0)
    mmd_6p      = mmd.get('6+mo', 0)

    # PrEP
    pnew = _safe(prep, 'PrEP_NEW', 'value')
    pct_ = _safe(prep, 'PrEP_CT',  'value')
    pcurr= _safe(prep, 'PrEP_CURR','value')

    d = {
        # Treatment
        'TX_CURR':        txc_total,
        'TX_CURR_F':      _safe(txc, 'disagg', 'Female'),
        'TX_CURR_M':      _safe(txc, 'disagg', 'Male'),
        'TX_CURR_LT15':   _safe(txc, 'disagg', '<15'),
        'TX_CURR_BIO':    txc.get('biometric', 0),
        'TX_CURR_STATE':  txc.get('state', {}),
        'TX_NEW':         txn.get('value', 0),
        'TX_NEW_STATE':   txn.get('state', {}),
        # Retention
        'TX_ML':          txml.get('value', 0),
        'TX_ML_OUTCOMES': txml.get('outcomes', {}),
        'TX_ML_STATE':    txml.get('state', {}),
        'TX_RTT':         rtt.get('value', 0),
        # VL
        'TX_PVLS_D':      pvls_d,
        'TX_PVLS_N':      pvls_n,
        'VL_COVERAGE':    vl_cov_pct,
        'VL_SUPPRESSION': vl_supp_pct,
        'VL_UNSUPP':      pvls.get('unsuppressed', 0),
        'VL_GAP':         vle.get('gap', 0),
        'VL_ELIGIBLE':    vle.get('eligible', pvls_d),
        # Testing
        'HTS_TST':        hts.get('value', 0),
        'HTS_TST_POS':    hts.get('pos', 0),
        'HTS_YIELD':      hts.get('yield', 0),
        'HTS_STATE':      hts.get('state', {}),
        'HTS_MODALITY':   hts.get('modality', {}),
        # PMTCT
        'PMTCT_STAT_N':   pmts.get('n', 0),
        'PMTCT_STAT_POS': pmts.get('pos', 0),
        'PMTCT_ART_D':    pmta.get('art_fy', 0),
        'PMTCT_EID':      pmta.get('eid_pcr', 0),
        'PMTCT_DELIVERED':pmta.get('delivered', 0),
        'PMTCT_ANC1':     pmts.get('anc1', pmts.get('n', 0)),
        'PMTCT_POSTANC':  pmts.get('post_anc', 0),
        'PMTCT_BF':       pmts.get('breastfeeding', 0),
        # TB
        'TB_SCREEN':      tb.get('screened', 0),
        'TB_SCREEN_POS':  tb.get('positive', 0),
        'TB_PREV_N':      tpt.get('started_radet', 0),
        'TX_TB_N':        0,  # from radet if available
        'TB_ART':         0,  # annual indicator
        # DSD
        'MMD_3P':         mmd_3p,
        'MMD_6P':         mmd_6p,
        'MMD_LT3':        mmd.get('<3mo', 0),
        # CxCa
        'CXCA_SCRN':      cxca.get('eligible', 0),
        'CXCA_TX':        cxca.get('screened', 0),
        'CXCA_RESULTS':   cxca.get('results', {}),
        # AHD
        'AHD_SCRN':       ahd.get('total', 0),
        'AHD_CONF':       ahd.get('ahd_yes', 0),
        'AHD_CD4':        ahd.get('cd4_done', 0),
        'AHD_TBLAM_POS':  ahd.get('tblam_pos', 0),
        'AHD_CRAG_POS':   ahd.get('crag_pos', 0),
        # PrEP
        'PrEP_NEW':       pnew,
        'PrEP_CT':        pct_,
        'PrEP_CURR':      pcurr,
        'PrEP_NEW_STATE': _safe(prep, 'PrEP_NEW', 'state'),
        'PrEP_NEW_DISAGG':_safe(prep, 'PrEP_NEW', 'disagg'),
        'PrEP_NEW_POP':   _safe(prep, 'PrEP_NEW', 'pop_type'),
        # Quarter label
        'quarter': quarter,

        # EAC
        'EAC_CASELOAD':    eac.get('total_caseload', 0),
        'EAC_SESS1':       eac.get('eac1_completed', 0),
        'EAC_SESS2':       eac.get('eac2_completed', 0),
        'EAC_SESS3':       eac.get('eac3_completed', 0),
        'EAC_EXT':         eac.get('extended', 0),
        'EAC_NO_SESS':     eac.get('no_session_yet', 0),
        'EAC_POST_VL_N':   eac.get('post_vl_collected', 0),
        'EAC_POST_SUPP_N': eac.get('post_supp_n', 0),
        'EAC_POST_SUPP_R': eac.get('post_supp_rate', 0),
        'EAC_INDICATION':  eac.get('indication', {}),
        'EAC_STATE':       eac.get('state', {}),
        'EAC_SWITCHED':    eac.get('switched', 0),
    }

    # ── attach target values and % achieved ──────────────────────────────────
    for key, meta in INDICATOR_META.items():
        indicator_val = d.get(key)
        if indicator_val is None or not isinstance(indicator_val, (int, float)):
            continue
        annual_tgt = get_annual_target(key, prog_tgts)
        d[f'{key}_TGT']     = annual_tgt
        d[f'{key}_PCT_TGT'] = pct_achieved(indicator_val, annual_tgt)
        d[f'{key}_STATUS']  = status_flag(d[f'{key}_PCT_TGT'])

    return d


def _build_semi(q1: dict, q2: dict, prog_tgts: dict) -> dict:
    """
    Build semi-annual totals from Q1 + Q2 dicts.
    Snapshots (TX_CURR, PrEP_CURR) use Q2 value.
    Cumulative indicators are summed.
    """
    SNAPSHOT_KEYS = {'TX_CURR', 'TX_CURR_F', 'TX_CURR_M', 'TX_CURR_LT15',
                     'TX_CURR_BIO', 'VL_COVERAGE', 'VL_SUPPRESSION',
                     'PrEP_CURR', 'MMD_3P', 'MMD_6P', 'MMD_LT3'}

    semi = {'quarter': 'SEMI'}
    all_keys = set(list(q1.keys()) + list(q2.keys()))

    for k in all_keys:
        v1 = q1.get(k)
        v2 = q2.get(k)
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            semi[k] = v2 if k in SNAPSHOT_KEYS else v1 + v2
        elif v2 is not None:
            semi[k] = v2
        elif v1 is not None:
            semi[k] = v1

    # Recalculate derived rates using semi-annual totals
    if semi.get('TX_PVLS_D', 0) > 0:
        semi['VL_SUPPRESSION'] = _pct(semi.get('TX_PVLS_N', 0), semi.get('TX_PVLS_D', 0))
    if semi.get('TX_CURR', 0) > 0:
        semi['VL_COVERAGE'] = _pct(semi.get('TX_PVLS_D', 0), semi.get('TX_CURR', 0))

    # Re-attach targets for semi-annual totals
    for key, meta in INDICATOR_META.items():
        val = semi.get(key)
        if val is None or not isinstance(val, (int, float)):
            continue
        annual_tgt = get_annual_target(key, prog_tgts)
        semi[f'{key}_TGT']     = annual_tgt
        semi[f'{key}_PCT_TGT'] = pct_achieved(val, annual_tgt)
        semi[f'{key}_STATUS']  = status_flag(semi[f'{key}_PCT_TGT'])

    return semi
