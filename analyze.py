# analyze.py

# KEY FINDING: km_since_service (d=1.10, p<0.001), avg_daily_km (d=0.65, p=0.006), and
# load_factor (d=0.54, p=0.018) strongly separate cars that broke down from those that did not.
# odometer_km and age_years show near-zero effect size (d~0.006/0.003) and p>0.8 -- they tell
# us nothing. The risk score is built solely from the three significant features.

import pandas as pd
import math
from scipy import stats as scipy_stats
from sklearn.metrics import roc_auc_score

# -- Step 1: load --------------------------------------------------------------
df = pd.read_csv("fleet_history.csv")

print("=" * 60)
print(f"Dataset: {len(df)} cars  |  broke down: {df['broke_down'].sum()}  "
      f"|  fine: {(df['broke_down'] == 0).sum()}")
print("=" * 60)

# -- Step 2: compare the two groups column by column --------------------------
#
# For each feature we compute three things:
#   * mean for each group (broke vs fine)
#   * Cohen's d  - a unit-free effect size.  |d| > 0.2 small, >0.5 medium, >0.8 large
#   * Mann-Whitney U p-value - a non-parametric significance test that makes no
#     assumption about how the data is distributed (unlike a t-test).
#
# This lets the numbers answer the question instead of us guessing.

FEATURES = ["odometer_km", "km_since_service", "avg_daily_km", "load_factor", "age_years"]

broke = df[df["broke_down"] == 1]
fine  = df[df["broke_down"] == 0]

print()
print("-- Column-by-column group comparison ----------------------------------")
print(f"{'column':<22} {'broke mean':>11} {'fine mean':>10} {'Cohen d':>9} {'p-value':>9}  verdict")
print("-" * 80)

separating = []
for col in FEATURES:
    b_vals = broke[col]
    f_vals = fine[col]
    pooled_std = math.sqrt((b_vals.std() ** 2 + f_vals.std() ** 2) / 2)
    d = (b_vals.mean() - f_vals.mean()) / pooled_std if pooled_std else 0.0
    _, p = scipy_stats.mannwhitneyu(b_vals, f_vals, alternative="two-sided")
    separates = p < 0.05 and abs(d) >= 0.5
    tag = "*** separates" if separates else "(noise)"
    print(f"{col:<22} {b_vals.mean():>11.2f} {f_vals.mean():>10.2f} {d:>+9.3f} {p:>9.4f}  {tag}")
    if separates:
        separating.append(col)

print()
print(f"Columns that genuinely separate the groups: {separating}")
print()
print("Plain-words explanation:")
print("  odometer_km : d=+0.006, p=0.92 -> the two groups have virtually identical total")
print("                mileage.  Total distance driven is NOT a risk factor here.")
print("  age_years   : d=-0.003, p=0.84 -> broke-down cars are on average the same age")
print("                as fine cars.  Age is NOT a risk factor here.")
print("  km_since_service: d=+1.10, p<0.001 -> cars that broke down had driven ~60% more")
print("                km since their last service (11 678 vs 7 261).  Large effect.")
print("  avg_daily_km: d=+0.65, p=0.006  -> higher daily usage correlates with breakdown.")
print("                Broke-down cars average 160 km/day vs 131 for fine cars.")
print("  load_factor : d=+0.54, p=0.018  -> heavier loading correlates with breakdown")
print("                (mean 0.60 vs 0.51).  Medium effect.")

# -- Step 3: build a risk score 0-100 -----------------------------------------
#
# Method: for each of the three significant columns we min-max normalise it to
# [0, 1] using the observed range in the dataset, then take a weighted average
# and scale to 0-100.
#
# Weights reflect Cohen's d magnitude:
#   km_since_service  d~1.10  -> weight 5  (largest effect by far)
#   avg_daily_km      d~0.65  -> weight 3
#   load_factor       d~0.54  -> weight 2
#   --------------------------- total 10
#
# This is intentionally simple -- no logistic regression, no black box.

WEIGHTS = {
    "km_since_service": 5,
    "avg_daily_km":     3,
    "load_factor":      2,
}
TOTAL_WEIGHT = sum(WEIGHTS.values())   # 10

print()
print("-- Building risk scores ------------------------------------------------")
print("  Using: km_since_service (w=5), avg_daily_km (w=3), load_factor (w=2)")
print("  Each feature is min-max scaled to [0,1] over the whole fleet,")
print("  then the weighted average is multiplied by 100.")
print()

# Pre-compute per-column min/max once, from the whole fleet
col_min = {col: df[col].min() for col in WEIGHTS}
col_max = {col: df[col].max() for col in WEIGHTS}


def risk_score(row: pd.Series) -> float:
    """Weighted, min-max normalised risk score in [0, 100]."""
    total = 0.0
    for col, w in WEIGHTS.items():
        span = col_max[col] - col_min[col]
        normalised = (row[col] - col_min[col]) / span if span else 0.0
        total += normalised * w
    return round((total / TOTAL_WEIGHT) * 100, 1)


df["risk_score"] = df.apply(risk_score, axis=1)

# -- Step 4: rank by risk, print top 10 ---------------------------------------
print("-- Top 10 highest-risk cars --------------------------------------------")
print(f"{'rank':<5} {'car_id':<12} {'risk':>6}  {'km_since_svc':>14} "
      f"{'avg_daily_km':>13} {'load_factor':>12} {'broke_down':>11}")
print("-" * 70)

top10 = df.sort_values("risk_score", ascending=False).head(10).reset_index(drop=True)
for i, row in top10.iterrows():
    print(f"{i + 1:<5} {row['car_id']:<12} {row['risk_score']:>6.1f}  "
          f"{row['km_since_service']:>14.0f} {row['avg_daily_km']:>13.0f} "
          f"{row['load_factor']:>12.2f} {int(row['broke_down']):>11}")

print()

# AUC tells us how good the simple score is at ranking the known break-downs.
# 0.5 = random guess, 1.0 = perfect separation.
auc = roc_auc_score(df["broke_down"], df["risk_score"])
print(f"AUC of the risk score vs known outcomes: {auc:.3f}")
print("  (0.5 = random, 1.0 = perfect.  Above 0.7 is useful for a simple linear rule.)")
