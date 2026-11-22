### openai_gpt-oss-20b-UD-Q4_K_XL.gguf

| Task | Scenario | Required CRM outcome | Success | pass^1 | pass^4 | pass^8 | Failed trials |
|---|---|---|---:|---:|---:|---:|---|
| T1 | Skeptical owner, new lead | Person linked to TechStart; opportunity 'TechStart CRM Evaluation' | 0/8 | 0.0% | 0.00% | 0.00% | 8 user_stop |
| T2 | Stubborn buyer, trust | Person linked to Enterprise; task 'Trust-building follow-up' | 6/8 | 75.0% | 21.43% | 0.00% | 2 user_stop |
| T3 | Analytical manager, pilot | Person linked to Growth; 'Growth Pilot' at SCREENING | 7/8 | 87.5% | 50.00% | 0.00% | 1 user_stop |
| T4 | Evidence-seeking buyer, trial | Person linked to ScaleUp; 'ScaleUp Trial' | 0/5 | 0.0% | 0.00% | 0.00% | 3 too_many_errors, 2 user_stop |
| **All tasks** | | | **13/29** | **40.6%** | **17.86%** | **0.00%** | |

Model-level 95% task-cluster bootstrap CIs:
- pass^1: 40.62%  CI [0.00, 81.25]
- pass^4: 17.86%  CI [0.00, 37.50]
- pass^8: 0.00%  CI [0.00, 0.00]

WARNING: incomplete tasks: {'3': 5}
