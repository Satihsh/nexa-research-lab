# S14 option E: demo forward check (fill logging). Deployment record

**Approved 2026-10-04:** decisions 2 (survival pause kept), 3 (install alongside, production inputs) and 5 (tick logger).
**Label:** DEMO FORWARD CHECK, production inputs. This is NOT research evidence of edge.

## Account (read-only MCP check, 2026-10-04)
- **Login:** Pepperstone-Demo <demo-account>.
- **Account:** DEMO (`trade_mode` 0), $200 USD, leverage 1:200, trading and EAs allowed, no open positions.
- **Symbols:** EURUSD, GBPUSD, USDJPY and XAUUSD match `data/pepperstone/contracts.json`: market execution, IOC fills, 0.01 minimum and step, no minimum stop distance or freeze level.
- **Spreads:** look like a raw-spread (Razor) account. The commission per lot is confirmed from the first CLOSE row.

## Binaries
| File | SHA-256 (prefix) | Where |
|---|---|---|
| `build/NEXA_EA_S14.ex5` | `ff30ac38` | install as `MQL5\Experts\Advisors\NEXA_EA_S14.ex5` (new name) |
| `build/NEXA_TickLogger.ex5` | `f1f847e8` (source `f1bd3a20`) | install as `MQL5\Experts\Advisors\NEXA_TickLogger.ex5` |
| deployed `NEXA_EA.ex5` | `f0ae9618` | **unchanged**; back up to `build/deployed_backup/`; do NOT attach it |
| `NEXA_EA_S14_DEMO_PRODUCTION.set` | (this folder) | copy to `MQL5\Presets\` |

The `.set` file lists all 64 inputs at the compiled source defaults, which are the production values (same pins as the engineering regressions). That includes:
- `InpEnableTrading=true`, `InpRequireDemoAccount=true`;
- `InpMaxSameCurrencyNet=2`, `InpRiskPercent=0.30`, `InpHardRiskCeiling=1.00`;
- `InpMinSampleForSurvival=20`, `InpExpectancyPauseR=-0.10`.

## Charts (8 in total, one EA per chart)
- **`NEXA_EA_S14`** on EURUSD, GBPUSD, USDJPY and XAUUSD, **M1**. Load the preset and tick "Allow Algo Trading".
- **`NEXA_TickLogger`** on a second chart of each of the four symbols. It places no orders. Its session tags use naive server hours; the analysis recomputes sessions with the DST-aware clock. Its timestamps are whole seconds.
- Then switch on Algo Trading in the toolbar. The Mac and the terminal must stay awake during market hours.

## Outputs (Common\Files)
- **`NEXA_TradeDNA_<SYM>.csv`:** one per symbol. FILL rows carry `SLIPPAGE_PTS_<abs>_ADVERSE_<±x>`; a guard firing shows as `FILL_RISK_ABOVE_HARD_CEILING_*`.
- **`NEXA_TickLog_<SYM>_<date>.csv`.**
- **Do not run any tester script while the demo is live.** The regression runners delete `Common\Files\NEXA_TradeDNA_<SYM>.csv` before each run. They also refuse to start while terminal64.exe is running, which protects these files only as long as the terminal is up.

## Duration and stop rules
- **Duration:** at least 4 weeks or 100 fills, whichever comes later; 8 weeks at most.
- **Stop immediately** (switch off Algo Trading, remove the EAs) if:
  - a position has no stop;
  - orders are rejected or requoted in a loop;
  - the terminal is on any account other than <demo-account>;
  - an unexpected EA is attached.
- **Review, don't stop:** a guard firing, or the survival pause or daily-loss gate tripping.

## Analysis (read-only)
- Weekly: FILL rows plus deal history (commission, swap).
- Measures: signed slippage in points and in R (from the stop distance), split by symbol and session; latency from send to fill; requotes and retries.
- Feeds H-DEVIATION-OPT and Q3 (multi-chart lock contention, requotes, freeze levels).

## Status
- [x] Install, done by the user on 2026-10-04 (the agent's attempt was blocked by the permission system), verified by the agent:
  - backup `build/deployed_backup/NEXA_EA_deployed_f0ae9618.ex5` = `f0ae9618`;
  - `Advisors\NEXA_EA_S14.ex5` = `ff30ac38`;
  - `Advisors\NEXA_TickLogger.ex5` = `f1f847e8`;
  - `Advisors\NEXA_EA.ex5` unchanged at `f0ae9618`.

  The preset was not copied; the defaults are the production values.
- [x] Charts attached 2026-10-04 03:22–03:34 (+08, Sunday, market closed). Verified read-only.
  - **Saved profile:** `NEXA_EA_S14` is on XAUUSD, USDJPY, GBPUSD and EURUSD, one M1 chart each. All 64 inputs match `NEXA_EA_S14_DEMO_PRODUCTION.set`.
  - **Tick logger:** on XAUUSD, USDJPY and GBPUSD M1, and on EURUSD H1. The timeframe doesn't matter for a tick logger.
  - **Experts log:** every instance initialised (`AI=NONE`, schema v1.0). The 4 DNA files and 4 tick-log files were created under `drive_c/users/user/.../Common/Files`; the tick logs are named `_2026.10.02` (last server date).
  - **Account:** <demo-account>, $200, no positions.
  - **Global Algo Trading:** switched off at 03:35:27, then **re-enabled at 03:41:44** (terminal log). **The forward check is LIVE from 2026-10-04 03:41 +08**; the first tradable session is the market open, Monday about 05:00 +08.
- [x] **Interruption and restart, 2026-10-04/05.**
  - **Down:** the terminal was shut down cleanly at 2026-10-04 03:53:27 +08 (all EAs removed, exit 0). The market reopen was missed.
  - **Up:** at 2026-10-05 05:05:18 +08 an agent read-only MCP query (`get_account_info`) **auto-launched terminal64.exe**. It logged into <demo-account>, reloaded all 8 EAs and kept Algo Trading on. It was not a user action. **The user approved continuing (option a) at about 05:09 +08.**
  - **Health at 05:06–05:09 +08:**
    - $200, 0 positions;
    - EURUSD and GBPUSD ticking, DNA DECISION rows written (no trades; opening spread 4–7× ATR, above the cap);
    - USDJPY and XAUUSD had no ticks yet at 00:09 server;
    - no errors, rejects or requotes.
  - **Output location changed:** the MCP-launched instance runs as Wine user `<user>`, so the DNA and tick logs now go to `drive_c/users/<user>/AppData/Roaming/MetaQuotes/Terminal/Common/Files/`. The 2026-10-04 header-only files remain in `drive_c/users/user/.../Common/Files/`. **The weekly analysis must read both locations.**
- [ ] First fill reviewed
- [x] **Second interruption and restart, 2026-10-05 → 2026-10-11.**
  - **Down:** the terminal exited cleanly at 2026-10-05 06:59:13 +08 (all EAs removed, exit 0, no errors). It was the MCP-launched instance; it most likely ended with the launching MCP/agent session. **Six trading days were lost** (10-05 → 10-09); TradeDNA had 355 DECISION rows and 0 fills.
  - **Up:** user-approved ("Approved, start MT5 and restart the S14 demo check"), 2026-10-11 19:46 +08, Sunday, market closed. **Launched via the MetaTrader 5 app** (`open -a "MetaTrader 5"`), not via MCP, so it does not depend on an agent session. No MCP call was made.
  - **Verified (read-only, files and logs):**
    - build 6230; authorized on <demo-account> Pepperstone-Demo, demo/hedging; 0 positions, 0 orders;
    - all 8 EAs loaded. The profile Default charts 01–08 map to `Experts\Advisors\NEXA_EA_S14.ex5` (ff30ac38) on XAUUSD, USDJPY, GBPUSD and EURUSD, plus `NEXA_TickLogger.ex5` (f1f847e8) on each. `NEXA_EA.ex5` (f0ae9618) is not attached;
    - every S14 init line reads `AI=NONE | schema v1.0 | spread cap=15.0% ATR`;
    - `common.ini` `[Experts] Enabled=1` (Algo Trading on).
  - **Output location (third one):** the app instance runs as Wine user `user`, so outputs are back in `drive_c/users/user/.../Common/Files/` (new tick logs `_2026.10.09`). **The weekly analysis must read both user folders.**
  - **Power risk:** at restart the Mac was on battery (42 %, about 7 h); idle sleep is 1 min, prevented only by app assertions. The user must keep it on AC power with the lid open during market hours.
  - **Clock:** the minimum 4 weeks / 100 fills restarts from the 2026-10-12 market open (about 05:00 +08). Maximum 8 weeks, i.e. by 2026-12-07.
- [ ] **Planned move to Google Cloud (G-2), prepared 2026-10-11.**
  - User travelling, so the Mac cannot stay on.
  - Pack: `gcp_g2/`, with README, scripts and the verified upload files (S14 ff30ac38, TickLogger f1f847e8, preset 1873bfe3).
  - Windows VM us-east4, <gcp-project>, paid from the free credit (≈ RM760 of RM1,225); tear-down by 2026-12-08.
  - Cut-over rule: quit the Mac MT5 **before** switching on Algo Trading on the VM (one terminal per account).
  - Not yet executed; the user creates every resource.
- [x] **GCP VM built by the agent, 2026-10-11 ~21:00–21:40 +08** (user approvals: install gcloud, create the VM, alerts to the user's Gmail; "Yes 1 and 2" for the MT5 installer and Windows Update set to manual).
  - **Server:** <gcp-project>, VM `nexa-s14` (e2-medium, Windows Server 2022, us-east4-c, external IP <redacted-ip>).
  - **Firewall:** `nexa-access-myip` allows tcp 22/3389 from <redacted-ip>/32 only. `default-allow-rdp` and `default-allow-ssh` are disabled.
  - **Storage and access:** bucket `gs://nexa-s14-<gcp-project>` (private). Service account `nexa-s14-vm` with objectAdmin on the bucket and logWriter only.
  - **MT5:** `pepperstone5setup.exe` (6,310,984 B, sha256 4778C39A…, Authenticode Valid, signer MetaQuotes Ltd.), installed silently. Portable copy at `C:\MT5`.
  - **Hash-verified:**
    - `MQL5\Experts\Advisors\NEXA_EA_S14.ex5` ff30ac38 and `NEXA_TickLogger.ex5` f1f847e8;
    - preset 1873bfe3;
    - profile `NEXA_S14` = the Mac's 8 chart files.
  - **First start:** `nexa_first.ini` sets <demo-account> / Pepperstone-Demo / profile NEXA_S14 / **Algo Trading OFF**.
  - **Windows Update:** policy NoAutoUpdate=1.
  - **Alert:** heartbeat metric `s14_heartbeat_ok`, email channel, policy `5663138342355737928` (**disabled until cut-over**).
  - **Next:** the user sets the `nexa` password, connects over RDP, does the first start and enters the demo password. Then the cut-over (quit the Mac MT5 → Algo Trading ON on the VM → register the sync task → enable the alert).
- [x] **CUT-OVER to GCP VM, 2026-10-11 21:44–21:56 +08 (13:44–13:56 UTC).** The forward check now runs ONLY on VM `nexa-s14`.
  - **Steps:**
    - The user set the `nexa` password privately (a first, exposed password was superseded; `Password last set` 13:30:28 UTC).
    - The user connected over RDP, did the first start (account <demo-account> Pepperstone-Demo, profile NEXA_S14, 8 charts) and switched Algo Trading ON. The VM log shows `automated trading is enabled` at 13:44:40 UTC.
    - The agent then quit the Mac MT5 (`osascript quit`; terminal64 gone), so the Mac no longer runs S14.
  - **VM init:** all 4 `NEXA init on <SYM> | … | AI=NONE | schema v1.0`, plus 4 TickLoggers.
    - A transient `NEXA INIT FAILED: not a demo account` appeared ≈ 0.7 s before account authorization; the EAs re-initialised OK after login. This is the fail-closed guard working, and it is expected on every cold start.
  - **Permissions fix:** `C:\MT5` was owned by the admin account, giving `servers.dat replace error [Access is denied]`. Fixed with `icacls C:\MT5 /grant nexa:(OI)(CI)M /T` (1,293 files, 0 failures).
  - **Autostart:** the All-Users Startup shortcut `MT5 NEXA.lnk` runs `C:\MT5\terminal64.exe /portable` when `nexa` logs in.
  - **Outputs:** `C:\Users\nexa\AppData\Roaming\MetaQuotes\Terminal\Common\Files\` (4 DNA + tick logs). Cosmetic: tick-log files named `_2021.10.22` were created before the server date synced.
  - **Sync:**
    - Task `NEXA_S14_Sync` runs as SYSTEM every 15 min, copying to `gs://nexa-s14-<gcp-project>/s14/`, plus the heartbeat `nexa-s14-heartbeat`.
    - First clean heartbeat (INFO) at 13:54 UTC: terminal_running=true, errors=[].
    - Today's tick logs are held open by the logger without read-sharing, so they reach the bucket after the day changes (`tick_locked_active`, expected).
  - **Alert:** policy `5663138342355737928` ENABLED (no terminal-running heartbeat for 30 min → email to the user).
  - **Clock:** the 4-week / 100-fill minimum starts at the 2026-10-12 open. Tear-down by 2026-12-08.
- [x] **2026-10-11 22:20 +08: Mac MT5 safety net.** The Mac MT5 `config/common.ini` [Experts] Enabled 1 → 0 (Algo Trading OFF). An accidental launch, e.g. by the meta-trader-mcp auto-launch, can no longer trade <demo-account> while the VM is live. Reverse by setting it back to 1 if S14 ever returns to the Mac.
- [x] **2026-10-11 ~23:00 +08: inbound access CLOSED while the user travels** (user: "close access").
  - Firewall `nexa-access-myip` (tcp 22/3389 from <redacted-ip>) is **disabled**; the defaults stay disabled. Ports 22 and 3389 verified unreachable.
  - Outbound is unaffected: MT5 to Pepperstone, the bucket sync and the heartbeat all still work.
  - **Re-open** (Cloud Shell, as owner): `gcloud compute firewall-rules update nexa-access-myip --source-ranges=<current IPv4>/32 --no-disabled`
- [x] **2026-10-19 ~00:55 +08: S14 forward check ENDED EARLY by user decision** (futures-only plan; credit re-used for the ATAS X recorder VM).
  - MT5 closed gracefully; final sync verified (12 objects, 468 MiB); alert disabled; VM stopped, disk and snapshots kept until 2026-12-08.
  - Result: 19 trades, gross −0.235 R, net −0.387 R, slippage 0.
  - See `S14_FINAL_REPORT.md`.
