"""
ACE3 HTML Report Generator — v2
Cascade order: HTS → TX_NEW → PMTCT → TX_CURR → Retention → VL → EAC → TB → PrEP → CxCa → AHD → Targets
KPI scorecards: HTS_TST · TX_NEW · TX_CURR · TX_ML · VL Suppression · PMTCT
No mention of PEPFAR or USAID anywhere.
"""
import json

# ── shared base CSS ───────────────────────────────────────────────────────────
BASE_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;600&display=swap');
:root{
  --navy:#1F4E79;--blue:#2E75B6;--lblue:#D6E4F0;--sblue:#EBF3FB;
  --red:#BA0C2F;--lred:#FDEAEA;--green:#1A6632;--lgreen:#E6F2EB;
  --amber:#C87000;--lamber:#FEF3E2;--teal:#0E7490;--lteal:#E0F2FE;
  --border:#CBD5E1;--bg:#F0F4F8;--white:#FFFFFF;
  --dark:#0F172A;--mid:#475569;--light:#94A3B8;
  --font:'IBM Plex Sans',sans-serif;--mono:'IBM Plex Mono',monospace;
}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:var(--font);background:var(--bg);color:var(--dark);font-size:12.5px;line-height:1.5;}
.hdr{background:linear-gradient(135deg,#0F2942 0%,var(--navy) 60%,#2056a0 100%);color:#fff;display:grid;grid-template-columns:1fr auto;border-bottom:4px solid var(--red);}
.hdr-l{padding:20px 28px;}
.hdr-eyebrow{font-size:9.5px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:rgba(255,255,255,.5);margin-bottom:5px;}
.hdr-title{font-size:22px;font-weight:700;line-height:1.2;letter-spacing:-.2px;}
.hdr-sub{font-size:11.5px;color:rgba(255,255,255,.65);margin-top:5px;}
.hdr-r{background:rgba(0,0,0,.22);padding:18px 24px;border-left:1px solid rgba(255,255,255,.1);display:flex;flex-direction:column;justify-content:center;gap:7px;min-width:255px;}
.meta{display:flex;justify-content:space-between;align-items:center;gap:14px;}
.ml{font-size:9px;letter-spacing:1px;text-transform:uppercase;color:rgba(255,255,255,.45);}
.mv{font-size:11px;font-weight:600;}
.alert{background:#FFFAEB;border-top:1px solid #F5C842;border-bottom:1px solid #F5C842;border-left:5px solid var(--amber);padding:9px 18px;font-size:10.5px;font-weight:600;color:#7B4500;display:flex;gap:6px;align-items:flex-start;}
.alert-items{display:flex;flex-wrap:wrap;gap:4px 18px;}
.ai{display:flex;align-items:center;gap:5px;}
.ai-dot{width:7px;height:7px;background:var(--red);border-radius:50%;flex-shrink:0;}
.dash{padding:16px 20px;display:flex;flex-direction:column;gap:16px;}
.sec-hdr{font-size:9px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:var(--navy);border-bottom:2px solid var(--navy);padding-bottom:4px;margin-bottom:10px;}
.kpi-row{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;}
.kpi{background:var(--white);border:1px solid var(--border);padding:13px 13px 10px;position:relative;overflow:hidden;}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;}
.kpi.navy::before{background:var(--navy);}.kpi.blue::before{background:var(--blue);}
.kpi.green::before{background:var(--green);}.kpi.red::before{background:var(--red);}
.kpi.amber::before{background:var(--amber);}.kpi.teal::before{background:var(--teal);}
.kpi-lbl{font-size:9px;font-weight:600;letter-spacing:.8px;text-transform:uppercase;color:var(--light);line-height:1.3;margin-bottom:6px;}
.kpi-val{font-size:25px;font-weight:700;font-family:var(--mono);line-height:1;margin-bottom:3px;}
.kpi-sub{font-size:9.5px;color:var(--mid);}
.badge{display:inline-block;font-size:8.5px;font-weight:700;padding:2px 6px;margin-top:5px;}
.bg{background:var(--lgreen);color:var(--green);}.br{background:var(--lred);color:var(--red);}
.ba{background:var(--lamber);color:var(--amber);}.bb{background:var(--sblue);color:var(--navy);}
.bt{background:var(--lteal);color:var(--teal);}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;}
.g32{display:grid;grid-template-columns:2fr 1fr;gap:12px;}
.g23{display:grid;grid-template-columns:1fr 2fr;gap:12px;}
.card{background:var(--white);border:1px solid var(--border);padding:14px;}
.ct{font-size:11px;font-weight:700;color:var(--dark);margin-bottom:2px;}
.cs{font-size:9.5px;color:var(--light);margin-bottom:10px;}
.leg{display:flex;flex-direction:column;gap:5px;margin-top:8px;}
.li{display:flex;align-items:center;gap:6px;}
.ld{width:9px;height:9px;border-radius:50%;flex-shrink:0;}
.lt{font-size:10px;color:var(--mid);flex:1;}.lv{font-size:10px;font-weight:700;font-family:var(--mono);}
.lp{font-size:9px;color:var(--light);margin-left:3px;}
.prg-wrap{display:flex;flex-direction:column;gap:12px;margin-top:10px;}
.prg-hdr{display:flex;justify-content:space-between;margin-bottom:5px;}
.prg-name{font-size:11px;font-weight:600;}.prg-pct{font-size:12px;font-weight:700;font-family:var(--mono);}
.prg-tgt{font-size:9.5px;color:var(--light);}.prg-note{font-size:9px;color:var(--light);}
.bar-bg{height:9px;background:#E8ECF0;position:relative;}
.bar-fill{height:100%;}.bar-tline{position:absolute;top:-4px;width:2px;height:17px;background:rgba(0,0,0,.35);}
.stats{display:flex;border:1px solid var(--border);}
.sb{flex:1;padding:10px 12px;border-right:1px solid var(--border);text-align:center;}
.sb:last-child{border-right:none;}
.sbv{font-size:17px;font-weight:700;font-family:var(--mono);}
.sbl{font-size:8.5px;text-transform:uppercase;letter-spacing:.8px;color:var(--light);margin-top:2px;}
.tbl{width:100%;border-collapse:collapse;margin-top:6px;}
.tbl th{font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;background:var(--navy);color:#fff;padding:6px 9px;text-align:left;}
.tbl td{padding:6px 9px;font-size:11px;border-bottom:1px solid var(--border);}
.tbl tr:nth-child(even) td{background:#F8FAFC;}
.num{font-family:var(--mono);font-weight:600;text-align:right;}
.dn{color:var(--red);font-weight:700;}.ok{color:var(--green);font-weight:700;}
.mini-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;text-align:center;margin-top:10px;}
.mini-2{display:grid;grid-template-columns:1fr 1fr;gap:6px;text-align:center;margin-top:10px;}
.mini-4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;text-align:center;margin-top:10px;}
.mt{padding:8px 6px;border:1px solid var(--border);}
.mt-v{font-size:19px;font-weight:700;font-family:var(--mono);}
.mt-l{font-size:8.5px;text-transform:uppercase;letter-spacing:.7px;color:var(--light);margin-top:2px;line-height:1.3;}
.ahd-g{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px;}
.ahd-t{padding:9px 11px;border:1px solid var(--border);}
.ahd-v{font-size:20px;font-weight:700;font-family:var(--mono);}
.ahd-l{font-size:8.5px;text-transform:uppercase;letter-spacing:.8px;color:var(--light);margin-top:2px;}
.ahd-s{font-size:9.5px;color:var(--mid);margin-top:1px;}
.ftr{background:var(--dark);color:rgba(255,255,255,.5);padding:10px 24px;display:flex;justify-content:space-between;align-items:center;font-size:9.5px;margin-top:6px;}
.ftr-brand{font-weight:700;font-size:10.5px;color:#fff;}
</style>"""

CHARTJS = '<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>'

CHART_DEFAULTS = """<script>
Chart.defaults.font.family="'IBM Plex Sans',sans-serif";
Chart.defaults.font.size=10.5;
Chart.defaults.plugins.legend.display=false;
Chart.defaults.plugins.tooltip.padding=8;
Chart.defaults.plugins.tooltip.cornerRadius=2;
Chart.defaults.plugins.tooltip.backgroundColor='#1F4E79';
function gauge(id,val,color){
  new Chart(document.getElementById(id),{
    type:'doughnut',
    data:{datasets:[{data:[val,100-val],backgroundColor:[color,'#E8ECF0'],borderWidth:0}]},
    options:{responsive:true,maintainAspectRatio:false,circumference:240,rotation:-120,cutout:'75%',
      plugins:{tooltip:{enabled:false}}}
  });
}
</script>"""

# ── helpers ───────────────────────────────────────────────────────────────────
def _n(v, dec=0):
    if v is None: return '—'
    if isinstance(v, float) and dec > 0: return f"{v:,.{dec}f}"
    return f"{int(round(float(v))):,}" if isinstance(v,(int,float)) else str(v)

def _p(v, dec=1):
    if v is None: return '—'
    return f"{float(v):.{dec}f}%"

def _chg(v1, v2):
    if not isinstance(v1,(int,float)) or not isinstance(v2,(int,float)): return '—','—',''
    diff=v2-v1; pct=(diff/v1*100) if v1!=0 else 0
    sign='▲' if diff>0 else '▼'
    return f"{sign} {abs(int(diff)):,}", f"{sign} {abs(pct):.1f}%", ('up' if diff>0 else 'ok')

def _col(val, threshold, invert=False):
    """Return css colour name based on threshold."""
    if invert:
        return 'green' if val<=threshold*0.05 else ('amber' if val<=threshold*0.1 else 'red')
    return 'green' if val>=threshold else ('amber' if val>=threshold*0.8 else 'red')

def _progress_bar(name, note, value, threshold):
    w   = min(float(value), 100)
    col = _col(value, threshold)
    return f"""<div>
  <div class="prg-hdr">
    <div><div class="prg-name">{name}</div><div class="prg-note">{note}</div></div>
    <div style="text-align:right">
      <div class="prg-pct" style="color:var(--{col})">{_p(value)}</div>
      <div class="prg-tgt">Target: {threshold}% {'✓' if value>=threshold else '⚠'}</div>
    </div>
  </div>
  <div class="bar-bg">
    <div class="bar-fill" style="width:{w}%;background:var(--{col})"></div>
    <div class="bar-tline" style="left:{threshold}%"></div>
  </div>
</div>"""

def _header(period, quarter_label, d):
    txc=d.get('TX_CURR',0); fem=d.get('TX_CURR_F',0)
    fem_pct=f"{fem/txc*100:.1f}" if txc else "0"
    return f"""<div class="hdr">
  <div class="hdr-l">
    <div class="hdr-eyebrow">ACE3 Programme · HSCL · Performance Report</div>
    <div class="hdr-title">ACE3 — Accelerating Control of the HIV Epidemic in Nigeria</div>
    <div class="hdr-sub">Implementing Partner: HSCL &nbsp;·&nbsp; Kebbi, Sokoto &amp; Zamfara &nbsp;·&nbsp; 37 Supported Facilities</div>
  </div>
  <div class="hdr-r">
    <div class="meta"><span class="ml">Period</span><span class="mv">{period}</span></div>
    <div class="meta"><span class="ml">Report</span><span class="mv">{quarter_label}</span></div>
    <div class="meta"><span class="ml">Active on ART</span><span class="mv">{_n(txc)}</span></div>
    <div class="meta"><span class="ml">Female</span><span class="mv">{fem_pct}%</span></div>
    <div class="meta"><span class="ml">Facilities</span><span class="mv">37</span></div>
  </div>
</div>"""

def _footer(period):
    return f"""<div class="ftr">
  <div>
    <div class="ftr-brand">ACE3 · HSCL · Programme Performance Report</div>
    <div style="margin-top:2px;">{period} · Kebbi, Sokoto &amp; Zamfara · 37 Facilities</div>
  </div>
  <div style="text-align:right">
    <div style="color:rgba(255,255,255,.9);font-weight:600;font-size:10px;">CONFIDENTIAL — Internal Use Only</div>
    <div style="margin-top:2px;">Source: LAMIS+ / DHIS2 · Auto-generated by ACE3 Report System</div>
  </div>
</div>"""

def _alert_banner(alerts):
    if not alerts: return ''
    items=''.join(f'<div class="ai"><div class="ai-dot"></div>{a}</div>' for a in alerts)
    return f"""<div class="alert">
  <span style="font-size:14px;margin-right:4px;">⚠</span>
  <div>
    <div style="margin-bottom:4px;font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:var(--amber);">Programme Alerts Requiring Management Attention</div>
    <div class="alert-items">{items}</div>
  </div>
</div>"""

def _build_alerts(d, q1=None, q2=None):
    alerts=[]
    if q1 and q2:
        ml1,ml2=q1.get('TX_ML',0),q2.get('TX_ML',0)
        if ml1 and ml2 and ml2>ml1:
            pct=(ml2-ml1)/ml1*100
            if pct>20: alerts.append(f"IIT surge: +{pct:.1f}% Q1→Q2 ({_n(ml1)} → {_n(ml2)})")
        h1,h2=q1.get('HTS_TST',0),q2.get('HTS_TST',0)
        if h1 and h2 and h2<h1:
            pct=(h1-h2)/h1*100
            if pct>15: alerts.append(f"HIV testing −{pct:.1f}% Q1→Q2 ({_n(h1)} → {_n(h2)})")
    vl_c=d.get('VL_COVERAGE',0)
    if vl_c and vl_c<95: alerts.append(f"VL coverage {_p(vl_c)} — {95-vl_c:.1f} pp below 95% target")
    cxca_e=d.get('CXCA_SCRN',0); cxca_t=d.get('CXCA_TX',0)
    if cxca_e and cxca_t:
        cov=cxca_t/cxca_e*100
        if cov<80: alerts.append(f"CxCa coverage {cov:.1f}% — {cxca_e-cxca_t:,} eligible WLHIV unscreened")
    eid=d.get('PMTCT_EID',0); deliv=d.get('PMTCT_DELIVERED',0)
    if deliv and eid and eid/deliv*100<95: alerts.append(f"EID PCR {eid/deliv*100:.1f}% of deliveries")
    return alerts


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD HTML — cascade order
# ─────────────────────────────────────────────────────────────────────────────
def build_dashboard(results, period, quarter_label, quarter_mode):
    q1=results.get('q1',{}); q2=results.get('q2',{})
    d=results.get('semi') if quarter_mode in ('SEMI','CUM') else (q2 if quarter_mode=='Q2' else q1)
    tgts=results.get('targets',{})

    # ── extract all values ───────────────────────────────────────────────────
    txc=d.get('TX_CURR',0); fem=d.get('TX_CURR_F',0); male=d.get('TX_CURR_M',0)
    lt15=d.get('TX_CURR_LT15',0); bio=d.get('TX_CURR_BIO',0)
    vl_s=d.get('VL_SUPPRESSION',0); vl_c=d.get('VL_COVERAGE',0)
    pvls_d=d.get('TX_PVLS_D',0); pvls_n=d.get('TX_PVLS_N',0)
    unsupp=d.get('VL_UNSUPP',0); vl_gap=d.get('VL_GAP',0)
    hts=d.get('HTS_TST',0); hts_p=d.get('HTS_TST_POS',0); hts_y=d.get('HTS_YIELD',0)
    hts_mod=d.get('HTS_MODALITY',{})
    tx_ml=d.get('TX_ML',0); tx_rtt=d.get('TX_RTT',0); tx_new=d.get('TX_NEW',0)
    mmd_3p=d.get('MMD_3P',0); mmd_6p=d.get('MMD_6P',0); mmd_lt3=d.get('MMD_LT3',0)
    mmd_35=mmd_3p-mmd_6p; mmd_pct=mmd_3p/txc*100 if txc else 0
    tpt=d.get('TB_PREV_N',0); tb_scr=d.get('TB_SCREEN',0); tb_pos=d.get('TB_SCREEN_POS',0)
    pnew=d.get('PrEP_NEW',0); pct_=d.get('PrEP_CT',0); pcurr=d.get('PrEP_CURR',0)
    cxca_e=d.get('CXCA_SCRN',0); cxca_t=d.get('CXCA_TX',0); cxca_r=d.get('CXCA_RESULTS',{})
    ahd_s=d.get('AHD_SCRN',0); ahd_c=d.get('AHD_CONF',0)
    ahd_cd4=d.get('AHD_CD4',0); ahd_tbl=d.get('AHD_TBLAM_POS',0); ahd_cr=d.get('AHD_CRAG_POS',0)
    eid=d.get('PMTCT_EID',0); deliv=d.get('PMTCT_DELIVERED',0)
    pmtc_n=d.get('PMTCT_STAT_N',0); pmtc_p=d.get('PMTCT_STAT_POS',0); pmtc_a=d.get('PMTCT_ART_D',0)
    eac_cl=d.get('EAC_CASELOAD',0); eac_s1=d.get('EAC_SESS1',0); eac_s2=d.get('EAC_SESS2',0)
    eac_pvl=d.get('EAC_POST_VL_N',0); eac_psr=d.get('EAC_POST_SUPP_R',0)
    eac_psn=d.get('EAC_POST_SUPP_N',0); eac_ind=d.get('EAC_INDICATION',{})
    eac_st=d.get('EAC_STATE',{})

    # derived
    rtt_r=tx_rtt/tx_ml*100 if tx_ml else 0
    eid_c=eid/deliv*100 if deliv else 0
    tpt_c=tpt/txc*100 if txc else 0
    cxca_c=cxca_t/cxca_e*100 if cxca_e else 0
    ahd_r=ahd_c/ahd_s*100 if ahd_s else 0
    bio_p=bio/txc*100 if txc else 0
    fem_p=fem/txc*100 if txc else 0
    link_r=tx_new/hts_p*100 if hts_p else 0

    states=['Kebbi','Sokoto','Zamfara']
    state_curr=d.get('TX_CURR_STATE',{})
    state_hts=d.get('HTS_STATE',{})
    state_txn=d.get('TX_NEW_STATE',{})
    state_prep=d.get('PrEP_NEW_STATE',{})
    ml_out=d.get('TX_ML_OUTCOMES',{})
    iit_n=ml_out.get('IIT',0); died_n=ml_out.get('Died',0)
    to_n=ml_out.get('Transferred Out',0); stop_n=ml_out.get('Stopped Treatment',0)
    cxca_neg=cxca_r.get('Negative',0) or cxca_r.get('Negative VIA',0) or 0
    cxca_pos=cxca_r.get('Positive',0) or cxca_r.get('Positive VIA',0) or 0
    cxca_sus=cxca_r.get('Suspicious',0) or 0
    cxca_un=max(0,cxca_e-cxca_t)
    prep_pop=d.get('PrEP_NEW_POP',{})
    fem_r=fem/txc if txc else 0.645
    state_f=[round(state_curr.get(s,0)*fem_r) for s in states]
    state_m=[round(state_curr.get(s,0)*(1-fem_r)) for s in states]

    # HTS modality data for grouped bar
    mod_labels=list(hts_mod.keys())[:8] if hts_mod else []
    mod_tested=[hts_mod[m].get('tested',0) if isinstance(hts_mod.get(m),dict) else 0 for m in mod_labels]
    mod_yield_=[round(hts_mod[m].get('yield',0),2) if isinstance(hts_mod.get(m),dict) else 0 for m in mod_labels]

    # Q1 vs Q2
    qoq_html=''
    if quarter_mode in ('SEMI','CUM') and q1 and q2:
        def _row(label,k,invert=False):
            v1,v2=q1.get(k,0),q2.get(k,0)
            _,p,c=_chg(v1,v2)
            if invert: c='ok' if c=='up' else 'dn'
            return f"<tr><td>{label}</td><td class='num'>{_n(v1)}</td><td class='num'>{_n(v2)}</td><td class='num {c}'>{p}</td></tr>"
        qoq_html=f"""<div class="card">
  <div class="ct">Q1 vs Q2 — Quarter-on-Quarter</div>
  <div class="cs">Oct–Dec 2025 vs Jan–Mar 2026</div>
  <table class="tbl">
    <thead><tr><th>Indicator</th><th style="text-align:right">Q1</th><th style="text-align:right">Q2</th><th style="text-align:right">Change</th></tr></thead>
    <tbody>
      {_row('HIV Tests (HTS_TST)','HTS_TST')}
      {_row('New ART Initiations','TX_NEW')}
      {_row('Tx Interruptions (IIT)','TX_ML',True)}
      {_row('PMTCT ANC Tested','PMTCT_STAT_N')}
      {_row('PrEP_NEW','PrEP_NEW')}
    </tbody>
  </table>
</div>"""

    # targets tracker rows
    tgt_rows=''
    TGT_MAP=[
        ('HTS_TST','HIV Tests','HTS_TST'),('TX_NEW','New Initiations','TX_NEW'),
        ('TX_CURR','Active on ART','TX_CURR'),('TX_PVLS_D','VL Tests','TX_PVLS_D'),
        ('TX_PVLS_N','VL Suppressed','TX_PVLS_N'),('PMTCT_STAT_N','ANC Tested','PMTCT_STAT_N'),
        ('PrEP_NEW','PrEP New','PrEP_NEW'),('TB_PREV_N','TPT Started','TB_PREV_N'),
    ]
    for vk,label,tk in TGT_MAP:
        val=d.get(vk,0); tgt=tgts.get(tk)
        if tgt and tgt>0:
            pa=val/tgt*100; bw=min(pa,100)
            col='green' if pa>=75 else ('amber' if pa>=50 else 'red')
            tgt_rows+=f"""<tr>
  <td>{label}</td><td class="num">{_n(val)}</td><td class="num">{_n(tgt)}</td>
  <td class="num" style="color:var(--{col});font-weight:700">{pa:.1f}%</td>
  <td style="width:120px"><div class="bar-bg" style="height:7px">
    <div class="bar-fill" style="width:{bw}%;background:var(--{col})"></div>
  </div></td>
</tr>"""

    alerts=_build_alerts(d,q1 if quarter_mode in ['Q2','SEMI'] else None,
                            q2 if quarter_mode in ('SEMI','CUM') else None)

    html=f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ACE3 · {quarter_label} Dashboard</title>
{CHARTJS}{BASE_CSS}
</head>
<body>
{_header(period,quarter_label,d)}
{_alert_banner(alerts)}
<div class="dash">

<!-- KPI ROW: HTS · TX_NEW · TX_CURR · TX_ML · VL Supp · PMTCT -->
<div>
<div class="sec-hdr">Key Programme Indicators — {quarter_label}</div>
<div class="kpi-row">
  <div class="kpi blue">
    <div class="kpi-lbl">HIV Tests<br>HTS_TST</div>
    <div class="kpi-val">{_n(hts) if hts<1000000 else f"{hts/1000:.0f}K"}</div>
    <div class="kpi-sub">Yield {_p(hts_y)} · {_n(hts_p)} confirmed+</div>
    <span class="badge bb">{_n(hts_p)} positive</span>
  </div>
  <div class="kpi navy">
    <div class="kpi-lbl">New Initiations<br>TX_NEW</div>
    <div class="kpi-val">{_n(tx_new)}</div>
    <div class="kpi-sub">Linkage {_p(link_r)} of HIV+</div>
    <span class="badge {'bg' if link_r>=95 else 'ba'}">{'✓ ≥95%' if link_r>=95 else f'⚠ {link_r:.1f}%'} linkage</span>
  </div>
  <div class="kpi navy">
    <div class="kpi-lbl">Active on ART<br>TX_CURR</div>
    <div class="kpi-val">{_n(txc)}</div>
    <div class="kpi-sub">{fem_p:.1f}% female · {lt15/txc*100:.1f}% paediatric</div>
    <span class="badge bb">{bio_p:.1f}% biometric</span>
  </div>
  <div class="kpi red">
    <div class="kpi-lbl">Tx Interruptions<br>TX_ML</div>
    <div class="kpi-val" style="color:var(--red)">{_n(tx_ml)}</div>
    <div class="kpi-sub">RTT: {_n(tx_rtt)} returned ({rtt_r:.1f}%)</div>
    <span class="badge br">Needs attention</span>
  </div>
  <div class="kpi green">
    <div class="kpi-lbl">VL Suppression<br>TX_PVLS N/D</div>
    <div class="kpi-val" style="color:var(--{'green' if vl_s>=95 else 'amber'})">{_p(vl_s)}</div>
    <div class="kpi-sub">{_n(pvls_n)} suppressed / {_n(pvls_d)}</div>
    <span class="badge {'bg' if vl_s>=95 else 'ba'}">{'▲ Exceeds 95%' if vl_s>=95 else '⚠ Below 95%'}</span>
  </div>
  <div class="kpi teal">
    <div class="kpi-lbl">PMTCT ANC<br>PMTCT_STAT</div>
    <div class="kpi-val" style="color:var(--teal)">{_n(pmtc_n)}</div>
    <div class="kpi-sub">{_n(pmtc_p)} HIV+ · {pmtc_p/pmtc_n*100:.3f}% prev.</div>
    <span class="badge bt">{_n(pmtc_a)} on ART</span>
  </div>
</div>
</div>

<!-- ROW 1: SECTION 1 — HIV TESTING -->
<div>
<div class="sec-hdr">1 · HIV Testing Services</div>
<div class="g23">
  <div class="card">
    <div class="ct">HTS Volume &amp; Positivity by State</div>
    <div class="cs">Total {_n(hts)} tested · Yield {_p(hts_y)} · {_n(hts_p)} HIV positive</div>
    <div style="height:180px"><canvas id="cHTS"></canvas></div>
    <div class="stats" style="margin-top:10px">
      <div class="sb"><div class="sbv">{_n(hts_p)}</div><div class="sbl">HIV Positive</div></div>
      <div class="sb"><div class="sbv" style="color:var(--amber)">{_p(hts_y)}</div><div class="sbl">Yield</div></div>
      <div class="sb"><div class="sbv">{_n(tx_new)}</div><div class="sbl">Linked to ART</div></div>
    </div>
  </div>
  <div class="card">
    <div class="ct">HTS by Modality — Volume &amp; Yield</div>
    <div class="cs">Tested and positivity yield (%) per testing modality</div>
    {'<div style="height:220px"><canvas id="cMOD"></canvas></div>' if mod_labels else '<div style="padding:20px;color:var(--light);font-size:11px">Modality data not available — upload HTS file</div>'}
  </div>
</div>
</div>

<!-- ROW 2: SECTION 2 — TX_NEW + LINKAGE -->
<div>
<div class="sec-hdr">2 · New ART Initiations &amp; Linkage</div>
<div class="g32">
  <div class="card">
    <div class="ct">TX_NEW by State</div>
    <div class="cs">Total {_n(tx_new)} new initiations · Linkage rate {_p(link_r)}</div>
    <div style="height:180px"><canvas id="cTXNEW"></canvas></div>
  </div>
  <div class="card">
    <div class="ct">Linkage Cascade</div>
    <div class="cs">HIV+ tested → linked to ART</div>
    <div class="stats" style="margin-top:16px">
      <div class="sb"><div class="sbv">{_n(hts_p)}</div><div class="sbl">HIV Positive</div></div>
      <div class="sb"><div class="sbv">{_n(tx_new)}</div><div class="sbl">Started ART</div></div>
    </div>
    <div style="margin-top:14px">
      <div class="bar-bg" style="height:12px">
        <div class="bar-fill" style="width:{min(link_r,100):.1f}%;background:var(--{'green' if link_r>=95 else 'amber'})"></div>
        <div class="bar-tline" style="left:95%"></div>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:4px;font-size:9px;color:var(--light)">
        <span>0%</span><span style="font-weight:700;color:var(--{'green' if link_r>=95 else 'amber'})">{_p(link_r)} linkage</span><span>Target: 95%</span>
      </div>
    </div>
  </div>
</div>
</div>

<!-- ROW 3: SECTION 3 — PMTCT -->
<div>
<div class="sec-hdr">3 · PMTCT &amp; Early Infant Diagnosis</div>
<div class="g3">
  <div class="card">
    <div class="ct">PMTCT Cascade</div>
    <div class="cs">ANC tested → HIV+ → on ART → EID</div>
    <div style="height:160px;margin-top:4px"><canvas id="cPMTCT"></canvas></div>
  </div>
  <div class="card">
    <div class="ct">PMTCT by Modality</div>
    <div class="cs">ANC1 vs Post-ANC1 (Pregnancy/L&amp;D)</div>
    <div style="height:160px;margin-top:4px"><canvas id="cPMTCTMOD"></canvas></div>
  </div>
  <div class="card">
    <div class="ct">PMTCT Key Metrics</div>
    <div class="cs">Case identification &amp; EID outcomes</div>
    <div class="mini-3">
      <div class="mt" style="background:var(--sblue);border-color:#C0D8EE">
        <div class="mt-v" style="color:var(--navy)">{_n(pmtc_p)}</div>
        <div class="mt-l">HIV+ at ANC<br>{pmtc_p/pmtc_n*100:.3f}%</div>
      </div>
      <div class="mt" style="background:var(--sblue);border-color:#C0D8EE">
        <div class="mt-v" style="color:var(--navy)">{_n(pmtc_a)}</div>
        <div class="mt-l">On ART<br>PMTCT_ART</div>
      </div>
      <div class="mt" style="background:var(--{'lgreen' if eid_c>=95 else 'lamber'})">
        <div class="mt-v" style="color:var(--{'green' if eid_c>=95 else 'amber'})">{_p(eid_c)}</div>
        <div class="mt-l">EID PCR<br>{_n(eid)} of {_n(deliv)}</div>
      </div>
    </div>
    <div style="margin-top:10px">
      {_progress_bar('EID PCR Coverage',f'{_n(eid)} of {_n(deliv)} HEI tested',eid_c,95)}
    </div>
  </div>
</div>
</div>

<!-- ROW 4: SECTION 4 — TX_CURR + MMD -->
<div>
<div class="sec-hdr">4 · Active Treatment &amp; Differentiated Service Delivery</div>
<div class="g32">
  <div class="card">
    <div class="ct">TX_CURR by State &amp; Sex</div>
    <div class="cs">Total {_n(txc)} · {fem_p:.1f}% female · {lt15/txc*100:.1f}% paediatric · {bio_p:.1f}% biometric</div>
    <div style="height:210px"><canvas id="cCascade"></canvas></div>
  </div>
  <div class="card">
    <div class="ct">Multi-Month Dispensing (MMD)</div>
    <div class="cs">{_p(mmd_pct)} on ≥3 months — DSD</div>
    <div style="display:flex;gap:12px;align-items:center;margin-top:4px">
      <div style="width:145px;height:145px;flex-shrink:0"><canvas id="cMMD"></canvas></div>
      <div class="leg">
        <div class="li"><div class="ld" style="background:var(--green)"></div><span class="lt">6+ months</span><span class="lv">{_n(mmd_6p)}</span><span class="lp">{mmd_6p/txc*100:.1f}%</span></div>
        <div class="li"><div class="ld" style="background:var(--blue)"></div><span class="lt">3–5 months</span><span class="lv">{_n(mmd_35)}</span><span class="lp">{mmd_35/txc*100:.1f}%</span></div>
        <div class="li"><div class="ld" style="background:var(--red)"></div><span class="lt">&lt;3 months</span><span class="lv">{_n(mmd_lt3)}</span><span class="lp">{mmd_lt3/txc*100:.1f}%</span></div>
      </div>
    </div>
    <div style="margin-top:10px">{_progress_bar('MMD ≥3 Months',f'{_n(mmd_3p)} of {_n(txc)} clients',mmd_pct,90)}</div>
  </div>
</div>
</div>

<!-- ROW 5: SECTION 5 — RETENTION -->
<div>
<div class="sec-hdr">5 · Treatment Retention</div>
<div class="g23">
  <div class="card">
    <div class="ct">TX_ML Outcomes — {_n(tx_ml)} total</div>
    <div class="cs">IIT defined as ≥28 days since last expected contact · RTT rate {_p(rtt_r)}</div>
    <div style="height:160px"><canvas id="cTXML"></canvas></div>
    <div class="stats" style="margin-top:8px">
      <div class="sb"><div class="sbv" style="color:var(--red)">{_n(tx_ml)}</div><div class="sbl">Total TX_ML</div></div>
      <div class="sb"><div class="sbv">{_n(tx_rtt)}</div><div class="sbl">RTT</div></div>
      <div class="sb"><div class="sbv" style="color:var(--{'green' if rtt_r>=60 else 'red'})">{_p(rtt_r)}</div><div class="sbl">RTT Rate</div></div>
    </div>
  </div>
  <div>
    {qoq_html if qoq_html else f'<div class="card"><div class="ct">Retention Summary</div><div class="cs">{quarter_label}</div><div class="stats" style="margin-top:16px"><div class="sb"><div class="sbv" style="color:var(--red)">{_n(iit_n)}</div><div class="sbl">IIT (Lost)</div></div><div class="sb"><div class="sbv">{_n(died_n)}</div><div class="sbl">Died</div></div><div class="sb"><div class="sbv">{_n(to_n)}</div><div class="sbl">Transferred</div></div></div></div>'}
  </div>
</div>
</div>

<!-- ROW 6: SECTION 6 — VIRAL LOAD -->
<div>
<div class="sec-hdr">6 · Viral Load — TX_PVLS</div>
<div class="g23">
  <div class="card">
    <div class="ct">TX_PVLS — Coverage &amp; Suppression</div>
    <div class="cs">Coverage: TX_PVLS_D ÷ TX_CURR · Suppression: TX_PVLS_N ÷ TX_PVLS_D</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:4px">
      <div style="text-align:center">
        <div style="width:130px;height:130px;margin:0 auto"><canvas id="cVLS"></canvas></div>
        <div style="font-size:28px;font-weight:700;font-family:var(--mono);color:var(--{'green' if vl_s>=95 else 'amber'});margin-top:-4px">{_p(vl_s)}</div>
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;color:var(--light)">VL Suppression</div>
        <div style="font-size:9px;color:var(--{'green' if vl_s>=95 else 'amber'});font-weight:700;margin-top:3px">TX_PVLS_N / TX_PVLS_D</div>
      </div>
      <div style="text-align:center">
        <div style="width:130px;height:130px;margin:0 auto"><canvas id="cVLC"></canvas></div>
        <div style="font-size:28px;font-weight:700;font-family:var(--mono);color:var(--{'green' if vl_c>=95 else 'amber'});margin-top:-4px">{_p(vl_c)}</div>
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;color:var(--light)">VL Coverage</div>
        <div style="font-size:9px;color:var(--{'green' if vl_c>=95 else 'amber'});font-weight:700;margin-top:3px">TX_PVLS_D / TX_CURR</div>
      </div>
    </div>
    <div class="stats" style="margin-top:10px">
      <div class="sb"><div class="sbv">{_n(unsupp)}</div><div class="sbl">Unsuppressed</div></div>
      <div class="sb"><div class="sbv">{_n(pvls_d)}</div><div class="sbl">TX_PVLS_D</div></div>
      <div class="sb"><div class="sbv" style="color:var(--red)">{_n(vl_gap)}</div><div class="sbl">Pending Samples</div></div>
    </div>
  </div>
  <div class="card">
    <div class="ct">95–95–95 Progress</div>
    <div class="cs">Clinical thresholds (│) shown on each bar</div>
    <div class="prg-wrap">
      {_progress_bar('TX_PVLS_D/TX_CURR — VL Coverage',f'{_n(pvls_d)} of {_n(txc)} with VL result',vl_c,95)}
      {_progress_bar('TX_PVLS_N/TX_PVLS_D — VL Suppression',f'{_n(pvls_n)} of {_n(pvls_d)} suppressed',vl_s,95)}
      {_progress_bar('DSD — MMD ≥3 Months',f'{_n(mmd_3p)} of {_n(txc)} on ≥3mo supply',mmd_pct,90)}
      {_progress_bar('TPT Coverage',f'{_n(tpt)} of {_n(txc)} on TPT',tpt_c,90)}
      {_progress_bar('CxCa Screening',f'{_n(cxca_t)} of {_n(cxca_e)} eligible screened',cxca_c,80)}
      {_progress_bar('EID PCR Coverage',f'{_n(eid)} of {_n(deliv)} HEI tested',eid_c,95)}
    </div>
    <div style="margin-top:9px;padding:6px 9px;background:var(--sblue);font-size:9px;color:var(--navy)">
      <strong>Key:</strong> │ = threshold &nbsp;·&nbsp;
      <span style="color:var(--green);font-weight:700">■ Green</span> = met &nbsp;·&nbsp;
      <span style="color:var(--amber);font-weight:700">■ Amber</span> = gap &nbsp;·&nbsp;
      <span style="color:var(--red);font-weight:700">■ Red</span> = critical
    </div>
  </div>
</div>
</div>

<!-- ROW 7: SECTION 7 — EAC -->
<div>
<div class="sec-hdr">7 · Enhanced Adherence Counselling (EAC)</div>
<div class="g3">
  <div class="card">
    <div class="ct">EAC Caseload by State</div>
    <div class="cs">Total unsuppressed clients actively managed: {_n(eac_cl)}</div>
    <div style="height:160px"><canvas id="cEACSTATE"></canvas></div>
  </div>
  <div class="card">
    <div class="ct">EAC Sessions Completed</div>
    <div class="cs">Session completion cascade</div>
    <div style="height:160px"><canvas id="cEACSESS"></canvas></div>
  </div>
  <div class="card">
    <div class="ct">Post-EAC Outcomes</div>
    <div class="cs">VL collection &amp; re-suppression after counselling</div>
    <div class="mini-2" style="margin-top:14px">
      <div class="mt" style="background:var(--sblue)">
        <div class="mt-v" style="color:var(--navy)">{_n(eac_pvl)}</div>
        <div class="mt-l">Post-EAC VL<br>collected</div>
      </div>
      <div class="mt" style="background:var(--{'lgreen' if eac_psr>=90 else 'lamber'})">
        <div class="mt-v" style="color:var(--{'green' if eac_psr>=90 else 'amber'})">{_p(eac_psr)}</div>
        <div class="mt-l">Re-suppression<br>{_n(eac_psn)} clients</div>
      </div>
    </div>
    <div style="margin-top:12px;padding:8px;background:var(--{'lgreen' if eac_psr>=90 else 'lamber'});border-left:3px solid var(--{'green' if eac_psr>=90 else 'amber'})">
      <div style="font-size:10px;font-weight:700;color:var(--{'green' if eac_psr>=90 else 'amber'})">{_p(eac_psr)} post-EAC re-suppression rate</div>
      <div style="font-size:9px;color:var(--mid)">{_n(eac_psn)} of {_n(eac_pvl)} clients with VL result re-suppressed</div>
    </div>
  </div>
</div>
</div>

<!-- ROW 8: SECTION 8 — TB/HIV -->
<div>
<div class="sec-hdr">8 · TB/HIV Integration</div>
<div class="g32">
  <div class="card">
    <div class="ct">TB Screening &amp; TPT</div>
    <div class="cs">Screened {_n(tb_scr)} · Positive {_n(tb_pos)} · TPT {_n(tpt)} ({_p(tpt_c)} coverage)</div>
    <div style="height:170px"><canvas id="cTB"></canvas></div>
  </div>
  <div class="card">
    <div class="ct">TPT Coverage</div>
    <div class="cs">TB Preventive Therapy among TX_CURR</div>
    <div class="mini-2" style="margin-top:12px">
      <div class="mt" style="background:var(--{'lgreen' if tpt_c>=90 else 'lamber'})">
        <div class="mt-v" style="color:var(--{'green' if tpt_c>=90 else 'amber'})">{_p(tpt_c)}</div>
        <div class="mt-l">TPT Coverage<br>{'✓ ≥90% target' if tpt_c>=90 else '⚠ Below 90%'}</div>
      </div>
      <div class="mt">
        <div class="mt-v" style="color:var(--navy)">{_n(tpt)}</div>
        <div class="mt-l">Clients on TPT<br>of {_n(tb_scr)} screened</div>
      </div>
    </div>
    <div style="margin-top:10px">{_progress_bar('TPT Coverage',f'{_n(tpt)} of {_n(txc)} TX_CURR',tpt_c,90)}</div>
  </div>
</div>
</div>

<!-- ROW 9: SECTION 9 — PrEP -->
<div>
<div class="sec-hdr">9 · PrEP Programme</div>
<div class="g3">
  <div class="card">
    <div class="ct">PrEP_NEW by State</div>
    <div class="cs">Total {_n(pnew)} new initiations</div>
    <div style="height:160px"><canvas id="cPREP"></canvas></div>
  </div>
  <div class="card">
    <div class="ct">PrEP_NEW by Population Type</div>
    <div class="cs">Key population disaggregation</div>
    {'<div style="height:160px"><canvas id="cPREPPOP"></canvas></div>' if prep_pop else '<div style="padding:20px;color:var(--light);font-size:11px">Population data not available</div>'}
  </div>
  <div class="card">
    <div class="ct">PrEP Summary</div>
    <div class="cs">PrEP_NEW · PrEP_CT · PrEP_CURR snapshot</div>
    <div class="mini-3">
      <div class="mt" style="background:var(--sblue);border-top:3px solid var(--navy)">
        <div class="mt-v" style="color:var(--navy)">{_n(pnew)}</div>
        <div class="mt-l">PrEP_NEW<br>Initiations</div>
      </div>
      <div class="mt" style="border-top:3px solid var(--blue)">
        <div class="mt-v" style="color:var(--blue)">{_n(pct_)}</div>
        <div class="mt-l">PrEP_CT<br>Follow-up</div>
      </div>
      <div class="mt" style="background:var(--lgreen);border-top:3px solid var(--green)">
        <div class="mt-v" style="color:var(--green)">{_n(pcurr)}</div>
        <div class="mt-l">Active<br>Snapshot</div>
      </div>
    </div>
  </div>
</div>
</div>

<!-- ROW 10: SECTION 10 — CxCa -->
<div>
<div class="sec-hdr">10 · Cervical Cancer Screening (CxCa)</div>
<div class="g32">
  <div class="card">
    <div class="ct">CxCa Coverage &amp; Results</div>
    <div class="cs">Eligible: {_n(cxca_e)} · Screened: {_n(cxca_t)} · Coverage: {_p(cxca_c)}</div>
    <div style="display:flex;gap:12px;align-items:center;margin-top:6px">
      <div style="width:148px;height:148px;flex-shrink:0"><canvas id="cCXCA"></canvas></div>
      <div style="flex:1">
        <div class="leg">
          <div class="li"><div class="ld" style="background:#C8C8C8"></div><span class="lt">Not screened</span><span class="lv">{_n(cxca_un)}</span><span class="lp">{cxca_un/cxca_e*100:.1f}%</span></div>
          <div class="li"><div class="ld" style="background:var(--green)"></div><span class="lt">Negative</span><span class="lv">{_n(cxca_neg)}</span></div>
          <div class="li"><div class="ld" style="background:var(--amber)"></div><span class="lt">Positive</span><span class="lv">{_n(cxca_pos)}</span></div>
          <div class="li"><div class="ld" style="background:var(--red)"></div><span class="lt">Suspicious</span><span class="lv">{_n(cxca_sus)}</span></div>
        </div>
        {f'<div style="margin-top:8px;padding:7px 9px;background:var(--lred);border-left:3px solid var(--red)"><div style="font-size:9.5px;font-weight:700;color:var(--red)">{cxca_pos+cxca_sus} women need urgent follow-up</div><div style="font-size:9px;color:#8B0000">Positive + Suspicious findings</div></div>' if cxca_pos+cxca_sus>0 else ''}
      </div>
    </div>
  </div>
  <div class="card">
    <div class="ct">CxCa Progress</div>
    <div class="cs">Coverage vs 80% target</div>
    <div style="margin-top:16px">{_progress_bar('CxCa Screening Coverage',f'{_n(cxca_t)} of {_n(cxca_e)} eligible WLHIV screened',cxca_c,80)}</div>
    <div class="stats" style="margin-top:14px">
      <div class="sb"><div class="sbv" style="color:var(--red)">{_n(cxca_un)}</div><div class="sbl">Unscreened</div></div>
      <div class="sb"><div class="sbv" style="color:var(--amber)">{_n(cxca_pos+cxca_sus)}</div><div class="sbl">Urgent F/U</div></div>
    </div>
  </div>
</div>
</div>

<!-- ROW 11: SECTION 11 — AHD -->
<div>
<div class="sec-hdr">11 · Advanced HIV Disease (AHD)</div>
<div class="g32">
  <div class="card">
    <div class="ct">AHD Screening &amp; Diagnostics</div>
    <div class="cs">{_n(ahd_s)} screened · {_n(ahd_c)} confirmed ({ahd_r:.1f}% detection)</div>
    <div style="height:160px;margin-top:4px"><canvas id="cAHD"></canvas></div>
  </div>
  <div class="card">
    <div class="ct">AHD Diagnostic Outcomes</div>
    <div class="cs">CD4 · TB-LAM · CrAg results</div>
    <div class="ahd-g">
      <div class="ahd-t"><div class="ahd-v" style="color:var(--navy)">{_n(ahd_cd4)}</div><div class="ahd-l">CD4 Tests Done</div><div class="ahd-s">{ahd_cd4/ahd_s*100:.1f}% of screened</div></div>
      <div class="ahd-t"><div class="ahd-v" style="color:var(--amber)">{_n(ahd_tbl)}</div><div class="ahd-l">TB-LAM Positive</div></div>
      <div class="ahd-t"><div class="ahd-v" style="color:var(--red)">{_n(ahd_cr)}</div><div class="ahd-l">CrAg Positive</div><div class="ahd-s">Fluconazole Rx urgent</div></div>
      <div class="ahd-t"><div class="ahd-v" style="color:var(--navy)">{_n(ahd_c)}</div><div class="ahd-l">AHD Confirmed</div><div class="ahd-s">{ahd_r:.1f}% of screened</div></div>
    </div>
  </div>
</div>
</div>

<!-- ROW 12: SECTION 12 — TARGETS -->
<div>
<div class="sec-hdr">12 · Targets Achievement Tracker</div>
<div class="card">
  <div class="ct">Result vs Annual Target — {quarter_label}</div>
  <div class="cs">Cumulative result vs full annual target. TX_CURR is period-end snapshot. TB_ART annual indicator — full comparison at Q4.</div>
  <table class="tbl">
    <thead><tr><th>Indicator</th><th style="text-align:right">Result</th><th style="text-align:right">Annual Target</th><th style="text-align:right">% Achieved</th><th>Progress</th></tr></thead>
    <tbody>{tgt_rows}</tbody>
  </table>
</div>
</div>

</div>
{_footer(period)}

{CHART_DEFAULTS}
<script>
// 1. HTS by state
new Chart(document.getElementById('cHTS'),{{
  type:'bar',
  data:{{labels:{json.dumps(states)},
        datasets:[{{data:{json.dumps([state_hts.get(s,0) for s in states])},backgroundColor:['#1F4E79','#2E75B6','#4A90C4'],barPercentage:.65}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{grid:{{display:false}}}},y:{{grid:{{color:'#EAECEF'}},ticks:{{callback:v=>v>=1000?(v/1000).toFixed(0)+'K':v}}}}}}
  }}
}});

// 2. HTS modality grouped bar (volume + yield)
{f"""new Chart(document.getElementById('cMOD'),{{
  type:'bar',
  data:{{
    labels:{json.dumps(mod_labels)},
    datasets:[
      {{label:'Tested',data:{json.dumps(mod_tested)},backgroundColor:'#1F4E79',barPercentage:.4,yAxisID:'y'}},
      {{label:'Yield %',data:{json.dumps(mod_yield_)},backgroundColor:'#C87000',barPercentage:.4,yAxisID:'y1'}}
    ]
  }},
  options:{{
    responsive:true,maintainAspectRatio:false,
    scales:{{
      x:{{grid:{{display:false}},ticks:{{font:{{size:9}}}}}},
      y:{{grid:{{color:'#EAECEF'}},ticks:{{callback:v=>v>=1000?(v/1000).toFixed(0)+'K':v}},position:'left'}},
      y1:{{grid:{{display:false}},ticks:{{callback:v=>v+'%'}},position:'right',max:5}}
    }},
    plugins:{{legend:{{display:true,position:'top',labels:{{boxWidth:9,padding:10,font:{{size:9}}}}}}}}
  }}
}});""" if mod_labels else "// no modality data"}

// 3. TX_NEW by state
new Chart(document.getElementById('cTXNEW'),{{
  type:'bar',
  data:{{labels:{json.dumps(states)},
        datasets:[{{data:{json.dumps([state_txn.get(s,0) for s in states])},backgroundColor:['#1F4E79','#2E75B6','#4A90C4'],barPercentage:.6}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{grid:{{display:false}}}},y:{{grid:{{color:'#EAECEF'}}}}}}
  }}
}});

// 4. PMTCT cascade
new Chart(document.getElementById('cPMTCT'),{{
  type:'bar',
  data:{{labels:['ANC Tested','HIV+','On ART','EID PCR'],
        datasets:[{{data:[{pmtc_n},{pmtc_p},{pmtc_a},{eid}],backgroundColor:['#0E7490','#BA0C2F','#1A6632','#C87000'],barPercentage:.6}}]}},
  options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,
    scales:{{x:{{type:'logarithmic',grid:{{color:'#EAECEF'}},ticks:{{callback:v=>[1,10,100,1000,10000,100000].includes(v)?(v>=1000?(v/1000)+'K':v):''}}}},y:{{grid:{{display:false}}}}}}
  }}
}});

// 5. PMTCT modality
new Chart(document.getElementById('cPMTCTMOD'),{{
  type:'bar',
  data:{{
    labels:['ANC1 Only','Post-ANC1 (Preg/L&D)','Breastfeeding'],
    datasets:[{{
      label:'Tested',
      data:[{d.get('PMTCT_ANC1',pmtc_n)},{d.get('PMTCT_POSTANC',0)},{d.get('PMTCT_BF',0)}],
      backgroundColor:['#0E7490','#2E75B6','#7BB8F0'],barPercentage:.6
    }}]
  }},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{grid:{{display:false}},ticks:{{font:{{size:9}}}}}},y:{{grid:{{color:'#EAECEF'}},ticks:{{callback:v=>v>=1000?(v/1000).toFixed(0)+'K':v}}}}}}
  }}
}});

// 6. TX_CURR stacked bar
new Chart(document.getElementById('cCascade'),{{
  type:'bar',
  data:{{labels:{json.dumps(states)},datasets:[
    {{label:'Female',data:{json.dumps(state_f)},backgroundColor:'#2E75B6',barPercentage:.6}},
    {{label:'Male',data:{json.dumps(state_m)},backgroundColor:'#1F4E79',barPercentage:.6}}
  ]}},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{stacked:true,grid:{{display:false}}}},y:{{stacked:true,grid:{{color:'#EAECEF'}},ticks:{{callback:v=>v>=1000?(v/1000).toFixed(0)+'K':v}}}}}},
    plugins:{{legend:{{display:true,position:'top',labels:{{boxWidth:9,padding:10,font:{{size:9}}}}}}}}
  }}
}});

// 7. MMD donut
new Chart(document.getElementById('cMMD'),{{
  type:'doughnut',
  data:{{labels:['6+ months','3–5 months','<3 months'],
        datasets:[{{data:[{mmd_6p},{mmd_35},{mmd_lt3}],backgroundColor:['#1A6632','#2E75B6','#BA0C2F'],borderWidth:2,borderColor:'#fff'}}]}},
  options:{{responsive:true,maintainAspectRatio:false,cutout:'68%'}}
}});

// 8. TX_ML horizontal bar
new Chart(document.getElementById('cTXML'),{{
  type:'bar',
  data:{{labels:['IIT (Lost)','Died','Transferred Out','Stopped'],
        datasets:[{{data:[{iit_n},{died_n},{to_n},{stop_n}],backgroundColor:['#BA0C2F','#7B1D1D','#1F4E79','#888'],barPercentage:.6}}]}},
  options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,
    scales:{{x:{{grid:{{color:'#EAECEF'}}}},y:{{grid:{{display:false}}}}}}
  }}
}});

gauge('cVLS',{vl_s},'{"#1A6632" if vl_s>=95 else "#C87000"}');
gauge('cVLC',{vl_c},'{"#1A6632" if vl_c>=95 else "#C87000"}');

// 9. EAC state
new Chart(document.getElementById('cEACSTATE'),{{
  type:'bar',
  data:{{labels:{json.dumps(list(eac_st.keys()) or states)},
        datasets:[{{data:{json.dumps([int(v) for v in eac_st.values()] or [0,0,0])},backgroundColor:['#1F4E79','#2E75B6','#4A90C4'],barPercentage:.6}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{grid:{{display:false}}}},y:{{grid:{{color:'#EAECEF'}}}}}}
  }}
}});

// 10. EAC sessions
new Chart(document.getElementById('cEACSESS'),{{
  type:'bar',
  data:{{labels:['1st EAC','2nd EAC','3rd EAC','Extended'],
        datasets:[{{data:[{eac_s1},{eac_s2},{d.get('EAC_SESS3',0)},{d.get('EAC_EXT',0)}],backgroundColor:['#1F4E79','#2E75B6','#4A90C4','#C87000'],barPercentage:.6}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{grid:{{display:false}}}},y:{{grid:{{color:'#EAECEF'}}}}}}
  }}
}});

// 11. TB
new Chart(document.getElementById('cTB'),{{
  type:'bar',
  data:{{labels:['TB Screened','Screen+','TPT Started'],
        datasets:[{{data:[{tb_scr},{tb_pos},{tpt}],backgroundColor:['#2E75B6','#BA0C2F','#1A6632'],barPercentage:.6}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{grid:{{display:false}}}},y:{{grid:{{color:'#EAECEF'}},ticks:{{callback:v=>v>=1000?(v/1000).toFixed(0)+'K':v}}}}}}
  }}
}});

// 12. PrEP by state
new Chart(document.getElementById('cPREP'),{{
  type:'bar',
  data:{{labels:{json.dumps(list(state_prep.keys()) or states)},
        datasets:[{{data:{json.dumps([int(v) for v in state_prep.values()] or [0,0,0])},backgroundColor:['#1F4E79','#2E75B6','#4A90C4'],barPercentage:.6}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{grid:{{display:false}}}},y:{{grid:{{color:'#EAECEF'}}}}}}
  }}
}});

// 13. PrEP population type
{f"""new Chart(document.getElementById('cPREPPOP'),{{
  type:'doughnut',
  data:{{labels:{json.dumps(list(prep_pop.keys())[:6])},
        datasets:[{{data:{json.dumps([int(v) for v in list(prep_pop.values())[:6]])},
          backgroundColor:['#1F4E79','#2E75B6','#4A90C4','#0E7490','#1A6632','#C87000'],borderWidth:2,borderColor:'#fff'}}]}},
  options:{{responsive:true,maintainAspectRatio:false,cutout:'55%',
    plugins:{{legend:{{display:true,position:'right',labels:{{boxWidth:9,padding:6,font:{{size:9}}}}}}}}
  }}
}});""" if prep_pop else ""}

// 14. AHD
new Chart(document.getElementById('cAHD'),{{
  type:'bar',
  data:{{labels:['Screened','AHD Confirmed','CD4 Done'],
        datasets:[{{data:[{ahd_s},{ahd_c},{ahd_cd4}],backgroundColor:['#1F4E79','#BA0C2F','#2E75B6'],barPercentage:.6}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{grid:{{display:false}}}},y:{{grid:{{color:'#EAECEF'}}}}}}
  }}
}});

// 15. CxCa donut
new Chart(document.getElementById('cCXCA'),{{
  type:'doughnut',
  data:{{labels:['Not Screened','Negative','Positive','Suspicious'],
        datasets:[{{data:[{cxca_un},{cxca_neg},{cxca_pos},{cxca_sus}],
          backgroundColor:['#C8C8C8','#1A6632','#C87000','#BA0C2F'],borderWidth:2,borderColor:'#fff'}}]}},
  options:{{responsive:true,maintainAspectRatio:false,cutout:'65%'}}
}});
</script>
</body></html>"""
    return html


# ─────────────────────────────────────────────────────────────────────────────
# NARRATIVE REPORT — cascade order
# ─────────────────────────────────────────────────────────────────────────────
def build_narrative(results, period, quarter_label, quarter_mode):
    q1=results.get('q1',{}); q2=results.get('q2',{})
    d=results.get('semi') if quarter_mode in ('SEMI','CUM') else (q2 if quarter_mode=='Q2' else q1)
    tgts=results.get('targets',{})

    txc=d.get('TX_CURR',0); fem=d.get('TX_CURR_F',0); lt15=d.get('TX_CURR_LT15',0)
    bio=d.get('TX_CURR_BIO',0); male=d.get('TX_CURR_M',0)
    vl_s=d.get('VL_SUPPRESSION',0); vl_c=d.get('VL_COVERAGE',0)
    pvls_d=d.get('TX_PVLS_D',0); pvls_n=d.get('TX_PVLS_N',0)
    unsupp=d.get('VL_UNSUPP',0); vl_gap=d.get('VL_GAP',0)
    hts=d.get('HTS_TST',0); hts_p=d.get('HTS_TST_POS',0); hts_y=d.get('HTS_YIELD',0)
    tx_ml=d.get('TX_ML',0); tx_rtt=d.get('TX_RTT',0); tx_new=d.get('TX_NEW',0)
    mmd_3p=d.get('MMD_3P',0); mmd_6p=d.get('MMD_6P',0)
    tpt=d.get('TB_PREV_N',0); tb_scr=d.get('TB_SCREEN',0); tb_pos=d.get('TB_SCREEN_POS',0)
    pnew=d.get('PrEP_NEW',0); pct_=d.get('PrEP_CT',0); pcurr=d.get('PrEP_CURR',0)
    cxca_e=d.get('CXCA_SCRN',0); cxca_t=d.get('CXCA_TX',0); cxca_r=d.get('CXCA_RESULTS',{})
    ahd_s=d.get('AHD_SCRN',0); ahd_c=d.get('AHD_CONF',0)
    ahd_cd4=d.get('AHD_CD4',0); ahd_tbl=d.get('AHD_TBLAM_POS',0); ahd_cr=d.get('AHD_CRAG_POS',0)
    eid=d.get('PMTCT_EID',0); deliv=d.get('PMTCT_DELIVERED',0)
    pmtc_n=d.get('PMTCT_STAT_N',0); pmtc_p=d.get('PMTCT_STAT_POS',0); pmtc_a=d.get('PMTCT_ART_D',0)
    eac_cl=d.get('EAC_CASELOAD',0); eac_s1=d.get('EAC_SESS1',0); eac_s2=d.get('EAC_SESS2',0)
    eac_pvl=d.get('EAC_POST_VL_N',0); eac_psr=d.get('EAC_POST_SUPP_R',0); eac_psn=d.get('EAC_POST_SUPP_N',0)
    state_curr=d.get('TX_CURR_STATE',{})

    rtt_r=tx_rtt/tx_ml*100 if tx_ml else 0
    eid_c=eid/deliv*100 if deliv else 0
    tpt_c=tpt/txc*100 if txc else 0
    cxca_c=cxca_t/cxca_e*100 if cxca_e else 0
    mmd_p=mmd_3p/txc*100 if txc else 0
    ahd_r=ahd_c/ahd_s*100 if ahd_s else 0
    fem_p=fem/txc*100 if txc else 0
    bio_p=bio/txc*100 if txc else 0
    link_r=tx_new/hts_p*100 if hts_p else 0

    # Q-on-Q section
    qoq_sec=''
    if quarter_mode in ('SEMI','CUM') and q1 and q2:
        ml1,ml2=q1.get('TX_ML',0),q2.get('TX_ML',0)
        h1,h2=q1.get('HTS_TST',0),q2.get('HTS_TST',0)
        n1,n2=q1.get('TX_NEW',0),q2.get('TX_NEW',0)
        p1,p2=q1.get('PMTCT_STAT_N',0),q2.get('PMTCT_STAT_N',0)
        ml_c=(ml2-ml1)/ml1*100 if ml1 else 0
        h_c=(h2-h1)/h1*100 if h1 else 0
        n_c=(n2-n1)/n1*100 if n1 else 0
        qoq_sec=f"""  <div class="report-section">
    <div class="rsh"><div class="rsh-icon">9</div>Quarter-on-Quarter Performance Analysis</div>
    <p class="report-p">Comparing Q1 (October–December 2025) with Q2 (January–March 2026): HIV testing {'declined' if h_c<0 else 'increased'} by <strong>{abs(h_c):.1f}%</strong> ({_n(h1)} to {_n(h2)}), new ART initiations {'declined' if n_c<0 else 'increased'} by <strong>{abs(n_c):.1f}%</strong> ({_n(n1)} to {_n(n2)}), and PMTCT ANC testing moved from {_n(p1)} to {_n(p2)}. Treatment interruptions {'surged' if ml_c>20 else 'changed'} by <strong>{'+' if ml_c>0 else ''}{ml_c:.1f}%</strong> ({_n(ml1)} to {_n(ml2)}).</p>
    {'<div class="gap-box"><strong>⚠ Concurrent Q2 Declines:</strong> Multiple indicators declined simultaneously in Q2, suggesting a systemic programme stress event. Root-cause investigation at facility level is a priority for the next quarter.</div>' if ml_c>20 and h_c<-15 else ''}
  </div>"""

    # priorities
    pris=[]
    if tx_ml>0 and rtt_r<60:
        pris.append(f"<strong>Retention Response:</strong> Implement 30-day intensive tracing for all {_n(tx_ml)} TX_ML clients. Target RTT rate ≥60% by next quarter end.")
    if vl_c<95:
        pris.append(f"<strong>VL Coverage Acceleration:</strong> Clear {_n(vl_gap)}-sample TX_PVLS_D backlog. Implement VL scheduling matrix at all 37 sites. Target TX_PVLS_D/TX_CURR ≥90%.")
    if eac_cl>0 and eac_pvl<eac_cl*0.5:
        pris.append(f"<strong>EAC Follow-up:</strong> Ensure all {_n(eac_cl)} EAC clients receive post-EAC viral load. Current post-EAC VL collection rate is below 50% of caseload.")
    if cxca_c<80:
        pris.append(f"<strong>CxCa Gap Closure:</strong> Screen additional {_n(cxca_e-cxca_t)} eligible WLHIV. Complete clinical follow-up for all {_n(cxca_r.get('Positive',0)+cxca_r.get('Suspicious',0))} positive/suspicious findings.")
    if eid_c<95 and deliv>0:
        pris.append(f"<strong>EID Coverage:</strong> Trace all untested HIV-exposed infants. Implement HEI tracking registers at all 37 sites.")
    pris.append("<strong>Root-Cause Investigation:</strong> Commission structured site-level review of performance gaps. Document corrective action plans per facility.")
    while len(pris)<5:
        pris.append("<strong>Data Quality:</strong> Continue routine cross-referencing of EMR and source documents at all supported facilities.")
    pri_html=''.join(f'<li>{p}</li>' for p in pris[:5])

    narrative_css=BASE_CSS+"""<style>
.report-wrap{max-width:870px;margin:0 auto;padding:32px 28px;}
.report-cover{background:linear-gradient(135deg,#0F2942,var(--navy));color:#fff;padding:40px 48px;margin-bottom:28px;}
.report-flag{font-size:8.5px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:rgba(255,255,255,.4);margin-bottom:12px;}
.report-h1{font-size:28px;font-weight:700;line-height:1.2;margin-bottom:8px;}
.report-meta{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;margin-top:24px;background:rgba(255,255,255,.15);}
.report-meta-item{background:rgba(0,0,0,.3);padding:10px 14px;}
.rmi-l{font-size:8px;letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,.4);margin-bottom:3px;}
.rmi-v{font-size:11px;font-weight:700;}
.exec-sum{background:var(--sblue);border-left:5px solid var(--navy);padding:16px 20px;margin-bottom:22px;}
.exec-sum h3{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--navy);margin-bottom:8px;}
.exec-sum p{font-size:11.5px;line-height:1.7;color:#1E293B;}
.report-section{margin-bottom:24px;}
.rsh{font-size:13px;font-weight:700;color:var(--navy);border-bottom:2px solid var(--navy);padding-bottom:5px;margin-bottom:12px;display:flex;align-items:center;gap:8px;}
.rsh-icon{width:22px;height:22px;background:var(--navy);color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0;}
.report-p{font-size:11.5px;line-height:1.75;color:#1E293B;margin-bottom:10px;}
.report-p strong{color:var(--navy);}
.highlight{background:var(--sblue);border-left:3px solid var(--blue);padding:8px 12px;margin:8px 0;font-size:11px;line-height:1.6;}
.gap-box{background:var(--lred);border-left:3px solid var(--red);padding:8px 12px;margin:8px 0;font-size:11px;line-height:1.6;}
.gap-box strong{color:var(--red);}
.action-box{background:var(--lamber);border-left:3px solid var(--amber);padding:8px 12px;margin:8px 0;font-size:11px;line-height:1.6;}
.action-box strong{color:var(--amber);}
.priorities-list{counter-reset:pri;list-style:none;display:flex;flex-direction:column;gap:8px;margin-top:10px;}
.priorities-list li{counter-increment:pri;display:flex;align-items:flex-start;gap:10px;font-size:11.5px;line-height:1.6;padding:10px 12px;background:var(--white);border:1px solid var(--border);}
.priorities-list li::before{content:counter(pri);min-width:22px;height:22px;background:var(--navy);color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0;}
</style>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>ACE3 · {quarter_label} Narrative Report</title>
{narrative_css}</head>
<body>
<div class="report-wrap">
  <div class="report-cover">
    <div class="report-flag">ACE3 Programme · HSCL · Performance Narrative Report · CONFIDENTIAL</div>
    <div class="report-h1">ACE3 — Accelerating Control of the HIV Epidemic in Nigeria</div>
    <div style="font-size:11.5px;color:rgba(255,255,255,.65);margin-top:6px">{quarter_label} · HSCL · Kebbi, Sokoto &amp; Zamfara</div>
    <div class="report-meta">
      <div class="report-meta-item"><div class="rmi-l">Period</div><div class="rmi-v">{period}</div></div>
      <div class="report-meta-item"><div class="rmi-l">Active on ART</div><div class="rmi-v">{_n(txc)}</div></div>
      <div class="report-meta-item"><div class="rmi-l">Facilities</div><div class="rmi-v">37 sites</div></div>
      <div class="report-meta-item"><div class="rmi-l">States</div><div class="rmi-v">Kebbi · Sokoto · Zamfara</div></div>
    </div>
  </div>

  <div class="exec-sum"><h3>Executive Summary</h3>
    <p>The ACE3 programme, implemented by HSCL across 37 facilities in Kebbi, Sokoto, and Zamfara, supports <strong>{_n(txc)} clients on ART</strong> during {period}.
    The programme conducted <strong>{_n(hts)} HIV tests</strong> with a positivity yield of {_p(hts_y)}, initiating <strong>{_n(tx_new)} new clients</strong> on ART at a linkage rate of {_p(link_r)}.
    Viral load suppression (TX_PVLS_N/TX_PVLS_D) reached <strong>{_p(vl_s)}</strong> — {'exceeding' if vl_s>=95 else 'approaching'} the 95% threshold — while TX_PVLS_D/TX_CURR coverage of <strong>{_p(vl_c)}</strong> and treatment interruptions of <strong>{_n(tx_ml)} clients</strong> remain priority focus areas.</p>
  </div>

  <div class="report-section">
    <div class="rsh"><div class="rsh-icon">1</div>HIV Testing Services</div>
    <p class="report-p">During {period}, the programme conducted <strong>{_n(hts)} HIV tests</strong> across Kebbi ({_n(state_curr.get('Kebbi',0))} tested), Sokoto, and Zamfara, identifying <strong>{_n(hts_p)} HIV-positive individuals</strong> at a positivity yield of <strong>{_p(hts_y)}</strong>.
    {'This represents ' + str(round(hts/tgts['HTS_TST']*100,1)) + '% of the annual testing target of ' + _n(tgts['HTS_TST']) + '.' if tgts.get('HTS_TST') else ''}
    The low positivity yield indicates testing is predominantly reaching HIV-negative populations; targeted index testing and community risk stratification are recommended to improve efficiency.</p>
    {'<div class="gap-box"><strong>⚠ Testing Gap:</strong> Testing volume requires acceleration against the annual target. Strengthening index testing and community outreach will improve both volume and yield.</div>' if tgts.get('HTS_TST') and hts/tgts['HTS_TST']<0.5 else ''}
  </div>

  <div class="report-section">
    <div class="rsh"><div class="rsh-icon">2</div>New ART Initiations &amp; Linkage</div>
    <p class="report-p"><strong>{_n(tx_new)} clients were newly initiated on ART</strong> during {period}, representing a linkage rate of <strong>{_p(link_r)}</strong> of HIV-positive individuals identified through testing.
    {'This is ' + str(round(tx_new/tgts['TX_NEW']*100,1)) + '% of the annual TX_NEW target of ' + _n(tgts['TX_NEW']) + '.' if tgts.get('TX_NEW') else ''}
    Prompt linkage of newly diagnosed individuals to ART remains central to achieving epidemic control.</p>
    {'<div class="highlight"><strong>Achievement:</strong> Linkage rate of ' + _p(link_r) + ' demonstrates strong case management and same-day ART initiation protocols across supported facilities.</div>' if link_r>=90 else ''}
  </div>

  <div class="report-section">
    <div class="rsh"><div class="rsh-icon">3</div>PMTCT &amp; Paediatric Services</div>
    <p class="report-p"><strong>{_n(pmtc_n)} pregnant women were tested for HIV at ANC</strong> during {period}, identifying <strong>{_n(pmtc_p)} HIV-positive women</strong> (prevalence {pmtc_p/pmtc_n*100:.3f}%).
    {_n(pmtc_a)} women were on ART through PMTCT services. {'This represents ' + str(round(pmtc_n/tgts['PMTCT_STAT_N']*100,1)) + '% of the annual ANC testing target.' if tgts.get('PMTCT_STAT_N') else ''}</p>
    {'<div class="gap-box"><strong>⚠ EID Coverage:</strong> Only ' + _n(eid) + ' of ' + _n(deliv) + ' HIV-exposed infants (' + _p(eid_c) + ') received EID PCR testing, below the 95% target. Untested HEI risk undetected paediatric infection.</div>' if eid_c<95 and deliv>0 else ''}
    {'<div class="action-box"><strong>Action:</strong> Implement HEI tracking registers at all 37 sites. Trace all untested HIV-exposed infants and schedule EID at 6 weeks post-delivery.</div>' if eid_c<95 and deliv>0 else ''}
  </div>

  <div class="report-section">
    <div class="rsh"><div class="rsh-icon">4</div>Active Treatment Cohort &amp; DSD</div>
    <p class="report-p">As of {period}, <strong>{_n(txc)} clients are active on ART</strong> across 37 facilities ({fem_p:.1f}% female, {lt15/txc*100:.1f}% paediatric, {bio_p:.1f}% biometrically enrolled).
    <strong>{_p(mmd_p)}</strong> of clients ({_n(mmd_3p)}) are on multi-month dispensing of ≥3 months, with {_p(mmd_6p/txc*100 if txc else 0)} on a 6-month supply — {'exceeding' if mmd_p>=90 else 'approaching'} the 90% DSD threshold.</p>
    {'<div class="highlight"><strong>Achievement:</strong> MMD coverage at ' + _p(mmd_p) + ' reflects full operationalisation of differentiated service delivery.</div>' if mmd_p>=90 else ''}
  </div>

  <div class="report-section">
    <div class="rsh"><div class="rsh-icon">5</div>Treatment Retention</div>
    <p class="report-p">Treatment interruptions (TX_ML — clients ≥28 days past last expected contact) totalled <strong>{_n(tx_ml)} clients</strong> during {period}.
    Of these, {_n(tx_ml)} broke down as: {_n(d.get('TX_ML_OUTCOMES',{}).get('IIT',0))} lost to follow-up, {_n(d.get('TX_ML_OUTCOMES',{}).get('Died',0))} deaths, {_n(d.get('TX_ML_OUTCOMES',{}).get('Transferred Out',0))} transfers out, and {_n(d.get('TX_ML_OUTCOMES',{}).get('Stopped Treatment',0))} stopped treatment.
    <strong>{_n(tx_rtt)} clients ({_p(rtt_r)})</strong> were successfully returned to treatment (RTT).</p>
    {'<div class="gap-box"><strong>⚠ Retention Alert:</strong> RTT rate of ' + _p(rtt_r) + ' represents a net cohort loss requiring urgent tracing response. Target RTT rate ≥60%.</div>' if rtt_r<60 and tx_ml>0 else ''}
    {'<div class="action-box"><strong>Action:</strong> Implement intensive tracing for all ' + _n(tx_ml) + ' TX_ML clients. Review IIT patterns by facility to identify high-burden sites.</div>' if tx_ml>0 else ''}
  </div>

  <div class="report-section">
    <div class="rsh"><div class="rsh-icon">6</div>Viral Load — TX_PVLS</div>
    <p class="report-p">Of {_n(pvls_d)} clients with a TX_PVLS result, <strong>{_n(pvls_n)} ({_p(vl_s)}) are virally suppressed</strong> below 1,000 copies/mL (TX_PVLS_N/TX_PVLS_D) —
    {'exceeding' if vl_s>=95 else 'below'} the 95% threshold. TX_PVLS_D/TX_CURR coverage stands at <strong>{_p(vl_c)}</strong>, with <strong>{_n(vl_gap)} clients</strong> without a VL result.
    {_n(unsupp)} clients remain unsuppressed and require enhanced adherence counselling.</p>
    {'<div class="highlight"><strong>Achievement:</strong> TX_PVLS_N/TX_PVLS_D at ' + _p(vl_s) + ' demonstrates strong treatment quality across the programme.</div>' if vl_s>=95 else ''}
    {'<div class="gap-box"><strong>⚠ VL Coverage Gap:</strong> TX_PVLS_D/TX_CURR at ' + _p(vl_c) + ' is ' + str(round(95-vl_c,1)) + ' pp below the 95% target. ' + _n(vl_gap) + ' clients have not had a VL sample collected.</div>' if vl_c<95 else ''}
    {'<div class="action-box"><strong>Action:</strong> Prioritise clearance of ' + _n(vl_gap) + ' pending VL samples. Enrol all ' + _n(unsupp) + ' unsuppressed clients in structured EAC sessions.</div>' if vl_c<95 else ''}
  </div>

  <div class="report-section">
    <div class="rsh"><div class="rsh-icon">7</div>Enhanced Adherence Counselling (EAC)</div>
    <p class="report-p">A total of <strong>{_n(eac_cl)} unsuppressed clients</strong> are actively managed through Enhanced Adherence Counselling during {period}.
    EAC session completion: <strong>{_n(eac_s1)} completed 1st EAC</strong> and {_n(eac_s2)} completed 2nd EAC sessions.
    Of {_n(eac_pvl)} clients with a post-EAC VL result, <strong>{_n(eac_psn)} ({_p(eac_psr)}) achieved re-suppression</strong> — a {'strong' if eac_psr>=90 else 'moderate'} outcome demonstrating the effectiveness of structured adherence support.</p>
    {'<div class="highlight"><strong>Achievement:</strong> Post-EAC re-suppression rate of ' + _p(eac_psr) + ' confirms that structured EAC is effective in returning clients to viral suppression.</div>' if eac_psr>=90 else ''}
    {'<div class="action-box"><strong>Action:</strong> Accelerate post-EAC VL collection. Only ' + _n(eac_pvl) + ' of ' + _n(eac_cl) + ' EAC clients have a post-EAC VL result. All clients completing 3 EAC sessions should have a repeat VL scheduled.</div>' if eac_cl>0 and eac_pvl<eac_cl*0.5 else ''}
  </div>

  <div class="report-section">
    <div class="rsh"><div class="rsh-icon">8</div>TB/HIV Integration</div>
    <p class="report-p"><strong>{_n(tb_scr)} clients were screened for tuberculosis</strong>, with {_n(tb_pos)} screen-positive.
    TB preventive therapy (TPT) was initiated or sustained for <strong>{_n(tpt)} clients ({_p(tpt_c)} of TX_CURR)</strong> —
    {'exceeding' if tpt_c>=90 else 'below'} the 90% target.</p>
    {'<div class="highlight"><strong>Achievement:</strong> TPT coverage at ' + _p(tpt_c) + ' substantially reduces TB disease risk across the programme cohort.</div>' if tpt_c>=90 else ''}
  </div>

  <div class="report-section">
    <div class="rsh"><div class="rsh-icon">9</div>PrEP Programme</div>
    <p class="report-p"><strong>{_n(pnew)} individuals newly initiated PrEP</strong> (PrEP_NEW) during {period}, with {_n(pct_)} continuing clients returning for follow-up (PrEP_CT). The active PrEP snapshot stands at <strong>{_n(pcurr)} clients</strong>.
    {'This represents ' + str(round(pnew/tgts['PrEP_NEW']*100,1)) + '% of the annual PrEP_NEW target of ' + _n(tgts['PrEP_NEW']) + '.' if tgts.get('PrEP_NEW') else ''}</p>
    {'<div class="gap-box"><strong>⚠ PrEP Target Gap:</strong> PrEP_NEW at ' + _n(pnew) + ' is below pace against the annual target. Strengthening demand generation for high-risk populations is recommended.</div>' if tgts.get('PrEP_NEW') and pnew/tgts['PrEP_NEW']<0.4 else ''}
  </div>

  <div class="report-section">
    <div class="rsh"><div class="rsh-icon">10</div>Women's Health: CxCa &amp; AHD</div>
    <p class="report-p">Of {_n(cxca_e)} eligible WLHIV, <strong>{_n(cxca_t)} were screened for cervical cancer ({_p(cxca_c)} coverage)</strong>.
    {f'{_n(cxca_r.get("Positive",0)+cxca_r.get("Suspicious",0))} women with positive or suspicious findings require urgent clinical follow-up.' if cxca_r else ''}
    AHD screening identified <strong>{_n(ahd_c)} confirmed AHD cases ({ahd_r:.1f}%)</strong> from {_n(ahd_s)} screened, with {_n(ahd_cr)} CrAg positives requiring urgent fluconazole.</p>
    {'<div class="gap-box"><strong>⚠ CxCa Gap:</strong> Coverage at ' + _p(cxca_c) + ' is ' + str(round(80-cxca_c,1)) + ' pp below the 80% target. ' + _n(cxca_e-cxca_t) + ' eligible WLHIV remain unscreened.</div>' if cxca_c<80 else ''}
  </div>

  {qoq_sec}

  <div class="report-section">
    <div class="rsh"><div class="rsh-icon">{'10' if not qoq_sec else '11'}</div>Key Priorities — Next Quarter</div>
    <ol class="priorities-list">{pri_html}</ol>
  </div>

  <div style="margin-top:28px;padding:14px 18px;background:var(--sblue);border-top:3px solid var(--navy);font-size:11px;line-height:1.7;color:#1E293B">
    <strong>Forward Look:</strong> The ACE3 programme enters the next quarter with {'strong' if vl_s>=95 else 'improving'} viral suppression, {'high' if mmd_p>=90 else 'growing'} MMD coverage, and {'excellent' if tpt_c>=90 else 'strong'} TPT coverage.
    Priority areas are {'retention, ' if tx_ml>0 else ''}{'VL coverage, ' if vl_c<95 else ''}{'EAC follow-up, ' if eac_pvl<eac_cl*0.5 else ''}and CxCa screening expansion.
    The programme team remains committed to evidence-based corrective actions across all identified gaps.
  </div>

  <div style="margin-top:18px;padding:10px 16px;background:#F8FAFC;border:1px solid var(--border);font-size:9.5px;color:var(--light);text-align:center">
    ACE3 · HSCL · {period} · Kebbi, Sokoto &amp; Zamfara · 37 Facilities · Source: LAMIS+ / DHIS2 · CONFIDENTIAL
  </div>
</div>
{_footer(period)}
</body></html>"""


# ─────────────────────────────────────────────────────────────────────────────
# TALKING POINTS — cascade order
# ─────────────────────────────────────────────────────────────────────────────
def build_talking_points(results, period, quarter_label, quarter_mode):
    q1=results.get('q1',{}); q2=results.get('q2',{})
    d=results.get('semi') if quarter_mode in ('SEMI','CUM') else (q2 if quarter_mode=='Q2' else q1)
    tgts=results.get('targets',{})

    txc=d.get('TX_CURR',0); vl_s=d.get('VL_SUPPRESSION',0); vl_c=d.get('VL_COVERAGE',0)
    mmd_3p=d.get('MMD_3P',0); mmd_p=mmd_3p/txc*100 if txc else 0
    tpt=d.get('TB_PREV_N',0); tpt_c=tpt/txc*100 if txc else 0
    tx_ml=d.get('TX_ML',0); tx_rtt=d.get('TX_RTT',0); rtt_r=tx_rtt/tx_ml*100 if tx_ml else 0
    hts=d.get('HTS_TST',0); hts_p=d.get('HTS_TST_POS',0); hts_y=d.get('HTS_YIELD',0)
    pvls_d=d.get('TX_PVLS_D',0); pvls_n=d.get('TX_PVLS_N',0); vl_gap=d.get('VL_GAP',0)
    cxca_e=d.get('CXCA_SCRN',0); cxca_t=d.get('CXCA_TX',0); cxca_c=cxca_t/cxca_e*100 if cxca_e else 0
    eid=d.get('PMTCT_EID',0); deliv=d.get('PMTCT_DELIVERED',0); eid_c=eid/deliv*100 if deliv else 0
    bio=d.get('TX_CURR_BIO',0); bio_p=bio/txc*100 if txc else 0
    tx_new=d.get('TX_NEW',0); link_r=tx_new/hts_p*100 if hts_p else 0
    pmtc_n=d.get('PMTCT_STAT_N',0); unsupp=d.get('VL_UNSUPP',0)
    pnew=d.get('PrEP_NEW',0)
    eac_cl=d.get('EAC_CASELOAD',0); eac_psr=d.get('EAC_POST_SUPP_R',0); eac_psn=d.get('EAC_POST_SUPP_N',0)
    eac_pvl=d.get('EAC_POST_VL_N',0)

    # achievements — cascade ordered
    ach=[]
    if vl_s>=95: ach.append(('g','VL SUPPRESSION',f'<strong>{_p(vl_s)} TX_PVLS_N/TX_PVLS_D</strong> — {_n(pvls_n)} of {_n(pvls_d)} clients suppressed, exceeding the 95% threshold.'))
    if mmd_p>=90: ach.append(('g','DSD / MMD',f'<strong>{_p(mmd_p)} on ≥3-month ART supply</strong> — {_n(d.get("MMD_6P",0))} on 6-month supply. Exceeds 90% DSD target.'))
    if tpt_c>=90: ach.append(('g','TB/HIV — TPT',f'<strong>{_p(tpt_c)} TPT coverage</strong> — {_n(tpt)} clients on TB preventive therapy, exceeding 90% target.'))
    if eac_psr>=90: ach.append(('g','EAC OUTCOMES',f'<strong>{_p(eac_psr)} post-EAC re-suppression</strong> — {_n(eac_psn)} of {_n(eac_pvl)} EAC clients re-suppressed after structured adherence counselling.'))
    if bio_p>=95: ach.append(('g','DATA QUALITY',f'<strong>{bio_p:.1f}% biometric enrolment</strong> — {_n(bio)} of {_n(txc)} clients enrolled, ensuring data integrity across 37 sites.'))
    if link_r>=90: ach.append(('g','LINKAGE',f'<strong>{_p(link_r)} linkage to ART</strong> — {_n(tx_new)} of {_n(hts_p)} HIV-positive individuals successfully linked to treatment.'))
    while len(ach)<5: ach.append(('b','PROGRAMME',f'Programme maintaining {_n(txc)} active clients across 37 facilities in Kebbi, Sokoto and Zamfara.'))

    # concerns — cascade ordered
    con=[]
    if tx_ml>0: con.append(('r','HIGH PRIORITY',f'<strong>TX_ML {_n(tx_ml)} clients</strong> — RTT rate only {_p(rtt_r)}. Net client loss threatens cohort size. Tracing campaign required.'))
    if vl_c<95: con.append(('r','CRITICAL GAP',f'<strong>TX_PVLS_D/TX_CURR {_p(vl_c)} — {95-vl_c:.1f} pp below 95%</strong>. {_n(vl_gap)} clients without VL result. Phlebotomy blitz required.'))
    if tgts.get('HTS_TST') and hts/tgts['HTS_TST']<0.5: con.append(('r','HIGH PRIORITY',f'<strong>HTS_TST {round(hts/tgts["HTS_TST"]*100,1)}% of annual target</strong> — {_n(hts)} tested. Yield {_p(hts_y)} — index testing scale-up needed.'))
    if cxca_c<80: con.append(('r','CRITICAL GAP',f'<strong>CxCa {_p(cxca_c)} vs 80% target</strong> — {_n(cxca_e-cxca_t)} eligible WLHIV unscreened.'))
    if eid_c<95 and deliv>0: con.append(('a','MONITOR',f'<strong>EID PCR {_p(eid_c)}</strong> — {_n(max(0,deliv-eid))} HIV-exposed infants untested. Risk of undetected paediatric infection.'))
    if eac_cl>0 and eac_pvl<eac_cl*0.5: con.append(('a','MONITOR',f'<strong>Post-EAC VL collection below 50%</strong> of {_n(eac_cl)} EAC caseload. Repeat VL scheduling needs strengthening.'))
    while len(con)<5: con.append(('a','WATCH','Continue monitoring all programme areas for emerging performance trends.'))

    ach_html=''.join(f'<li><span class="tp-tag g">{t}</span><div>{txt}</div></li>' for _,t,txt in ach[:5])
    con_html=''.join(f'<li><span class="tp-tag {c}">{t}</span><div>{txt}</div></li>' for c,t,txt in con[:5])

    # Q-on-Q
    qoq_rows=''
    if quarter_mode in ('SEMI','CUM') and q1 and q2:
        def _qr(label,code,k,inv=False):
            v1,v2=q1.get(k,0),q2.get(k,0)
            if not v1 and not v2: return ''
            diff=v2-v1; pct=(diff/v1*100) if v1 else 0
            sign='▲' if diff>0 else '▼'
            good=(diff<=0) if inv else (diff>=0)
            css='ok' if good else 'dn'
            return f"<tr><td>{label}</td><td style='font-family:monospace;font-size:9.5px'>{code}</td><td class='num'>{_n(v1)}</td><td class='num'>{_n(v2)}</td><td class='num {css}'>{sign}{abs(int(diff)):,}</td><td class='num {css}'>{sign}{abs(pct):.1f}%</td></tr>"
        qoq_rows=(
            _qr('HIV Tests','HTS_TST','HTS_TST')+
            _qr('New Initiations','TX_NEW','TX_NEW')+
            _qr('Tx Interruptions','TX_ML','TX_ML',True)+
            _qr('PMTCT ANC Tested','PMTCT_STAT','PMTCT_STAT_N')+
            _qr('PrEP New','PrEP_NEW','PrEP_NEW')
        )

    # below target
    btm_rows=''
    BTM=[
        ('TX_PVLS_D/TX_CURR — VL Coverage',vl_c,95,'Phlebotomy blitz; clear TX_PVLS_D sample backlog'),
        ('CxCa Coverage',cxca_c,80,f'Screen {_n(cxca_e-cxca_t)} remaining eligible WLHIV'),
        ('EID PCR Coverage',eid_c,95,'Trace untested HEI; implement HEI tracking registers'),
        ('TPT Coverage',tpt_c,90,'Maintain; complete TPT courses'),
        ('MMD ≥3 Months',mmd_p,90,'Review <3mo clients; ensure uninterrupted supply'),
    ]
    for label,val,thr,act in BTM:
        if val<thr:
            gap=thr-val; col='crit' if gap>15 else 'mod'
            btm_rows+=f"<tr><td>{label}</td><td class='num'>{_p(val)}</td><td class='num'>{thr}%</td><td class='num {col}'>−{gap:.1f} pp</td><td style='font-size:10px'>{act}</td></tr>"

    # management actions
    acts=[]
    if tx_ml>0: acts.append(('RETENTION',f'30-day tracing for all {_n(tx_ml)} TX_ML clients; assign facility case managers; target RTT ≥60%.'))
    if vl_c<95: acts.append(('VL COVERAGE',f'Clear {_n(vl_gap)}-sample TX_PVLS_D backlog in 6 weeks; deploy VL scheduling matrix; target TX_PVLS_D/TX_CURR ≥90%.'))
    if eac_cl>0: acts.append(('EAC',f'Schedule repeat VL for all {_n(eac_cl)} EAC clients who have completed ≥3 sessions. Target: post-EAC VL for 100% of eligible.'))
    if cxca_c<80: acts.append(('CXCA',f'Screen ≥{_n(min(5000,cxca_e-cxca_t))} additional WLHIV; complete follow-up for all positive/suspicious findings.'))
    if eid_c<95 and deliv>0: acts.append(('EID',f'Trace {_n(max(0,deliv-eid))} untested HEI; implement HEI tracking registers at all delivery sites.'))
    acts.append(('ROOT CAUSE','Commission site-level review of performance gaps; document corrective action plans; share findings with programme management within 30 days.'))

    act_html=''.join(f'<li><div class="li-content"><div class="li-label">{lb}</div>{txt}</div></li>' for lb,txt in acts[:5])

    tp_css=BASE_CSS+"""<style>
.tp-wrap{max-width:870px;margin:0 auto;padding:28px;}
.tp-section{margin-bottom:22px;}
.tp-hdr{display:flex;align-items:center;gap:10px;padding:10px 14px;margin-bottom:12px;}
.tp-hdr.ach{background:var(--lgreen);border-left:4px solid var(--green);}
.tp-hdr.con{background:var(--lred);border-left:4px solid var(--red);}
.tp-hdr.qoq{background:var(--sblue);border-left:4px solid var(--blue);}
.tp-hdr.tgt{background:var(--lamber);border-left:4px solid var(--amber);}
.tp-hdr.act{background:#F5F3FF;border-left:4px solid #6B46C1;}
.tp-hdr-icon{font-size:18px;}
.tp-hdr-text h3{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;}
.tp-hdr-text p{font-size:9.5px;color:var(--mid);}
.tp-list{list-style:none;display:flex;flex-direction:column;gap:6px;}
.tp-list li{display:flex;align-items:flex-start;gap:10px;padding:8px 12px;background:var(--white);border:1px solid var(--border);font-size:11px;line-height:1.55;}
.tp-tag{font-size:8px;font-weight:700;padding:2px 7px;white-space:nowrap;flex-shrink:0;margin-top:2px;}
.tp-tag.g{background:var(--lgreen);color:var(--green);}
.tp-tag.r{background:var(--lred);color:var(--red);}
.tp-tag.a{background:var(--lamber);color:var(--amber);}
.tp-tag.b{background:var(--sblue);color:var(--navy);}
.qoq-tbl{width:100%;border-collapse:collapse;}
.qoq-tbl th{background:var(--navy);color:#fff;font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:7px 10px;text-align:left;}
.qoq-tbl td{padding:7px 10px;font-size:10.5px;border-bottom:1px solid var(--border);}
.qoq-tbl tr:nth-child(even) td{background:#F8FAFC;}
.qoq-tbl .num{font-family:monospace;font-weight:600;text-align:right;}
.qoq-tbl .dn{color:var(--red);font-weight:700;}.qoq-tbl .ok{color:var(--green);font-weight:700;}
.below-tgt-tbl{width:100%;border-collapse:collapse;}
.below-tgt-tbl th{background:var(--red);color:#fff;font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:7px 10px;text-align:left;}
.below-tgt-tbl td{padding:7px 10px;font-size:10.5px;border-bottom:1px solid var(--border);}
.below-tgt-tbl tr:nth-child(even) td{background:#FFF5F5;}
.below-tgt-tbl .num{font-family:monospace;font-weight:600;text-align:right;}
.below-tgt-tbl .crit{color:var(--red);font-weight:700;}.below-tgt-tbl .mod{color:var(--amber);font-weight:700;}
.mgmt-list{list-style:none;counter-reset:mgmt;display:flex;flex-direction:column;gap:7px;}
.mgmt-list li{counter-increment:mgmt;display:flex;align-items:flex-start;gap:10px;padding:10px 14px;background:var(--white);border:1px solid var(--border);}
.mgmt-list li::before{content:counter(mgmt);min-width:24px;height:24px;background:#6B46C1;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0;}
.li-content{font-size:11px;line-height:1.55;}
.li-label{font-size:8.5px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:#6B46C1;margin-bottom:2px;}
</style>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>ACE3 · {quarter_label} Talking Points</title>
{tp_css}</head>
<body>
<div style="background:linear-gradient(135deg,#0F2942,var(--navy));color:#fff;padding:22px 28px;margin-bottom:0">
  <div style="font-size:8.5px;letter-spacing:3px;text-transform:uppercase;color:rgba(255,255,255,.4);margin-bottom:8px">ACE3 Programme · HSCL · {period}</div>
  <div style="font-size:20px;font-weight:700;font-family:var(--mono)">Executive Talking Points — {quarter_label}</div>
  <div style="font-size:10.5px;color:rgba(255,255,255,.6);margin-top:4px">Cascade order: Testing → Linkage → PMTCT → Treatment → Retention → VL → EAC → TB → PrEP · CONFIDENTIAL</div>
</div>
<div class="tp-wrap">

  <div class="tp-section">
    <div class="tp-hdr ach"><div class="tp-hdr-icon">🏆</div>
      <div class="tp-hdr-text"><h3>Top 5 Achievements</h3><p>Lead with these — cascade order</p></div></div>
    <ul class="tp-list">{ach_html}</ul>
  </div>

  <div class="tp-section">
    <div class="tp-hdr con"><div class="tp-hdr-icon">⚠️</div>
      <div class="tp-hdr-text"><h3>Top 5 Performance Concerns</h3><p>Requires management attention</p></div></div>
    <ul class="tp-list">{con_html}</ul>
  </div>

  {'<div class="tp-section"><div class="tp-hdr qoq"><div class="tp-hdr-icon">📊</div><div class="tp-hdr-text"><h3>Quarter-on-Quarter Changes</h3><p>Q1 vs Q2</p></div></div><table class="qoq-tbl"><thead><tr><th>Indicator</th><th>Code</th><th style="text-align:right">Q1</th><th style="text-align:right">Q2</th><th style="text-align:right">Change</th><th style="text-align:right">%Δ</th></tr></thead><tbody>' + qoq_rows + '</tbody></table></div>' if qoq_rows else ''}

  {'<div class="tp-section"><div class="tp-hdr tgt"><div class="tp-hdr-icon">🎯</div><div class="tp-hdr-text"><h3>Indicators Below Target</h3><p>Gaps requiring action</p></div></div><table class="below-tgt-tbl"><thead><tr><th>Indicator</th><th style="text-align:right">Actual</th><th style="text-align:right">Target</th><th style="text-align:right">Gap</th><th>Action Required</th></tr></thead><tbody>' + btm_rows + '</tbody></table></div>' if btm_rows else ''}

  <div class="tp-section">
    <div class="tp-hdr act"><div class="tp-hdr-icon">📋</div>
      <div class="tp-hdr-text"><h3>Management Actions — Next Quarter</h3><p>5 priority actions</p></div></div>
    <ol class="mgmt-list">{act_html}</ol>
  </div>

  <div style="padding:10px 16px;background:#F8FAFC;border:1px solid var(--border);font-size:9px;color:var(--light);text-align:center;margin-top:10px">
    ACE3 · HSCL · {period} · Kebbi, Sokoto &amp; Zamfara · 37 Facilities · CONFIDENTIAL — Internal Use Only
  </div>
</div>
{_footer(period)}
</body></html>"""
