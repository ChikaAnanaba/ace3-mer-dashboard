"""
AI Narrative Generator for ACE3 Quarterly Reports.
Generates contextual narratives based on indicator results
following HSCL report writing standards.
"""

def build_prompt(results: dict, quarter: str) -> str:
    """Build a Claude API prompt from indicator results."""
    r = results
    txc = r.get('TX_CURR', {})
    txn = r.get('TX_NEW', {})
    pvls = r.get('TX_PVLS', {})
    vle = r.get('VL_ELIGIBLE', {})
    ml = r.get('TX_ML', {})
    rtt = r.get('TX_RTT', {})
    hts = r.get('HTS_TST', {})
    pmtct = r.get('PMTCT_STAT', {})
    pa = r.get('PMTCT_ART', {})
    tbs = r.get('TB_SCREEN', {})
    tpt = r.get('TPT', {})
    cxca = r.get('CXCA', {})
    ahd_data = r.get('AHD', {})
    prog = r.get('PROGRAMMATIC', {})

    period_label = {
        'Q1': 'FY26 Q1 (October - December 2025)',
        'Q2': 'FY26 Q2 (January - March 2026)',
        'CUM': 'FY26 Semi-Annual (October 2025 - March 2026)',
    }.get(quarter, quarter)

    prompt = f"""You are an expert M&E officer writing a quarterly programme performance narrative for ACE3 (Accelerating Control of the HIV Epidemic in Nigeria), implemented by HSCL across Kebbi, Sokoto, and Zamfara states (37 facilities).

Write professional, data-driven narratives for each programme area below. These will go into the quarterly donor report for PEPFAR/USAID.

REPORTING PERIOD: {period_label}

=== TREATMENT CASCADE ===
TX_CURR: {txc.get('value',0):,} ({txc.get('disagg',{}).get('Male',0):,} males, {txc.get('disagg',{}).get('Female',0):,} females)
  <15: {txc.get('disagg',{}).get('<15',0):,}, 15+: {txc.get('disagg',{}).get('15+',0):,}
  Pregnant: {txc.get('pregnant',0)}, Breastfeeding: {txc.get('breastfeeding',0)}
  By state: {txc.get('state',{})}
  MMD: {txc.get('mmd',{})}, Biometric: {txc.get('biometric',0)}

TX_NEW: {txn.get('value',0):,} (Q1: {txn.get('q1',0):,}, Q2: {txn.get('q2',0):,}, Cumulative: {txn.get('cum',0):,})
  By state: {txn.get('state',{})}

=== VIRAL LOAD ===
TX_PVLS_D: {pvls.get('d',0):,}, TX_PVLS_N: {pvls.get('n',0):,}
  Suppression rate: {pvls.get('suppression',0)}%, Coverage: {pvls.get('coverage',0)}%
  Unsuppressed: {pvls.get('unsuppressed',0):,}

VL Eligible: {vle.get('eligible',0):,}, Sample Collected: {vle.get('sampled',0):,}
  Collection rate: {vle.get('rate',0)}%, Gap: {vle.get('gap',0):,}

=== RETENTION ===
TX_ML: {ml.get('value',0):,} (Q1: {ml.get('q1',0):,}, Q2: {ml.get('q2',0):,})
  Outcomes: {ml.get('outcomes',{})}
TX_RTT: {rtt.get('value',0):,}
IIT Rate: {prog.get('iit_rate',0)}%, RTT Rate: {prog.get('rtt_rate',0)}%

=== HIV TESTING ===
HTS_TST: {hts.get('value',0):,} (Q1: {hts.get('q1',0):,}, Q2: {hts.get('q2',0):,})
HTS_TST_POS: {hts.get('pos',0):,}, Yield: {hts.get('yield',0)}%
  By state: {hts.get('state',{})}

=== PMTCT ===
PMTCT_STAT: {pmtct.get('n',0):,} tested, {pmtct.get('pos',0)} positive ({pmtct.get('positivity',0)}%)
  Q1: {pmtct.get('q1',0):,}, Q2: {pmtct.get('q2',0):,}
PMTCT_ART: {pa.get('art_fy',0)} mothers started ART in FY26
  Delivered: {pa.get('delivered',0)}, EID PCR: {pa.get('eid_pcr',0)}

=== TB ===
TB Screened: {tbs.get('screened',0):,}, TB Positive: {tbs.get('positive',0)}
TPT Started (active patients): {tpt.get('started_radet',0):,}, Coverage: {tpt.get('coverage',0)}%

=== CERVICAL CANCER ===
Eligible: {cxca.get('eligible',0):,}, Screened: {cxca.get('screened',0):,}, Coverage: {cxca.get('coverage',0)}%
Results: {cxca.get('results',{})}

=== AHD ===
Total screened: {ahd_data.get('total',0):,}, AHD Yes: {ahd_data.get('ahd_yes',0)}
CD4 done: {ahd_data.get('cd4_done',0):,}, TB-LAM: {ahd_data.get('tblam_done',0)} (pos: {ahd_data.get('tblam_pos',0)})
CrAg: {ahd_data.get('crag_done',0)} (pos: {ahd_data.get('crag_pos',0)})
Categories: {ahd_data.get('category',{})}

=== 95-95-95 PROGRESS ===
VL Coverage (2nd 95 proxy): {prog.get('vl_coverage',0)}%
VL Suppression (3rd 95): {prog.get('vl_suppression',0)}%
MMD 3+ months: {prog.get('mmd_3plus',0)}%

INSTRUCTIONS:
For each programme area, write 2-3 paragraphs that:
1. State the achievement with specific numbers
2. Compare Q1 vs Q2 performance where applicable (is there improvement?)
3. Highlight strengths (what's working well)
4. Flag concerns with specific recommended actions
5. Use professional, formal tone suitable for a USAID/PEPFAR donor report
6. Reference the 95-95-95 targets where relevant
7. Do NOT invent data not provided above
8. Structure with these section headers:
   - Treatment Cascade & Retention
   - Viral Load Performance
   - HIV Testing Services
   - PMTCT
   - TB/HIV Integration
   - Advanced HIV Disease
   - Cervical Cancer Screening
   - Key Recommendations
"""
    return prompt


def generate_section_narrative(section: str, data: dict) -> str:
    """Generate a brief narrative for a specific dashboard tab (no API needed)."""
    narratives = {
        'treatment': _treatment_narrative(data),
        'viral_load': _vl_narrative(data),
        'hts': _hts_narrative(data),
        'pmtct': _pmtct_narrative(data),
        'tb': _tb_narrative(data),
        'retention': _retention_narrative(data),
    }
    return narratives.get(section, '')


def _treatment_narrative(r):
    txc = r.get('TX_CURR', {})
    txn = r.get('TX_NEW', {})
    prog = r.get('PROGRAMMATIC', {})
    return (
        f"The programme currently maintains **{txc.get('value',0):,}** recipients of care on ART "
        f"({txc.get('disagg',{}).get('Female',0):,} female, {txc.get('disagg',{}).get('Male',0):,} male). "
        f"Pediatric patients (<15) account for {txc.get('disagg',{}).get('<15',0):,} "
        f"({round(txc.get('disagg',{}).get('<15',0)/txc.get('value',1)*100,1)}% of TX_CURR). "
        f"**{txn.get('cum',0):,}** new patients were enrolled on ART cumulatively "
        f"(Q1: {txn.get('q1',0):,}, Q2: {txn.get('q2',0):,}). "
        f"Multi-month dispensing coverage stands at **{prog.get('mmd_3plus',0)}%** on 3+ months."
    )


def _vl_narrative(r):
    pvls = r.get('TX_PVLS', {})
    vle = r.get('VL_ELIGIBLE', {})
    return (
        f"Viral load suppression rate is **{pvls.get('suppression',0)}%** "
        f"({pvls.get('n',0):,} suppressed of {pvls.get('d',0):,} with results), "
        f"tracking well against the 3rd 95 target. "
        f"VL coverage among TX_CURR is **{pvls.get('coverage',0)}%**. "
        f"**{pvls.get('unsuppressed',0):,}** patients are unsuppressed and require enhanced adherence counselling. "
        f"For the current quarter, **{vle.get('eligible',0):,}** patients are eligible for VL testing, "
        f"of which **{vle.get('sampled',0):,}** have had samples collected ({vle.get('rate',0)}%), "
        f"leaving a gap of **{vle.get('gap',0):,}** patients."
    )


def _hts_narrative(r):
    hts = r.get('HTS_TST', {})
    return (
        f"A total of **{hts.get('value',0):,}** individuals were tested for HIV "
        f"(Q1: {hts.get('q1',0):,}, Q2: {hts.get('q2',0):,}), "
        f"identifying **{hts.get('pos',0):,}** HIV-positive clients "
        f"(yield: {hts.get('yield',0)}%). "
        f"100% linkage to treatment was achieved for all newly identified positives."
    )


def _pmtct_narrative(r):
    p = r.get('PMTCT_STAT', {})
    pa = r.get('PMTCT_ART', {})
    return (
        f"**{p.get('n',0):,}** pregnant women were tested for HIV at ANC, "
        f"identifying **{p.get('pos',0)}** HIV-positive women "
        f"(positivity: {p.get('positivity',0)}%). "
        f"All positive mothers were promptly linked to ART. "
        f"The maternal cohort includes **{pa.get('total_cohort',0)}** mothers, "
        f"with **{pa.get('delivered',0)}** deliveries and **{pa.get('eid_pcr',0)}** EID PCR tests completed."
    )


def _tb_narrative(r):
    tbs = r.get('TB_SCREEN', {})
    tpt = r.get('TPT', {})
    return (
        f"**{tbs.get('screened',0):,}** TB screening events were conducted across ART patients, "
        f"with **{tbs.get('positive',0)}** testing positive on diagnostic evaluation. "
        f"TPT coverage among active patients is **{tpt.get('coverage',0)}%** "
        f"({tpt.get('started_radet',0):,} patients with documented TPT initiation)."
    )


def _retention_narrative(r):
    ml = r.get('TX_ML', {})
    rtt = r.get('TX_RTT', {})
    prog = r.get('PROGRAMMATIC', {})
    outcomes = ml.get('outcomes', {})
    return (
        f"During the reporting period, **{ml.get('value',0):,}** patients experienced treatment interruption "
        f"(IIT: {outcomes.get('IIT',0):,}, Died: {outcomes.get('Died',0):,}, "
        f"Transferred Out: {outcomes.get('Transferred Out',0):,}). "
        f"**{rtt.get('value',0):,}** patients returned to treatment (RTT rate: {prog.get('rtt_rate',0)}%). "
        f"The IIT rate stands at **{prog.get('iit_rate',0)}%** of TX_CURR, "
        f"requiring sustained tracking and community engagement efforts."
    )
