"""
Excel Export — generates ACE3_Data_Report.xlsx with DATA_INPUT sheet.
All indicator values auto-populated from engine results.
"""
import io
import pandas as pd


def generate_excel(results: dict) -> bytes:
    """
    Generate Excel workbook from assembled results dict.
    Returns bytes for Streamlit download_button.
    """
    buf = io.BytesIO()

    # Use semi-annual if available, else Q1
    d = results.get('semi') or results.get('q1') or {}
    tgts = results.get('targets', {})

    def _n(v):
        try:
            return int(round(float(v)))
        except (TypeError, ValueError):
            return 0

    def _f(v, dec=1):
        try:
            return round(float(v), dec)
        except (TypeError, ValueError):
            return 0.0

    rows = [
        # ── Treatment ──────────────────────────────────────────────────────
        ('TX_CURR',          'Active on ART (snapshot)',        _n(d.get('TX_CURR',0)),          _n(tgts.get('TX_CURR',0)),    'Quarterly'),
        ('TX_CURR_F',        'TX_CURR Female',                  _n(d.get('TX_CURR_F',0)),        '',                           'Quarterly'),
        ('TX_CURR_M',        'TX_CURR Male',                    _n(d.get('TX_CURR_M',0)),        '',                           'Quarterly'),
        ('TX_CURR_LT15',     'TX_CURR <15 (Paediatric)',        _n(d.get('TX_CURR_LT15',0)),     '',                           'Quarterly'),
        ('TX_CURR_BIO',      'TX_CURR Biometrically Enrolled',  _n(d.get('TX_CURR_BIO',0)),      '',                           'Quarterly'),
        ('TX_NEW',           'New ART Initiations',             _n(d.get('TX_NEW',0)),           _n(tgts.get('TX_NEW',0)),     'Quarterly'),
        ('TX_ML',            'Treatment Interruptions',         _n(d.get('TX_ML',0)),            '',                           'Quarterly'),
        ('TX_ML_IIT',        'TX_ML — IIT',                     _n(d.get('TX_ML_OUTCOMES',{}).get('IIT',0)), '', 'Quarterly'),
        ('TX_ML_DIED',       'TX_ML — Died',                    _n(d.get('TX_ML_OUTCOMES',{}).get('Died',0)), '', 'Quarterly'),
        ('TX_ML_TO',         'TX_ML — Transferred Out',         _n(d.get('TX_ML_OUTCOMES',{}).get('Transferred Out',0)), '', 'Quarterly'),
        ('TX_ML_STOPPED',    'TX_ML — Stopped Treatment',       _n(d.get('TX_ML_OUTCOMES',{}).get('Stopped Treatment',0)), '', 'Quarterly'),
        ('TX_RTT',           'Returned to Treatment',           _n(d.get('TX_RTT',0)),           '',                           'Quarterly'),
        ('MMD_3P',           'MMD ≥3 Months',                   _n(d.get('MMD_3P',0)),           '',                           'Quarterly'),
        ('MMD_6P',           'MMD 6+ Months',                   _n(d.get('MMD_6P',0)),           '',                           'Quarterly'),
        ('MMD_LT3',          'MMD <3 Months',                   _n(d.get('MMD_LT3',0)),          '',                           'Quarterly'),

        # ── Viral Load ─────────────────────────────────────────────────────
        ('TX_PVLS_D',        'VL Tests Resulted (TX_PVLS_D)',   _n(d.get('TX_PVLS_D',0)),        _n(tgts.get('TX_PVLS_D',0)), 'Quarterly'),
        ('TX_PVLS_N',        'VL Suppressed (TX_PVLS_N)',       _n(d.get('TX_PVLS_N',0)),        _n(tgts.get('TX_PVLS_N',0)), 'Quarterly'),
        ('VL_SUPPRESSION',   'VL Suppression %',                _f(d.get('VL_SUPPRESSION',0)),   95.0,                         'Quarterly'),
        ('VL_COVERAGE',      'VL Coverage %',                   _f(d.get('VL_COVERAGE',0)),      95.0,                         'Quarterly'),
        ('VL_UNSUPP',        'Unsuppressed Clients',            _n(d.get('VL_UNSUPP',0)),        '',                           'Quarterly'),
        ('PVLS_PREG_ELIG',   'PVLS Eligible (Preg+BF+PP)',      _n(d.get('PVLS_PREG_ELIG',0)),   '',                           'Quarterly'),
        ('PVLS_PREG_D',      'PVLS_D Preg+BF+PP',              _n(d.get('PVLS_PREG_D',0)),      '',                           'Quarterly'),
        ('PVLS_PREG_N',      'PVLS_N Preg+BF+PP (suppressed)', _n(d.get('PVLS_PREG_N',0)),      '',                           'Quarterly'),

        # ── HTS ────────────────────────────────────────────────────────────
        ('HTS_TST',          'HIV Tests (HTS_TST)',              _n(d.get('HTS_TST',0)),          _n(tgts.get('HTS_TST',0)),   'Quarterly'),
        ('HTS_TST_POS',      'HIV Positive Results',            _n(d.get('HTS_TST_POS',0)),      _n(tgts.get('HTS_TST_POS',0)),'Quarterly'),
        ('HTS_YIELD',        'HIV Testing Yield %',             _f(d.get('HTS_YIELD',0),2),      '',                           'Quarterly'),

        # ── PMTCT ──────────────────────────────────────────────────────────
        ('PMTCT_STAT_N',     'ANC Clients Tested (PMTCT_STAT)', _n(d.get('PMTCT_STAT_N',0)),     _n(tgts.get('PMTCT_STAT_N',0)),'Quarterly'),
        ('PMTCT_STAT_POS',   'HIV+ at ANC',                     _n(d.get('PMTCT_STAT_POS',0)),   '',                           'Quarterly'),
        ('PMTCT_ART_D',      'PMTCT Mothers on ART',            _n(d.get('PMTCT_ART_D',0)),      _n(tgts.get('PMTCT_ART_D',0)),'Quarterly'),
        ('PMTCT_EID',        'EID PCR Done',                    _n(d.get('PMTCT_EID',0)),        '',                           'Quarterly'),
        ('PMTCT_DELIVERED',  'Deliveries',                      _n(d.get('PMTCT_DELIVERED',0)),  '',                           'Quarterly'),

        # ── TB ─────────────────────────────────────────────────────────────
        ('TB_SCREEN',        'TB Screened',                     _n(d.get('TB_SCREEN',0)),        '',                           'Quarterly'),
        ('TB_SCREEN_POS',    'TB Screen Positive',              _n(d.get('TB_SCREEN_POS',0)),    '',                           'Quarterly'),
        ('TB_PREV_D',        'TB_PREV Denominator (TPT Started)',_n(d.get('TB_PREV_D',0)),       '',                           'Semi-Annual'),
        ('TB_PREV_N',        'TB_PREV Numerator (TPT Completed)',_n(d.get('TB_PREV_N',0)),       _n(tgts.get('TB_PREV_N',0)), 'Semi-Annual'),
        ('TX_TB_D',          'TX_TB Denominator (TB Screened)', _n(d.get('TX_TB_D',0)),          '',                           'Semi-Annual'),
        ('TX_TB_N',          'TX_TB Numerator (TB/HIV on ART)', _n(d.get('TX_TB_N',0)),          '',                           'Semi-Annual'),

        # ── CxCa ───────────────────────────────────────────────────────────
        ('CXCA_SCRN',        'CxCa Eligible (F 15+)',           _n(d.get('CXCA_SCRN',0)),        '',                           'Semi-Annual'),
        ('CXCA_TX',          'CxCa Screened',                   _n(d.get('CXCA_TX',0)),          '',                           'Semi-Annual'),

        # ── AHD ────────────────────────────────────────────────────────────
        ('AHD_SCRN',         'AHD Screened',                    _n(d.get('AHD_SCRN',0)),         '',                           'Programme'),
        ('AHD_CONF',         'AHD Confirmed',                   _n(d.get('AHD_CONF',0)),         '',                           'Programme'),
        ('AHD_CD4',          'CD4 Tests Done',                  _n(d.get('AHD_CD4',0)),          '',                           'Programme'),
        ('AHD_TBLAM_POS',    'TB-LAM Positive',                 _n(d.get('AHD_TBLAM_POS',0)),    '',                           'Programme'),
        ('AHD_CRAG_POS',     'CrAg Positive',                   _n(d.get('AHD_CRAG_POS',0)),     '',                           'Programme'),

        # ── PrEP ───────────────────────────────────────────────────────────
        ('PrEP_NEW',         'PrEP New Initiations',            _n(d.get('PrEP_NEW',0)),         _n(tgts.get('PrEP_NEW',0)),  'Quarterly'),
        ('PrEP_CT',          'PrEP Continuing',                 _n(d.get('PrEP_CT',0)),          '',                           'Quarterly'),
        ('PrEP_CURR',        'PrEP Current (snapshot)',         _n(d.get('PrEP_CURR',0)),        '',                           'Quarterly'),

        # ── EAC ────────────────────────────────────────────────────────────
        ('EAC_CASELOAD',     'EAC Caseload (Unsuppressed)',     _n(d.get('EAC_CASELOAD',0)),     '',                           'Programme'),
        ('EAC_POST_VL_N',    'Post-EAC VL Collected',          _n(d.get('EAC_POST_VL_N',0)),    '',                           'Programme'),
        ('EAC_POST_SUPP_N',  'Post-EAC Re-suppressed',         _n(d.get('EAC_POST_SUPP_N',0)),  '',                           'Programme'),
        ('EAC_POST_SUPP_R',  'Post-EAC Re-suppression Rate %', _f(d.get('EAC_POST_SUPP_R',0)),  '',                           'Programme'),
    ]

    df_out = pd.DataFrame(rows, columns=[
        'Indicator', 'Description', 'Result', 'Annual Target', 'MER Frequency'
    ])

    # State breakdown sheets
    state_data = {
        'TX_CURR': d.get('TX_CURR_STATE', {}),
        'TX_NEW':  d.get('TX_NEW_STATE', {}),
        'HTS_TST': d.get('HTS_STATE', {}),
        'PrEP_NEW':d.get('PrEP_NEW_STATE', {}),
        'EAC':     d.get('EAC_STATE', {}),
    }

    with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
        wb = writer.book

        # ── Formats ────────────────────────────────────────────────────────
        hdr_fmt = wb.add_format({
            'bold': True, 'bg_color': '#1F4E79', 'font_color': 'white',
            'border': 1, 'font_name': 'Calibri', 'font_size': 11
        })
        num_fmt  = wb.add_format({'num_format': '#,##0', 'border': 1, 'font_name': 'Calibri'})
        pct_fmt  = wb.add_format({'num_format': '0.0"%"', 'border': 1, 'font_name': 'Calibri'})
        text_fmt = wb.add_format({'border': 1, 'font_name': 'Calibri'})
        grn_fmt  = wb.add_format({'bg_color': '#E6F2EB', 'border': 1, 'font_name': 'Calibri', 'num_format': '#,##0'})
        red_fmt  = wb.add_format({'bg_color': '#FDEAEA', 'border': 1, 'font_name': 'Calibri', 'num_format': '#,##0'})

        # ── DATA_INPUT sheet ───────────────────────────────────────────────
        ws = wb.add_worksheet('DATA_INPUT')
        writer.sheets['DATA_INPUT'] = ws

        ws.set_column('A:A', 20)
        ws.set_column('B:B', 40)
        ws.set_column('C:C', 15)
        ws.set_column('D:D', 15)
        ws.set_column('E:E', 15)

        headers = ['Indicator', 'Description', 'Result', 'Annual Target', 'MER Frequency']
        for col, h in enumerate(headers):
            ws.write(0, col, h, hdr_fmt)

        for row_idx, row in enumerate(rows, start=1):
            ind, desc, result, target, freq = row
            ws.write(row_idx, 0, ind, text_fmt)
            ws.write(row_idx, 1, desc, text_fmt)
            # Result — use pct format for % indicators
            if '%' in desc or ind in ('VL_SUPPRESSION','VL_COVERAGE','HTS_YIELD','EAC_POST_SUPP_R'):
                ws.write(row_idx, 2, result, pct_fmt)
            else:
                ws.write(row_idx, 2, result, num_fmt)
            ws.write(row_idx, 3, target if target != '' else '', num_fmt if target != '' else text_fmt)
            ws.write(row_idx, 4, freq, text_fmt)

        ws.freeze_panes(1, 0)

        # ── State Breakdown sheet ──────────────────────────────────────────
        ws2 = wb.add_worksheet('STATE_BREAKDOWN')
        writer.sheets['STATE_BREAKDOWN'] = ws2
        ws2.set_column('A:A', 20)
        ws2.set_column('B:D', 15)

        ws2.write(0, 0, 'Indicator', hdr_fmt)
        ws2.write(0, 1, 'Kebbi', hdr_fmt)
        ws2.write(0, 2, 'Sokoto', hdr_fmt)
        ws2.write(0, 3, 'Zamfara', hdr_fmt)

        for i, (ind, sdata) in enumerate(state_data.items(), start=1):
            ws2.write(i, 0, ind, text_fmt)
            ws2.write(i, 1, _n(sdata.get('Kebbi', 0)), num_fmt)
            ws2.write(i, 2, _n(sdata.get('Sokoto', 0)), num_fmt)
            ws2.write(i, 3, _n(sdata.get('Zamfara', 0)), num_fmt)

    buf.seek(0)
    return buf.read()
