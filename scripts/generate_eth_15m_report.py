"""Minimal, clean ETH 15m report generator.

This script runs the EthereumGoldbachAnalyzer, writes a JSON audit record and a
small markdown summary under `analysis_reports/`. If matplotlib is available
it will also write a simple PNG chart. The script is defensive and always
writes the JSON audit so runs are auditable even on failures.
"""
from pathlib import Path
from datetime import datetime, timezone
import time
import json
import traceback
import sys

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
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_dir = Path.cwd() / "analysis_reports"
    safe_mkdir(out_dir)

    report_path = out_dir / f"eth_15m_{ts}.md"
    json_path = out_dir / f"eth_15m_{ts}.json"
    png_path = out_dir / f"eth_15m_{ts}.png"

    meta = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "script": Path(__file__).name,
        "symbol": "X:ETHUSD",
        "days_requested": days,
        "status": "ok",
        "notes": [],
    }

    try:
        analyzer = EthereumGoldbachAnalyzer()
    except Exception as e:
        meta.update({"status": "failed", "error": str(e)})
        meta["notes"].append(traceback.format_exc())
        json_path.write_text(json.dumps(meta, indent=2))
        report_path.write_text("# FAILED: initialization error\n\n{}".format(str(e)))
        print("Initialization failed:", e)
        return

    try:
        df = analyzer.get_eth_data(days=days)
        cycle = analyzer.find_recent_algo_cycle(df)
        algo = analyzer.identify_algorithms(df)
        amd = analyzer.identify_amd_phases(df)
        po3 = analyzer.identify_po3_levels(df)

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
            meta["notes"].append("snapshot error: {}".format(e))

        # Decide authoritative current_price: prefer Coinbase snapshot when available
        authoritative_price = None
        try:
            # default to last close from bars
            bar_price = float(df["close"].iloc[-1]) if not df.empty else None
        except Exception:
            bar_price = None

        if snapshot and snapshot.get("source") and "coinbase" in str(snapshot.get("source")).lower():
            try:
                authoritative_price = float(snapshot.get("price"))
                meta["notes"].append("Using Coinbase snapshot as authoritative current_price")
            except Exception:
                authoritative_price = bar_price
                meta["notes"].append("Failed to parse snapshot price; falling back to bar close price")
        else:
            authoritative_price = bar_price

        meta.update({
            "bars_count": int(len(df)),
            "current_price": authoritative_price,
            "cycle": cycle,
            "algo": algo,
            "amd": amd,
            "po3": po3,
            "snapshot": snapshot,
        })

        # Timing check between report timestamp and snapshot
        try:
            rep_ts = meta.get("timestamp_utc")
            snap_ts = snapshot.get("timestamp") if snapshot else None
            if rep_ts and snap_ts:
                from datetime import datetime as _dt
                try:
                    t_rep = _dt.fromisoformat(rep_ts.replace('Z',''))
                except Exception:
                    t_rep = None
                t_snap = None
                if snap_ts:
                    try:
                        t_snap = _dt.fromisoformat(snap_ts)
                    except Exception:
                        try:
                            t_snap = _dt.strptime(snap_ts, '%Y-%m-%d %H:%M:%S.%f')
                        except Exception:
                            try:
                                t_snap = _dt.strptime(snap_ts, '%Y-%m-%d %H:%M:%S')
                            except Exception:
                                t_snap = None
                if t_rep and t_snap:
                    diff = (t_rep - t_snap).total_seconds()
                    if abs(diff) > 60:
                        meta["notes"].append(f"Snapshot/report timestamp mismatch: {diff:.0f} seconds")
        except Exception:
            pass

        # Normalize snapshot timestamp to UTC if possible and record original
        try:
            if snapshot and snapshot.get('timestamp'):
                orig = snapshot.get('timestamp')
                snapshot['timestamp_original'] = orig
                st = orig
                t = None
                # try multiple parse formats
                parse_attempts = [
                    lambda s: datetime.fromisoformat(s),
                    lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f'),
                    lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M:%S'),
                ]
                for fn in parse_attempts:
                    try:
                        t = fn(st)
                        break
                    except Exception:
                        t = None
                if t is not None:
                    # assume naive timestamps are in local timezone; convert to UTC
                    try:
                        if t.tzinfo is None:
                            local_tz = datetime.now().astimezone().tzinfo
                            t = t.replace(tzinfo=local_tz)
                        t_utc = t.astimezone(timezone.utc)
                        snapshot['timestamp'] = t_utc.isoformat().replace('+00:00', 'Z')
                        meta.setdefault('notes', []).append('Normalized snapshot timestamp to UTC')
                    except Exception:
                        # fallback: leave original
                        pass
        except Exception:
            pass

        json_path.write_text(json.dumps(meta, default=str, indent=2))

        # concise markdown
        lines = [f"# ETH 15m Goldbach Analysis - {ts} (UTC)", ""]
        lines.append("Current price: {}".format(meta.get("current_price")))
        lines.append("Bars analyzed: {}".format(meta.get("bars_count")))
        lines.append("")
        lines.append("Algorithm: {}".format(algo.get("current_algorithm")))
        lines.append("Phase: {}".format(amd.get("current_phase")))
        lines.append("PO3 level: {}".format(po3.get("active_po3_level")))
        lines.append("")
        lines.append("Audit metadata (JSON written to {})".format(json_path.name))

        report_path.write_text("\n".join(lines))

        # optional chart
        try:
            import matplotlib.pyplot as plt

            plot_df = df.tail(bars_to_plot).copy()
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(plot_df.index, plot_df["close"], label="Close", color="tab:blue")

            try:
                premium = float(po3.get("premium_zone"))
                eq = float(po3.get("equilibrium"))
                discount = float(po3.get("discount_zone"))
                ax.axhline(premium, color="red", linestyle="--", label="Premium Zone")
                ax.axhline(eq, color="orange", linestyle="-.", label="Equilibrium")
                ax.axhline(discount, color="green", linestyle="--", label="Discount Zone")
            except Exception:
                pass

            current_price = meta.get("current_price")
            if current_price is not None and not plot_df.empty:
                ax.scatter(plot_df.index[-1], current_price, color="black", zorder=5)
                ax.text(plot_df.index[-1], current_price, f"  ${current_price:.2f}", va="bottom")

            ax.set_title(f"ETH 15-min Close - Generated {ts} UTC")
            ax.set_ylabel("Price (USD)")
            ax.legend()
            fig.autofmt_xdate()
            fig.tight_layout()
            fig.savefig(str(png_path))
            plt.close(fig)
        except Exception as e:
            meta["notes"].append("chart error: {}".format(e))
            json_path.write_text(json.dumps(meta, default=str, indent=2))

        print("Report:", report_path)
        print("JSON:", json_path)
        print("PNG:", png_path)

    except Exception as e:
        meta.update({"status": "failed", "error": str(e)})
        meta["notes"].append(traceback.format_exc())
        json_path.write_text(json.dumps(meta, default=str, indent=2))
        report_path.write_text("# FAILED: analysis error\n\n{}".format(str(e)))


if __name__ == "__main__":
    generate_report()
