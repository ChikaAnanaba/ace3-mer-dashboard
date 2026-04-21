"""
Targets loader for ACE3 programme.
Reads facility-level annual targets from CSV or Excel.
"""
import pandas as pd


def load_targets(src):
    """
    Load targets file and return (df_raw, site_targets_dict, programme_targets_dict).
    programme_targets_dict maps indicator name -> annual target total.
    """
    try:
        if hasattr(src, 'read'):
            # Try Excel first, then CSV
            try:
                src.seek(0)
                df = pd.read_excel(src)
            except Exception:
                src.seek(0)
                df = pd.read_csv(src)
        elif str(src).endswith('.csv'):
            df = pd.read_csv(src)
        else:
            df = pd.read_excel(src)
    except Exception as e:
        raise ValueError(f'Cannot read targets file: {e}')

    # Standardise column names
    df.columns = [str(c).strip() for c in df.columns]

    # Build programme-level totals
    prog_tgts = {}
    indicator_cols = [
        'TX_CURR', 'TX_NEW', 'HTS_TST', 'HTS_TST_POS',
        'TX_PVLS_D', 'TX_PVLS_N', 'PMTCT_STAT_N', 'PMTCT_ART_D',
        'PrEP_NEW', 'TB_PREV_N', 'TX_TB_N', 'TB_ART',
    ]
    for col in indicator_cols:
        if col in df.columns:
            try:
                prog_tgts[col] = int(pd.to_numeric(df[col], errors='coerce').sum())
            except Exception:
                pass

    return df, {}, prog_tgts
