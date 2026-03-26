"""
ACE3 Charts — Statista Infographic Standard
Each chart = one clear story. Bold headline. Clean flat bars.
Minimal axes. Data labels on bars. White background. HSCL brand footer.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patheffects as pe
import numpy as np
import os

# ── PALETTE ──────────────────────────────────────────────
C = {
    'navy':    '#0A2342',
    'teal':    '#0E7C7B',
    'emerald': '#17A550',
    'sky':     '#2B8FD4',
    'orange':  '#E8611A',
    'red':     '#D72638',
    'gold':    '#F0A500',
    'purple':  '#6C3082',
    'coral':   '#FF6B6B',
    'slate':   '#5C6B7A',
    'light':   '#F5F7FA',
    'mid':     '#D0D7DE',
    'dark':    '#1A1A2E',
}

FONT = 'DejaVu Sans'  # Available everywhere

def _base(fig, ax, w=10, h=5.5):
    """Statista base: white bg, no top/right spines, subtle bottom/left."""
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color(C['mid'])
    ax.spines['bottom'].set_linewidth(0.5)
    ax.tick_params(left=False, bottom=True, colors=C['slate'], labelsize=9, length=0)
    ax.yaxis.set_visible(False)

def _headline(ax, text, sub=""):
    """Statista-style bold headline above chart."""
    ax.set_title(text, fontsize=16, fontweight='bold', color=C['dark'], loc='left',
                 pad=20, fontfamily=FONT)
    if sub:
        ax.text(0, 1.12, sub, transform=ax.transAxes, fontsize=10, color=C['slate'],
                fontfamily=FONT, va='bottom')

def _footer(fig, source="Source: ACE3/HSCL RADET & Line-Lists · FY26"):
    """Brand footer strip."""
    fig.text(0.04, 0.015, source, fontsize=9, color=C['slate'], fontfamily=FONT)
    # Navy brand line at very bottom
    fig.patches.append(plt.Rectangle((0, 0), 1, 0.012, transform=fig.transFigure,
                                      facecolor=C['navy'], zorder=10)); fig.subplots_adjust(bottom=0.08)

def _bar_labels(ax, bars, vals, fmt='{:,}', fs=10, color=C['dark'], above=True):
    """Place value labels directly on or above bars."""
    for bar, val in zip(bars, vals):
        y = bar.get_height()
        if above:
            ax.text(bar.get_x() + bar.get_width()/2, y + max(vals)*0.02,
                    fmt.format(val), ha='center', va='bottom', fontsize=fs,
                    fontweight='bold', color=color, fontfamily=FONT)
        else:
            ax.text(bar.get_x() + bar.get_width()/2, y/2,
                    fmt.format(val), ha='center', va='center', fontsize=fs,
                    fontweight='bold', color='white', fontfamily=FONT)

def _save(fig, path):
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none', pad_inches=0.3)
    plt.close(fig)
    return path


# ══════════════════════════════════════════════════════════
# 1. TREATMENT CASCADE
# ══════════════════════════════════════════════════════════
def treatment_cascade(r, d):
    h = r.get('HTS_TST', {}); pv = r.get('TX_PVLS', {}); tc = r.get('TX_CURR', {}); tn = r.get('TX_NEW', {})

    labels = ['Tested\n(HTS_TST)', 'Positive\n(HTS_POS)', 'Linked\n(TX_NEW)', 'On ART\n(TX_CURR)',
              'VL Done\n(PVLS_D)', 'Suppressed\n(PVLS_N)']
    vals = [h.get('value',0), h.get('pos',0), tn.get('cum', tn.get('value',0)),
            tc.get('value',0), pv.get('d',0), pv.get('n',0)]
    colors = [C['sky'], C['orange'], C['gold'], C['navy'], C['teal'], C['emerald']]

    fig, ax = plt.subplots(figsize=(11, 6))
    _base(fig, ax)
    _headline(ax, f"{tc.get('value',0):,} patients currently on ART across 37 facilities",
              "HIV Treatment Cascade — ACE3 FY26 Semi-Annual")

    bars = ax.bar(labels, vals, color=colors, width=0.55, edgecolor='white', linewidth=1.5, zorder=3)
    _bar_labels(ax, bars, vals, fs=11)
    ax.set_ylim(0, max(vals) * 1.18)
    _footer(fig)
    return _save(fig, os.path.join(d, 'cascade.png'))


# ══════════════════════════════════════════════════════════
# 2. 95-95-95 PROGRESS
# ══════════════════════════════════════════════════════════
def progress_95(r, d):
    pv = r.get('TX_PVLS', {})
    cov = pv.get('coverage', 0)
    sup = pv.get('suppression', 0)

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor('white'); ax.set_facecolor('white')
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(left=False, bottom=False, labelbottom=False, labelleft=False)

    _headline(ax, f"Viral suppression at {sup}% — closing in on the 3rd 95 target",
              "Progress toward UNAIDS 95-95-95")

    items = [
        ('1st 95: Know HIV Status', None, C['mid']),
        ('2nd 95: On Treatment', cov, C['teal'] if cov >= 90 else C['gold']),
        ('3rd 95: Virally Suppressed', sup, C['emerald'] if sup >= 90 else C['gold']),
    ]
    for i, (label, val, color) in enumerate(items):
        y = 2 - i
        # Background bar
        ax.barh(y, 100, height=0.55, color=C['light'], edgecolor='none', zorder=1)
        if val is not None:
            ax.barh(y, val, height=0.55, color=color, edgecolor='none', zorder=2)
            ax.text(val + 1.5, y, f'{val}%', va='center', fontsize=14, fontweight='bold',
                    color=C['dark'], fontfamily=FONT, zorder=3)
        else:
            ax.text(50, y, 'N/A at facility level', va='center', ha='center',
                    fontsize=10, color=C['slate'], style='italic', fontfamily=FONT, zorder=3)
        ax.text(-1, y, label, va='center', ha='right', fontsize=10, fontweight='bold',
                color=C['dark'], fontfamily=FONT, zorder=3)

    ax.axvline(95, color=C['red'], linestyle='--', linewidth=1, alpha=0.6, zorder=2)
    ax.text(95.5, 2.6, '95% target', fontsize=8, color=C['red'], fontfamily=FONT)
    ax.set_xlim(-55, 108)
    ax.set_ylim(-0.5, 3.2)
    _footer(fig)
    return _save(fig, os.path.join(d, '95_progress.png'))


# ══════════════════════════════════════════════════════════
# 3. TX_CURR BY STATE
# ══════════════════════════════════════════════════════════
def tx_curr_by_state(r, d):
    st = r.get('TX_CURR', {}).get('state', {})
    if not st: return None
    states = list(st.keys()); vals = list(st.values())
    total = sum(vals)

    fig, ax = plt.subplots(figsize=(8, 5))
    _base(fig, ax)
    _headline(ax, f"Kebbi leads with {max(vals):,} patients on ART",
              f"TX_CURR by state — {total:,} total")

    colors = [C['navy'], C['teal'], C['emerald']][:len(states)]
    bars = ax.bar(states, vals, color=colors, width=0.45, edgecolor='white', linewidth=1.5, zorder=3)
    _bar_labels(ax, bars, vals, fs=13)

    # Add percentage labels below value
    for bar, val in zip(bars, vals):
        pct = round(val / total * 100, 1)
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(vals)*0.08,
                f'({pct}%)', ha='center', va='bottom', fontsize=9, color=C['slate'], fontfamily=FONT)

    ax.set_ylim(0, max(vals) * 1.22)
    _footer(fig)
    return _save(fig, os.path.join(d, 'tx_curr_state.png'))


# ══════════════════════════════════════════════════════════
# 4. HTS MODALITY + YIELD
# ══════════════════════════════════════════════════════════
def hts_modality_yield(r, d):
    mod = r.get('HTS_TST', {}).get('modality', {})
    if not mod: return None
    total = r.get('HTS_TST', {}).get('value', 0)
    pos = r.get('HTS_TST', {}).get('pos', 0)

    sm = sorted(mod.items(), key=lambda x: -x[1].get('tested', 0))[:7]
    labels = [m[0] for m in sm]
    tested = [m[1]['tested'] for m in sm]
    yields = [m[1]['yield'] for m in sm]

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white'); ax.set_facecolor('white')
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(left=False, bottom=False, labelbottom=False, labelleft=False)

    _headline(ax, f"{total:,} HIV tests conducted — {pos:,} positive ({r.get('HTS_TST',{}).get('yield',0)}% yield)",
              "HIV Testing by Modality — FY26 Semi-Annual")

    y = np.arange(len(labels))
    bars = ax.barh(y, tested, height=0.55, color=C['sky'], edgecolor='none', zorder=3)
    ax.invert_yaxis()

    for i, (bar, val, yld) in enumerate(zip(bars, tested, yields)):
        # Label on the right of bar
        ax.text(bar.get_width() + max(tested)*0.01, i, f'{val:,}',
                va='center', fontsize=10, fontweight='bold', color=C['dark'], fontfamily=FONT)
        # Yield badge
        yc = C['emerald'] if yld >= 2 else (C['gold'] if yld >= 1 else C['slate'])
        ax.text(max(tested)*1.15, i, f'{yld}%', va='center', fontsize=9, fontweight='bold',
                color=yc, fontfamily=FONT,
                bbox=dict(boxstyle='round,pad=0.3', facecolor=C['light'], edgecolor='none'))
        # Label on the left
        ax.text(-max(tested)*0.01, i, labels[i], va='center', ha='right',
                fontsize=9, color=C['dark'], fontfamily=FONT)

    ax.set_xlim(-max(tested)*0.45, max(tested)*1.25)
    ax.set_ylim(len(labels)-0.5, -0.8)

    # Yield column header
    ax.text(max(tested)*1.15, -0.7, 'Yield', ha='center', fontsize=8, fontweight='bold',
            color=C['slate'], fontfamily=FONT)

    _footer(fig)
    return _save(fig, os.path.join(d, 'hts_modality.png'))


# ══════════════════════════════════════════════════════════
# 5. TX_ML OUTCOMES
# ══════════════════════════════════════════════════════════
def tx_ml_outcomes(r, d):
    oc = r.get('TX_ML', {}).get('outcomes', {})
    if not oc: return None
    total = sum(oc.values())

    labels = list(oc.keys()); vals = list(oc.values())
    colors = [C['orange'], C['red'], C['slate'], C['purple']][:len(labels)]

    fig, ax = plt.subplots(figsize=(8, 5))
    _base(fig, ax)
    _headline(ax, f"{total:,} patients interrupted treatment — IIT accounts for {round(oc.get('IIT',0)/total*100)}%",
              "Treatment Interruption Outcomes (TX_ML)")

    bars = ax.bar(labels, vals, color=colors, width=0.5, edgecolor='white', linewidth=1.5, zorder=3)

    for bar, val in zip(bars, vals):
        pct = round(val / total * 100, 1)
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(vals)*0.02,
                f'{val:,}\n({pct}%)', ha='center', va='bottom', fontsize=10,
                fontweight='bold', color=C['dark'], fontfamily=FONT, linespacing=1.3)

    ax.set_ylim(0, max(vals) * 1.22)
    _footer(fig)
    return _save(fig, os.path.join(d, 'tx_ml_outcomes.png'))


# ══════════════════════════════════════════════════════════
# 6. Q1 vs Q2 COMPARISON
# ══════════════════════════════════════════════════════════
def q1_q2_comparison(q1, q2, d):
    inds = ['TX_NEW', 'TX_ML', 'TX_RTT', 'HTS_POS']
    v1 = [q1['TX_NEW']['value'], q1['TX_ML']['value'], q1['TX_RTT']['value'],
          q1.get('HTS_TST', {}).get('pos', 0)]
    v2 = [q2['TX_NEW']['value'], q2['TX_ML']['value'], q2['TX_RTT']['value'],
          q2.get('HTS_TST', {}).get('pos', 0)]

    x = np.arange(len(inds)); w = 0.3
    fig, ax = plt.subplots(figsize=(9, 5.5))
    _base(fig, ax)
    _headline(ax, "Q2 saw increased treatment interruptions but strong return-to-treatment",
              "Q1 vs Q2 Performance Comparison")

    b1 = ax.bar(x - w/2, v1, w, color=C['teal'], edgecolor='white', linewidth=1, label='Q1 (Oct–Dec)', zorder=3)
    b2 = ax.bar(x + w/2, v2, w, color=C['navy'], edgecolor='white', linewidth=1, label='Q2 (Jan–Mar)', zorder=3)

    for bars, vals in [(b1, v1), (b2, v2)]:
        _bar_labels(ax, bars, vals, fs=9)

    ax.set_xticks(x)
    ax.set_xticklabels(inds, fontsize=11, fontweight='bold', color=C['dark'])
    ax.legend(fontsize=9, frameon=False, loc='upper right')
    ax.set_ylim(0, max(max(v1), max(v2)) * 1.22)
    _footer(fig)
    return _save(fig, os.path.join(d, 'q1_q2_comparison.png'))


# ══════════════════════════════════════════════════════════
# 7. PMTCT CASCADE
# ══════════════════════════════════════════════════════════
def pmtct_cascade(r, d):
    pm = r.get('PMTCT_STAT', {}); pa = r.get('PMTCT_ART', {})
    if not pm: return None

    labels = ['ANC\nTested', 'HIV\nPositive', 'Started\nART', 'Delivered', 'EID\nPCR']
    vals = [pm.get('n', 0), pm.get('pos', 0), pa.get('art_fy', 0),
            pa.get('delivered', 0), pa.get('eid_pcr', 0)]
    colors = [C['sky'], C['orange'], C['emerald'], C['navy'], C['purple']]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    _base(fig, ax)
    _headline(ax, f"{pm.get('n',0):,} women tested at ANC — {pm.get('pos',0)} HIV positive ({pm.get('positivity',0)}%)",
              "PMTCT Cascade — FY26 Semi-Annual")

    bars = ax.bar(labels, vals, color=colors, width=0.5, edgecolor='white', linewidth=1.5, zorder=3)
    _bar_labels(ax, bars, vals, fs=11)
    ax.set_ylim(0, max(vals) * 1.18)
    _footer(fig)
    return _save(fig, os.path.join(d, 'pmtct_cascade.png'))


# ══════════════════════════════════════════════════════════
# 8. VL PERFORMANCE
# ══════════════════════════════════════════════════════════
def vl_performance(r, d):
    pv = r.get('TX_PVLS', {}); tc = r.get('TX_CURR', {}).get('value', 0)
    vle = r.get('VL_ELIGIBLE', {})

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [1.2, 1]})

    # Left: VL cascade bars
    _base(fig, ax1)
    labels = ['TX_CURR', 'VL Done', 'Suppressed', 'Unsuppressed']
    vals = [tc, pv.get('d', 0), pv.get('n', 0), pv.get('unsuppressed', 0)]
    colors = [C['navy'], C['teal'], C['emerald'], C['red']]
    bars = ax1.bar(labels, vals, color=colors, width=0.5, edgecolor='white', linewidth=1.5, zorder=3)
    _bar_labels(ax1, bars, vals, fs=10)
    ax1.set_ylim(0, max(vals) * 1.18)
    ax1.set_title('Viral Load Cascade', fontsize=13, fontweight='bold', color=C['dark'],
                  loc='left', pad=12, fontfamily=FONT)

    # Right: rates as horizontal bars
    ax2.set_facecolor('white')
    for sp in ax2.spines.values(): sp.set_visible(False)
    ax2.tick_params(left=False, bottom=False, labelbottom=False)

    rates = [('VL Coverage', pv.get('coverage', 0)),
             ('VL Suppression', pv.get('suppression', 0)),
             ('Sample Collection', vle.get('rate', 0))]

    for i, (lbl, val) in enumerate(rates):
        y = 2 - i
        ax2.barh(y, 100, height=0.5, color=C['light'], edgecolor='none', zorder=1)
        color = C['emerald'] if val >= 90 else (C['gold'] if val >= 80 else C['red'])
        ax2.barh(y, val, height=0.5, color=color, edgecolor='none', zorder=2)
        ax2.text(val + 1.5, y, f'{val}%', va='center', fontsize=12, fontweight='bold',
                 color=C['dark'], fontfamily=FONT, zorder=3)
        ax2.text(-1, y, lbl, va='center', ha='right', fontsize=9, fontweight='bold',
                 color=C['dark'], fontfamily=FONT, zorder=3)

    ax2.axvline(95, color=C['red'], linestyle='--', linewidth=0.8, alpha=0.5, zorder=2)
    ax2.set_xlim(-45, 108)
    ax2.set_ylim(-0.5, 3)
    ax2.set_title('Performance Rates', fontsize=13, fontweight='bold', color=C['dark'],
                  loc='left', pad=12, fontfamily=FONT)

    fig.tight_layout(w_pad=5)
    _footer(fig)
    return _save(fig, os.path.join(d, 'vl_performance.png'))


# ══════════════════════════════════════════════════════════
# 9. TB/HIV CASCADE
# ══════════════════════════════════════════════════════════
def tb_cascade(r, d):
    tb = r.get('TB_SCREEN', {}); tp = r.get('TPT', {})
    if not tb: return None
    cv = tp.get('coverage', 0)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    _base(fig, ax)
    _headline(ax, f"TPT coverage reaches {cv}% of active patients on ART",
              "TB/HIV Integration — Screening & TPT")

    labels = ['TB\nScreened', 'TB\nPositive', 'TPT\nStarted']
    vals = [tb.get('screened', 0), tb.get('positive', 0), tp.get('started_radet', 0)]
    colors = [C['sky'], C['red'], C['emerald']]
    bars = ax.bar(labels, vals, color=colors, width=0.45, edgecolor='white', linewidth=1.5, zorder=3)
    _bar_labels(ax, bars, vals, fs=11)

    # Coverage badge — top left, clear of bars
    ax.text(0.02, 0.92, f'TPT Coverage\n{cv}%', transform=ax.transAxes,
            fontsize=13, fontweight='bold', color=C['emerald'] if cv >= 80 else C['gold'],
            fontfamily=FONT, ha='left', va='top', linespacing=1.4,
            bbox=dict(boxstyle='round,pad=0.6', facecolor='white',
                      edgecolor=C['emerald'] if cv >= 80 else C['gold'], linewidth=2))

    ax.set_ylim(0, max(vals) * 1.18)
    _footer(fig)
    return _save(fig, os.path.join(d, 'tb_cascade.png'))


# ══════════════════════════════════════════════════════════
# 10. AHD CASCADE
# ══════════════════════════════════════════════════════════
def ahd_cascade(r, d):
    a = r.get('AHD', {})
    if not a: return None

    fig, ax = plt.subplots(figsize=(11, 5.5))
    _base(fig, ax)
    _headline(ax, f"{a.get('ahd_yes',0)} of {a.get('total',0):,} screened patients had advanced HIV disease",
              "AHD Treatment Cascade")

    labels = ['Screened', 'AHD+', 'CD4\nDone', 'TB-LAM\nDone', 'TB-LAM+', 'CrAg\nDone', 'CrAg+']
    vals = [a.get('total',0), a.get('ahd_yes',0), a.get('cd4_done',0),
            a.get('tblam_done',0), a.get('tblam_pos',0), a.get('crag_done',0), a.get('crag_pos',0)]
    colors = [C['navy'], C['red'], C['sky'], C['teal'], C['orange'], C['purple'], C['coral']]

    bars = ax.bar(labels, vals, color=colors, width=0.5, edgecolor='white', linewidth=1.5, zorder=3)
    _bar_labels(ax, bars, vals, fs=10)
    ax.set_ylim(0, max(vals) * 1.18)
    _footer(fig)
    return _save(fig, os.path.join(d, 'ahd_cascade.png'))


# ══════════════════════════════════════════════════════════
# 11. CXCA SCREENING
# ══════════════════════════════════════════════════════════
def cxca_chart(r, d):
    cx = r.get('CXCA', {})
    if not cx or cx.get('eligible', 0) == 0: return None
    cov = cx.get('coverage', 0)
    gap = cx['eligible'] - cx['screened']

    fig, ax = plt.subplots(figsize=(9, 5))
    _base(fig, ax)
    _headline(ax, f"Cervical cancer screening coverage at {cov}% — gap of {gap:,} women",
              "CXCA Screening among eligible females (15+)")

    labels = ['Eligible\n(F 15+)', 'Screened', 'Gap']
    vals = [cx['eligible'], cx['screened'], gap]
    colors = [C['navy'], C['emerald'], C['coral']]
    bars = ax.bar(labels, vals, color=colors, width=0.45, edgecolor='white', linewidth=1.5, zorder=3)
    _bar_labels(ax, bars, vals, fs=11)
    ax.set_ylim(0, max(vals) * 1.18)
    _footer(fig)
    return _save(fig, os.path.join(d, 'cxca_screening.png'))


# ══════════════════════════════════════════════════════════
# 12. SEX DISAGGREGATION
# ══════════════════════════════════════════════════════════
def sex_disagg(r, d):
    td = r.get('TX_CURR', {}).get('disagg', {}); nd = r.get('TX_NEW', {}).get('disagg', {})
    hd = r.get('HTS_TST', {}).get('disagg', {})

    fig, ax = plt.subplots(figsize=(10, 4.5))
    fig.patch.set_facecolor('white'); ax.set_facecolor('white')
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(left=False, bottom=False, labelbottom=False, labelleft=False)

    _headline(ax, "Female patients dominate across all cascade indicators",
              "Sex Disaggregation — Key Indicators")

    inds = ['TX_CURR', 'TX_NEW', 'HTS_TST']
    males = [td.get('Male', 0), nd.get('Male', 0), hd.get('Male', 0)]
    females = [td.get('Female', 0), nd.get('Female', 0), hd.get('Female', 0)]

    y = np.arange(len(inds))
    h = 0.28
    b1 = ax.barh(y - h/2, males, h, color=C['sky'], edgecolor='none', label='Male', zorder=3)
    b2 = ax.barh(y + h/2, females, h, color=C['coral'], edgecolor='none', label='Female', zorder=3)

    mx = max(max(males), max(females))
    for bars in [b1, b2]:
        for bar in bars:
            w = bar.get_width()
            ax.text(w + mx * 0.01, bar.get_y() + bar.get_height()/2,
                    f'{int(w):,}', va='center', fontsize=9, fontweight='bold',
                    color=C['dark'], fontfamily=FONT)

    for i, label in enumerate(inds):
        ax.text(-mx * 0.01, i, label, va='center', ha='right', fontsize=11,
                fontweight='bold', color=C['dark'], fontfamily=FONT)

    ax.legend(fontsize=9, frameon=False, loc='lower right')
    ax.set_xlim(-mx * 0.2, mx * 1.2)
    ax.set_ylim(-0.6, len(inds) - 0.3)
    _footer(fig)
    return _save(fig, os.path.join(d, 'sex_disagg.png'))


# ══════════════════════════════════════════════════════════
# GENERATE ALL
# ══════════════════════════════════════════════════════════
def generate_all_charts(results, q1_results, q2_results, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    c = {}
    c['cascade'] = treatment_cascade(results, out_dir)
    c['progress_95'] = progress_95(results, out_dir)
    c['tx_curr_state'] = tx_curr_by_state(results, out_dir)
    c['vl_performance'] = vl_performance(results, out_dir)
    c['hts_modality'] = hts_modality_yield(results, out_dir)
    c['tx_ml_outcomes'] = tx_ml_outcomes(results, out_dir)
    c['q1_q2'] = q1_q2_comparison(q1_results, q2_results, out_dir)
    c['pmtct_cascade'] = pmtct_cascade(results, out_dir)
    c['tb_cascade'] = tb_cascade(results, out_dir)
    c['ahd_cascade'] = ahd_cascade(results, out_dir)
    c['cxca_screening'] = cxca_chart(results, out_dir)
    c['sex_disagg'] = sex_disagg(results, out_dir)
    return {k: v for k, v in c.items() if v is not None}
