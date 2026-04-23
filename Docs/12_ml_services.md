# ML Services

ML does not deliver messages. It improves decisions **before** the send (what to send, when to send, whom to send to) and **after** the send (what the reply means, whether the system should pause). Every model starts simple and improves with data.

---

## 10.1 Pre-Send Spam Scorer (Model 1)

Scores content + context. Returns probability 0–1. **Send only if score < 0.2.**

- **Features:** subject length, spam word count, all-caps ratio, link count, body length, punctuation density, personalization score, domain age, warmup age, recipient engagement history, recent complaint rate
- **Label:** `did_complain` OR `did_hard_bounce` within 48h of send
- **Weeks 1–2:** heuristic rules only (no ML)
- **Week 3+:** sklearn LogisticRegression, retrained weekly
- **Week 12+:** evaluate XGBoost if logistic regression's AUC plateaus
- **Serving:** in-process Python at send time, p99 < 5ms

---

## 10.2 Reply Intent Classifier (Model 2)

Classifies every inbound reply into an intent class. Action depends on class.

- **Classes:** `interested`, `not_now`, `unsubscribe`, `out_of_office`, `angry`, `objection`, `question`
- **Seed training:** 200 Claude-generated synthetic examples per class (1,400 total)
- **Initial model:** TF-IDF + sklearn LinearSVC — fast, interpretable, strong on short text
- **Evolution:** at 5K+ labeled real replies, evaluate fine-tuned DistilBERT
- **Serving:** called from reply processing worker, p99 < 100ms
- **Actions:**
  - `unsubscribe` / `angry` → instant suppression
  - `interested` → CRM webhook
  - `not_now` → re-queue in 90 days

---

## 10.3 Anomaly Detection

Monitors rolling metrics for statistical anomalies — sudden changes not caught by static thresholds. Alerts on-call before a circuit breaker trips.

- **Metrics monitored:** bounce rate, complaint rate, open rate, click rate, reply rate, unsubscribe rate
- **Algorithm v1:** exponential moving average with 3σ threshold (simple, robust)
- **Algorithm v2 (future):** Prophet-based forecasting for seasonal campaigns
- **Output:** `anomaly_alerts` table entries with severity and probable cause

---

## 10.4 Send-Time Optimization

Predicts the best hour/day to send each campaign-to-contact combination. Improves open and reply rates, which are the dominant deliverability signals.

- **Features:** recipient timezone, prior open history, prior click history, day-of-week patterns, campaign type
- **Model:** gradient boosting per recipient, predicting probability of open per `(hour, day-of-week)` slot
- **Output:** `best_send_hour_utc` and `best_send_day_of_week`, stored in `contact_ml_features`
- **Used by:** orchestrator when `schedule_type = 'optimized'`
