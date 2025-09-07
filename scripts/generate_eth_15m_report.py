"""Ethereum 15m Institutional PDF Report Generator (Goldbach Strategy)

Generates a single professionally formatted PDF report (no markdown / JSON / PNG
side artifacts) containing:
    - Executive summary table of key market / strategy metrics
    - Algorithm classification, AMD phase, PO3 context & relative position
    - 15m linear regression forecast with 68% & 95% confidence bands + slope
    - ATR(14) (15m), recent realized volatility & annualized volatility estimate
    - Risk distance to Premium / Discount / Equilibrium in USD & ATR units
    - Annotated price chart (PO3 levels, cycle markers, forecast point & bands)
    - Narrative trader notes & audit appendix (raw key values + error notes)

STRICT REAL DATA RULE: Never uses simulated/demo data. Coinbase snapshot is
preferred for the authoritative current price; falls back to last bar close only
if snapshot unavailable or unparsable.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import time
import traceback
import sys
import numpy as np
from io import BytesIO

# PDF/reportlab imports (lazy failure captured in try blocks later)
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, Preformatted
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# make repo root importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from analyze_eth_goldbach import EthereumGoldbachAnalyzer
except Exception:
    # editor relative import
    from .analyze_eth_goldbach import EthereumGoldbachAnalyzer  # type: ignore


def safe_mkdir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def generate_report(days: int = 5, bars_to_plot: int = 96):
    """Generate enriched ETH 15m report with cycle, algorithm, PO3, forecast & trader metrics."""
    # Use timezone-aware UTC timestamp
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    # Unified PDF reports directory (renamed from legacy 'analysis_reports')
    out_dir = Path.cwd() / "analyzed-reports"
    safe_mkdir(out_dir)
    pdf_path = out_dir / f"eth_15m_{ts}.pdf"

    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "script": Path(__file__).name,
        "symbol": "X:ETHUSD",
        "days_requested": days,
        "status": "ok",
        "notes": [],
    }

    # Initialize analyzer
    try:
        analyzer = EthereumGoldbachAnalyzer()
    except Exception as e:
        meta.update({"status": "failed", "error": str(e)})
        meta["notes"].append(traceback.format_exc())
        print("Initialization failed:", e)
        # Attempt minimal failure PDF
        try:
            doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
            styles = getSampleStyleSheet()
            flow = [Paragraph("Ethereum 15m Goldbach Report - FAILURE", styles['Title']), Spacer(1,0.2*inch), Paragraph(str(e), styles['BodyText']), Preformatted("\n".join(meta.get('notes', [])), styles['Code'])]
            doc.build(flow)
            print('PDF written (failure):', pdf_path)
        except Exception:
            pass
        return

    try:
        # Core analyses
        df = analyzer.get_eth_data(days=days)
        cycle = analyzer.find_recent_algo_cycle(df)
        algo = analyzer.identify_algorithms(df)
        amd = analyzer.identify_amd_phases(df)
        po3 = analyzer.identify_po3_levels(df)

        # Market snapshot (Coinbase preferred)
        snapshot = None
        try:
            adapter = getattr(analyzer, "polygon", None)
            if adapter and hasattr(adapter, "get_market_snapshot"):
                start = time.time()
                s = adapter.get_market_snapshot("X:ETHUSD")
                snapshot = {
                    "source": getattr(s, "source", None),
                    "price": getattr(s, "price", None),
                    "timestamp": getattr(s, "timestamp", None),
                    "latency_seconds": time.time() - start,
                }
        except Exception as e:
            meta["notes"].append(f"snapshot error: {e}")

        # Authoritative price selection
        try:
            bar_price = float(df["close"].iloc[-1]) if not df.empty else None
        except Exception:
            bar_price = None
        if snapshot and snapshot.get("source") and "coinbase" in str(snapshot.get("source")).lower():
            try:
                authoritative_price = float(snapshot.get("price"))
                meta["notes"].append("Using Coinbase snapshot as authoritative current_price")
            except Exception:
                authoritative_price = bar_price
                meta["notes"].append("Failed to parse snapshot price; fallback to last bar close")
        else:
            authoritative_price = bar_price

        # Simple linear forecast (next 15m) + confidence bands (68% & 95%) + slope metrics
        forecast = None
        try:
            recent_for_forecast = df['close'].tail(24)  # up to 6 hours of data
            if len(recent_for_forecast) >= 5:
                xs = np.arange(len(recent_for_forecast), dtype=float)
                ys = recent_for_forecast.values.astype(float)
                slope, intercept = np.polyfit(xs, ys, 1)
                next_x = xs[-1] + 1.0
                forecast_price = float(slope * next_x + intercept)
                # Regression diagnostics
                yhat = slope * xs + intercept
                residuals = ys - yhat
                dof = max(1, len(xs) - 2)
                s_err = float(np.sqrt(np.sum(residuals**2) / dof)) if dof > 0 else 0.0
                x_bar = np.mean(xs)
                ssx = np.sum((xs - x_bar)**2)
                if ssx == 0:
                    pred_stderr = s_err
                else:
                    pred_stderr = float(s_err * np.sqrt(1 + 1/len(xs) + (next_x - x_bar)**2 / ssx))
                band68_lower = forecast_price - pred_stderr
                band68_upper = forecast_price + pred_stderr
                band95_lower = forecast_price - 1.96 * pred_stderr
                band95_upper = forecast_price + 1.96 * pred_stderr
                last_idx = recent_for_forecast.index[-1]
                forecast_ts = (last_idx + timedelta(minutes=15)).isoformat()
                slope_per_bar = float(slope)
                slope_per_hour = slope_per_bar * 4.0
                forecast = {
                    "price": forecast_price,
                    "timestamp": forecast_ts,
                    "method": "linear_regression",
                    "std_error": pred_stderr,
                    "band_68": {
                        "confidence_level": "~68%",
                        "lower": band68_lower,
                        "upper": band68_upper
                    },
                    "band_95": {
                        "confidence_level": "~95%",
                        "lower": band95_lower,
                        "upper": band95_upper
                    },
                    "slope_per_15m": slope_per_bar,
                    "slope_per_hour": slope_per_hour,
                    "points_used": int(len(xs))
                }
        except Exception as e:
            meta.setdefault('notes', []).append(f'forecast error: {e}')

        # Additional trader metrics
        atr_lookback = 14
        atr = None
        po3_position_pct = None
        try:
            if len(df) > atr_lookback:
                highs = df['high'].tail(atr_lookback+1).values
                lows = df['low'].tail(atr_lookback+1).values
                closes = df['close'].tail(atr_lookback+1).values
                trs = []
                for i in range(1, len(highs)):
                    tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
                    trs.append(tr)
                atr = float(np.mean(trs)) if trs else None
            # PO3 relative position (0 = range low, 100 = range high)
            try:
                rng = (po3.get('range_high') - po3.get('range_low'))
                if rng and rng != 0:
                    po3_position_pct = (authoritative_price - po3.get('range_low')) / rng * 100.0
            except Exception:
                pass
        except Exception as e:
            meta.setdefault('notes', []).append(f'atr calc error: {e}')

        # Normalize snapshot timestamp -> UTC
        try:
            if snapshot and snapshot.get('timestamp'):
                orig = snapshot['timestamp']
                snapshot['timestamp_original'] = orig
                parsed = None
                for fn in (
                    lambda s: datetime.fromisoformat(s),
                    lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f'),
                    lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M:%S'),
                ):
                    try:
                        parsed = fn(orig)
                        break
                    except Exception:
                        continue
                if parsed:
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=datetime.now().astimezone().tzinfo)
                    snapshot['timestamp'] = parsed.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
                    meta['notes'].append('Normalized snapshot timestamp to UTC')
        except Exception:
            pass

        # Update meta basic fields
        meta.update({
            "bars_count": int(len(df)),
            "current_price": authoritative_price,
            "cycle": cycle,
            "algo": algo,
            "amd": amd,
            "po3": po3,
            "snapshot": snapshot,
            "forecast": forecast,
            "atr_15m": atr,
            "po3_position_pct": po3_position_pct,
        })

        # Volatility & annualized vol + risk metrics
        try:
            vol_window = df['close'].tail(24)
            if len(vol_window) > 2:
                returns_std = float(vol_window.pct_change().std())
                vol_pct = returns_std * 100
                bars_per_year = 96 * 252
                ann_vol = returns_std * np.sqrt(bars_per_year) * 100
                meta['recent_vol_pct_24'] = vol_pct
                meta['annualized_vol_pct'] = ann_vol
        except Exception as e:
            meta.setdefault('notes', []).append(f'vol calc error: {e}')

        # Risk metrics
        try:
            px = authoritative_price
            prem = float(po3.get('premium_zone'))
            disc = float(po3.get('discount_zone'))
            eq = float(po3.get('equilibrium'))
            if px is not None and atr and atr > 0:
                risk_metrics = {
                    'distance_to_premium': prem - px,
                    'distance_to_discount': px - disc,
                    'distance_to_equilibrium': px - eq,
                    'distance_to_premium_atr': (prem - px) / atr,
                    'distance_to_discount_atr': (px - disc) / atr,
                    'distance_to_equilibrium_atr': (px - eq) / atr,
                }
                meta['risk_metrics'] = risk_metrics
        except Exception as e:
            meta.setdefault('notes', []).append(f'risk metrics error: {e}')

        # ------------------------- Professional PDF Construction -------------------------
        styles = getSampleStyleSheet()
        def safe_add(style: ParagraphStyle):
            try:
                styles.add(style)
            except KeyError:
                pass  # already exists
        safe_add(ParagraphStyle(name='CoverTitle', parent=styles['Title'], fontSize=24, leading=28, spaceAfter=18))
        safe_add(ParagraphStyle(name='SectionHeader', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#0a3d62'), spaceBefore=12, spaceAfter=6))
        safe_add(ParagraphStyle(name='Small', parent=styles['BodyText'], fontSize=8, textColor=colors.grey))
        safe_add(ParagraphStyle(name='MetricLabel', parent=styles['BodyText'], fontSize=9, textColor=colors.HexColor('#555555')))
        safe_add(ParagraphStyle(name='MetricValue', parent=styles['BodyText'], fontSize=9, textColor=colors.HexColor('#000000')))
        # Use existing 'Bullet' if present; ensure minimal difference
        if 'Bullet' not in styles:
            safe_add(ParagraphStyle(name='Bullet', parent=styles['BodyText'], leftIndent=12, bulletIndent=0, spaceAfter=2))

        def fmt(v, fmt_str="{:.2f}"):
            try:
                return fmt_str.format(float(v))
            except Exception:
                return str(v)

        # Derive cycle start/end for table
        cycle_info = cycle or {}
        cycle_start, cycle_end, cycle_range = None, None, None
        if cycle_info.get('cycle_found'):
            try:
                t_end = datetime.fromisoformat(str(cycle_info.get('completion_time')))
                bars_in_cycle = int(cycle_info.get('bars_in_cycle') or 0)
                if bars_in_cycle > 0:
                    cycle_end = t_end
                    cycle_start = t_end - timedelta(minutes=15 * bars_in_cycle)
                    cycle_range = cycle_info.get('cycle_range')
            except Exception:
                pass

        # Risk metrics for table
        risk = meta.get('risk_metrics', {})

        # Build metric summary table
        summary_data = [
            [Paragraph('<b>Metric</b>', styles['MetricLabel']), Paragraph('<b>Value</b>', styles['MetricLabel'])],
            ['Current Price', fmt(authoritative_price)],
            ['Bars Analyzed', str(len(df))],
            ['Algorithm', algo.get('current_algorithm')],
            ['AMD Phase', amd.get('current_phase')],
            ['PO3 Active Level', str(po3.get('active_po3_level'))],
            ['PO3 Zone', po3.get('current_zone')],
            ['PO3 Position %', fmt(po3_position_pct, '{:.1f}%') if po3_position_pct is not None else '—'],
            ['ATR(14) 15m', fmt(atr) if atr else '—'],
            ['Recent 24-bar Vol %', fmt(meta.get('recent_vol_pct_24'), '{:.2f}%') if meta.get('recent_vol_pct_24') else '—'],
            ['Annualized Vol %', fmt(meta.get('annualized_vol_pct'), '{:.2f}%') if meta.get('annualized_vol_pct') else '—'],
        ]
        if cycle_start and cycle_end:
            summary_data.extend([
                ['Cycle Start', cycle_start.isoformat()],
                ['Cycle End', cycle_end.isoformat()],
                ['Cycle Range', fmt(cycle_range)],
            ])
        if forecast:
            b68 = forecast.get('band_68') or {}
            b95 = forecast.get('band_95') or {}
            summary_data.extend([
                ['Forecast (15m)', fmt(forecast.get('price'))],
                ['Forecast Time', forecast.get('timestamp')],
                ['Forecast 68% Band', f"{fmt(b68.get('lower'))} - {fmt(b68.get('upper'))}" if b68 else '—'],
                ['Forecast 95% Band', f"{fmt(b95.get('lower'))} - {fmt(b95.get('upper'))}" if b95 else '—'],
                ['Slope USD/15m', fmt(forecast.get('slope_per_15m'))],
                ['Slope USD/hr', fmt(forecast.get('slope_per_hour'))],
            ])
        if risk:
            summary_data.extend([
                ['Dist→Premium (ATR)', fmt(risk.get('distance_to_premium_atr'))],
                ['Dist→Equilibrium (ATR)', fmt(risk.get('distance_to_equilibrium_atr'))],
                ['Dist→Discount (ATR)', fmt(risk.get('distance_to_discount_atr'))],
            ])

        table_style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#dfe6e9')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#2d3436')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 4),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f7f9fa')]),
            ('GRID', (0,0), (-1,-1), 0.25, colors.HexColor('#b2bec3')),
        ])
        summary_table = Table(summary_data, hAlign='LEFT', colWidths=[1.6*inch, 4.9*inch])
        summary_table.setStyle(table_style)

        # Build chart in-memory (BytesIO) for embedding
        chart_flow = []
        try:
            import matplotlib.pyplot as plt
            plot_df = df.tail(bars_to_plot).copy()
            if not plot_df.empty:
                fig, ax = plt.subplots(figsize=(10, 4.2))
                ax.plot(plot_df.index, plot_df['close'], label='Close', color='#1e3799', linewidth=1.2)
                try:
                    ax.axhline(float(po3.get('premium_zone')), color='#e55039', linestyle='--', linewidth=0.9, label='Premium')
                    ax.axhline(float(po3.get('equilibrium')), color='#f6b93b', linestyle='-.', linewidth=0.9, label='Equilibrium')
                    ax.axhline(float(po3.get('discount_zone')), color='#78e08f', linestyle='--', linewidth=0.9, label='Discount')
                except Exception:
                    pass
                if authoritative_price is not None:
                    ax.scatter(plot_df.index[-1], authoritative_price, color='black', s=28, zorder=5, label='Current')
                if cycle_start and cycle_end:
                    ax.axvline(cycle_start, color='#6c5ce7', linestyle='--', linewidth=0.8, label='Cycle start')
                    ax.axvline(cycle_end, color='#341f97', linestyle='--', linewidth=0.8, label='Cycle end')
                if forecast and forecast.get('price') is not None:
                    try:
                        last_index = plot_df.index[-1]
                        next_ts = last_index + timedelta(minutes=15)
                        f_price = forecast['price']
                        ax.scatter([next_ts], [f_price], color='#e84393', marker='X', s=70, zorder=6, label='15m forecast')
                        b68 = forecast.get('band_68') or {}
                        if b68.get('lower') and b68.get('upper'):
                            ax.vlines(next_ts, b68['lower'], b68['upper'], colors='#e84393', linestyles='-', linewidth=1.5, label='68% band')
                        b95 = forecast.get('band_95') or {}
                        if b95.get('lower') and b95.get('upper'):
                            ax.vlines(next_ts, b95['lower'], b95['upper'], colors='#e84393', linestyles=':', linewidth=1, label='95% band')
                    except Exception:
                        pass
                ax.set_title(f"ETH 15m Close (UTC) - Generated {ts}", fontsize=10, pad=10)
                ax.set_ylabel('USD')
                ax.legend(fontsize=7, ncol=4, loc='upper center', bbox_to_anchor=(0.5, 1.15))
                ax.grid(alpha=0.2, linewidth=0.3)
                fig.autofmt_xdate()
                fig.tight_layout()
                bio = BytesIO()
                fig.savefig(bio, format='png', dpi=160)
                plt.close(fig)
                bio.seek(0)
                img = Image(bio, width=7.2*inch, height=3.2*inch)
                chart_flow.append(img)
        except Exception as e:
            meta['notes'].append(f'chart embed error: {e}')

        # Narrative bullets
        bullets = []
        if 'Market Maker' in (algo.get('current_algorithm') or ''):
            bullets.append('MM model: monitor extremes for mean reversion within PO3 context.')
        else:
            bullets.append('Trending conditions: favor continuation setups; validate with displacement and liquidity context.')
        if forecast:
            bullets.append('Forecast is indicative; manage risk independently and monitor variance vs. bands.')
        zone = po3.get('current_zone')
        if zone == 'Premium Zone':
            bullets.append('Premium zone: elevated probability of liquidity taking / mean reversion responses.')
        elif zone == 'Discount Zone':
            bullets.append('Discount zone: accumulation / potential expansion setups.')
        else:
            bullets.append('Equilibrium: neutral posture until decisive displacement.')

        disclaimer = ("This report is generated from live market data (Coinbase preferred) and is intended for informational "
                      "purposes only. No simulated or demo data were used. Not investment advice.")

        flow = []
        flow.append(Paragraph("Ethereum 15-Minute Goldbach Analysis", styles['CoverTitle']))
        flow.append(Paragraph(f"Generated {ts} UTC", styles['Small']))
        flow.append(Spacer(1, 0.15*inch))
        flow.append(Paragraph("Executive Summary", styles['SectionHeader']))
        flow.append(summary_table)
        flow.append(Spacer(1, 0.15*inch))
        flow.append(Paragraph("Market Structure & PO3 Context", styles['SectionHeader']))
        flow.append(Paragraph(f"Algorithm: {algo.get('current_algorithm')} — {algo.get('characteristics')}", styles['BodyText']))
        flow.append(Paragraph(f"AMD Phase: {amd.get('current_phase')} (Recent phases: {', '.join(amd.get('phases_detected', []) or [])})", styles['BodyText']))
        if cycle_start and cycle_end:
            flow.append(Paragraph(f"Last Full Cycle: {cycle_start.isoformat()} → {cycle_end.isoformat()} ({cycle_info.get('bars_in_cycle')} bars; Range {fmt(cycle_range)})", styles['BodyText']))
        flow.append(Paragraph(f"PO3 Active Level: {po3.get('active_po3_level')} | Zone: {po3.get('current_zone')} | Eq {fmt(po3.get('equilibrium'))} / Prem {fmt(po3.get('premium_zone'))} / Disc {fmt(po3.get('discount_zone'))}", styles['BodyText']))
        if forecast:
            flow.append(Paragraph(f"Forecast (next 15m): {fmt(forecast.get('price'))} USD (68% band {fmt(forecast.get('band_68',{}).get('lower'))} – {fmt(forecast.get('band_68',{}).get('upper'))}; 95% band {fmt(forecast.get('band_95',{}).get('lower'))} – {fmt(forecast.get('band_95',{}).get('upper'))})", styles['BodyText']))
        flow.append(Spacer(1, 0.12*inch))
        flow.append(Paragraph("Chart & Technical Overlay", styles['SectionHeader']))
        for comp in chart_flow:
            flow.append(comp)
        flow.append(Spacer(1, 0.12*inch))
        flow.append(Paragraph("Trader Notes", styles['SectionHeader']))
        for b in bullets:
            flow.append(Paragraph(b, styles['Bullet']))
        flow.append(Spacer(1, 0.15*inch))
        flow.append(Paragraph(disclaimer, styles['Small']))
        flow.append(PageBreak())
        flow.append(Paragraph("Audit Appendix", styles['SectionHeader']))
        core_audit_lines = []
        for k in ["timestamp_utc","symbol","current_price","bars_count","days_requested"]:
            core_audit_lines.append(f"{k}: {meta.get(k)}")
        if cycle_start and cycle_end:
            core_audit_lines.append(f"cycle_start: {cycle_start.isoformat()}")
            core_audit_lines.append(f"cycle_end: {cycle_end.isoformat()}")
        if forecast:
            core_audit_lines.append(f"forecast_price: {forecast.get('price')}")
            core_audit_lines.append(f"forecast_time: {forecast.get('timestamp')}")
        if atr:
            core_audit_lines.append(f"atr_15m: {atr}")
        if meta.get('annualized_vol_pct'):
            core_audit_lines.append(f"annualized_vol_pct: {meta.get('annualized_vol_pct')}")
        if meta.get('risk_metrics'):
            for rk,v in meta['risk_metrics'].items():
                core_audit_lines.append(f"{rk}: {v}")
        if meta.get('notes'):
            core_audit_lines.append("notes: ")
            core_audit_lines.extend(meta['notes'])
        flow.append(Preformatted("\n".join(core_audit_lines), styles['Code']))

        try:
            doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=0.6*inch, leftMargin=0.6*inch, topMargin=0.6*inch, bottomMargin=0.6*inch)
            doc.build(flow)
            print('PDF written:', pdf_path)
        except Exception as e:
            print('Failed to write PDF:', e)
            meta['status'] = 'failed'
        print('Artifacts: PDF only (per request)')

        # Removed other artifact prints per request

    except Exception as e:  # outer analysis try
        # Capture analysis failure & build a failure PDF so there's always an artifact
        meta.update({"status": "failed", "error": str(e)})
        tb = traceback.format_exc()
        meta["notes"].append(tb)
        print('ERROR during report generation:', e)
        print(tb)
        try:
            doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
            styles = getSampleStyleSheet()
            flow = [
                Paragraph("Ethereum 15m Goldbach Report - FAILURE", styles['Title']),
                Spacer(1, 0.15*inch),
                Paragraph(str(e), styles['BodyText']),
                Preformatted("\n".join(meta.get('notes', [])), styles['Code'])
            ]
            doc.build(flow)
            print('PDF written (failure):', pdf_path)
        except Exception as build_err:
            print('Secondary failure while writing failure PDF:', build_err)


if __name__ == "__main__":
    # Default execution: 5 days history, plot last 96 (24h) bars
    generate_report(days=5, bars_to_plot=96)
