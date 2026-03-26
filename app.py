"""
ACE3 Programme Report Generator
Run: streamlit run app.py
"""
import io, traceback
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif!important;}
.main{background:#F0F4F8;}
.block-container{padding-top:1rem!important;}
.stButton>button{background:#1F4E79;color:white;border:none;border-radius:2px;font-weight:600;font-size:13px;padding:10px 28px;width:100%;}
.stButton>button:hover{background:#2E75B6;}
.upload-slot{background:white;border:1px solid #CBD5E1;padding:12px 14px;margin-bottom:8px;}
.slot-label{font-size:9px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:#94A3B8;margin-bottom:6px;}
div[data-testid="metric-container"]{background:white;border:1px solid #CBD5E1;padding:12px;border-left:4px solid #1F4E79;}
</style>
""", unsafe_allow_html=True)

# ── session state ─────────────────────────────────────────────────────────────
for k in ['results','outputs_ready','quarter_mode','period','quarter_label']:
    if k not in st.session_state:
        st.session_state[k] = None
if 'outputs_ready' not in st.session_state:
    st.session_state.outputs_ready = False

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0F2942,#1F4E79);color:white;padding:16px;margin:-1rem -1rem 1rem;border-bottom:3px solid #BA0C2F">
      <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,.5);margin-bottom:4px">Programme Report System</div>
      <div style="font-size:17px;font-weight:700">ACE3 Generator</div>
      <div style="font-size:10px;color:rgba(255,255,255,.6);margin-top:3px">HSCL · Kebbi · Sokoto · Zamfara</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📅 Reporting Period")
    quarter_mode = st.selectbox(
        "Select quarter",
        ['Q1', 'Q2', 'Semi-Annual (Q1+Q2)', 'Q3 (placeholder)', 'Annual (placeholder)'],
        help="Q3 and Annual tabs will activate once those files are uploaded"
    )

    PERIOD_MAP = {
        'Q1':                       ('Oct – Dec 2025', 'FY26 Q1'),
        'Q2':                       ('Jan – Mar 2026', 'FY26 Q2'),
        'Semi-Annual (Q1+Q2)':      ('Oct 2025 – Mar 2026', 'FY26 Semi-Annual'),
        'Q3 (placeholder)':         ('Apr – Jun 2026', 'FY26 Q3'),
        'Annual (placeholder)':     ('Oct 2025 – Sep 2026', 'FY26 Annual'),
    }
    period_str, qlabel = PERIOD_MAP[quarter_mode]
    qmode_key = 'Q1' if 'Q1' in quarter_mode and 'Q2' not in quarter_mode else \
                'Q2' if quarter_mode == 'Q2' else \
                'SEMI' if 'Semi' in quarter_mode else 'Q1'

    st.markdown("---")
    st.markdown("#### 📁 Static Files *(upload once)*")
    st.caption("These are saved and reused every quarter")

    targets_file  = st.file_uploader("Targets file", type=['csv','xlsx'],
                                      key='tgt', help="Facility-level annual targets")
    vl_elig_file  = st.file_uploader("VL Eligible file", type=['xlsx'],
                                      key='vle', help="Patient-level VL eligibility flags")

    st.markdown("---")
    st.markdown("#### 📂 Q1 Files")
    radet_q1  = st.file_uploader("RADET",            type=['xlsx'], key='r1')
    hts_q1    = st.file_uploader("HTS",               type=['xlsx','csv'], key='h1')
    pmtct_h_q1= st.file_uploader("PMTCT HTS",         type=['xlsx'], key='ph1')
    pmtct_m_q1= st.file_uploader("PMTCT Maternal",    type=['xlsx'], key='pm1')
    tb_q1     = st.file_uploader("TB",                type=['xlsx'], key='tb1')
    ahd_q1    = st.file_uploader("AHD",               type=['xlsx'], key='ahd1')
    prep_q1   = st.file_uploader("PrEP",              type=['xlsx'], key='prep1')
    eac_q1    = st.file_uploader("EAC",               type=['xlsx'], key='eac1')

    if 'Semi' in quarter_mode or quarter_mode == 'Q2':
        st.markdown("#### 📂 Q2 Files")
        radet_q2   = st.file_uploader("RADET (Q2)",         type=['xlsx'], key='r2')
        hts_q2     = st.file_uploader("HTS (Q2)",            type=['xlsx','csv'], key='h2')
        pmtct_h_q2 = st.file_uploader("PMTCT HTS (Q2)",     type=['xlsx'], key='ph2')
        pmtct_m_q2 = st.file_uploader("PMTCT Maternal (Q2)",type=['xlsx'], key='pm2')
        tb_q2      = st.file_uploader("TB (Q2)",             type=['xlsx'], key='tb2')
        ahd_q2     = st.file_uploader("AHD (Q2)",            type=['xlsx'], key='ahd2')
        prep_q2    = st.file_uploader("PrEP (Q2)",           type=['xlsx'], key='prep2')
        eac_q2     = st.file_uploader("EAC (Q2)",            type=['xlsx'], key='eac2')
    else:
        radet_q2=hts_q2=pmtct_h_q2=pmtct_m_q2=tb_q2=ahd_q2=prep_q2=eac_q2=None

    st.markdown("---")
    if st.button("🔄 Reset / Clear Results", use_container_width=True):
        st.session_state.results = None
        st.session_state.outputs_ready = False
        st.rerun()

    run_btn = st.button("▶ Generate Reports", use_container_width=True)

# ── MAIN AREA ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0F2942,#1F4E79);color:white;padding:16px 24px;border-bottom:3px solid #BA0C2F;margin:-1rem -1rem 1.5rem">
  <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,.45);margin-bottom:4px">ACE3 Programme · HSCL · Performance Report System</div>
  <div style="font-size:20px;font-weight:700">Accelerating Control of the HIV Epidemic in Nigeria</div>
  <div style="font-size:11px;color:rgba(255,255,255,.6);margin-top:3px">{period_str} · {qlabel} · Kebbi, Sokoto &amp; Zamfara · 37 Facilities</div>
</div>
""", unsafe_allow_html=True)

# ── RUN ENGINE ────────────────────────────────────────────────────────────────
if run_btn:
    if not radet_q1:
        st.error("⚠ Q1 RADET file is required to generate reports.")
    elif ('Semi' in quarter_mode or quarter_mode == 'Q2') and not radet_q2:
        st.error("⚠ Q2 RADET file is required for this period selection.")
    else:
        with st.spinner("Running ACE3 engine — please wait..."):
            files_q1 = {
                'radet': radet_q1, 'hts': hts_q1,
                'pmtct_hts': pmtct_h_q1, 'pmtct_mat': pmtct_m_q1,
                'tb': tb_q1, 'ahd': ahd_q1, 'prep': prep_q1,
                'eac': eac_q1, 'vl_eligible': vl_elig_file,
            }
            files_q2 = {
                'radet': radet_q2, 'hts': hts_q2,
                'pmtct_hts': pmtct_h_q2, 'pmtct_mat': pmtct_m_q2,
                'tb': tb_q2, 'ahd': ahd_q2, 'prep': prep_q2,
                'eac': eac_q2,
            } if (radet_q2 is not None) else {}

            try:
                results = assemble(
                    files_q1=files_q1,
                    files_q2=files_q2 if files_q2 else None,
                    targets_src=targets_file,
                    quarter_mode=qmode_key
                )
                st.session_state.results = results
                st.session_state.quarter_mode = qmode_key
                st.session_state.period = period_str
                st.session_state.quarter_label = qlabel
                st.session_state.outputs_ready = True

                if results.get('errors'):
                    for e in results['errors']:
                        st.warning(f"⚠ {e}")
                else:
                    st.success("✓ Engine complete — reports ready below")
            except Exception as ex:
                st.error(f"Engine error: {ex}")
                st.code(traceback.format_exc())

# ── RESULTS DISPLAY ───────────────────────────────────────────────────────────
if st.session_state.outputs_ready and st.session_state.results:
    results = st.session_state.results
    qmode   = st.session_state.quarter_mode
    period  = st.session_state.period
    qlabel  = st.session_state.quarter_label

    d = results.get('semi') if qmode=='SEMI' else \
        results.get('q2')   if qmode=='Q2'  else results.get('q1',{})
    tgts = results.get('targets', {})

    if not d:
        st.warning("No results available for the selected quarter.")
        st.stop()

    # helper
    def _pct(n, denom, dec=1): return round(n/denom*100,dec) if denom else 0
    def _n(v): return f"{int(v):,}" if isinstance(v,(int,float)) else '—'

    txc    = d.get('TX_CURR',0)
    vl_s   = d.get('VL_SUPPRESSION',0)
    vl_c   = d.get('VL_COVERAGE',0)
    hts    = d.get('HTS_TST',0)
    tx_ml  = d.get('TX_ML',0)
    mmd_3p = d.get('MMD_3P',0)
    mmd_pct= _pct(mmd_3p,txc)
    tpt    = d.get('TB_PREV_N',0)
    pnew   = d.get('PrEP_NEW',0)
    pvls_d = d.get('TX_PVLS_D',0)
    pvls_n = d.get('TX_PVLS_N',0)
    vl_gap = d.get('VL_GAP',0)
    tx_rtt = d.get('TX_RTT',0)
    cxca_e = d.get('CXCA_SCRN',0)
    cxca_t = d.get('CXCA_TX',0)

    # ── KPI SCORECARDS ────────────────────────────────────────────────────────
    st.markdown("### Key Programme Indicators")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1:
        st.metric("TX_CURR — Active ART", _n(txc),
                  delta=f"{txc/tgts['TX_CURR']*100:.1f}% of target" if tgts.get('TX_CURR') else None)
    with c2:
        st.metric("VL Suppression (3rd 95)", f"{vl_s:.1f}%",
                  delta="✓ Above 95%" if vl_s>=95 else f"⚠ {95-vl_s:.1f}pp gap")
    with c3:
        st.metric("VL Coverage (2nd 95)", f"{vl_c:.1f}%",
                  delta=f"Gap: {_n(vl_gap)} samples" if vl_c<95 else "✓ On target")
    with c4:
        st.metric("HIV Tests (HTS_TST)", _n(hts),
                  delta=f"{hts/tgts['HTS_TST']*100:.1f}% of target" if tgts.get('HTS_TST') else None)
    with c5:
        rtt_r = _pct(tx_rtt, tx_ml)
        st.metric("TX_ML (Interruptions)", _n(tx_ml),
                  delta=f"RTT: {rtt_r:.1f}%", delta_color="inverse")
    with c6:
        st.metric("MMD ≥3 Months", f"{mmd_pct:.1f}%",
                  delta="✓ Above 90%" if mmd_pct>=90 else f"⚠ {90-mmd_pct:.1f}pp gap")

    st.markdown("---")

    # ── DASHBOARD TABS ────────────────────────────────────────────────────────
    tab_labels = ["📊 Dashboard", "🎯 Targets", "📈 VL & Retention",
                  "🧪 Testing & PMTCT", "💊 PrEP", "🏥 AHD & CxCa"]
    if qmode == 'SEMI':
        tab_labels.insert(1, "🔄 Q1 vs Q2")

    tabs = st.tabs(tab_labels)
    tab_idx = 0

    # DASHBOARD TAB
    with tabs[tab_idx]:
        tab_idx += 1
        col1, col2 = st.columns([2,1])
        with col1:
            state_curr = d.get('TX_CURR_STATE',{})
            states = list(state_curr.keys()) or ['Kebbi','Sokoto','Zamfara']
            fem_r  = d.get('TX_CURR_F',0)/txc if txc else 0.645
            fig = go.Figure()
            fig.add_bar(name='Female', x=states,
                        y=[round(state_curr.get(s,0)*fem_r) for s in states],
                        marker_color='#2E75B6')
            fig.add_bar(name='Male',   x=states,
                        y=[round(state_curr.get(s,0)*(1-fem_r)) for s in states],
                        marker_color='#1F4E79')
            fig.update_layout(barmode='stack', title='TX_CURR by State & Sex',
                              height=280, margin=dict(t=40,b=20,l=10,r=10),
                              legend=dict(orientation='h',y=1.1),
                              paper_bgcolor='white', plot_bgcolor='white')
            fig.update_xaxes(showgrid=False); fig.update_yaxes(gridcolor='#EAECEF')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            mmd_6p = d.get('MMD_6P',0); mmd_lt3=d.get('MMD_LT3',0)
            mmd_35 = mmd_3p - mmd_6p
            fig2 = go.Figure(go.Pie(
                labels=['6+ months','3–5 months','<3 months'],
                values=[mmd_6p, mmd_35, mmd_lt3],
                hole=0.65, marker_colors=['#1A6632','#2E75B6','#BA0C2F']
            ))
            fig2.update_layout(title='MMD Distribution', height=280,
                               margin=dict(t=40,b=20,l=10,r=10),
                               paper_bgcolor='white',
                               legend=dict(orientation='h',y=-0.1))
            st.plotly_chart(fig2, use_container_width=True)

        # TB + PrEP row
        col3, col4 = st.columns(2)
        with col3:
            tpt_c = _pct(tpt,txc); tb_scr=d.get('TB_SCREEN',0)
            fig3 = go.Figure()
            fig3.add_bar(x=['TB Screened','TPT Started','Screen+'],
                         y=[tb_scr, tpt, d.get('TB_SCREEN_POS',0)],
                         marker_color=['#2E75B6','#1A6632','#BA0C2F'])
            fig3.update_layout(title=f'TB/HIV — TPT Coverage {tpt_c:.1f}%',
                               height=260, margin=dict(t=40,b=20,l=10,r=10),
                               paper_bgcolor='white',plot_bgcolor='white')
            fig3.update_xaxes(showgrid=False)
            fig3.update_yaxes(gridcolor='#EAECEF',tickformat=',')
            st.plotly_chart(fig3, use_container_width=True)
        with col4:
            prep_st = d.get('PrEP_NEW_STATE',{}); prep_states = list(prep_st.keys()) or states
            fig4 = go.Figure(go.Bar(
                x=prep_states, y=[int(prep_st.get(s,0)) for s in prep_states],
                marker_color=['#1F4E79','#2E75B6','#4A90C4']
            ))
            fig4.update_layout(title=f'PrEP_NEW by State (Total: {_n(pnew)})',
                               height=260, margin=dict(t=40,b=20,l=10,r=10),
                               paper_bgcolor='white',plot_bgcolor='white')
            fig4.update_xaxes(showgrid=False)
            fig4.update_yaxes(gridcolor='#EAECEF')
            st.plotly_chart(fig4, use_container_width=True)

    # Q1 vs Q2 TAB (semi-annual only)
    if qmode == 'SEMI':
        with tabs[tab_idx]:
            tab_idx += 1
            q1d = results.get('q1',{}); q2d = results.get('q2',{})
            st.markdown("### Quarter-on-Quarter Performance: Q1 vs Q2")
            QOQ_INDICATORS = [
                ('HIV Tests (HTS_TST)', 'HTS_TST', False),
                ('New ART Initiations (TX_NEW)', 'TX_NEW', False),
                ('Treatment Interruptions (TX_ML)', 'TX_ML', True),
                ('VL Tests Resulted (TX_PVLS_D)', 'TX_PVLS_D', False),
                ('PMTCT ANC Tested', 'PMTCT_STAT_N', False),
                ('PrEP New (PrEP_NEW)', 'PrEP_NEW', False),
                ('TB Screened', 'TB_SCREEN', False),
                ('TPT Started', 'TB_PREV_N', False),
            ]
            rows = []
            for label, key, invert in QOQ_INDICATORS:
                v1 = q1d.get(key,0); v2 = q2d.get(key,0)
                if not v1 and not v2: continue
                diff = v2-v1; pct_c = diff/v1*100 if v1 else 0
                trend = '▲' if diff>0 else '▼' if diff<0 else '→'
                good = (diff<=0) if invert else (diff>=0)
                rows.append({'Indicator':label,'Q1':v1,'Q2':v2,
                             'Change':diff,'%Δ':f"{'+' if pct_c>=0 else ''}{pct_c:.1f}%",
                             'Trend':trend,'Signal':'✓' if good else '⚠'})
            if rows:
                df_qoq = pd.DataFrame(rows)
                st.dataframe(df_qoq.style.applymap(
                    lambda v: 'color:#BA0C2F;font-weight:bold' if v=='⚠' else 'color:#1A6632;font-weight:bold',
                    subset=['Signal']
                ), use_container_width=True, hide_index=True)

            # Visual comparison
            st.markdown("#### Visual: Q1 vs Q2 comparison")
            plot_keys = ['HTS_TST','TX_NEW','TX_ML','PMTCT_STAT_N','PrEP_NEW']
            plot_labels = ['HTS_TST','TX_NEW','TX_ML','PMTCT','PrEP_NEW']
            fig_qoq = go.Figure()
            fig_qoq.add_bar(name='Q1', x=plot_labels,
                            y=[q1d.get(k,0) for k in plot_keys], marker_color='#2E75B6')
            fig_qoq.add_bar(name='Q2', x=plot_labels,
                            y=[q2d.get(k,0) for k in plot_keys], marker_color='#1F4E79')
            fig_qoq.update_layout(barmode='group', height=320,
                                  margin=dict(t=20,b=20,l=10,r=10),
                                  paper_bgcolor='white', plot_bgcolor='white',
                                  legend=dict(orientation='h',y=1.1))
            fig_qoq.update_xaxes(showgrid=False)
            fig_qoq.update_yaxes(gridcolor='#EAECEF', tickformat=',')
            st.plotly_chart(fig_qoq, use_container_width=True)

    # TARGETS TAB
    with tabs[tab_idx]:
        tab_idx += 1
        st.markdown("### Targets Achievement Tracker")
        st.caption(f"Result ({qlabel} cumulative) vs Annual Target. TX_CURR is period-end snapshot.")

        TGT_DISPLAY = [
            ('TX_CURR', 'Active on ART', 'TX_CURR', True, 'Quarterly'),
            ('TX_NEW', 'New ART Initiations', 'TX_NEW', False, 'Quarterly'),
            ('HTS_TST', 'HIV Tests', 'HTS_TST', False, 'Quarterly'),
            ('HTS_TST_POS', 'HIV Positive Results', 'HTS_TST_POS', False, 'Quarterly'),
            ('TX_PVLS_D', 'VL Tests Resulted', 'TX_PVLS_D', False, 'Quarterly'),
            ('TX_PVLS_N', 'VL Suppressed', 'TX_PVLS_N', False, 'Quarterly'),
            ('PMTCT_STAT_N', 'ANC Clients Tested', 'PMTCT_STAT_N', False, 'Quarterly'),
            ('PMTCT_ART_D', 'PMTCT on ART', 'PMTCT_ART_D', False, 'Quarterly'),
            ('PrEP_NEW', 'New PrEP Initiations', 'PrEP_NEW', False, 'Quarterly'),
            ('TB_PREV_N', 'TPT Started', 'TB_PREV_N', False, 'Semi-Annual'),
            ('TX_TB_N', 'TB/HIV on ART', 'TX_TB_N', False, 'Semi-Annual'),
            ('TB_ART', 'TB Patients on ART', 'TB_ART', False, 'Annual — Q4 only'),
        ]
        rows = []
        for val_key, label, tgt_key, snap, freq in TGT_DISPLAY:
            val = d.get(val_key, 0)
            tgt = tgts.get(tgt_key)
            pct_a = round(val/tgt*100,1) if tgt and tgt>0 else None
            if freq == 'Annual — Q4 only' and qmode != 'Q4':
                status = '— Annual (Q4)'
            elif pct_a is None:
                status = '— No target'
            elif pct_a >= 75: status = '✓ On Track'
            elif pct_a >= 50: status = '⚠ Watch'
            else: status = '✗ Behind'
            rows.append({
                'Indicator': label, 'MER Freq': freq,
                'Result': val, 'Annual Target': tgt or '—',
                '% Achieved': f"{pct_a:.1f}%" if pct_a is not None else '—',
                'Status': status
            })

        df_tgt = pd.DataFrame(rows)
        def _colour_status(v):
            if '✓' in str(v): return 'background-color:#E6F2EB;color:#1A6632;font-weight:bold'
            if '⚠' in str(v): return 'background-color:#FEF3E2;color:#C87000;font-weight:bold'
            if '✗' in str(v): return 'background-color:#FDEAEA;color:#BA0C2F;font-weight:bold'
            return ''
        st.dataframe(df_tgt.style.applymap(_colour_status, subset=['Status']),
                     use_container_width=True, hide_index=True)

        # Progress bars
        st.markdown("#### Visual Progress Bars")
        for val_key, label, tgt_key, snap, freq in TGT_DISPLAY[:9]:
            val = d.get(val_key,0); tgt=tgts.get(tgt_key)
            if not tgt: continue
            pct_a = min(val/tgt*100, 100)
            col_a, col_b = st.columns([4,1])
            with col_a:
                colour = '#1A6632' if pct_a>=75 else ('#C87000' if pct_a>=50 else '#BA0C2F')
                st.markdown(f"""
                <div style="margin-bottom:8px">
                  <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px">
                    <span style="font-weight:600">{label}</span>
                    <span style="font-family:monospace;font-weight:700;color:{colour}">{pct_a:.1f}%</span>
                  </div>
                  <div style="height:8px;background:#E8ECF0;position:relative">
                    <div style="height:100%;width:{pct_a}%;background:{colour}"></div>
                  </div>
                </div>""", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"<div style='font-size:10px;color:#94A3B8;padding-top:4px'>{_n(val)} / {_n(tgt)}</div>",
                            unsafe_allow_html=True)

    # VL & RETENTION TAB
    with tabs[tab_idx]:
        tab_idx += 1
        st.markdown("### Viral Load & Retention")
        col1, col2 = st.columns(2)
        with col1:
            unsupp = d.get('VL_UNSUPP',0)
            fig_vl = go.Figure()
            fig_vl.add_trace(go.Indicator(
                mode='gauge+number', value=vl_s,
                title={'text':'VL Suppression (3rd 95)','font':{'size':13}},
                gauge={'axis':{'range':[0,100],'tickwidth':1},
                       'bar':{'color':'#1A6632' if vl_s>=95 else '#C87000'},
                       'steps':[{'range':[0,75],'color':'#FDEAEA'},
                                 {'range':[75,95],'color':'#FEF3E2'},
                                 {'range':[95,100],'color':'#E6F2EB'}],
                       'threshold':{'line':{'color':'#1F4E79','width':3},'value':95}},
                number={'suffix':'%','font':{'size':32,'family':'IBM Plex Mono'}}
            ))
            fig_vl.update_layout(height=280, margin=dict(t=60,b=20,l=30,r=30),
                                  paper_bgcolor='white')
            st.plotly_chart(fig_vl, use_container_width=True)
            st.metric("Unsuppressed clients", _n(unsupp), help="Require EAC")
        with col2:
            fig_vc = go.Figure()
            fig_vc.add_trace(go.Indicator(
                mode='gauge+number', value=vl_c,
                title={'text':'VL Coverage (2nd 95)','font':{'size':13}},
                gauge={'axis':{'range':[0,100],'tickwidth':1},
                       'bar':{'color':'#1A6632' if vl_c>=95 else '#C87000'},
                       'steps':[{'range':[0,75],'color':'#FDEAEA'},
                                 {'range':[75,95],'color':'#FEF3E2'},
                                 {'range':[95,100],'color':'#E6F2EB'}],
                       'threshold':{'line':{'color':'#1F4E79','width':3},'value':95}},
                number={'suffix':'%','font':{'size':32,'family':'IBM Plex Mono'}}
            ))
            fig_vc.update_layout(height=280, margin=dict(t=60,b=20,l=30,r=30),
                                  paper_bgcolor='white')
            st.plotly_chart(fig_vc, use_container_width=True)
            st.metric("Sample gap", _n(vl_gap), help="Clients without VL result")

        st.markdown("#### TX_ML Outcomes")
        ml_out = d.get('TX_ML_OUTCOMES',{})
        if ml_out:
            labels = list(ml_out.keys()); vals=[int(v) for v in ml_out.values()]
            fig_ml = go.Figure(go.Bar(
                y=labels, x=vals, orientation='h',
                marker_color=['#BA0C2F','#7B1D1D','#1F4E79','#888'][:len(labels)]
            ))
            fig_ml.update_layout(height=240, margin=dict(t=20,b=20,l=10,r=10),
                                  paper_bgcolor='white',plot_bgcolor='white')
            fig_ml.update_xaxes(gridcolor='#EAECEF',tickformat=',')
            fig_ml.update_yaxes(showgrid=False)
            st.plotly_chart(fig_ml, use_container_width=True)

    # TESTING & PMTCT TAB
    with tabs[tab_idx]:
        tab_idx += 1
        st.markdown("### HIV Testing & PMTCT")
        hts_p  = d.get('HTS_TST_POS',0); hts_y=d.get('HTS_YIELD',0)
        pmtc_n = d.get('PMTCT_STAT_N',0); pmtc_p=d.get('PMTCT_STAT_POS',0)
        pmtc_a = d.get('PMTCT_ART_D',0); eid=d.get('PMTCT_EID',0)
        deliv  = d.get('PMTCT_DELIVERED',0)
        col1,col2 = st.columns(2)
        with col1:
            state_hts = d.get('HTS_STATE',{})
            hs = list(state_hts.keys()) or ['Kebbi','Sokoto','Zamfara']
            fig_hts = go.Figure(go.Bar(
                x=hs, y=[int(state_hts.get(s,0)) for s in hs],
                marker_color=['#1F4E79','#2E75B6','#4A90C4']
            ))
            fig_hts.update_layout(
                title=f'HIV Tests by State — Yield {hts_y:.2f}%',
                height=280, margin=dict(t=40,b=20,l=10,r=10),
                paper_bgcolor='white',plot_bgcolor='white')
            fig_hts.update_xaxes(showgrid=False)
            fig_hts.update_yaxes(gridcolor='#EAECEF',tickformat=',')
            st.plotly_chart(fig_hts, use_container_width=True)
        with col2:
            fig_pm = go.Figure(go.Bar(
                y=['ANC Tested','HIV+','On ART','EID PCR'],
                x=[pmtc_n, pmtc_p, pmtc_a, eid],
                orientation='h',
                marker_color=['#1F4E79','#BA0C2F','#1A6632','#C87000']
            ))
            fig_pm.update_layout(title='PMTCT Cascade', height=280,
                                  margin=dict(t=40,b=20,l=10,r=10),
                                  paper_bgcolor='white',plot_bgcolor='white')
            fig_pm.update_xaxes(gridcolor='#EAECEF',tickformat=',',type='log')
            fig_pm.update_yaxes(showgrid=False)
            st.plotly_chart(fig_pm, use_container_width=True)
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;margin-top:8px">
          <div style="background:white;border:1px solid #CBD5E1;padding:12px;text-align:center">
            <div style="font-size:22px;font-weight:700;font-family:monospace;color:#1F4E79">{_n(pmtc_p)}</div>
            <div style="font-size:9px;text-transform:uppercase;letter-spacing:.8px;color:#94A3B8">HIV+ at ANC</div>
          </div>
          <div style="background:white;border:1px solid #CBD5E1;padding:12px;text-align:center">
            <div style="font-size:22px;font-weight:700;font-family:monospace;color:#1F4E79">{_n(pmtc_a)}</div>
            <div style="font-size:9px;text-transform:uppercase;letter-spacing:.8px;color:#94A3B8">PMTCT on ART</div>
          </div>
          <div style="background:white;border:1px solid #CBD5E1;padding:12px;text-align:center">
            <div style="font-size:22px;font-weight:700;font-family:monospace;color:#1F4E79">{_n(eid)}</div>
            <div style="font-size:9px;text-transform:uppercase;letter-spacing:.8px;color:#94A3B8">EID PCR Done</div>
          </div>
          <div style="background:{'#E6F2EB' if deliv and eid/deliv*100>=95 else '#FEF3E2'};border:1px solid #CBD5E1;padding:12px;text-align:center">
            <div style="font-size:22px;font-weight:700;font-family:monospace;color:{'#1A6632' if deliv and eid/deliv*100>=95 else '#C87000'}">{f'{eid/deliv*100:.1f}%' if deliv else '—'}</div>
            <div style="font-size:9px;text-transform:uppercase;letter-spacing:.8px;color:#94A3B8">EID Coverage</div>
          </div>
        </div>""", unsafe_allow_html=True)

    # PrEP TAB
    with tabs[tab_idx]:
        tab_idx += 1
        st.markdown("### PrEP Programme")
        pct_  = d.get('PrEP_CT',0); pcurr=d.get('PrEP_CURR',0)
        prep_pop = d.get('PrEP_NEW_POP',{})
        col1,col2 = st.columns(2)
        with col1:
            prep_st = d.get('PrEP_NEW_STATE',{})
            st_keys = list(prep_st.keys()) or ['Kebbi','Sokoto','Zamfara']
            fig_p = go.Figure(go.Bar(
                x=st_keys, y=[int(prep_st.get(s,0)) for s in st_keys],
                marker_color=['#1F4E79','#2E75B6','#4A90C4']
            ))
            fig_p.update_layout(title=f'PrEP_NEW by State — Total {_n(pnew)}',
                                 height=280, margin=dict(t=40,b=20,l=10,r=10),
                                 paper_bgcolor='white',plot_bgcolor='white')
            fig_p.update_xaxes(showgrid=False)
            fig_p.update_yaxes(gridcolor='#EAECEF')
            st.plotly_chart(fig_p, use_container_width=True)
        with col2:
            if prep_pop:
                fig_pp = go.Figure(go.Pie(
                    labels=list(prep_pop.keys()),
                    values=[int(v) for v in prep_pop.values()],
                    hole=0.5
                ))
                fig_pp.update_layout(title='PrEP_NEW by Population Type',
                                      height=280, margin=dict(t=40,b=20,l=10,r=10),
                                      paper_bgcolor='white',
                                      legend=dict(font=dict(size=10)))
                st.plotly_chart(fig_pp, use_container_width=True)
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:8px">
          <div style="background:white;border:1px solid #CBD5E1;padding:12px;text-align:center;border-top:3px solid #1F4E79">
            <div style="font-size:24px;font-weight:700;font-family:monospace;color:#1F4E79">{_n(pnew)}</div>
            <div style="font-size:9px;text-transform:uppercase;letter-spacing:.8px;color:#94A3B8;margin-top:4px">PrEP_NEW — New Initiations</div>
          </div>
          <div style="background:white;border:1px solid #CBD5E1;padding:12px;text-align:center;border-top:3px solid #2E75B6">
            <div style="font-size:24px;font-weight:700;font-family:monospace;color:#2E75B6">{_n(pct_)}</div>
            <div style="font-size:9px;text-transform:uppercase;letter-spacing:.8px;color:#94A3B8;margin-top:4px">PrEP_CT — Continuing</div>
          </div>
          <div style="background:white;border:1px solid #CBD5E1;padding:12px;text-align:center;border-top:3px solid #1A6632">
            <div style="font-size:24px;font-weight:700;font-family:monospace;color:#1A6632">{_n(pcurr)}</div>
            <div style="font-size:9px;text-transform:uppercase;letter-spacing:.8px;color:#94A3B8;margin-top:4px">PrEP_CURR — Active Snapshot</div>
          </div>
        </div>""", unsafe_allow_html=True)

    # AHD & CxCa TAB
    with tabs[tab_idx]:
        tab_idx += 1
        st.markdown("### Advanced HIV Disease & Cervical Cancer Screening")
        ahd_s=d.get('AHD_SCRN',0); ahd_c=d.get('AHD_CONF',0)
        ahd_cd4=d.get('AHD_CD4',0); ahd_tbl=d.get('AHD_TBLAM_POS',0); ahd_cr=d.get('AHD_CRAG_POS',0)
        cxca_r=d.get('CXCA_RESULTS',{})
        col1,col2 = st.columns(2)
        with col1:
            fig_ahd = go.Figure(go.Bar(
                x=['Screened','AHD Confirmed','CD4 Done'],
                y=[ahd_s, ahd_c, ahd_cd4],
                marker_color=['#1F4E79','#BA0C2F','#2E75B6']
            ))
            fig_ahd.update_layout(title=f'AHD — {ahd_c/ahd_s*100:.1f}% detection rate' if ahd_s else 'AHD',
                                   height=280, margin=dict(t=40,b=20,l=10,r=10),
                                   paper_bgcolor='white',plot_bgcolor='white')
            fig_ahd.update_xaxes(showgrid=False)
            fig_ahd.update_yaxes(gridcolor='#EAECEF',tickformat=',')
            st.plotly_chart(fig_ahd, use_container_width=True)
        with col2:
            cxca_neg=cxca_r.get('Negative',0) or cxca_r.get('Negative VIA',0) or 0
            cxca_pos=cxca_r.get('Positive',0) or cxca_r.get('Positive VIA',0) or 0
            cxca_sus=cxca_r.get('Suspicious',0) or 0
            cxca_un = max(0, cxca_e-cxca_t)
            fig_cx = go.Figure(go.Pie(
                labels=['Not screened','Negative','Positive','Suspicious'],
                values=[cxca_un, cxca_neg, cxca_pos, cxca_sus],
                hole=0.6, marker_colors=['#C8C8C8','#1A6632','#C87000','#BA0C2F']
            ))
            fig_cx.update_layout(
                title=f'CxCa — {cxca_t/cxca_e*100:.1f}% coverage ({_n(cxca_t)} of {_n(cxca_e)})' if cxca_e else 'CxCa',
                height=280, margin=dict(t=40,b=20,l=10,r=10),
                paper_bgcolor='white', legend=dict(font=dict(size=10)))
            st.plotly_chart(fig_cx, use_container_width=True)
        if cxca_pos+cxca_sus > 0:
            st.error(f"⚠ {cxca_pos+cxca_sus} women with positive/suspicious CxCa findings require urgent clinical follow-up.")

    # ── DOWNLOAD SECTION ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📥 Download All 4 Outputs")
    dl1, dl2, dl3, dl4 = st.columns(4)

    with dl1:
        dash_html = build_dashboard(results, period_str, qlabel, qmode)
        st.download_button(
            "📊 dashboard.html",
            data=dash_html.encode('utf-8'),
            file_name=f"ACE3_Dashboard_{qlabel.replace(' ','_')}.html",
            mime='text/html', use_container_width=True
        )
        st.caption("Full visual dashboard — all charts & KPIs")

    with dl2:
        narr_html = build_narrative(results, period_str, qlabel, qmode)
        st.download_button(
            "📄 narrative_report.html",
            data=narr_html.encode('utf-8'),
            file_name=f"ACE3_Narrative_{qlabel.replace(' ','_')}.html",
            mime='text/html', use_container_width=True
        )
        st.caption("Formal narrative — all numbers auto-written")

    with dl3:
        tp_html = build_talking_points(results, period_str, qlabel, qmode)
        st.download_button(
            "🎯 talking_points.html",
            data=tp_html.encode('utf-8'),
            file_name=f"ACE3_TalkingPoints_{qlabel.replace(' ','_')}.html",
            mime='text/html', use_container_width=True
        )
        st.caption("Achievements, concerns, actions")

    with dl4:
        xl_bytes = generate_excel(results)
        st.download_button(
            "📋 ACE3_Data_Report.xlsx",
            data=xl_bytes,
            file_name=f"ACE3_Data_Report_{qlabel.replace(' ','_')}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True
        )
        st.caption("Single DATA_INPUT sheet — all indicators auto-populated")

else:
    # Welcome screen
    st.markdown("""
    <div style="background:white;border:1px solid #CBD5E1;padding:40px;text-align:center;margin-top:20px">
      <div style="font-size:48px;margin-bottom:16px">📊</div>
      <div style="font-size:18px;font-weight:700;color:#1F4E79;margin-bottom:8px">Ready to generate reports</div>
      <div style="font-size:13px;color:#475569;max-width:500px;margin:0 auto;line-height:1.7">
        Upload your files in the sidebar, select the reporting quarter, then click <strong>Generate Reports</strong>.
        You will receive 4 downloadable outputs: dashboard, narrative report, talking points, and Excel data report.
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;margin-top:32px;max-width:700px;margin-left:auto;margin-right:auto">
        <div style="background:#EBF3FB;padding:14px;border-top:3px solid #1F4E79">
          <div style="font-size:20px">📊</div><div style="font-size:11px;font-weight:600;color:#1F4E79;margin-top:6px">dashboard.html</div>
          <div style="font-size:10px;color:#64748B">All charts & KPIs</div>
        </div>
        <div style="background:#E6F2EB;padding:14px;border-top:3px solid #1A6632">
          <div style="font-size:20px">📄</div><div style="font-size:11px;font-weight:600;color:#1A6632;margin-top:6px">narrative_report.html</div>
          <div style="font-size:10px;color:#64748B">Auto-written report</div>
        </div>
        <div style="background:#FEF3E2;padding:14px;border-top:3px solid #C87000">
          <div style="font-size:20px">🎯</div><div style="font-size:11px;font-weight:600;color:#C87000;margin-top:6px">talking_points.html</div>
          <div style="font-size:10px;color:#64748B">Achievements & actions</div>
        </div>
        <div style="background:#FDEAEA;padding:14px;border-top:3px solid #BA0C2F">
          <div style="font-size:20px">📋</div><div style="font-size:11px;font-weight:600;color:#BA0C2F;margin-top:6px">Data_Report.xlsx</div>
          <div style="font-size:10px;color:#64748B">DATA_INPUT sheet</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
