# Signal Bot: accuracy review and changes

Data used: `app_paper_trades.csv` (205 trades, 182 closed, Oct 31 17:50 to Nov 1 05:05 UTC) and `lab_*` files (1,500 snapshots).
`bot_paper_log.csv` has only the header row, so there is nothing to analyse for the GitHub bot.

## 1. What the results show (before any change)
| | n | win rate | net R | profit factor |
|---|---|---|---|---|
| All closed app trades | 182 | 40.7% | -42.7 | 0.62 |
| BUY | 79 | 43.0% | -14.5 | 0.69 |
| SELL | 103 | 38.8% | -28.3 | 0.57 |
| 5m | 161 | 41.6% | -34.7 | 0.65 |
| 30m | 16 | 31.2% | -6.8 | 0.41 |
| 1h / 15m | 3 / 2 | too few | | |

With a 1:1 target and the 0.05R fee, a trade must win **52.5%** to break even. 40.7% over 182 trades is clearly below that
(about 3 standard errors), so the poor accuracy is real, not noise.

The numbers in your brief (BUY 40.63%, SELL 54.29%, overall 47.76%) do not match any CSV you uploaded (67 closed trades would be needed).
Please send the file they came from if you want those tuned.

## 2. Root cause that the data supports
Price extension from EMA20 at entry (`ext_atr`):
| extension | n | win | net R |
|---|---|---|---|
| up to 1.0 ATR | 62 | 41.9% | -13.1 |
| 1.0 to 1.2 ATR | 37 | 56.8% | +3.6 |
| **1.2 to 1.5 ATR** | **83** | **32.5%** | **-33.3** |

The old gate allowed up to 1.5 ATR. Those 83 late entries produce 78% of all losses, and the pattern holds in both the first (36%) and
second (27%) time halves of the data. This confirms your observation.
Other findings: signal score is not monotonic (score 0.5-0.6 won only 27.6%, n=29), 5m trades are 88% of the sample, and the old
quality score of 4 (n=124) won 37%.

## 3. Counterfactual with the new extension limit (not a true backtest)
Dropping the trades with extension above 1.2 ATR from the same data:
| | n | win | net R | avg R |
|---|---|---|---|---|
| Before | 182 | 40.7% | -42.7 | -0.235 |
| After (ext <= 1.2) | 99 | 47.5% | -9.5 | -0.096 |
| After, first 60% of time | 59 | 42.4% | -11.5 | -0.194 |
| After, last 40% of time | 40 | 55.0% | +2.0 | +0.050 |
Still below break-even overall (95% interval for the win rate: 37.9% to 57.2%). So this change removes most of the loss, but
**it does not prove a profitable edge.** BUY after the gate: 45 trades, 55.6%, +3.2R. SELL after the gate: 54 trades, 40.7%, -12.7R, negative
in both halves. That sample is one 11-hour window in a mostly rising market, so treat the BUY/SELL gap as a hypothesis.

## 4. Indicator lab (1,500 snapshots, one night, highly correlated across coins)
Overall verdict: direction right 46.4%, race win 49.5% (no edge). Best: RSI(14) 58.4% (n=436), RSI(2) 52.7%, Z-score 52.1%,
CCI 52.0%, Bollinger %B 52.0%. Worst: ADX 44.8%, Ichimoku 45.2%, Linear regression 45.7%, TRIX 45.9%.
The pattern is that mean-reversion style indicators beat trend-following ones in this sample. RSI, CCI, Stochastic, Williams and %B all
measure the same thing, so they count as about one signal, not five. One night of data cannot support re-weighting the verdict, so the
weights are unchanged and the lab keeps collecting.

## 5. What changed in the app (`app_src/main.dart`)
* **Paper tab live board**: every open trade shows exchange, side, entry, current rate, TP, SL, unrealized P&L ($ and R), P&L %, TP progress,
  SL distance, status (OPEN LIVE / STALE / OFFLINE) and time since entry; summary cards (open, unrealized, realized, winning now, losing now,
  average TP progress, average SL distance); manual refresh; last update time. Open trades are not counted as wins or losses.
* **Rates**: Binance best bid/ask for all symbols in one request every 3 seconds (futures, spot as fallback). BUY is valued at the bid, SELL at
  the ask, minus the 0.05R fee. Forex/gold/oil use Yahoo Finance (can be delayed, labelled). Not a WebSocket stream.
* **Signal quality gate**, separate BUY/SELL constants (`gateExtMax`, `gateRsiLimit`, `gateMinScoreAdd`): anti-chasing limit lowered
  from 1.5 to 1.2 ATR; market regime (strong up/down trend, ranging, high/low volatility, possible reversal) with counter-trend, high-volatility
  and low-volatility rejections; late-entry check (over 3 ATR in 5 candles); strong opposite candle check; support/resistance within 0.5 ATR;
  existing volume, RSI, higher-timeframe, Bitcoin and funding checks are kept. Every rejection is shown as NO TRADE with the reason (Paper tab list, and
  a line under the Final call in Markets).
* **Dashboard**: signals (session), executed, open, closed, wins, losses, win rate, TP rate, SL rate, average win/loss, net P&L, profit factor,
  expectancy, max drawdown, direction-right vs profitable, plus breakdowns by timeframe, direction, ADX range, market regime and agreeing indicator.
* **Amount per trade (USD)**: new input in the Paper settings. Typed amount = position size, so profit/loss = price move % x amount and a stop-out loses about amount x stop distance %. Empty = the old rule (risk 1% of the paper account). New `Amount` column in the live board and `amount_usd` in the CSV. The bot has the same option: `PAPER_AMOUNT` in `config.py` (None = old rule). The 1:1 reward-to-risk is unchanged.
* **Stop a trade manually**: a red `Close` button on every open trade (live board and on the Markets chart card). It asks for confirmation, exits at the current bid (BUY) or ask (SELL), charges the same 0.05R fee, saves immediately and counts as a closed trade with reason MANUAL.
* **Tap a trade to see it on the chart**: tapping a row (open or closed) in the Paper tab switches to Markets, selects that coin and timeframe, and for open trades draws Entry, SL and TP lines on the chart plus a summary card with live P&L.
* Trades now store `market_regime` and `agreeing_indicators` (two new CSV columns at the end; old saved trades still load).

## 6. What was NOT done, and why
* **No backtest per timeframe (5m/15m/30m/1h) and no out-of-sample optimisation of RSI/Z-score/weights**: this environment has no market-data access
  and no Flutter/Dart, so I could not download history or run the app. The new regime, late-entry, candle and support/resistance limits are
  sensible defaults, not validated values. Use the new CSV columns to judge them after 100+ trades per rule.
* **TP/SL, trailing stop, break-even, partial profits not changed**: the CSV only has best/worst move, not the path, so the effect cannot be
  measured. 26 of 108 losing trades reached +0.5R first, which makes break-even worth testing, but it needs candle-by-candle data.
* **No WebSocket**, no per-timeframe parameter sets, and the Python bot was not changed.
* Look-ahead: the app already enters at the next candle's open using only the closed candle, which I kept.

## 7. Testing
* `tests/test_logic.py`: Python mirrors of the new formulas (live P&L for BUY/SELL, bid/ask side, regime rules, dashboard maths checked against an independent
  pandas calculation on your CSV: PF 0.895, net -421.65 $, max drawdown 10.74% on the older 74-trade file). These test the logic, **not the Dart code**.
* The Dart code was checked for balanced brackets and lexing only. **It has not been compiled or run.** If Build APK fails, send me the log.
* Not tested: real-device rendering, restart behaviour, offline handling on a phone, exchange symbol mapping against live APIs.

## 8. Modified files
`app_src/main.dart`, `config.py` and `paper.py` (new `PAPER_AMOUNT` option only), `tests/test_logic.py` (new), `PERFORMANCE_REPORT.md` (new). Everything else is unchanged from your upload.
