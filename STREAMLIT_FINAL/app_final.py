"""
ACE3 PEPFAR MER Dashboard — v2
Health Systems Consult Limited (HSCL)
Kebbi | Sokoto | Zamfara
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import os, tempfile
from io import BytesIO
from ace3_engine import ACE3Engine
from narratives import generate_section_narrative, build_prompt
from charts import (treatment_cascade, progress_95, tx_curr_by_state, vl_performance,
                     hts_modality_yield, tx_ml_outcomes, q1_q2_comparison,
                     pmtct_cascade, tb_cascade, ahd_cascade, cxca_chart, sex_disagg)

st.set_page_config(page_title="ACE3 MER Dashboard", page_icon="📊", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
* { font-family: 'DM Sans', sans-serif; }
.block-container { padding-top: 1rem; }
.main-header { font-size: 2rem; font-weight: 700; color: #0A2342; letter-spacing: -0.5px; }
.sub-header { font-size: 0.95rem; color: #0E7C7B; font-weight: 500; margin-bottom: 1rem; }
.kpi-container { display: flex; gap: 12px; flex-wrap: wrap; margin: 1rem 0; }
.kpi-box { background: linear-gradient(135deg, #0A2342 0%, #156082 100%); border-radius: 12px; padding: 16px 20px; flex: 1; min-width: 130px; color: white; text-align: center; }
.kpi-box-alt { background: linear-gradient(135deg, #0E7C7B 0%, #17A550 100%); border-radius: 12px; padding: 16px 20px; flex: 1; min-width: 130px; color: white; text-align: center; }
.kpi-box-warn { background: linear-gradient(135deg, #E8611A 0%, #D72638 100%); border-radius: 12px; padding: 16px 20px; flex: 1; min-width: 130px; color: white; text-align: center; }
.kpi-val { font-size: 1.7rem; font-weight: 700; }
.kpi-label { font-size: 0.72rem; opacity: 0.9; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.5px; }
.narrative-box { background: #F0F7FF; border-radius: 10px; padding: 16px 20px; border-left: 4px solid #0E7C7B; margin: 12px 0; font-size: 0.9rem; color: #333; line-height: 1.6; }
.section-title { font-size: 1.3rem; font-weight: 700; color: #0A2342; margin: 1.2rem 0 0.5rem 0; border-bottom: 3px solid #0E7C7B; padding-bottom: 6px; display: inline-block; }
.period-badge { display: inline-block; background: #0A2342; color: white; padding: 4px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; margin-bottom: 10px; }
.stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

logo_path = os.path.join(os.path.dirname(__file__), "hscl_logo.png")
if os.path.exists(logo_path):
    st.image(logo_path, width=100)
st.markdown('<div class="main-header">ACE3 MER Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">HSCL — Kebbi · Sokoto · Zamfara · 37 Facilities</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📂 Data Upload")
    radet_f = st.file_uploader("RADET", type=["xlsx"], key="r")
    hts_f1 = st.file_uploader("HTS (file 1)", type=["xlsx","csv"], key="h1")
    hts_f2 = st.file_uploader("HTS (file 2)", type=["xlsx","csv"], key="h2")
    pmtct_hts_f = st.file_uploader("PMTCT-HTS", type=["xlsx"], key="ph")
    pmtct_mat_f = st.file_uploader("PMTCT Maternal", type=["xlsx"], key="pm")
    tb_f = st.file_uploader("TB Report", type=["xlsx"], key="tb")
    ahd_f = st.file_uploader("AHD Report", type=["xlsx"], key="ahd")
    vl_elig_f = st.file_uploader("VL Eligible File", type=["xlsx"], key="vle")
    st.markdown("---")
    api_key = st.text_input("🔑 Anthropic API Key", type="password")
    st.caption("ACE3 · HSCL · FY26")

if radet_f is None:
    st.markdown("---")
    st.info("👈 Upload at least the **RADET file** in the sidebar to begin.")
    st.stop()

@st.cache_data(show_spinner="⏳ Computing indicators...")
def run_engine(rb, h1b, h2b, phb, pmb, tbb, ahdb, vleb=None):
    e = ACE3Engine()
    e.load_radet(BytesIO(rb))
    for hb in [h1b, h2b]:
        if hb:
            try:
                e.load_hts(BytesIO(hb))
            except Exception:
                import io
                e.load_hts(pd.read_csv(io.BytesIO(hb), encoding='latin-1', low_memory=False))
    if phb: e.load_pmtct_hts(BytesIO(phb))
    if pmb: e.load_pmtct_mat(BytesIO(pmb))
    if tbb: e.load_tb(BytesIO(tbb))
    if ahdb: e.load_ahd(BytesIO(ahdb))
    if vleb: e.load_vl_eligible(BytesIO(vleb))
    return {'Q1': e.compute('Q1'), 'Q2': e.compute('Q2'), 'CUM': e.compute('CUM')}

rb = radet_f.read()
h1b = hts_f1.read() if hts_f1 else None
h2b = hts_f2.read() if hts_f2 else None
all_results = run_engine(rb, h1b, h2b,
    pmtct_hts_f.read() if pmtct_hts_f else None,
    pmtct_mat_f.read() if pmtct_mat_f else None,
    tb_f.read() if tb_f else None,
    ahd_f.read() if ahd_f else None,
    vl_elig_f.read() if vl_elig_f else None)

@st.cache_data
def make_charts(_cum, _q1, _q2):
    d = tempfile.mkdtemp()
    c = {}
    c['cascade'] = treatment_cascade(_cum, d)
    c['progress_95'] = progress_95(_cum, d)
    c['tx_curr_state'] = tx_curr_by_state(_cum, d)
    c['vl'] = vl_performance(_cum, d)
    c['hts'] = hts_modality_yield(_cum, d)
    c['ml'] = tx_ml_outcomes(_cum, d)
    c['q1q2'] = q1_q2_comparison(_q1, _q2, d)
    c['pmtct'] = pmtct_cascade(_cum, d)
    c['tb'] = tb_cascade(_cum, d)
    c['ahd'] = ahd_cascade(_cum, d)
    c['cxca'] = cxca_chart(_cum, d)
    c['sex'] = sex_disagg(_cum, d)
    return {k: v for k, v in c.items() if v}

charts = make_charts(all_results['CUM'], all_results['Q1'], all_results['Q2'])

def kc(label, value, style="kpi-box"):
    return f'<div class="{style}"><div class="kpi-val">{value}</div><div class="kpi-label">{label}</div></div>'

def kr(cards):
    return '<div class="kpi-container">' + ''.join(cards) + '</div>'

def img(key, cap=""):
    if key in charts: st.image(charts[key], use_container_width=True, caption=cap)

st.markdown("---")
period = st.radio("📅", ["Q1 (Oct–Dec 2025)", "Q2 (Jan–Mar 2026)", "Semi-Annual", "Q3 🔒", "Annual 🔒"], horizontal=True, index=2)
if "🔒" in period:
    st.warning("Available when data is loaded for this period.")
    st.stop()

qk = {'Q1 (Oct–Dec 2025)':'Q1','Q2 (Jan–Mar 2026)':'Q2','Semi-Annual':'CUM'}[period]
r = all_results[qk]
st.markdown(f'<span class="period-badge">{period}</span>', unsafe_allow_html=True)

h = r.get('HTS_TST',{}); pv = r.get('TX_PVLS',{}); pg = r.get('PROGRAMMATIC',{})
st.markdown(kr([kc("HTS Tested",f"{h.get('value',0):,}"), kc("HTS Positive",f"{h.get('pos',0):,}"),
    kc("TX_CURR",f"{r['TX_CURR']['value']:,}"), kc("TX_NEW",f"{r['TX_NEW']['value']:,}"),
    kc("VL Suppression",f"{pv.get('suppression',0)}%","kpi-box-alt"),
    kc("VL Coverage",f"{pv.get('coverage',0)}%","kpi-box-alt"),
    kc("IIT Rate",f"{pg.get('iit_rate',0)}%","kpi-box-warn")]), unsafe_allow_html=True)

tabs = st.tabs(["🔬 Testing","💊 Treatment","🧬 Viral Load","🤰 PMTCT","🫁 TB/HIV",
                "🔄 Retention","🩺 AHD","♀ CXCA","👶 Pediatric","📊 Q1 vs Q2","📝 Narrative","📥 Export"])

with tabs[0]:
    if h:
        st.markdown('<div class="section-title">HIV Testing Services</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="narrative-box">{generate_section_narrative("hts", r)}</div>', unsafe_allow_html=True)
        st.markdown(kr([kc("HTS_TST",f"{h.get('value',0):,}"),kc("HTS_POS",f"{h.get('pos',0):,}"),
            kc("Yield",f"{h.get('yield',0)}%","kpi-box-alt")]), unsafe_allow_html=True)
        img('hts','HTS by Modality and Positivity Yield')
    else: st.info("Upload HTS data.")

with tabs[1]:
    st.markdown('<div class="section-title">Treatment Cascade</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="narrative-box">{generate_section_narrative("treatment", r)}</div>', unsafe_allow_html=True)
    st.markdown(kr([kc("TX_CURR",f"{r['TX_CURR']['value']:,}"),kc("TX_NEW",f"{r['TX_NEW']['value']:,}"),
        kc("Male",f"{r['TX_CURR']['disagg'].get('Male',0):,}"),kc("Female",f"{r['TX_CURR']['disagg'].get('Female',0):,}"),
        kc("P+BF",f"{r['TX_CURR']['pregnant']+r['TX_CURR']['breastfeeding']}","kpi-box-alt")]), unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1: img('cascade','Treatment Cascade')
    with c2: img('tx_curr_state','TX_CURR by State')
    img('sex','Sex Disaggregation')

with tabs[2]:
    st.markdown('<div class="section-title">Viral Load</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="narrative-box">{generate_section_narrative("viral_load", r)}</div>', unsafe_allow_html=True)
    vle=r.get('VL_ELIGIBLE',{})
    st.markdown(kr([kc("TX_PVLS_D",f"{pv.get('d',0):,}"),kc("TX_PVLS_N",f"{pv.get('n',0):,}"),
        kc("Suppression",f"{pv.get('suppression',0)}%","kpi-box-alt"),kc("Unsuppressed",f"{pv.get('unsuppressed',0):,}","kpi-box-warn")]), unsafe_allow_html=True)
    img('vl','Viral Load Cascade and Rates')
    st.markdown(kr([kc("VL Eligible",f"{vle.get('eligible',0):,}"),kc("Sampled",f"{vle.get('sampled',0):,}"),
        kc("Rate",f"{vle.get('rate',0)}%","kpi-box-alt"),kc("Gap",f"{vle.get('gap',0):,}","kpi-box-warn")]), unsafe_allow_html=True)
    img('progress_95','95-95-95 Targets')

with tabs[3]:
    pm=r.get('PMTCT_STAT',{}); pa=r.get('PMTCT_ART',{})
    if pm:
        st.markdown('<div class="section-title">PMTCT</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="narrative-box">{generate_section_narrative("pmtct", r)}</div>', unsafe_allow_html=True)
        st.markdown(kr([kc("ANC Tested",f"{pm.get('n',0):,}"),kc("HIV+",f"{pm.get('pos',0)}"),
            kc("Positivity",f"{pm.get('positivity',0)}%","kpi-box-alt")]), unsafe_allow_html=True)
        img('pmtct','PMTCT Cascade')
    else: st.info("Upload PMTCT-HTS data.")

with tabs[4]:
    tb=r.get('TB_SCREEN',{}); tp=r.get('TPT',{})
    if tb:
        st.markdown('<div class="section-title">TB/HIV Integration</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="narrative-box">{generate_section_narrative("tb", r)}</div>', unsafe_allow_html=True)
        st.markdown(kr([kc("TB Screened",f"{tb.get('screened',0):,}"),kc("TB Positive",f"{tb.get('positive',0)}"),
            kc("TPT Started",f"{tp.get('started_radet',0):,}"),kc("TPT Coverage",f"{tp.get('coverage',0)}%","kpi-box-alt")]), unsafe_allow_html=True)
        img('tb','TB/HIV Cascade')
    else: st.info("Upload TB data.")

with tabs[5]:
    st.markdown('<div class="section-title">Retention</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="narrative-box">{generate_section_narrative("retention", r)}</div>', unsafe_allow_html=True)
    st.markdown(kr([kc("TX_ML",f"{r['TX_ML']['value']:,}","kpi-box-warn"),kc("TX_RTT",f"{r['TX_RTT']['value']:,}","kpi-box-alt"),
        kc("IIT Rate",f"{pg.get('iit_rate',0)}%","kpi-box-warn"),kc("RTT Rate",f"{pg.get('rtt_rate',0)}%","kpi-box-alt")]), unsafe_allow_html=True)
    img('ml','Treatment Interruption Outcomes')

with tabs[6]:
    ad=r.get('AHD',{})
    if ad:
        st.markdown('<div class="section-title">Advanced HIV Disease</div>', unsafe_allow_html=True)
        st.markdown(kr([kc("Screened",f"{ad.get('total',0):,}"),kc("AHD+",f"{ad.get('ahd_yes',0)}","kpi-box-warn"),
            kc("CD4",f"{ad.get('cd4_done',0):,}"),kc("TB-LAM",f"{ad.get('tblam_done',0)}")]), unsafe_allow_html=True)
        img('ahd','AHD Cascade')
    else: st.info("Upload AHD data.")

with tabs[7]:
    cx=r.get('CXCA',{})
    st.markdown('<div class="section-title">Cervical Cancer Screening</div>', unsafe_allow_html=True)
    st.markdown(kr([kc("Eligible",f"{cx.get('eligible',0):,}"),kc("Screened",f"{cx.get('screened',0):,}"),
        kc("Coverage",f"{cx.get('coverage',0)}%","kpi-box-alt")]), unsafe_allow_html=True)
    img('cxca','CXCA Screening')

with tabs[8]:
    st.markdown('<div class="section-title">Pediatric (&lt;15)</div>', unsafe_allow_html=True)
    dt=r['TX_CURR']['disagg']; dn=r['TX_NEW']['disagg']; dd=r['TX_PVLS']['disagg_d']; ddn=r['TX_PVLS']['disagg_n']
    ps=round(ddn.get('<15',0)/dd.get('<15',1)*100,1) if dd.get('<15',0)>0 else 0
    pp=round(dt.get('<15',0)/r['TX_CURR']['value']*100,1) if r['TX_CURR']['value']>0 else 0
    st.markdown(kr([kc("TX_CURR <15",f"{dt.get('<15',0):,}"),kc("% of Total",f"{pp}%"),
        kc("TX_NEW <15",f"{dn.get('<15',0):,}"),kc("VL Supp <15",f"{ps}%","kpi-box-alt")]), unsafe_allow_html=True)

with tabs[9]:
    st.markdown('<div class="section-title">Q1 vs Q2</div>', unsafe_allow_html=True)
    img('q1q2','Quarterly Comparison')
    q1r,q2r=all_results['Q1'],all_results['Q2']
    cp=pd.DataFrame({'Indicator':['TX_CURR','TX_NEW','TX_ML','TX_RTT','HTS_TST','HTS_POS','PMTCT'],
        'Q1':[q1r['TX_CURR']['value'],q1r['TX_NEW']['value'],q1r['TX_ML']['value'],q1r['TX_RTT']['value'],
              q1r.get('HTS_TST',{}).get('value',0),q1r.get('HTS_TST',{}).get('pos',0),q1r.get('PMTCT_STAT',{}).get('n',0)],
        'Q2':[q2r['TX_CURR']['value'],q2r['TX_NEW']['value'],q2r['TX_ML']['value'],q2r['TX_RTT']['value'],
              q2r.get('HTS_TST',{}).get('value',0),q2r.get('HTS_TST',{}).get('pos',0),q2r.get('PMTCT_STAT',{}).get('n',0)]})
    cp['Change']=cp['Q2']-cp['Q1']
    st.dataframe(cp, use_container_width=True, hide_index=True)

with tabs[10]:
    st.markdown('<div class="section-title">AI Narrative</div>', unsafe_allow_html=True)
    prompt=build_prompt(r,qk)
    with st.expander("View prompt"): st.code(prompt)
    if api_key:
        if st.button("🤖 Generate", type="primary"):
            with st.spinner("Generating..."):
                try:
                    import anthropic
                    msg=anthropic.Anthropic(api_key=api_key).messages.create(model="claude-sonnet-4-20250514",max_tokens=4000,messages=[{"role":"user","content":prompt}])
                    st.session_state['narrative']=msg.content[0].text
                except Exception as ex: st.error(f"{ex}")
        if 'narrative' in st.session_state: st.markdown(st.session_state['narrative'])
    else: st.warning("Add API key or copy prompt to Claude.ai")

with tabs[11]:
    st.markdown('<div class="section-title">Export</div>', unsafe_allow_html=True)
    buf=BytesIO()
    with pd.ExcelWriter(buf,engine='xlsxwriter') as w:
        rows=[]
        for qn in ['Q1','Q2','CUM']:
            rr=all_results[qn]
            rows.append({'Period':qn,'TX_CURR':rr['TX_CURR']['value'],'TX_NEW':rr['TX_NEW']['value'],
                'TX_PVLS_D':rr['TX_PVLS']['d'],'TX_PVLS_N':rr['TX_PVLS']['n'],
                'VL_%':rr['TX_PVLS']['suppression'],'TX_ML':rr['TX_ML']['value'],
                'HTS':rr.get('HTS_TST',{}).get('value',0),'HTS_POS':rr.get('HTS_TST',{}).get('pos',0),
                'PMTCT':rr.get('PMTCT_STAT',{}).get('n',0)})
        pd.DataFrame(rows).to_excel(w,sheet_name='Summary',index=False)
    buf.seek(0)
    st.download_button("📥 Excel Report",buf,file_name="ACE3_FY26.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",type="primary")

st.markdown("---")
st.markdown('<div style="text-align:center;color:#999;font-size:0.8rem;">ACE3 · HSCL · FY26</div>', unsafe_allow_html=True)
