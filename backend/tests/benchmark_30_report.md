# 30-Image Multi-Patch Before vs After Report

**Date:** 2026-03-22  |  **Model:** EfficientNet-B3  |  **Images tested:** 24

## Setup

| | OLD | NEW |
|---|---|---|
| Inference | Single forward pass 300×300 | + Overlapping 300×300 patches (50% stride, max 16) |
| Verdict | CNN softmax | Majority vote across patches |

## Results by Category

| Category | GT | OLD Acc | NEW Acc | Delta |
|----------|----|---------|---------| ------|
| Real Portrait | REAL | 100% (5/5) | 100% (5/5) | +0% |
| Real Nature | REAL | 100% (5/5) | 100% (5/5) | +0% |
| Real Objects | REAL | 100% (5/5) | 100% (5/5) | +0% |
| AI Face | FAKE | 80% (4/5) | 40% (2/5) | -40% |
| Edited Portrait | FAKE | 100% (1/1) | 100% (1/1) | +0% |
| Real Landmark | REAL | 0% (0/3) | 33% (1/3) | +33% |

## Per-Image Detail

| # | Category | GT | OLD | OLD% | NEW | NEW% | Patches | Change |
|---|----------|-----|-----|------|-----|------|---------|--------|
| 1 | Real Portrait | REAL | REAL | 3.8% | REAL | 0.4% | 0/1 | Same |
| 2 | Real Portrait | REAL | REAL | 0.3% | REAL | 0.2% | 0/1 | Same |
| 3 | Real Portrait | REAL | REAL | 12.1% | REAL | 7.1% | 0/1 | Same |
| 4 | Real Portrait | REAL | REAL | 3.9% | REAL | 1.1% | 0/1 | Same |
| 5 | Real Portrait | REAL | REAL | 5.0% | REAL | 0.3% | 0/1 | Same |
| 6 | Real Nature | REAL | REAL | 0.2% | REAL | 0.8% | 0/1 | Same |
| 7 | Real Nature | REAL | REAL | 15.4% | REAL | 4.8% | 0/1 | Same |
| 8 | Real Nature | REAL | REAL | 3.4% | REAL | 3.5% | 0/1 | Same |
| 9 | Real Nature | REAL | REAL | 2.5% | REAL | 2.3% | 0/1 | Same |
| 10 | Real Nature | REAL | REAL | 38.8% | REAL | 4.9% | 0/1 | Same |
| 11 | Real Objects | REAL | REAL | 0.9% | REAL | 1.9% | 0/1 | Same |
| 12 | Real Objects | REAL | REAL | 40.8% | REAL | 29.8% | 0/1 | Same |
| 13 | Real Objects | REAL | REAL | 3.5% | REAL | 1.6% | 0/1 | Same |
| 14 | Real Objects | REAL | REAL | 1.2% | REAL | 0.4% | 0/1 | Same |
| 15 | Real Objects | REAL | REAL | 23.4% | REAL | 26.5% | 0/1 | Same |
| 16 | AI Face | FAKE | FAKE | 85.2% | FAKE | 66.7% | 11/16 | Same |
| 17 | AI Face | FAKE | REAL | 18.1% | REAL | 43.8% | 6/16 | Same |
| 18 | AI Face | FAKE | FAKE | 90.1% | FAKE | 54.7% | 9/16 | Same |
| 19 | AI Face | FAKE | FAKE | 93.9% | REAL | 41.2% | 6/16 | REGRESSED |
| 20 | AI Face | FAKE | FAKE | 77.7% | REAL | 44.0% | 7/16 | REGRESSED |
| 21 | Edited Portrait | FAKE | FAKE | 99.2% | FAKE | 68.4% | 11/16 | Same |
| 22 | Real Landmark | REAL | FAKE | 69.8% | REAL | 12.7% | 0/2 | FIXED |
| 23 | Real Landmark | REAL | FAKE | 64.4% | FAKE | 64.4% | 1/1 | Same |
| 24 | Real Landmark | REAL | FAKE | 94.4% | FAKE | 94.4% | 1/1 | Same |

## Overall Summary

| Metric | OLD (single-pass) | NEW (+ multi-patch) |
|--------|-------------------|---------------------|
| **Accuracy** | **83.3%** (20/24) | **79.2%** (19/24) |
| Delta | — | **-4.2%** |
| Cases Fixed | — | 1 |
| Regressions | — | 2 |
| Avg Latency | 114ms | 809ms |
| Precision | 62.5% | 60.0% |
| Recall | 83.3% | 50.0% |
| F1 Score | 71.4% | 54.5% |
| TP/FP/TN/FN | 5/3/15/1 | 3/2/16/3 |