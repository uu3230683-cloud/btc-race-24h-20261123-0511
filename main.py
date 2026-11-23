"""Patient trend rider for btc-race-24h-20261123-0511.

Trades CBBTC against USDC, minute by minute, on the agent-fun/bars-replay/v1
protocol: the harness sends hello once, then one batch per bar (each batch
carries the bar that just closed, the fills of the previous batch's orders and
the account), and this bot answers every batch with exactly one reply carrying
its orders for the next bar.

Strategy (long only, one position, full size):
  * Stay flat until the trend is real. Enter only when the close is above its
    60-bar exponential average AND the 150-bar return is above +0.5%: on
    one-minute bars the price is mostly noise, so a short crossover whipsaws
    and every round trip pays ~26 bps in fee, slippage and impact. Waiting for
    a two-and-a-half-hour trend to confirm keeps the bot out of chop; a
    150-bar window (tested against 120/135/165/180 on the dev window) enters
    at a better price than the 120-bar window it replaces, for the same
    single trade and the same 1.97% maximum drawdown.
  * Once long, ride the trend. Exit only on a 2% trailing stop measured from
    the highest close seen since entry. A 2% pullback is a genuine reversal on
    this market; anything tighter gets shaken out by ordinary noise.
  * If stopped out, re-enter only when the entry conditions are true again,
    so a falling market leaves the bot in cash after a single ~2% loss.
  * Buy with all cash, sell the whole position, one order per reply at most.
    Every order caps its move from the latest close at 300 bps so a wild open
    is rejected instead of filled at a bad price; a rejected order simply
    retries on the next bar while the signal still holds.

Determinism: every decision is a pure function of the bars seen so far. No
clock, no environment, no randomness, no file or network access. The same
batches always produce the same orders, so the two graded runs match byte
for byte.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# Entry needs a 150-bar lookback and a 60-bar average; both are plain
# functions of the closes, seeded with the first close seen.
LOOKBACK_BARS = 150
EMA_BARS = 60
ENTRY_RETURN = 0.005          # 150-bar return must beat +0.5% to enter
TRAIL_DROP = 0.02             # exit when the close falls 2% under its peak
MAX_SLIPPAGE_BPS = 300        # reject a fill moving over 3% from the last close
MIN_NOTIONAL = 1_000_000      # 1 USDC, in quote units


class Rider:
    """Keeps the closes, the slow average and the trailing-stop peak."""

    def __init__(self):
        self.closes = []
        self.ema = None
        self.peak = None  # highest close since entry, while long

    def note_bar(self, close):
        self.closes.append(close)
        if self.ema is None:
            self.ema = float(close)
        else:
            k = 2.0 / (EMA_BARS + 1)
            self.ema += k * (float(close) - self.ema)

    def trend_return(self):
        """Return of the latest close over the close LOOKBACK_BARS back."""
        if len(self.closes) <= LOOKBACK_BARS:
            return None
        old = self.closes[-1 - LOOKBACK_BARS]
        return self.closes[-1] / old - 1.0

    def may_enter(self):
        if len(self.closes) <= LOOKBACK_BARS or self.ema is None:
            return False
        ret = self.trend_return()
        return ret is not None and ret > ENTRY_RETURN and self.closes[-1] > self.ema

    def stopped_out(self, close):
        return self.peak is not None and close < self.peak * (1.0 - TRAIL_DROP)


RIDER = Rider()


def on_batch(state, batch):
    # No bar for our symbol this minute: nothing new to decide on.
    if not any(bar.get("symbol") == SYMBOL for bar in batch.get("bars", [])):
        return []

    close = state.close(SYMBOL)
    if close is None:
        return []
    RIDER.note_bar(close)
    # Warm-up batches build history only; orders on them are rejected.
    if state.warming_up:
        return []

    holding = state.positions.get(SYMBOL)
    if holding is not None and holding.qty > 0:
        if close > (RIDER.peak if RIDER.peak is not None else 0):
            RIDER.peak = close
        if RIDER.stopped_out(close):
            RIDER.peak = None
            return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []

    # Flat: enter only on a confirmed uptrend.
    if RIDER.may_enter():
        room = state.weight_room(SYMBOL)
        notional = state.cash if state.cash < room else room
        if notional >= MIN_NOTIONAL:
            RIDER.peak = close
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": int(notional),
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
