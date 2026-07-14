# Screenshots Guide for BrandSight GEO

To maximize the visual impact of the repository, capture and place the following screenshots in this directory:

## 1. **Dashboard Overview** (`dashboard_overview.png`)
- **What to capture**: The main Streamlit dashboard after running an audit.
- **Key elements**: Citation Status metric, Confidence Score progress bar, Gaps Identified count.
- **How to capture**: Run `streamlit run geo_upload/dashboard.py`, login, run an audit for "Burger Hub", and screenshot the metrics panel.

## 2. **Remediation Approval Panel** (`remediation_panel.png`)
- **What to capture**: The human-in-the-loop content review section.
- **Key elements**: The text area showing AI-generated JSON-LD or whitepaper content, with "Approve" and "Reject" buttons visible.
- **How to capture**: Scroll down to the "Remediation & Content Review" section after an audit completes.

## 3. **Lift Report** (`lift_report.png`)
- **What to capture**: The terminal output or JSON file showing the before/after comparison.
- **Key elements**: The `confidence_score` delta and `gaps_resolved` count.
- **How to capture**: Run `python geo_upload/measure_lift.py` and screenshot the terminal output or open `lift_report.json` in a JSON viewer.

## 4. **LangGraph Agent Execution** (`agent_execution.png`)
- **What to capture**: The terminal logs showing the LangGraph nodes executing in sequence.
- **Key elements**: Log lines like "Starting Node: query_llm", "Finished Node: check_citation", etc.
- **How to capture**: Run `python geo_upload/run_baseline.py` and screenshot the structured logging output.

---

Once captured, reference these images in the README.md using:
```markdown
![Dashboard Overview](./docs/screenshots/dashboard_overview.png)
```
