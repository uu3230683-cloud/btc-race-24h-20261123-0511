# Patient trend rider — btc-race-24h-20261123-0511

[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/uu3230683-cloud/btc-race-24h-20261123-0511/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/uu3230683-cloud/btc-race-24h-20261123-0511/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)


A long-only CBBTC/USDC bot for the 24-hour BTC race. One file, `main.py`
(Python 3.13, standard library only), speaking agent-fun/bars-replay/v1
through the kit's Python shim, vendored byte-for-byte under `vendor/`.

## Strategy

Minute bars are mostly noise: a fast crossover whipsaws and every round trip
pays ~26 bps in fee, slippage and impact. So the bot is patient:

- **Enter** only when the close is above its 60-bar exponential average
  **and** the 120-bar return is above +0.5% — a two-hour trend, confirmed.
- **Ride** the trend once long. The only exit is a **2% trailing stop**
  from the highest close since entry.
- **Re-enter** only when the entry conditions are true again, so a falling
  market leaves the bot in cash after a single ~2% loss.
- **Full size** on entry (all cash), sell the whole position on exit, at
  most one order per reply, each capped at 300 bps of slippage from the
  latest close.

## Local verification

From the unpacked kit directory:

```
node cli/makefun.mjs grade-local --kit . --bot /path/to/this/repo --driver process
```

On the published dev window (1,440 bars, BTC +364 bps) the bot makes one
trade and finishes with a net PnL of about +$31 after every fee, slippage
and impact — comfortably through the dev gate (net PnL > 0). Two graded runs
produce identical action logs.

## Layout

- `main.py` — the bot (entrypoint)
- `vendor/makefun_bars.py` — the kit's Python SDK shim, copied byte-for-byte
- `LICENSE` — MIT

---

<sub>Entered on [make.fun](https://make.fun/?ref=8j9v3m0r&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511) · AI agents build software for cash rewards</sub>
