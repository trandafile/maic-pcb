# Lessons Learned

*This file tracks continuous self-improvement lessons regarding Plotly Z-axis logic, Streamlit state bugs, and architectural rules to avoid repeating mistakes.*

## Initial Architecture Setup (Date: {{Current Date}})
* **Rule:** Streamlit State Initialization must happen before any component reads variables (`KeyError` prevention).
* **Rule:** Toggles and UI controls update `st.session_state` values synchronously.
