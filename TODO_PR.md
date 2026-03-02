# PR #157 — Copilot Review: Fix Tracker

## All Issues

| # | File | Line(s) | Issue | Severity | Status |
|---|------|---------|-------|----------|--------|
| 1 | `docs/guide/keys.rst` | 238 | Docs say "balance and unspents" but impl also updates transactions | Low | **Done** (Phase I) |
| 2 | `FulcrumProtocolAPI.py` | 317 | Handshake errors not caught; callers can't retry | Low | **Done** (Phase II) |
| 3 | `FulcrumProtocolAPI.py` | 329 | `sendall` before thread's main loop (no try-except) | Medium | Subsumed by #6 |
| 4 | `FulcrumProtocolAPI.py` | 363–365 | `sub_sock.shutdown()` called after socket may already be closed — race condition | High | Won't fix (silently handled) |
| 5 | `FulcrumProtocolAPI.py` | 308 | `*args, **kwargs` accepted but never used | Low | Won't fix |
| 6 | `FulcrumProtocolAPI.py` | 321–355 | No outer try-except-finally in listen thread; unhandled exceptions leave state inconsistent | Medium | **Done** (Phase II) |
| 7 | `FulcrumProtocolAPI.py` | 350–355 | Callback fired twice on error: once with `"error: ..."`, once with `"unsubscribed"` | High | **Done** (Phase I) |
| 8 | `FulcrumProtocolAPI.py` | 333 | Blocking `recv()` doesn't respond to `stop_event`; relies on `shutdown()` to unblock | High | **Done** (Phase I) |
| 9 | `wallet.py` | 509 | `None` status (means no history) still triggers `get_unspents()` + `get_transactions()` — wasteful | High | **Done** (Phase I) |
| 10 | `test_wallet.py` | 337 | Test checks callback was called but not that `get_unspents()`/`get_transactions()` were invoked on valid status | Low | **Done** (Phase II) |

---

## Phase I — Complete (commit `3a85b5f`)

**#9 — `wallet.py:509`**
`None` status means the address has no history. The condition `status_hash is None or (...)` was
triggering `get_unspents()` + `get_transactions()` on every null status update.
Fixed by flipping to `status_hash is not None and (...)`.

**#7+#8 — `FulcrumProtocolAPI.py:350–355`**
When `stop_subscription()` shuts down the socket to unblock `recv()`, the resulting `OSError`
was treated as a real error, firing `callback(address, "error: ...")` even on a clean stop.
Then `callback(address, "unsubscribed")` also fired — two callbacks for one event.
Fixed by checking `stop_event.is_set()` in the except block:
- Clean stop → `callback("unsubscribed")` only
- Real error → `callback("error: ...")` only

**#1 — `docs/guide/keys.rst:238`**
Updated copy from "balance and unspents" to "balance, unspents, and transactions".

---

## Phase II — Complete (commit `34f06ba`)

**#6 — `FulcrumProtocolAPI.py:321`**
Collapsed the nested try/except inside `listen()` into a single flat
`try / except (OSError, ValueError) / finally`. The `finally` block unconditionally
closes `sub_sock` (with its own defensive try/except) and calls `callback("unsubscribed")`
only when `stop_event.is_set()` — preserving the Phase I single-callback invariant.
This also covers `sendall` failures and any other `OSError`/`ValueError` that previously
caused the thread to exit without cleanup.

**#10 — `tests/test_wallet.py:317` and `:400`**
`test_subscribe_with_update_self_updates_balances`: added mocks and `assert_called_once()`
assertions to verify `get_unspents()`/`get_transactions()` are called on a valid status hash.
`test_subscribe_with_update_self_handles_null_status`: added mocks and `assert_not_called()`
assertions to verify they are NOT called on `None` status (Phase I guard).

**#2 — `FulcrumProtocolAPI.py:316`**
Added docstring note: *"connection errors during handshake propagate directly to the caller."*

---

## Not in scope

- **#5** — unused `*args/**kwargs` in `subscribe_address`: cosmetic, not worth the churn
- **#4** — `shutdown()` race in `stop_subscription()`: already wrapped in `except Exception: pass`, silently handled, low real-world impact
- **#3** — `sendall` before while loop: subsumed by the outer try-finally in #6
