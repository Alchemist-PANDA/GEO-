import re
import os

file_path = 'pages/1_📈_Audit_Tool.py'
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    (r"st\.plotly_chart\(create_circular_gauge\(cov_score,\s*is_dark=\(st\.session_state\.theme == 'Dark'\)\),\s*use_container_width=True,\s*config=\{'displayModeBar': False\}\)",
     "render_chart_with_explain_button(create_circular_gauge(cov_score, is_dark=(st.session_state.theme == 'Dark')), 'Brand Coverage', {'coverage': cov_score}, 'Audit Tool', use_container_width=True, config={'displayModeBar': False})"),
    
    (r"st\.plotly_chart\(fig_multi,\s*use_container_width=True,\s*config=\{'displayModeBar': False\}\)",
     "render_chart_with_explain_button(fig_multi, 'Multi-Model Benchmark', {'type': 'multi_model'}, 'Audit Tool', use_container_width=True, config={'displayModeBar': False})"),
    
    (r"st\.plotly_chart\(fig_bv_trend,\s*use_container_width=True,\s*config=\{'displayModeBar': False\}\)",
     "render_chart_with_explain_button(fig_bv_trend, 'Brand Visibility Trend', {'type': 'visibility_trend'}, 'Audit Tool', use_container_width=True, config={'displayModeBar': False})"),
    
    (r"st\.plotly_chart\(fig_cr_trend,\s*use_container_width=True,\s*config=\{'displayModeBar': False\}\)",
     "render_chart_with_explain_button(fig_cr_trend, 'Citation Rate Trend', {'type': 'citation_trend'}, 'Audit Tool', use_container_width=True, config={'displayModeBar': False})"),
    
    (r"st\.plotly_chart\(fig_comp,\s*use_container_width=True\)",
     "render_chart_with_explain_button(fig_comp, 'Competitor Comparison', {'type': 'competitor_comparison'}, 'Audit Tool', use_container_width=True)"),
    
    (r"st\.plotly_chart\(fig_radar,\s*use_container_width=True\)",
     "render_chart_with_explain_button(fig_radar, 'Competitor Radar', {'type': 'radar'}, 'Audit Tool', use_container_width=True)"),
    
    (r"st\.plotly_chart\(fig_kw_trend,\s*use_container_width=True,\s*config=\{'displayModeBar': False\}\)",
     "render_chart_with_explain_button(fig_kw_trend, 'Keyword Trend', {'type': 'keyword_trend'}, 'Audit Tool', use_container_width=True, config={'displayModeBar': False})"),
    
    (r"st\.plotly_chart\(fig,\s*use_container_width=True\)",
     "render_chart_with_explain_button(fig, 'Historical Scores', {'type': 'historical'}, 'Audit Tool', use_container_width=True)"),
]

for pattern, repl in replacements:
    content = re.sub(pattern, repl, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
