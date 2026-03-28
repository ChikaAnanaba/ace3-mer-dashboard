"""
ACE3 Programme Report Generator — v4
95-95-95 tab flow · Q1→Q4 quarterly trend · 3 states: Kebbi · Sokoto · Zamfara
"""
import io, traceback
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title='ACE3 Report Generator',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded'
)

from assembler import assemble, _build_semi
from excel_export import generate_excel
from html_reports import build_dashboard, build_narrative, build_talking_points
from targets import INDICATOR_META

STATES = ['Kebbi', 'Sokoto', 'Zamfara']
STATE_COLOURS = {'Kebbi': '#1F4E79', 'Sokoto': '#2E75B6', 'Zamfara': '#4A90C4'}
PALETTE = ['#1F4E79', '#2E75B6', '#4A90C4', '#1A6632', '#BA0C2F', '#C87000', '#0E7490', '#888']

CHART_CFG = dict(paper_bgcolor='white', plot_bgcolor='white',
                 font=dict(family='IBM Plex Sans, sans-serif', size=11, color='#0F172A'),
                 margin=dict(t=48, b=28, l=12, r=12))

def _colours(n): return [PALETTE[i % len(PALETTE)] for i in range(n)]
def _pct(n, d, dec=1): return round(n/d*100, dec) if d else 0
def _n(v): return f"{int(round(float(v))):,}" if isinstance(v, (int, float)) else '—'
def _p(v, dec=1): return f"{float(v):.{dec}f}%" if v is not None else '—'

def _bar(fig, x, y, name='', colour=None, orientation='v', show_text=True):
    kwargs = dict(name=name, marker_color=colour or PALETTE[0],
                  texttemplate='%{y:,.0f}' if orientation=='v' else '%{x:,.0f}',
                  textposition='outside' if show_text else 'none',
                  textfont=dict(size=10))
    if orientation == 'v':
        fig.add_trace(go.Bar(x=x, y=y, **kwargs))
    else:
        fig.add_trace(go.Bar(y=x, x=y, orientation='h', **kwargs))
    return fig

def _chart_base(title='', height=300):
    fig = go.Figure()
    fig.update_layout(**CHART_CFG, title=dict(text=title, font=dict(size=12, weight='bold')),
                      height=height, showlegend=False)
    fig.update_xaxes(showgrid=False, linecolor='#E2E8F0')
    fig.update_yaxes(gridcolor='#F1F5F9', tickformat=',')
    return fig

def _kpi_card(label, value, sub='', colour='#1F4E79', bg='#EBF3FB'):
    return f"""<div style="background:{bg};border-top:3px solid {colour};padding:14px 12px;text-align:center;min-width:0">
  <div style="font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#64748B;margin-bottom:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{label}</div>
  <div style="font-size:26px;font-weight:700;font-family:'IBM Plex Mono',monospace;color:{colour};line-height:1">{value}</div>
  {'<div style="font-size:10px;color:#64748B;margin-top:5px">'+sub+'</div>' if sub else ''}
</div>"""

# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif!important;}
.main{background:#F0F4F8;}
.block-container{padding-top:1rem!important;}
.stButton>button{background:#1F4E79;color:white;border:none;border-radius:2px;font-weight:600;
  font-size:13px;padding:10px 28px;width:100%;transition:background .2s;}
.stButton>button:hover{background:#2E75B6;}
.stTabs [data-baseweb="tab"]{font-size:11.5px;font-weight:600;padding:8px 14px;}
.stTabs [aria-selected="true"]{color:#1F4E79!important;border-bottom-color:#1F4E79!important;}
div[data-testid="metric-container"]{background:white;border:1px solid #CBD5E1;
  padding:12px;border-left:4px solid #1F4E79;}
.semi-warn{background:#FEF3E2;border-left:4px solid #C87000;padding:10px 14px;
  font-size:11px;color:#7B4500;margin:8px 0;}
</style>""", unsafe_allow_html=True)

# ── session state ────────────────────────────────────────────────────────────
for k in ['results','outputs_ready','quarter_mode','period','quarter_label']:
    if k not in st.session_state:
        st.session_state[k] = None
if 'outputs_ready' not in st.session_state:
    st.session_state.outputs_ready = False

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div style="background:linear-gradient(135deg,#0F2942,#1F4E79);color:white;
    padding:16px;margin:-1rem -1rem 1rem;border-bottom:3px solid #BA0C2F">
      <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,.5);margin-bottom:4px">Programme Report System</div>
      <div style="font-size:17px;font-weight:700">ACE3 Generator</div>
      <div style="font-size:10px;color:rgba(255,255,255,.6);margin-top:3px">HSCL · Kebbi · Sokoto · Zamfara</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("#### 📅 Reporting Period")
    quarter_mode = st.selectbox("Select quarter",
        ['Q1','Q2','Semi-Annual (Q1+Q2)','Q3','Q4','Annual (Q1–Q4)'],
        help="Select the period you are reporting for")

    PERIOD_MAP = {
        'Q1':                  ('Oct – Dec 2025',      'FY26 Q1',          'Q1'),
        'Q2':                  ('Jan – Mar 2026',      'FY26 Q2',          'Q2'),
        'Semi-Annual (Q1+Q2)': ('Oct 2025 – Mar 2026', 'FY26 Semi-Annual', 'CUM'),
        'Q3':                  ('Apr – Jun 2026',      'FY26 Q3',          'Q3'),
        'Q4':                  ('Jul – Sep 2026',      'FY26 Q4',          'Q4'),
        'Annual (Q1–Q4)':      ('Oct 2025 – Sep 2026', 'FY26 Annual',      'ANNUAL'),
    }
    period_str, qlabel, qmode_key = PERIOD_MAP.get(quarter_mode, PERIOD_MAP['Q1'])

    st.markdown("---")
    st.markdown("#### 📁 Static Files *(once per FY)*")
    targets_file = st.file_uploader("Targets (CSV/Excel)", type=['csv','xlsx'], key='tgt')
    vl_elig_file = st.file_uploader("VL Eligible file",   type=['xlsx'],       key='vle')

    # ── Q file slots — show only what's needed ────────────────────────────────
    need_q2 = quarter_mode in ['Q2','Semi-Annual (Q1+Q2)','Annual (Q1–Q4)']
    need_q3 = quarter_mode in ['Q3','Annual (Q1–Q4)']
    need_q4 = quarter_mode in ['Q4','Annual (Q1–Q4)']

    def _uploaders(qn):
        st.markdown(f"#### 📂 {qn} Files")
        return {
            'radet':    st.file_uploader(f"RADET ({qn})",     type=['xlsx'],     key=f'r{qn}'),
            'hts':      st.file_uploader(f"HTS ({qn})",       type=['xlsx','csv'],key=f'h{qn}'),
            'pmtct_hts':st.file_uploader(f"PMTCT HTS ({qn})", type=['xlsx'],     key=f'ph{qn}'),
            'pmtct_mat':st.file_uploader(f"PMTCT Mat ({qn})", type=['xlsx'],     key=f'pm{qn}'),
            'tb':       st.file_uploader(f"TB ({qn})",        type=['xlsx'],     key=f'tb{qn}'),
            'ahd':      st.file_uploader(f"AHD ({qn})",       type=['xlsx'],     key=f'ahd{qn}'),
            'prep':     st.file_uploader(f"PrEP ({qn})",      type=['xlsx'],     key=f'prep{qn}'),
            'eac':      st.file_uploader(f"EAC ({qn})",       type=['xlsx'],     key=f'eac{qn}'),
        }

    files_q1 = _uploaders('Q1')
    files_q1['vl_eligible'] = vl_elig_file
    files_q2 = _uploaders('Q2') if need_q2 else {}
    files_q3 = _uploaders('Q3') if need_q3 else {}
    files_q4 = _uploaders('Q4') if need_q4 else {}

    st.markdown("---")
    if st.button("🔄 Reset / Clear Results", use_container_width=True):
        st.session_state.results = None
        st.session_state.outputs_ready = False
        st.rerun()
    run_btn = st.button("▶ Generate Reports", use_container_width=True)

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown(f"""<div style="background:linear-gradient(135deg,#0F2942,#1F4E79);color:white;
padding:16px 24px;border-bottom:3px solid #BA0C2F;margin:-1rem -1rem 1.5rem">
  <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,.45);margin-bottom:4px">ACE3 Programme · HSCL · Performance Report System</div>
  <div style="font-size:20px;font-weight:700">Accelerating Control of the HIV Epidemic in Nigeria</div>
  <div style="font-size:11px;color:rgba(255,255,255,.6);margin-top:3px">{period_str} · {qlabel} · Kebbi, Sokoto &amp; Zamfara · 37 Facilities</div>
</div>""", unsafe_allow_html=True)

# ── RUN ENGINE ────────────────────────────────────────────────────────────────
if run_btn:
    if not files_q1.get('radet'):
        st.error("⚠ Q1 RADET file is required.")
    elif need_q2 and not files_q2.get('radet'):
        st.error("⚠ Q2 RADET file is required for this period.")
    else:
        with st.spinner("Running ACE3 engine — please wait..."):
            try:
                results = assemble(
                    files_q1=files_q1,
                    files_q2=files_q2 if files_q2.get('radet') else None,
                    files_q3=files_q3 if files_q3.get('radet') else None,
                    files_q4=files_q4 if files_q4.get('radet') else None,
                    targets_src=targets_file,
                    quarter_mode=qmode_key
                )
                has_data = bool(results.get('q1')) or bool(results.get('semi'))
                st.session_state.results       = results
                st.session_state.quarter_mode  = qmode_key
                st.session_state.period        = period_str
                st.session_state.quarter_label = qlabel
                st.session_state.outputs_ready = has_data
                if results.get('errors'):
                    for e in results['errors']: st.warning(f"⚠ {e}")
                if has_data:
                    st.success("✓ Engine complete — reports ready below")
                else:
                    st.error("⚠ Engine ran but produced no results. Check RADET file has a sheet named 'radet'.")
                    for e in results.get('errors',[]): st.code(e)
            except Exception as ex:
                st.error(f"Engine error: {ex}")
                st.code(traceback.format_exc())

# ── RESULTS ───────────────────────────────────────────────────────────────────
if st.session_state.outputs_ready and st.session_state.results:
    results = st.session_state.results
    qmode   = st.session_state.quarter_mode
    period  = st.session_state.period
    qlabel  = st.session_state.quarter_label

    # primary data dict
    d    = results.get('semi') if qmode=='CUM' else results.get('q1',{})
    tgts = results.get('targets',{})

    if not d:
        st.error("⚠ No results. Check engine errors above.")
        for e in results.get('errors',[]): st.code(e)
        st.stop()

    # per-quarter dicts for trend tab
    q1d = results.get('q1',{})
    q2d = results.get('q2',{})
    q3d = results.get('q3',{})
    q4d = results.get('q4',{})
    quarters_available = {k:v for k,v in
                          [('Q1',q1d),('Q2',q2d),('Q3',q3d),('Q4',q4d)] if v}
    q_labels = list(quarters_available.keys())
    q_colours = {'Q1':'#1F4E79','Q2':'#2E75B6','Q3':'#4A90C4','Q4':'#0E7490'}

    # extract primary indicators
    txc    = d.get('TX_CURR',0)
    tx_new = d.get('TX_NEW',0)
    tx_ml  = d.get('TX_ML',0)
    tx_rtt = d.get('TX_RTT',0)
    hts    = d.get('HTS_TST',0)
    hts_p  = d.get('HTS_TST_POS',0)
    hts_y  = d.get('HTS_YIELD',0)
    pvls_d = d.get('TX_PVLS_D',0)
    pvls_n = d.get('TX_PVLS_N',0)
    vl_s   = d.get('VL_SUPPRESSION',0)
    vl_c   = d.get('VL_COVERAGE',0)
    vl_gap = d.get('VL_GAP',0)
    mmd_3p = d.get('MMD_3P',0)
    mmd_6p = d.get('MMD_6P',0)
    mmd_lt3= d.get('MMD_LT3',0)
    mmd_pct= _pct(mmd_3p,txc)
    tpt    = d.get('TB_PREV_N',0)
    pnew   = d.get('PrEP_NEW',0)
    pvls_d = d.get('TX_PVLS_D',0)
    pvls_n = d.get('TX_PVLS_N',0)
    cxca_e = d.get('CXCA_SCRN',0)
    cxca_t = d.get('CXCA_TX',0)
    rtt_r  = _pct(tx_rtt, tx_ml)
    link_r = _pct(tx_new, hts_p)
    eac_cl = d.get('EAC_CASELOAD',0)
    eac_psr= d.get('EAC_POST_SUPP_R',0)

    # ── KPI BANNER ────────────────────────────────────────────────────────────
    st.markdown("""<div style="font-size:9px;font-weight:700;letter-spacing:2px;
    text-transform:uppercase;color:#64748B;margin-bottom:8px">
    95–95–95 Programme Indicators · """ + qlabel + """</div>""", unsafe_allow_html=True)

    cards_html = f"""<div style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;margin-bottom:16px">
  {_kpi_card('HIV Tests<br>HTS_TST', _n(hts), f'Yield {_p(hts_y,2)} · {_n(hts_p)} HIV+', '#2E75B6','#EBF3FB')}
  {_kpi_card('New on ART<br>TX_NEW', _n(tx_new), f'Linkage {_p(link_r)} of HIV+', '#1F4E79','#EBF3FB')}
  {_kpi_card('Active on ART<br>TX_CURR', _n(txc), f'{_pct(d.get("TX_CURR_F",0),txc):.1f}% female', '#1F4E79','#EBF3FB')}
  {_kpi_card('Interruptions<br>TX_ML', _n(tx_ml), f'RTT {_p(rtt_r)} returned', '#BA0C2F','#FDEAEA')}
  {_kpi_card('VL Suppression<br>TX_PVLS N/D', _p(vl_s), f'{_n(pvls_n)} of {_n(pvls_d)}', '#1A6632' if vl_s>=95 else '#C87000', '#E6F2EB' if vl_s>=95 else '#FEF3E2')}
  {_kpi_card('ANC Tested<br>PMTCT_STAT', _n(d.get("PMTCT_STAT_N",0)), f'{d.get("PMTCT_STAT_POS",0)} HIV+', '#0E7490','#E0F2FE')}
</div>"""
    st.markdown(cards_html, unsafe_allow_html=True)
    st.markdown("---")

    # ── TABS — 95-95-95 order ─────────────────────────────────────────────────
    TAB_LABELS = [
        "📊 Overview",
        "🔬 1st 95 — Testing",
        "💊 2nd 95 — Treatment",
        "🤰 PMTCT",
        "📉 3rd 95 — Viral Load",
        "🛡️ Prevention",
        "🏥 AHD",
        "📈 Quarterly Trend",
        "🎯 Targets",
    ]
    tabs = st.tabs(TAB_LABELS)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 0 — OVERVIEW
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[0]:
        col1, col2 = st.columns([2,1])
        with col1:
            st.markdown("##### TX_CURR by State & Sex")
            sc = d.get('TX_CURR_STATE',{})
            fem_r = d.get('TX_CURR_F',0)/txc if txc else 0.645
            fig = go.Figure()
            fig.add_bar(name='Female', x=STATES,
                        y=[round(sc.get(s,0)*fem_r) for s in STATES],
                        marker_color='#2E75B6',
                        text=[_n(round(sc.get(s,0)*fem_r)) for s in STATES],
                        textposition='inside', textfont=dict(color='white',size=10))
            fig.add_bar(name='Male',   x=STATES,
                        y=[round(sc.get(s,0)*(1-fem_r)) for s in STATES],
                        marker_color='#1F4E79',
                        text=[_n(round(sc.get(s,0)*(1-fem_r))) for s in STATES],
                        textposition='inside', textfont=dict(color='white',size=10))
            fig.update_layout(**CHART_CFG, barmode='stack',
                height=300, title='TX_CURR by State & Sex',
                legend=dict(orientation='h',y=1.12,x=0))
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(gridcolor='#F1F5F9', tickformat=',')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.markdown("##### MMD Distribution")
            mmd_35 = mmd_3p - mmd_6p
            fig2 = go.Figure(go.Pie(
                labels=['6+ months','3–5 months','<3 months'],
                values=[mmd_6p, mmd_35, mmd_lt3],
                hole=0.65,
                marker=dict(colors=['#1A6632','#2E75B6','#BA0C2F'],
                            line=dict(color='white',width=2)),
                textinfo='percent', textfont=dict(size=10)
            ))
            fig2.update_layout(**CHART_CFG, height=300,
                title=f'MMD ≥3mo: {mmd_pct:.1f}%',
                legend=dict(orientation='h',y=-0.12,font=dict(size=10)))
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.markdown("##### 95–95–95 Progress")
            targets_95 = [
                ('1st 95 — VL Coverage', vl_c, 95),
                ('2nd 95 — VL Suppression', vl_s, 95),
                ('MMD ≥3 Months', mmd_pct, 90),
                ('TPT Coverage', _pct(tpt,txc), 90),
                ('CxCa Coverage', _pct(cxca_t,cxca_e) if cxca_e else 0, 80),
            ]
            for label, val, thr in targets_95:
                col = '#1A6632' if val>=thr else ('#C87000' if val>=thr*0.8 else '#BA0C2F')
                w = min(val, 100)
                st.markdown(f"""<div style="margin-bottom:10px">
  <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px">
    <span style="font-weight:600;color:#1E293B">{label}</span>
    <span style="font-family:monospace;font-weight:700;color:{col}">{val:.1f}%</span>
  </div>
  <div style="height:8px;background:#E2E8F0;position:relative;border-radius:2px">
    <div style="height:100%;width:{w}%;background:{col};border-radius:2px"></div>
    <div style="position:absolute;top:-3px;left:{thr}%;width:2px;height:14px;background:#475569"></div>
  </div>
  <div style="font-size:9px;color:#94A3B8;margin-top:2px">Target: {thr}% &nbsp;│&nbsp; Gap: {max(0,thr-val):.1f} pp</div>
</div>""", unsafe_allow_html=True)
        with col4:
            st.markdown("##### TB/HIV & PrEP Summary")
            tb_scr = d.get('TB_SCREEN',0)
            fig3 = go.Figure()
            fig3.add_bar(x=['TB Screened','TPT Started','Screen+'],
                         y=[tb_scr, tpt, d.get('TB_SCREEN_POS',0)],
                         marker_color=['#2E75B6','#1A6632','#BA0C2F'],
                         text=[_n(tb_scr), _n(tpt), _n(d.get('TB_SCREEN_POS',0))],
                         textposition='outside', textfont=dict(size=10))
            fig3.update_layout(**CHART_CFG, height=280,
                title=f'TB/HIV — TPT Coverage {_pct(tpt,txc):.1f}%')
            fig3.update_xaxes(showgrid=False)
            fig3.update_yaxes(gridcolor='#F1F5F9', tickformat=',')
            st.plotly_chart(fig3, use_container_width=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 1 — 1st 95: TESTING (MER: Quarterly)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[1]:
        st.caption("HTS_TST · Quarterly indicator · First 95 — know your status")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### HTS_TST by State")
            sh = d.get('HTS_STATE',{})
            fig_h = go.Figure()
            for s in STATES:
                fig_h.add_bar(x=[s], y=[sh.get(s,0)],
                              marker_color=STATE_COLOURS[s], name=s,
                              text=[_n(sh.get(s,0))], textposition='outside',
                              textfont=dict(size=10))
            fig_h.update_layout(**CHART_CFG, height=300,
                title=f'HIV Tests by State — Total {_n(hts)} · Yield {_p(hts_y,2)}',
                showlegend=False)
            fig_h.update_xaxes(showgrid=False)
            fig_h.update_yaxes(gridcolor='#F1F5F9', tickformat=',')
            st.plotly_chart(fig_h, use_container_width=True)
        with col2:
            st.markdown("##### Positivity Summary")
            fig_pos = go.Figure()
            fig_pos.add_trace(go.Indicator(
                mode='gauge+number',
                value=hts_y,
                number={'suffix':'%','font':{'size':32,'family':'IBM Plex Mono'}},
                title={'text':'HIV Positivity Yield','font':{'size':13}},
                gauge={'axis':{'range':[0,10]},
                       'bar':{'color':'#BA0C2F'},
                       'bgcolor':'#F1F5F9',
                       'threshold':{'value':5,'line':{'color':'#1F4E79','width':2}}}
            ))
            fig_pos.update_layout(**CHART_CFG, height=300)
            st.plotly_chart(fig_pos, use_container_width=True)

        # Modality chart
        hts_mod = d.get('HTS_MODALITY',{})
        if hts_mod:
            st.markdown("##### HTS by Modality — Volume & Yield")
            mod_labels = list(hts_mod.keys())
            mod_tested = [hts_mod[m].get('tested',0) if isinstance(hts_mod[m],dict) else 0 for m in mod_labels]
            mod_yield_ = [round(hts_mod[m].get('yield',0),2) if isinstance(hts_mod[m],dict) else 0 for m in mod_labels]
            mod_pos    = [hts_mod[m].get('pos',0) if isinstance(hts_mod[m],dict) else 0 for m in mod_labels]

            fig_mod = make_subplots(specs=[[{"secondary_y": True}]])
            fig_mod.add_trace(go.Bar(
                name='Tests', x=mod_labels, y=mod_tested,
                marker_color='#1F4E79',
                text=[_n(v) for v in mod_tested],
                textposition='outside', textfont=dict(size=9)
            ), secondary_y=False)
            fig_mod.add_trace(go.Scatter(
                name='Yield %', x=mod_labels, y=mod_yield_,
                mode='lines+markers',
                line=dict(color='#BA0C2F', width=2.5),
                marker=dict(size=8, color='#BA0C2F',
                            line=dict(color='white',width=1.5))
            ), secondary_y=True)
            fig_mod.update_layout(**CHART_CFG, height=340,
                title=f'HTS by Modality — {_n(hts)} total · {_n(hts_p)} positive',
                legend=dict(orientation='h',y=1.12,x=0))
            fig_mod.update_xaxes(showgrid=False, tickangle=-20)
            fig_mod.update_yaxes(title_text='Tests', gridcolor='#F1F5F9',
                                  tickformat=',', secondary_y=False)
            fig_mod.update_yaxes(title_text='Yield %', ticksuffix='%',
                                  showgrid=False, secondary_y=True)
            st.plotly_chart(fig_mod, use_container_width=True)

            mod_df = pd.DataFrame([{
                'Modality': m,
                'Tested': _n(hts_mod[m].get('tested',0) if isinstance(hts_mod[m],dict) else 0),
                'HIV+': _n(hts_mod[m].get('pos',0) if isinstance(hts_mod[m],dict) else 0),
                'Yield %': f"{hts_mod[m].get('yield',0):.2f}%" if isinstance(hts_mod[m],dict) else '0.00%'
            } for m in mod_labels])
            st.dataframe(mod_df, hide_index=True, use_container_width=True)
        else:
            st.info("Upload the HTS file to see modality breakdown and yield by modality.")

        # Linkage
        st.markdown("##### Linkage to Treatment")
        st.markdown(f"""<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:6px">
  {_kpi_card('HIV Positive', _n(hts_p), f'{_p(hts_y,2)} positivity', '#BA0C2F','#FDEAEA')}
  {_kpi_card('Linked to ART<br>TX_NEW', _n(tx_new), f'{_p(link_r)} linkage rate', '#1F4E79','#EBF3FB')}
  {_kpi_card('Not Linked', _n(max(0,hts_p-tx_new)), 'Require follow-up', '#C87000','#FEF3E2')}
</div>""", unsafe_allow_html=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 2 — 2nd 95: TREATMENT (MER: Quarterly)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[2]:
        st.caption("TX_NEW · TX_CURR · TX_ML · TX_RTT · Quarterly indicators · Second 95 — on treatment")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### TX_CURR by State")
            sc = d.get('TX_CURR_STATE',{})
            fig_tc = go.Figure()
            for s in STATES:
                fig_tc.add_bar(x=[s], y=[sc.get(s,0)],
                               marker_color=STATE_COLOURS[s],
                               text=[_n(sc.get(s,0))], textposition='outside',
                               textfont=dict(size=10))
            fig_tc.update_layout(**CHART_CFG, height=300,
                title=f'TX_CURR by State — Total {_n(txc)}', showlegend=False)
            fig_tc.update_xaxes(showgrid=False)
            fig_tc.update_yaxes(gridcolor='#F1F5F9', tickformat=',')
            st.plotly_chart(fig_tc, use_container_width=True)
        with col2:
            st.markdown("##### TX_ML — Treatment Interruptions")
            ml_out = d.get('TX_ML_OUTCOMES',{})
            iit_n  = ml_out.get('IIT',0)
            died_n = ml_out.get('Died',0)
            to_n   = ml_out.get('Transferred Out',0)
            stop_n = ml_out.get('Stopped Treatment',0)
            fig_ml = go.Figure(go.Bar(
                y=['IIT (Lost to F/U)','Died','Transferred Out','Stopped'],
                x=[iit_n, died_n, to_n, stop_n],
                orientation='h',
                marker_color=['#BA0C2F','#7B1D1D','#1F4E79','#94A3B8'],
                text=[_n(v) for v in [iit_n,died_n,to_n,stop_n]],
                textposition='outside', textfont=dict(size=10)
            ))
            fig_ml.update_layout(**CHART_CFG, height=300,
                title=f'TX_ML Outcomes — {_n(tx_ml)} total · RTT {_p(rtt_r)}')
            fig_ml.update_xaxes(gridcolor='#F1F5F9', tickformat=',')
            fig_ml.update_yaxes(showgrid=False)
            st.plotly_chart(fig_ml, use_container_width=True)

        st.markdown("##### Treatment Cohort Summary")
        st.markdown(f"""<div style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;margin-top:6px">
  {_kpi_card('TX_NEW<br>New Initiations', _n(tx_new), f'{_p(link_r)} linkage', '#1F4E79','#EBF3FB')}
  {_kpi_card('TX_CURR<br>Active on ART', _n(txc), f'{_pct(d.get("TX_CURR_LT15",0),txc):.1f}% paediatric', '#1F4E79','#EBF3FB')}
  {_kpi_card('TX_ML<br>Interruptions', _n(tx_ml), f'{_p(rtt_r)} RTT rate', '#BA0C2F','#FDEAEA')}
  {_kpi_card('TX_RTT<br>Returned', _n(tx_rtt), 'Returned to ART', '#1A6632','#E6F2EB')}
  {_kpi_card('MMD ≥3 Months<br>DSD Coverage', _p(mmd_pct), f'{_n(mmd_3p)} clients', '#1A6632' if mmd_pct>=90 else '#C87000', '#E6F2EB' if mmd_pct>=90 else '#FEF3E2')}
</div>""", unsafe_allow_html=True)

        st.markdown("##### Biometrics & MMD")
        col3, col4 = st.columns(2)
        with col3:
            bio = d.get('TX_CURR_BIO',0)
            bio_p = _pct(bio, txc)
            st.markdown(f"""<div style="margin-top:10px">
  <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px">
    <span style="font-weight:600">Biometric Enrolment</span>
    <span style="font-family:monospace;font-weight:700;color:{'#1A6632' if bio_p>=95 else '#C87000'}">{bio_p:.1f}%</span>
  </div>
  <div style="height:10px;background:#E2E8F0;border-radius:2px">
    <div style="height:100%;width:{min(bio_p,100)}%;background:{'#1A6632' if bio_p>=95 else '#C87000'};border-radius:2px"></div>
  </div>
  <div style="font-size:9px;color:#94A3B8;margin-top:2px">{_n(bio)} of {_n(txc)} enrolled</div>
</div>""", unsafe_allow_html=True)
        with col4:
            st.markdown(f"""<div style="margin-top:10px">
  <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px">
    <span style="font-weight:600">MMD ≥3 Months Coverage</span>
    <span style="font-family:monospace;font-weight:700;color:{'#1A6632' if mmd_pct>=90 else '#C87000'}">{mmd_pct:.1f}%</span>
  </div>
  <div style="height:10px;background:#E2E8F0;border-radius:2px;position:relative">
    <div style="height:100%;width:{min(mmd_pct,100)}%;background:{'#1A6632' if mmd_pct>=90 else '#C87000'};border-radius:2px"></div>
    <div style="position:absolute;top:-2px;left:90%;width:2px;height:14px;background:#475569"></div>
  </div>
  <div style="font-size:9px;color:#94A3B8;margin-top:2px">{_n(mmd_3p)} on ≥3mo · {_n(mmd_6p)} on 6mo · Target: 90%</div>
</div>""", unsafe_allow_html=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 3 — PMTCT (MER: Quarterly)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[3]:
        st.caption("PMTCT_STAT · PMTCT_ART · PMTCT_EID · Quarterly indicators")
        pmtc_n = d.get('PMTCT_STAT_N',0); pmtc_p=d.get('PMTCT_STAT_POS',0)
        pmtc_a = d.get('PMTCT_ART_D',0); eid=d.get('PMTCT_EID',0)
        deliv  = d.get('PMTCT_DELIVERED',0)
        eid_c  = _pct(eid,deliv)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### PMTCT Cascade")
            cascade_vals = [pmtc_n, pmtc_p, pmtc_a, eid]
            cascade_labs = ['ANC Tested','HIV+','On ART','EID PCR']
            fig_pm = go.Figure()
            for i,(l,v) in enumerate(zip(cascade_labs,cascade_vals)):
                fig_pm.add_bar(x=[l], y=[v],
                               marker_color=['#0E7490','#BA0C2F','#1A6632','#C87000'][i],
                               text=[_n(v)], textposition='outside', textfont=dict(size=11))
            fig_pm.update_layout(**CHART_CFG, height=300,
                title=f'PMTCT Cascade — {_n(pmtc_n)} tested · {pmtc_p} HIV+',
                showlegend=False)
            fig_pm.update_xaxes(showgrid=False)
            fig_pm.update_yaxes(gridcolor='#F1F5F9', tickformat=',')
            st.plotly_chart(fig_pm, use_container_width=True)
        with col2:
            st.markdown("##### PMTCT by Modality")
            anc1 = d.get('PMTCT_ANC1', pmtc_n)
            post = d.get('PMTCT_POSTANC',0)
            bf   = d.get('PMTCT_BF',0)
            fig_pmod = go.Figure()
            for label, val, col in [('ANC1 Only',anc1,'#0E7490'),
                                     ('Post-ANC1 (Preg/L&D)',post,'#2E75B6'),
                                     ('Breastfeeding',bf,'#4A90C4')]:
                if val > 0:
                    fig_pmod.add_bar(x=[label], y=[val], marker_color=col,
                                     text=[_n(val)], textposition='outside',
                                     textfont=dict(size=10))
            fig_pmod.update_layout(**CHART_CFG, height=300,
                title='PMTCT Testing by Modality (MER ANC1 / Post-ANC1)',
                showlegend=False)
            fig_pmod.update_xaxes(showgrid=False, tickfont=dict(size=10))
            fig_pmod.update_yaxes(gridcolor='#F1F5F9', tickformat=',')
            st.plotly_chart(fig_pmod, use_container_width=True)

        st.markdown("##### Key PMTCT Metrics")
        eid_col = '#1A6632' if eid_c>=95 else '#C87000'
        st.markdown(f"""<div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-top:6px">
  {_kpi_card('PMTCT_STAT<br>ANC Tested', _n(pmtc_n), f'Since Oct 2025', '#0E7490','#E0F2FE')}
  {_kpi_card('HIV Positive<br>at ANC', _n(pmtc_p), f'{pmtc_p/pmtc_n*100:.3f}% prevalence' if pmtc_n else '', '#BA0C2F','#FDEAEA')}
  {_kpi_card('PMTCT_ART<br>Mothers on ART', _n(pmtc_a), 'PMTCT ART coverage', '#1A6632','#E6F2EB')}
  {_kpi_card('EID PCR<br>Coverage', _p(eid_c), f'{_n(eid)} of {_n(deliv)} HEI', eid_col,'#E6F2EB' if eid_c>=95 else '#FEF3E2')}
</div>""", unsafe_allow_html=True)
        if eid_c < 95 and deliv > 0:
            st.markdown(f"""<div class="semi-warn">⚠ <strong>EID Coverage Alert:</strong>
            {_n(max(0,deliv-eid))} HIV-exposed infants have not received EID PCR testing. Target: ≥95%.</div>""",
            unsafe_allow_html=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 4 — 3rd 95: VIRAL LOAD + EAC (MER: Quarterly)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[4]:
        st.caption("TX_PVLS · EAC · Quarterly indicator · Third 95 — virally suppressed")
        unsupp = d.get('VL_UNSUPP',0)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### TX_PVLS — VL Suppression (3rd 95)")
            fig_vl = go.Figure(go.Indicator(
                mode='gauge+number+delta',
                value=vl_s,
                number={'suffix':'%','font':{'size':40,'family':'IBM Plex Mono','color':'#1A6632' if vl_s>=95 else '#C87000'}},
                delta={'reference':95,'suffix':'pp vs 95%','font':{'size':13}},
                title={'text':'TX_PVLS_N / TX_PVLS_D','font':{'size':13}},
                gauge={'axis':{'range':[0,100],'tickwidth':1,'tickcolor':'#CBD5E1'},
                       'bar':{'color':'#1A6632' if vl_s>=95 else '#C87000','thickness':0.25},
                       'bgcolor':'#F8FAFC',
                       'borderwidth':0,
                       'threshold':{'line':{'color':'#1F4E79','width':3},'value':95},
                       'steps':[{'range':[0,95],'color':'#F1F5F9'},
                                {'range':[95,100],'color':'#E6F2EB'}]}
            ))
            fig_vl.update_layout(**CHART_CFG, height=300)
            st.plotly_chart(fig_vl, use_container_width=True)
        with col2:
            st.markdown("##### TX_PVLS_D — VL Coverage")
            fig_vc = go.Figure(go.Indicator(
                mode='gauge+number+delta',
                value=vl_c,
                number={'suffix':'%','font':{'size':40,'family':'IBM Plex Mono','color':'#1A6632' if vl_c>=95 else '#C87000'}},
                delta={'reference':95,'suffix':'pp vs 95%','font':{'size':13}},
                title={'text':'TX_PVLS_D / TX_CURR','font':{'size':13}},
                gauge={'axis':{'range':[0,100],'tickwidth':1,'tickcolor':'#CBD5E1'},
                       'bar':{'color':'#1A6632' if vl_c>=95 else '#C87000','thickness':0.25},
                       'bgcolor':'#F8FAFC',
                       'borderwidth':0,
                       'threshold':{'line':{'color':'#1F4E79','width':3},'value':95},
                       'steps':[{'range':[0,95],'color':'#F1F5F9'},
                                {'range':[95,100],'color':'#E6F2EB'}]}
            ))
            fig_vc.update_layout(**CHART_CFG, height=300)
            st.plotly_chart(fig_vc, use_container_width=True)

        st.markdown(f"""<div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:8px 0">
  {_kpi_card('TX_PVLS_D<br>VL Resulted', _n(pvls_d), f'of {_n(txc)} TX_CURR', '#1F4E79','#EBF3FB')}
  {_kpi_card('TX_PVLS_N<br>Suppressed', _n(pvls_n), f'{_p(vl_s)} suppression', '#1A6632','#E6F2EB')}
  {_kpi_card('Unsuppressed<br>Clients', _n(unsupp), 'Require EAC', '#BA0C2F','#FDEAEA')}
  {_kpi_card('VL Sample Gap<br>Pending', _n(vl_gap), 'Need sample collection', '#C87000','#FEF3E2')}
</div>""", unsafe_allow_html=True)

        # EAC
        st.markdown("##### Enhanced Adherence Counselling (EAC)")
        eac_s1 = d.get('EAC_SESS1',0); eac_s2=d.get('EAC_SESS2',0)
        eac_pvl= d.get('EAC_POST_VL_N',0); eac_psn=d.get('EAC_POST_SUPP_N',0)
        eac_st = d.get('EAC_STATE',{})
        col3, col4 = st.columns(2)
        with col3:
            fig_eac = go.Figure()
            for s in STATES:
                fig_eac.add_bar(x=[s], y=[eac_st.get(s,0)],
                                marker_color=STATE_COLOURS[s],
                                text=[_n(eac_st.get(s,0))],
                                textposition='outside', textfont=dict(size=10))
            fig_eac.update_layout(**CHART_CFG, height=260,
                title=f'EAC Caseload by State — {_n(eac_cl)} total', showlegend=False)
            fig_eac.update_xaxes(showgrid=False)
            fig_eac.update_yaxes(gridcolor='#F1F5F9', tickformat=',')
            st.plotly_chart(fig_eac, use_container_width=True)
        with col4:
            fig_sess = go.Figure(go.Bar(
                x=['1st EAC','2nd EAC','3rd EAC','Extended'],
                y=[eac_s1, eac_s2, d.get('EAC_SESS3',0), d.get('EAC_EXT',0)],
                marker_color=['#1F4E79','#2E75B6','#4A90C4','#C87000'],
                text=[_n(v) for v in [eac_s1,eac_s2,d.get('EAC_SESS3',0),d.get('EAC_EXT',0)]],
                textposition='outside', textfont=dict(size=10)
            ))
            fig_sess.update_layout(**CHART_CFG, height=260,
                title='EAC Sessions Completed')
            fig_sess.update_xaxes(showgrid=False)
            fig_sess.update_yaxes(gridcolor='#F1F5F9', tickformat=',')
            st.plotly_chart(fig_sess, use_container_width=True)

        eac_col = '#1A6632' if eac_psr>=90 else '#C87000'
        st.markdown(f"""<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:6px">
  {_kpi_card('EAC Caseload<br>Unsuppressed', _n(eac_cl), 'Actively managed', '#BA0C2F','#FDEAEA')}
  {_kpi_card('Post-EAC VL<br>Collected', _n(eac_pvl), f'of {_n(eac_cl)} caseload', '#1F4E79','#EBF3FB')}
  {_kpi_card('Post-EAC<br>Re-suppression', _p(eac_psr), f'{_n(eac_psn)} clients', eac_col,'#E6F2EB' if eac_psr>=90 else '#FEF3E2')}
</div>""", unsafe_allow_html=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 5 — PREVENTION: TB_PREV · CxCa · PrEP (MER: Semi-Annual)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[5]:
        if qmode in ['Q1','Q3']:
            st.markdown("""<div class="semi-warn">⚠ <strong>Semi-Annual Indicators:</strong>
            TB_PREV (TPT), CxCa, and TX_TB are semi-annual indicators per MER v2.8 —
            reported at Q2 and Q4 only. Results shown here are cumulative since FY start
            but DATIM submission occurs at Q2 and Q4.</div>""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### TB_PREV — TPT Coverage *(Semi-Annual)*")
            tb_scr = d.get('TB_SCREEN',0); tb_pos=d.get('TB_SCREEN_POS',0)
            tpt_c  = _pct(tpt,txc)
            fig_tb = go.Figure(go.Bar(
                x=['TB Screened','TB Screen+','TPT Started'],
                y=[tb_scr, tb_pos, tpt],
                marker_color=['#2E75B6','#BA0C2F','#1A6632'],
                text=[_n(tb_scr), _n(tb_pos), _n(tpt)],
                textposition='outside', textfont=dict(size=10)
            ))
            fig_tb.update_layout(**CHART_CFG, height=300,
                title=f'TB/HIV — TPT Coverage {tpt_c:.1f}% of TX_CURR')
            fig_tb.update_xaxes(showgrid=False)
            fig_tb.update_yaxes(gridcolor='#F1F5F9', tickformat=',')
            st.plotly_chart(fig_tb, use_container_width=True)

        with col2:
            st.markdown("##### CxCa — Cervical Cancer Screening *(Semi-Annual)*")
            cxca_r = d.get('CXCA_RESULTS',{})
            cxca_neg = int(cxca_r.get('Negative',0) or cxca_r.get('Negative VIA',0) or 0)
            cxca_pos = int(cxca_r.get('Positive',0) or cxca_r.get('Positive VIA',0) or 0)
            cxca_sus = int(cxca_r.get('Suspicious',0) or 0)
            cxca_un  = max(0, cxca_e-cxca_t)
            fig_cx = go.Figure(go.Pie(
                labels=['Not Screened','Negative','Positive','Suspicious'],
                values=[cxca_un, cxca_neg, cxca_pos, cxca_sus],
                hole=0.6,
                marker=dict(colors=['#CBD5E1','#1A6632','#C87000','#BA0C2F'],
                            line=dict(color='white',width=2)),
                textinfo='percent+value', textfont=dict(size=10)
            ))
            cxca_cov = _pct(cxca_t,cxca_e) if cxca_e else 0
            fig_cx.update_layout(**CHART_CFG, height=300,
                title=f'CxCa — {cxca_cov:.1f}% coverage ({_n(cxca_t)} of {_n(cxca_e)})',
                legend=dict(orientation='h',y=-0.12,font=dict(size=10)))
            st.plotly_chart(fig_cx, use_container_width=True)
            if cxca_pos+cxca_sus > 0:
                st.error(f"⚠ {cxca_pos+cxca_sus} women with positive/suspicious findings — urgent follow-up required.")

        # PrEP
        st.markdown("##### PrEP Programme *(Quarterly)*")
        pct_  = d.get('PrEP_CT',0); pcurr=d.get('PrEP_CURR',0)
        prep_st = d.get('PrEP_NEW_STATE',{})
        prep_pop= d.get('PrEP_NEW_POP',{})
        col3, col4 = st.columns(2)
        with col3:
            fig_p = go.Figure()
            for s in STATES:
                fig_p.add_bar(x=[s], y=[prep_st.get(s,0)],
                              marker_color=STATE_COLOURS[s],
                              text=[_n(prep_st.get(s,0))],
                              textposition='outside', textfont=dict(size=10))
            fig_p.update_layout(**CHART_CFG, height=260,
                title=f'PrEP_NEW by State — Total {_n(pnew)}', showlegend=False)
            fig_p.update_xaxes(showgrid=False)
            fig_p.update_yaxes(gridcolor='#F1F5F9')
            st.plotly_chart(fig_p, use_container_width=True)
        with col4:
            if prep_pop:
                fig_pp = go.Figure(go.Pie(
                    labels=list(prep_pop.keys()),
                    values=[int(v) for v in prep_pop.values()],
                    hole=0.55,
                    marker=dict(colors=_colours(len(prep_pop)),
                                line=dict(color='white',width=2)),
                    textinfo='percent', textfont=dict(size=10)
                ))
                fig_pp.update_layout(**CHART_CFG, height=260,
                    title='PrEP_NEW by Population Type',
                    legend=dict(orientation='h',y=-0.12,font=dict(size=9)))
                st.plotly_chart(fig_pp, use_container_width=True)

        st.markdown(f"""<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:6px">
  {_kpi_card('PrEP_NEW<br>New Initiations', _n(pnew), 'Commenced this period', '#1F4E79','#EBF3FB')}
  {_kpi_card('PrEP_CT<br>Continuing', _n(pct_), 'Follow-up visits', '#2E75B6','#EBF3FB')}
  {_kpi_card('PrEP_CURR<br>Active Snapshot', _n(pcurr), 'Currently on PrEP', '#1A6632','#E6F2EB')}
</div>""", unsafe_allow_html=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 6 — AHD
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[6]:
        ahd_s=d.get('AHD_SCRN',0); ahd_c=d.get('AHD_CONF',0)
        ahd_cd4=d.get('AHD_CD4',0); ahd_tbl=d.get('AHD_TBLAM_POS',0); ahd_cr=d.get('AHD_CRAG_POS',0)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### AHD Screening & Confirmation")
            fig_ahd = go.Figure(go.Bar(
                x=['Screened','AHD Confirmed','CD4 Done'],
                y=[ahd_s, ahd_c, ahd_cd4],
                marker_color=['#1F4E79','#BA0C2F','#2E75B6'],
                text=[_n(ahd_s), _n(ahd_c), _n(ahd_cd4)],
                textposition='outside', textfont=dict(size=10)
            ))
            det = f'{ahd_c/ahd_s*100:.1f}%' if ahd_s else '—'
            fig_ahd.update_layout(**CHART_CFG, height=300,
                title=f'AHD — {det} detection rate · {_n(ahd_cr)} CrAg+')
            fig_ahd.update_xaxes(showgrid=False)
            fig_ahd.update_yaxes(gridcolor='#F1F5F9', tickformat=',')
            st.plotly_chart(fig_ahd, use_container_width=True)
        with col2:
            st.markdown("##### AHD Diagnostics")
            st.markdown(f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px">
  {_kpi_card('AHD Confirmed', _n(ahd_c), f'{det} detection rate', '#BA0C2F','#FDEAEA')}
  {_kpi_card('CD4 Tests Done', _n(ahd_cd4), f'{_pct(ahd_cd4,ahd_s):.1f}% of screened', '#1F4E79','#EBF3FB')}
  {_kpi_card('TB-LAM Positive', _n(ahd_tbl), 'TB co-infection', '#C87000','#FEF3E2')}
  {_kpi_card('CrAg Positive', _n(ahd_cr), 'Fluconazole Rx urgent', '#BA0C2F','#FDEAEA')}
</div>""", unsafe_allow_html=True)
            if ahd_cr > 0:
                st.error(f"⚠ {ahd_cr} CrAg-positive clients require urgent fluconazole.")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 7 — QUARTERLY TREND Q1→Q4
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[7]:
        if len(quarters_available) < 2:
            st.info("Upload files for at least 2 quarters to see the quarterly trend comparison.")
        else:
            st.caption(f"Quarterly trend — {' · '.join(q_labels)} · MER v2.8 quarterly indicators")

            TREND_INDICATORS = [
                ('HTS_TST',      'HIV Tests (HTS_TST)',           False),
                ('HTS_TST_POS',  'HIV Positive (HTS_TST_POS)',    False),
                ('TX_NEW',       'New Initiations (TX_NEW)',       False),
                ('TX_CURR',      'Active on ART (TX_CURR)',        False),
                ('TX_ML',        'Interruptions (TX_ML)',          True),
                ('TX_RTT',       'Returned to Tx (TX_RTT)',        False),
                ('TX_PVLS_D',    'VL Resulted (TX_PVLS_D)',        False),
                ('TX_PVLS_N',    'VL Suppressed (TX_PVLS_N)',      False),
                ('PMTCT_STAT_N', 'ANC Tested (PMTCT_STAT)',        False),
                ('PrEP_NEW',     'PrEP_NEW',                       False),
            ]

            # Grouped bar — all quarters side by side per indicator
            st.markdown("##### Quarterly Trend — Key Indicators")
            plot_keys   = ['HTS_TST','TX_NEW','TX_CURR','TX_ML','TX_PVLS_D','PMTCT_STAT_N','PrEP_NEW']
            plot_labels = ['HTS_TST','TX_NEW','TX_CURR','TX_ML','TX_PVLS_D','PMTCT','PrEP_NEW']
            fig_trend = go.Figure()
            for qk, qdata in quarters_available.items():
                fig_trend.add_bar(
                    name=qk,
                    x=plot_labels,
                    y=[qdata.get(k,0) for k in plot_keys],
                    marker_color=q_colours[qk],
                    text=[_n(qdata.get(k,0)) for k in plot_keys],
                    textposition='outside', textfont=dict(size=8)
                )
            fig_trend.update_layout(**CHART_CFG, height=380, barmode='group',
                title='Quarter-on-Quarter Comparison — Quarterly Indicators',
                legend=dict(orientation='h',y=1.12,x=0))
            fig_trend.update_xaxes(showgrid=False, tickfont=dict(size=10))
            fig_trend.update_yaxes(gridcolor='#F1F5F9', tickformat=',')
            st.plotly_chart(fig_trend, use_container_width=True)

            # Summary table
            st.markdown("##### Quarter-by-Quarter Detail Table")
            rows = []
            for val_key, label, invert in TREND_INDICATORS:
                row = {'Indicator': label}
                prev = None
                for qk, qdata in quarters_available.items():
                    val = qdata.get(val_key,0)
                    row[qk] = val
                    if prev is not None:
                        diff = val - prev
                        pct_c = diff/prev*100 if prev else 0
                        good = (diff<=0) if invert else (diff>=0)
                        row[f'Δ {qk}'] = f"{'▲' if diff>0 else '▼'} {abs(pct_c):.1f}% {'✓' if good else '⚠'}"
                    prev = val
                rows.append(row)

            df_trend = pd.DataFrame(rows)
            # Format number columns
            for qk in q_labels:
                if qk in df_trend.columns:
                    df_trend[qk] = df_trend[qk].apply(lambda v: f"{int(v):,}" if v else '—')

            def _colour_delta(v):
                if isinstance(v,str):
                    if '✓' in v: return 'color:#1A6632;font-weight:bold'
                    if '⚠' in v: return 'color:#BA0C2F;font-weight:bold'
                return ''

            delta_cols = [c for c in df_trend.columns if c.startswith('Δ')]
            if delta_cols:
                st.dataframe(df_trend.style.applymap(_colour_delta, subset=delta_cols),
                             use_container_width=True, hide_index=True)
            else:
                st.dataframe(df_trend, use_container_width=True, hide_index=True)

            # Semi-annual note
            st.markdown("""<div class="semi-warn" style="margin-top:10px">
            <strong>Note:</strong> TB_PREV (TPT) and CxCa are <strong>semi-annual indicators</strong>
            per MER v2.8 — reported at Q2 and Q4 only. They are not included in this quarterly trend table.
            </div>""", unsafe_allow_html=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TAB 8 — TARGETS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with tabs[8]:
        st.caption(f"Cumulative result ({qlabel}) vs Annual Target · TX_CURR = period-end snapshot · TB_ART = Q4 annual only")
        TGT_DISPLAY = [
            ('TX_CURR',      'Active on ART',         'TX_CURR',      'Quarterly'),
            ('TX_NEW',       'New ART Initiations',   'TX_NEW',       'Quarterly'),
            ('HTS_TST',      'HIV Tests',             'HTS_TST',      'Quarterly'),
            ('HTS_TST_POS',  'HIV Positive Results',  'HTS_TST_POS',  'Quarterly'),
            ('TX_PVLS_D',    'VL Tests Resulted',     'TX_PVLS_D',    'Quarterly'),
            ('TX_PVLS_N',    'VL Suppressed',         'TX_PVLS_N',    'Quarterly'),
            ('PMTCT_STAT_N', 'ANC Clients Tested',    'PMTCT_STAT_N', 'Quarterly'),
            ('PMTCT_ART_D',  'PMTCT on ART',          'PMTCT_ART_D',  'Quarterly'),
            ('PrEP_NEW',     'PrEP New Initiations',  'PrEP_NEW',     'Quarterly'),
            ('TB_PREV_N',    'TPT Started',           'TB_PREV_N',    'Semi-Annual'),
            ('TX_TB_N',      'TB/HIV on ART',         'TX_TB_N',      'Semi-Annual'),
            ('TB_ART',       'TB Patients on ART',    'TB_ART',       'Annual — Q4'),
        ]
        rows = []
        for val_key, label, tgt_key, freq in TGT_DISPLAY:
            val = d.get(val_key, 0)
            tgt = tgts.get(tgt_key)
            if freq == 'Annual — Q4' and qmode != 'Q4':
                rows.append({'Indicator':label,'MER Frequency':freq,
                             'Result':'—','Annual Target':_n(tgt) if tgt else '—',
                             '% Achieved':'—','Status':'— Q4 Annual'})
                continue
            pct_a = round(val/tgt*100,1) if tgt and tgt>0 else None
            if pct_a is None:   status = '— No target'
            elif pct_a >= 75:   status = '✓ On Track'
            elif pct_a >= 50:   status = '⚠ Watch'
            else:               status = '✗ Behind'
            rows.append({'Indicator':label,'MER Frequency':freq,
                         'Result':_n(val),'Annual Target':_n(tgt) if tgt else '—',
                         '% Achieved':f"{pct_a:.1f}%" if pct_a is not None else '—',
                         'Status':status})

        df_tgt = pd.DataFrame(rows)
        def _cs(v):
            s = str(v)
            if '✓' in s: return 'background-color:#E6F2EB;color:#1A6632;font-weight:bold'
            if '⚠' in s: return 'background-color:#FEF3E2;color:#C87000;font-weight:bold'
            if '✗' in s: return 'background-color:#FDEAEA;color:#BA0C2F;font-weight:bold'
            return ''
        st.dataframe(df_tgt.style.applymap(_cs, subset=['Status']),
                     use_container_width=True, hide_index=True)

        st.markdown("##### Visual Progress")
        for val_key, label, tgt_key, freq in TGT_DISPLAY[:9]:
            val = d.get(val_key,0); tgt=tgts.get(tgt_key)
            if not tgt: continue
            pct_a = min(val/tgt*100, 100)
            col = '#1A6632' if pct_a>=75 else ('#C87000' if pct_a>=50 else '#BA0C2F')
            ca, cb = st.columns([4,1])
            with ca:
                st.markdown(f"""<div style="margin-bottom:8px">
  <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px">
    <span style="font-weight:600;color:#1E293B">{label} <span style="font-weight:400;color:#94A3B8;font-size:9px">({freq})</span></span>
    <span style="font-family:monospace;font-weight:700;color:{col}">{pct_a:.1f}%</span>
  </div>
  <div style="height:8px;background:#E2E8F0;position:relative;border-radius:2px">
    <div style="height:100%;width:{pct_a}%;background:{col};border-radius:2px"></div>
  </div>
</div>""", unsafe_allow_html=True)
            with cb:
                st.markdown(f"<div style='font-size:10px;color:#94A3B8;padding-top:4px'>{_n(val)} / {_n(tgt)}</div>",
                            unsafe_allow_html=True)

    # ── DOWNLOADS ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📥 Download All 4 Outputs")
    dl1,dl2,dl3,dl4 = st.columns(4)
    with dl1:
        dash_html = build_dashboard(results, period_str, qlabel, qmode)
        st.download_button("📊 dashboard.html", data=dash_html.encode('utf-8'),
            file_name=f"ACE3_Dashboard_{qlabel.replace(' ','_')}.html",
            mime='text/html', use_container_width=True)
        st.caption("Full visual dashboard")
    with dl2:
        narr_html = build_narrative(results, period_str, qlabel, qmode)
        st.download_button("📄 narrative_report.html", data=narr_html.encode('utf-8'),
            file_name=f"ACE3_Narrative_{qlabel.replace(' ','_')}.html",
            mime='text/html', use_container_width=True)
        st.caption("Auto-written formal narrative")
    with dl3:
        tp_html = build_talking_points(results, period_str, qlabel, qmode)
        st.download_button("🎯 talking_points.html", data=tp_html.encode('utf-8'),
            file_name=f"ACE3_TalkingPoints_{qlabel.replace(' ','_')}.html",
            mime='text/html', use_container_width=True)
        st.caption("Achievements · concerns · actions")
    with dl4:
        xl_bytes = generate_excel(results)
        st.download_button("📋 ACE3_Data_Report.xlsx", data=xl_bytes,
            file_name=f"ACE3_Data_{qlabel.replace(' ','_')}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True)
        st.caption("DATA_INPUT sheet auto-populated")

else:
    # Welcome screen
    st.markdown("""<div style="background:white;border:1px solid #CBD5E1;padding:48px;text-align:center;margin-top:20px">
  <div style="font-size:52px;margin-bottom:16px">📊</div>
  <div style="font-size:18px;font-weight:700;color:#1F4E79;margin-bottom:8px">ACE3 Programme Report Generator</div>
  <div style="font-size:13px;color:#475569;max-width:520px;margin:0 auto;line-height:1.8">
    Upload your quarterly files in the sidebar, select the reporting period,
    then click <strong>Generate Reports</strong>.
    The system follows the <strong>95–95–95 cascade</strong> and produces 4 downloadable outputs.
  </div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:36px;max-width:720px;margin-left:auto;margin-right:auto">
    <div style="background:#EBF3FB;padding:16px;border-top:3px solid #1F4E79">
      <div style="font-size:22px">📊</div>
      <div style="font-size:11px;font-weight:700;color:#1F4E79;margin-top:6px">dashboard.html</div>
      <div style="font-size:10px;color:#64748B;margin-top:3px">All charts · KPIs · 95-95-95</div>
    </div>
    <div style="background:#E6F2EB;padding:16px;border-top:3px solid #1A6632">
      <div style="font-size:22px">📄</div>
      <div style="font-size:11px;font-weight:700;color:#1A6632;margin-top:6px">narrative_report.html</div>
      <div style="font-size:10px;color:#64748B;margin-top:3px">Auto-written · all numbers</div>
    </div>
    <div style="background:#FEF3E2;padding:16px;border-top:3px solid #C87000">
      <div style="font-size:22px">🎯</div>
      <div style="font-size:11px;font-weight:700;color:#C87000;margin-top:6px">talking_points.html</div>
      <div style="font-size:10px;color:#64748B;margin-top:3px">Achievements · actions</div>
    </div>
    <div style="background:#FDEAEA;padding:16px;border-top:3px solid #BA0C2F">
      <div style="font-size:22px">📋</div>
      <div style="font-size:11px;font-weight:700;color:#BA0C2F;margin-top:6px">Data_Report.xlsx</div>
      <div style="font-size:10px;color:#64748B;margin-top:3px">DATA_INPUT auto-populated</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
