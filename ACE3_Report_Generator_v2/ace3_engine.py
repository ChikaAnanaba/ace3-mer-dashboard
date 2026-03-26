"""
ACE3 MER Indicator Engine — Final Build
All logic confirmed against Power BI DAX.

PEPFAR FY26: Oct 1 2025 – Sep 30 2026
  Q1: Oct 1 – Dec 31
  Q2: Jan 1 – Mar 31 (current semi-annual submission)
  Q3: Apr 1 – Jun 30 (placeholder)
  Q4: Jul 1 – Sep 30 (placeholder)
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore')

FY_START = pd.to_datetime('2025-10-01')
Q1_START = pd.to_datetime('2025-10-01')
Q1_END = pd.to_datetime('2025-12-31')
Q2_START = pd.to_datetime('2026-01-01')
Q2_END = pd.to_datetime('2026-03-31')
INVALID = ['Invalid - Duplicates', 'Invalid - Nonexistent', 'Invalid - Biometrical Naive']
ACTIVE = ['Active', 'Active Restart']


def parse_dates(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors='coerce')
    return df


def clean_str(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()
    return df


def disagg(df, sex_col='Sex', age_col='_age'):
    """Standard disaggregation: M/F, <15/15+, Pregnant/BF"""
    r = {}
    if age_col in df.columns:
        r['<15_M'] = int(((df[age_col] < 15) & (df[sex_col] == 'Male')).sum())
        r['<15_F'] = int(((df[age_col] < 15) & (df[sex_col] == 'Female')).sum())
        r['<15'] = r['<15_M'] + r['<15_F']
        r['15+_M'] = int(((df[age_col] >= 15) & (df[sex_col] == 'Male')).sum())
        r['15+_F'] = int(((df[age_col] >= 15) & (df[sex_col] == 'Female')).sum())
        r['15+'] = r['15+_M'] + r['15+_F']
    r['Male'] = int((df[sex_col] == 'Male').sum())
    r['Female'] = int((df[sex_col] == 'Female').sum())
    r['Total'] = len(df)
    return r


def by_state(df, col='State'):
    return dict(sorted(df.groupby(col).size().to_dict().items()))


class ACE3Engine:
    """Compute all ACE3/PEPFAR indicators from line lists."""

    def __init__(self):
        self.radet = None
        self.hts = None
        self.pmtct_hts = None
        self.pmtct_mat = None
        self.tb = None
        self.ahd = None
        self.vl_eligible_df = None
        self.results = {}


    def load_vl_eligible(self, src):
        if isinstance(src, pd.DataFrame):
            df = src
        else:
            df = pd.read_excel(src)
        df['Patient ID'] = df['Patient ID'].astype(str).str.strip()
        for c in ['VL_Q1_Flag', 'VL_Q2_Flag', 'VL_Q3_Flag', 'VL_Q4_Flag',
                   'FY26_Q1_samples_collected_Number', 'VL_Sampled_Q1_Flag', 'IsActiveValid']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
        self.vl_eligible_df = df
        return self

    # ── Loaders ──────────────────────────────────────────────

    def load_radet(self, src):
        if isinstance(src, pd.DataFrame):
            df = src
        else:
            df = pd.read_excel(src, sheet_name="radet")
        df = parse_dates(df, [
            'ART Start Date (yyyy-mm-dd)', 'Last Pickup Date (yyyy-mm-dd)',
            'Date of Current ViralLoad Result Sample (yyyy-mm-dd)',
            'Date of Current Viral Load (yyyy-mm-dd)',
            'Date of Current ART Status', 'Date of Start of Current ART Regimen',
            'Date Biometrics Enrolled (yyyy-mm-dd)',
            'Date of Viral Load Sample Collection (yyyy-mm-dd)',
            'Date of Viral Load Eligibility Status',
            'Date of TB Screening (yyyy-mm-dd)',
            'Date of TPT Start (yyyy-mm-dd)',
            'Date of Cervical Cancer Screening (yyyy-mm-dd)',
        ])
        df = clean_str(df, ['Current ART Status', 'Client Verification Outcome', 'Sex',
                            'Pregnancy Status', 'Current Regimen Line',
                            'Viral Load Eligibility Status', 'TB status',
                            'TB Screening Type', 'TPT Completion status',
                            'Result of Cervical Cancer Screening'])
        df['_vl'] = pd.to_numeric(df['Current Viral Load (c/ml)'], errors='coerce')
        df['_age'] = pd.to_numeric(df['Age'], errors='coerce')
        df['_arv'] = pd.to_numeric(df['Months of ARV Refill'], errors='coerce')
        self.radet = df
        self._valid = df[~df['Current ART Status'].isin(INVALID)].copy()
        self._txc = self._valid[
            (self._valid['Current ART Status'].isin(ACTIVE)) &
            (self._valid['Client Verification Outcome'].str.lower() == 'valid')
        ].copy()
        return self

    def load_hts(self, src, encoding='latin-1'):
        if isinstance(src, pd.DataFrame):
            df = src
        elif isinstance(src, str):
            if src.endswith('.csv'):
                df = pd.read_csv(src, encoding=encoding, low_memory=False)
            else:
                df = pd.read_excel(src)
        else:
            # BytesIO — try excel first, then csv
            try:
                df = pd.read_excel(src)
            except Exception:
                src.seek(0)
                try:
                    df = pd.read_csv(src, encoding='latin-1', low_memory=False)
                except Exception:
                    src.seek(0)
                    df = pd.read_csv(src, encoding='latin-1', low_memory=False, sep=None, engine='python')
        # Handle date formats
        dcol = 'Date Of HIV Testing (yyyy-mm-dd)'
        if dcol in df.columns:
            # Try standard first, then dayfirst
            df['_td'] = pd.to_datetime(df[dcol], errors='coerce')
            if df['_td'].isna().sum() > len(df) * 0.5:
                df['_td'] = pd.to_datetime(df[dcol], errors='coerce', dayfirst=True)
        df = clean_str(df, ['Final HIV Test Result', 'Sex', 'Modality', 'Testing Setting'])
        df['_age'] = pd.to_numeric(df.get('Age', pd.Series(dtype=float)), errors='coerce')
        if self.hts is None:
            self.hts = df
        else:
            common = list(set(self.hts.columns) & set(df.columns))
            self.hts = pd.concat([self.hts[common], df[common]], ignore_index=True)
        return self

    def load_pmtct_hts(self, src):
        if isinstance(src, pd.DataFrame):
            df = src
        else:
            df = pd.read_excel(src, sheet_name="Pmtct-hts")
        df = parse_dates(df, ['Date Tested for HIV'])
        df = clean_str(df, ['HIV Test Result'])
        df['_age'] = pd.to_numeric(df.get('Age', pd.Series(dtype=float)), errors='coerce')
        self.pmtct_hts = df
        return self

    def load_pmtct_mat(self, src):
        if isinstance(src, pd.DataFrame):
            df = src
        else:
            df = pd.read_excel(src, sheet_name="pmtct-maternal-cohort")
        art_col = [c for c in df.columns if 'ART Start' in c][0] if any('ART Start' in c for c in df.columns) else None
        if art_col:
            df[art_col] = pd.to_datetime(df[art_col], errors='coerce')
            df['_mat_art_date'] = df[art_col]
        for c in ['Date of Delivery', 'Date of Index ANC Registration',
                   'Date of First DNA PCR Sample collection']:
            if c in df.columns:
                df[c] = pd.to_datetime(df[c], errors='coerce')
        self.pmtct_mat = df
        return self

    def load_tb(self, src):
        if isinstance(src, pd.DataFrame):
            df = src
        else:
            df = pd.read_excel(src, sheet_name="tb")
        df = parse_dates(df, ['Date of TB Screening', 'Date of TPT Start (yyyy-mm-dd)',
                              'TPT completion date', 'Date of TB Treatment'])
        df = clean_str(df, ['TB Status', 'TPT completion status', 'TB Screening Type',
                            'TB Diagnostic Result', 'TPT Type'])
        self.tb = df
        return self

    def load_ahd(self, src):
        if isinstance(src, pd.DataFrame):
            df = src
        else:
            df = pd.read_excel(src, sheet_name="ahd")
        for c in ['ART start date', 'Date of HIV diagnosis', 'Date of last visit']:
            if c in df.columns:
                df[c] = pd.to_datetime(df[c], errors='coerce')
        df = clean_str(df, ['AHD Status', 'Category', 'WHO Staging', 'Current Status',
                            'TB_LAM', 'Serum crAg', 'CSF crAg'])
        self.ahd = df
        return self

    # ── Compute All ──────────────────────────────────────────

    def compute(self, quarter='Q2'):
        """Compute all indicators. quarter = 'Q1', 'Q2', 'CUM' (cumulative)"""
        r = {}

        if quarter == 'Q1':
            q_start, q_end = Q1_START, Q1_END
        elif quarter == 'Q2':
            q_start, q_end = Q2_START, Q2_END
        else:  # CUM
            q_start, q_end = FY_START, Q2_END

        # ── TX_CURR (snapshot — same regardless of quarter) ──
        txc = self._txc
        preg = txc[txc['Pregnancy Status'] == 'Pregnant']
        bf = txc[txc['Pregnancy Status'] == 'Breastfeeding']

        r['TX_CURR'] = {
            'value': len(txc), 'disagg': disagg(txc), 'state': by_state(txc),
            'pregnant': len(preg), 'breastfeeding': len(bf), 'pbf': len(preg) + len(bf),
            'mmd': {
                '<3mo': int((txc['_arv'] < 3).sum()),
                '3-5mo': int(((txc['_arv'] >= 3) & (txc['_arv'] < 6)).sum()),
                '6+mo': int((txc['_arv'] >= 6).sum()),
            },
            'biometric': int(txc['Date Biometrics Enrolled (yyyy-mm-dd)'].notna().sum()),
            'no_biometric': int(txc['Date Biometrics Enrolled (yyyy-mm-dd)'].isna().sum()),
        }

        # ── TX_NEW (cumulative from FY start always) ──
        txn_cum = self._valid[
            (self._valid['ART Start Date (yyyy-mm-dd)'].notna()) &
            (self._valid['ART Start Date (yyyy-mm-dd)'] >= FY_START) &
            (self._valid['Date of Start of Current ART Regimen'].notna()) &
            (self._valid['Date of Start of Current ART Regimen'] >= FY_START)
        ]
        txn_q1 = txn_cum[txn_cum['ART Start Date (yyyy-mm-dd)'] <= Q1_END]
        txn_q2 = txn_cum[txn_cum['ART Start Date (yyyy-mm-dd)'] >= Q2_START]

        if quarter == 'Q1':
            txn = txn_q1
        elif quarter == 'Q2':
            txn = txn_q2
        else:
            txn = txn_cum

        r['TX_NEW'] = {
            'value': len(txn), 'cum': len(txn_cum),
            'q1': len(txn_q1), 'q2': len(txn_q2),
            'disagg': disagg(txn), 'state': by_state(txn),
        }

        # ── TX_PVLS (PBI formula: both sample AND result date within 365 days) ──
        # Anchored to Q2 end for final submission; during quarter uses Q2_END
        vl_anchor = Q2_END
        vl_365 = vl_anchor - pd.Timedelta(days=365)
        vl_result_col = 'Date of Current ViralLoad Result Sample (yyyy-mm-dd)'
        vl_sample_col = 'Date of Viral Load Sample Collection (yyyy-mm-dd)'

        pvd = txc[
            (txc[vl_result_col].notna()) &
            (txc[vl_result_col] >= vl_365) &
            (txc[vl_sample_col].notna()) &
            (txc[vl_sample_col] >= vl_365) &
            (txc['_vl'].notna())
        ]
        pvn = pvd[pvd['_vl'] < 1000]

        r['TX_PVLS'] = {
            'd': len(pvd), 'n': len(pvn),
            'suppression': round(len(pvn) / len(pvd) * 100, 1) if len(pvd) > 0 else 0,
            'coverage': round(len(pvd) / len(txc) * 100, 1) if len(txc) > 0 else 0,
            'unsuppressed': len(pvd) - len(pvn),
            'disagg_d': disagg(pvd), 'disagg_n': disagg(pvn),
            'state_d': by_state(pvd), 'state_n': by_state(pvn),
        }

        # ── VL ELIGIBLE (from uploaded VL eligible file, or RADET fallback) ──
        if self.vl_eligible_df is not None:
            vle = self.vl_eligible_df.copy()
            if quarter == 'Q1':
                elig = vle[vle['VL_Q1_Flag'] == 1]
                if 'FY26_Q1_samples_collected_Number' in vle.columns:
                    collected = elig[elig['FY26_Q1_samples_collected_Number'] == 1]
                else:
                    collected = pd.DataFrame()
                sampled_count = len(collected)
            elif quarter == 'Q2':
                elig = vle[vle['VL_Q2_Flag'] == 1]
                sc = 'VL Sample Date (from FY26)_2'
                if sc in vle.columns:
                    vle[sc] = pd.to_datetime(vle[sc], errors='coerce')
                    collected = elig[(elig[sc].notna()) &
                                     (elig[sc] >= pd.to_datetime('2025-12-01')) &
                                     (elig[sc] <= Q2_END)]
                else:
                    collected = pd.DataFrame()
                sampled_count = len(collected)
            else:  # CUM = semi-annual
                q1e = vle[vle['VL_Q1_Flag'] == 1]
                q2e = vle[vle['VL_Q2_Flag'] == 1]
                elig = pd.concat([q1e, q2e]).drop_duplicates(subset='Patient ID')
                # Q1 collected
                if 'FY26_Q1_samples_collected_Number' in vle.columns:
                    q1c = set(q1e[q1e['FY26_Q1_samples_collected_Number'] == 1]['Patient ID'].values)
                else:
                    q1c = set()
                # Q2 collected
                sc = 'VL Sample Date (from FY26)_2'
                if sc in vle.columns:
                    vle[sc] = pd.to_datetime(vle[sc], errors='coerce')
                    q2c = set(q2e[(q2e[sc].notna()) &
                                   (q2e[sc] >= pd.to_datetime('2025-12-01')) &
                                   (q2e[sc] <= Q2_END)]['Patient ID'].values)
                else:
                    q2c = set()
                sampled_count = len(q1c | q2c)

            elig_count = len(elig)
            vl_gap = elig_count - sampled_count
            vl_rate = round(sampled_count / elig_count * 100, 1) if elig_count > 0 else 0

            r['VL_ELIGIBLE'] = {
                'eligible': elig_count, 'sampled': sampled_count,
                'rate': vl_rate, 'gap': vl_gap,
                'q1_eligible': int((vle['VL_Q1_Flag'] == 1).sum()),
                'q2_eligible': int((vle['VL_Q2_Flag'] == 1).sum()),
                'q3_eligible': int((vle['VL_Q3_Flag'] == 1).sum()),
                'q4_eligible': int((vle['VL_Q4_Flag'] == 1).sum()),
                'annual_eligible': int((vle[['VL_Q1_Flag','VL_Q2_Flag','VL_Q3_Flag','VL_Q4_Flag']].sum(axis=1) > 0).sum()),
            }
        else:
            # Fallback: estimate from RADET
            last_samp_col = 'Date of Current ViralLoad Result Sample (yyyy-mm-dd)'
            new_samp_col = 'Date of Viral Load Sample Collection (yyyy-mm-dd)'
            q_end = Q2_END if quarter != 'Q1' else Q1_END
            txc_elig = txc.copy()
            txc_elig['_vl_anniversary'] = txc_elig[last_samp_col] + pd.Timedelta(days=365)
            has_prior = txc_elig[last_samp_col].notna()
            vl_due = txc_elig[has_prior & (txc_elig['_vl_anniversary'] < q_end + pd.Timedelta(days=1))]
            no_vl_ever = txc_elig[~has_prior]
            vl_eligible = pd.concat([vl_due, no_vl_ever])
            if quarter == 'Q2':
                samp_start, samp_end = Q2_START, Q2_END
            elif quarter == 'Q1':
                samp_start, samp_end = Q1_START, Q1_END
            else:
                samp_start, samp_end = FY_START, Q2_END
            vl_sampled = vl_eligible[
                (vl_eligible[new_samp_col].notna()) &
                (vl_eligible[new_samp_col] >= samp_start) &
                (vl_eligible[new_samp_col] <= samp_end)]
            vl_gap = len(vl_eligible) - len(vl_sampled)
            vl_rate = round(len(vl_sampled) / len(vl_eligible) * 100, 1) if len(vl_eligible) > 0 else 0
            r['VL_ELIGIBLE'] = {
                'eligible': len(vl_eligible), 'sampled': len(vl_sampled),
                'rate': vl_rate, 'gap': vl_gap,
                'q1_eligible': 0, 'q2_eligible': 0,
                'q3_eligible': 0, 'q4_eligible': 0, 'annual_eligible': 0,
            }

        # ── TX_ML / TX_RTT ──
        sd = self._valid['Date of Current ART Status']
        non_active = ['IIT', 'Died', 'Transferred Out', 'Stopped Treatment']

        ml_cum = self._valid[
            (self._valid['Current ART Status'].isin(non_active)) &
            (sd >= FY_START) & (sd <= Q2_END)
        ]
        ml_q1 = ml_cum[sd <= Q1_END]
        ml_q2 = ml_cum[sd >= Q2_START]
        ml = ml_cum if quarter == 'CUM' else (ml_q1 if quarter == 'Q1' else ml_q2)

        rtt_cum = self._valid[
            (self._valid['Current ART Status'] == 'Active Restart') &
            (sd >= FY_START) & (sd <= Q2_END)
        ]
        rtt_q1 = rtt_cum[sd <= Q1_END]
        rtt_q2 = rtt_cum[sd >= Q2_START]
        rtt = rtt_cum if quarter == 'CUM' else (rtt_q1 if quarter == 'Q1' else rtt_q2)

        r['TX_ML'] = {
            'value': len(ml), 'cum': len(ml_cum), 'q1': len(ml_q1), 'q2': len(ml_q2),
            'outcomes': ml['Current ART Status'].value_counts().to_dict(),
            'state': by_state(ml), 'disagg': disagg(ml),
        }
        r['TX_RTT'] = {
            'value': len(rtt), 'cum': len(rtt_cum), 'q1': len(rtt_q1), 'q2': len(rtt_q2),
            'state': by_state(rtt), 'disagg': disagg(rtt),
        }

        # ── HTS_TST ──
        if self.hts is not None:
            hts_cum = self.hts[(self.hts['_td'].notna()) & (self.hts['_td'] >= FY_START)]
            hts_q1 = hts_cum[hts_cum['_td'] <= Q1_END]
            hts_q2 = hts_cum[hts_cum['_td'] >= Q2_START]
            h = hts_cum if quarter == 'CUM' else (hts_q1 if quarter == 'Q1' else hts_q2)
            hp = h[h['Final HIV Test Result'] == 'Positive']

            mod = h['Modality'].value_counts().to_dict() if 'Modality' in h.columns else {}
            # Yield by modality
            mod_yield = {}
            for m, cnt in mod.items():
                pos = int((h[h['Modality'] == m]['Final HIV Test Result'] == 'Positive').sum())
                mod_yield[m] = {'tested': cnt, 'pos': pos,
                                'yield': round(pos / cnt * 100, 2) if cnt > 0 else 0}

            st_col = 'State Of Residence' if 'State Of Residence' in h.columns else 'State'
            r['HTS_TST'] = {
                'value': len(h), 'pos': len(hp), 'cum': len(hts_cum),
                'q1': len(hts_q1), 'q2': len(hts_q2),
                'yield': round(len(hp) / len(h) * 100, 2) if len(h) > 0 else 0,
                'modality': mod_yield,
                'disagg': disagg(h), 'disagg_pos': disagg(hp),
                'state': by_state(h, st_col), 'state_pos': by_state(hp, st_col),
            }

        # ── PMTCT_STAT ──
        if self.pmtct_hts is not None:
            pn_cum = self.pmtct_hts[
                (self.pmtct_hts['Date Tested for HIV'].notna()) &
                (self.pmtct_hts['Date Tested for HIV'] >= FY_START)
            ]
            pn_q1 = pn_cum[pn_cum['Date Tested for HIV'] <= Q1_END]
            pn_q2 = pn_cum[pn_cum['Date Tested for HIV'] >= Q2_START]
            pn = pn_cum if quarter == 'CUM' else (pn_q1 if quarter == 'Q1' else pn_q2)
            pp = pn[pn['HIV Test Result'] == 'Positive']

            # modality breakdown
            mod_anc1 = len(pn[pn.get('Modality', pd.Series(dtype=str)).str.contains('ANC1 Only', na=False)]) if 'Modality' in pn.columns else len(pn)
            mod_post = len(pn[pn.get('Modality', pd.Series(dtype=str)).str.contains('Post ANC1', na=False)]) if 'Modality' in pn.columns else 0
            mod_bf   = len(pn[pn.get('Modality', pd.Series(dtype=str)).str.contains('Breastfeeding', na=False)]) if 'Modality' in pn.columns else 0

            r['PMTCT_STAT'] = {
                'n': len(pn), 'pos': len(pp), 'cum': len(pn_cum),
                'q1': len(pn_q1), 'q2': len(pn_q2),
                'positivity': round(len(pp) / len(pn) * 100, 3) if len(pn) > 0 else 0,
                'state': by_state(pn),
                'anc1': mod_anc1, 'post_anc': mod_post, 'breastfeeding': mod_bf,
            }

        # ── PMTCT_ART ──
        if self.pmtct_mat is not None and '_mat_art_date' in self.pmtct_mat.columns:
            pa = self.pmtct_mat[
                (self.pmtct_mat['_mat_art_date'].notna()) &
                (self.pmtct_mat['_mat_art_date'] >= FY_START)
            ]
            delivered = self.pmtct_mat[self.pmtct_mat.get('Date of Delivery', pd.Series(dtype='datetime64[ns]')).notna()]
            pcr_col = 'Date of First DNA PCR Sample collection'
            pcr = self.pmtct_mat[self.pmtct_mat[pcr_col].notna()] if pcr_col in self.pmtct_mat.columns else pd.DataFrame()
            r['PMTCT_ART'] = {
                'art_fy': len(pa), 'total_cohort': len(self.pmtct_mat),
                'delivered': len(delivered), 'eid_pcr': len(pcr),
            }

        # ── TB SCREENED (rows — your DAX) ──
        if self.tb is not None:
            tbs = self.tb[
                (self.tb['TB Screening Type'].astype(str).str.len() > 0) &
                (~self.tb['TB Screening Type'].isin(['nan', ''])) &
                (self.tb['Date of TB Screening'].notna()) &
                (self.tb['Date of TB Screening'] >= FY_START)
            ]
            tbs_pos = tbs[tbs['TB Diagnostic Result'] == 'Positive']

            r['TB_SCREEN'] = {
                'screened': len(tbs), 'positive': len(tbs_pos),
                'state': by_state(tbs),
            }

            # TPT — unique active patients with TPT Type in TB report
            active_pids = set(
                self._valid[self._valid['Current ART Status'].isin(ACTIVE)]['Patient ID']
                .astype(str).str.strip().str.upper().values
            )
            self.tb['_pid'] = self.tb['Patient ID'].astype(str).str.strip().str.upper()
            tb_tpt = self.tb[
                (self.tb['_pid'] != '') & (self.tb['_pid'] != 'NAN') &
                (self.tb['_pid'].isin(active_pids)) &
                (self.tb['TPT Type'].notna()) &
                (~self.tb['TPT Type'].isin(['', 'nan']))
            ]
            tpt_unique = tb_tpt['_pid'].nunique()

            # Also from RADET
            radet_tpt = self._txc[self._txc['Date of TPT Start (yyyy-mm-dd)'].notna()]
            tpt_coverage = round(len(radet_tpt) / len(txc) * 100, 1) if len(txc) > 0 else 0

            r['TPT'] = {
                'started_tb': tpt_unique,
                'started_radet': len(radet_tpt),
                'coverage': tpt_coverage,
            }

        # ── CXCA ──
        elig_cxca = txc[(txc['Sex'] == 'Female') & (txc['_age'] >= 15)]
        scrn_cxca = elig_cxca[elig_cxca['Date of Cervical Cancer Screening (yyyy-mm-dd)'].notna()]
        cxca_results = scrn_cxca['Result of Cervical Cancer Screening'].value_counts().to_dict() if len(scrn_cxca) > 0 else {}

        r['CXCA'] = {
            'eligible': len(elig_cxca), 'screened': len(scrn_cxca),
            'coverage': round(len(scrn_cxca) / len(elig_cxca) * 100, 1) if len(elig_cxca) > 0 else 0,
            'results': cxca_results,
        }

        # ── AHD ──
        if self.ahd is not None:
            a = self.ahd
            cd4 = a[a['Visitect CD4 Count'].notna() & (a['Visitect CD4 Count'].astype(str).str.strip() != '')]
            tblam = a[a['TB_LAM'].notna() & (~a['TB_LAM'].isin(['', 'nan']))]
            tblam_p = a[a['TB_LAM'].str.lower().str.contains('pos', na=False)]
            crag = a[a['Serum crAg'].notna() & (~a['Serum crAg'].isin(['', 'nan']))]
            crag_p = a[a['Serum crAg'].str.lower().str.contains('pos', na=False)]

            r['AHD'] = {
                'total': len(a),
                'ahd_yes': int((a['AHD Status'] == 'Yes').sum()),
                'ahd_no': int((a['AHD Status'] == 'No').sum()),
                'category': a['Category'].value_counts().to_dict(),
                'cd4_done': len(cd4),
                'tblam_done': len(tblam), 'tblam_pos': len(tblam_p),
                'crag_done': len(crag), 'crag_pos': len(crag_p),
                'state': by_state(a),
                'who_staging': a['WHO Staging'].value_counts().to_dict(),
            }

        # ── PROGRAMMATIC ──
        iit = len(ml[ml['Current ART Status'] == 'IIT']) if len(ml) > 0 else 0
        r['PROGRAMMATIC'] = {
            'vl_coverage': r['TX_PVLS']['coverage'],
            'vl_suppression': r['TX_PVLS']['suppression'],
            'iit_rate': round(iit / len(txc) * 100, 1) if len(txc) > 0 else 0,
            'rtt_rate': round(len(rtt) / iit * 100, 1) if iit > 0 else 0,
            'linkage': round(len(txn) / r.get('HTS_TST', {}).get('pos', 1) * 100, 1)
                       if r.get('HTS_TST', {}).get('pos', 0) > 0 else 0,
            'mmd_3plus': round((r['TX_CURR']['mmd']['3-5mo'] + r['TX_CURR']['mmd']['6+mo']) / len(txc) * 100, 1)
                         if len(txc) > 0 else 0,
            'testing_yield': r.get('HTS_TST', {}).get('yield', 0),
        }

        self.results[quarter] = r
        return r
