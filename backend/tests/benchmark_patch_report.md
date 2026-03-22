# Multi-Patch Analysis — Before vs After Benchmark Report

**Date:** 2026-03-22  |  **Model:** EfficientNet-B3  |  **Images tested:** 6

## Change

**OLD:** Single forward pass on full image resized to 300x300
**NEW:** OLD pass + Multi-Patch (overlapping 300x300 crops at 50% stride, max 16 patches)

The verdict in NEW uses majority vote across patches.

---
## Real Photos (Ground Truth = REAL)

| Image | Label | OLD | OLD Conf | NEW | NEW Conf | Patches | Max Fake | Fixed? |
|-------|-------|-----|----------|-----|----------|---------|----------|--------|
| Real — Street scene | REAL | REAL | 93.3% | REAL | 98.5% | 0/9 | 4.5% | Same |
| Real — Portrait | REAL | REAL | 78.1% | REAL | 97.2% | 0/9 | 8.7% | Same |
| Real — Nature 800px | REAL | FAKE | 70.5% | REAL | 95.1% | 0/16 | 27.2% | FIXED |
---
## Medium Test — Large Real Images

| Image | Label | OLD | OLD Conf | NEW | NEW Conf | Patches | Max Fake | Fixed? |
|-------|-------|-----|----------|-----|----------|---------|----------|--------|
| Real [MED test] — 1200px landscape | REAL | FAKE | 73.8% | REAL | 97.6% | 0/16 | 8.7% | FIXED |
| Real [MED test] — 900px abstract | REAL | REAL | 53.0% | REAL | 84.5% | 2/16 | 56.9% | Same |
| Real [MED test] — 1400px street | REAL | REAL | 70.9% | REAL | 93.3% | 0/16 | 21.3% | Same |

---
## Summary

| Metric | OLD | NEW |
|--------|-----|-----|
| Correct | 4/6 (67%) | 6/6 (100%) |
| Cases Fixed | — | 2 |
| Regressions | — | 0 |
| Avg Latency | 168ms | 1915ms |