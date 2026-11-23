"""
Generates high-resolution academic figures for SentinelX Project Report
"""
import os
import matplotlib
os.environ['MPLCONFIGDIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".mpl_temp")
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

os.makedirs("report_assets", exist_ok=True)
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

# 1. Figure 1: Risk Distribution Donut Chart & Bar
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), dpi=200)

labels = ['LOW\n(0-29)', 'MEDIUM\n(30-59)', 'HIGH\n(60-79)', 'CRITICAL\n(80-100)']
counts = [5, 7, 4, 7]
colors = ['#10b981', '#f59e0b', '#f97316', '#ef4444']

# Donut
wedges, texts, autotexts = ax1.pie(
    counts, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors,
    wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2),
    textprops=dict(color="#1e293b", weight="bold", fontsize=9)
)
for at in autotexts:
    at.set_color('white')
    at.set_fontsize(9)
ax1.set_title("Operational Risk Band Distribution\n(4 Calibrated Tiers)", fontsize=11, fontweight="bold", pad=12)

# Bar chart
bars = ax2.bar(labels, counts, color=colors, edgecolor='#334155', linewidth=1.2, width=0.55)
ax2.set_ylabel("Transaction Count", fontsize=10, fontweight="bold")
ax2.set_title("Volume Count by Operational Risk Tier", fontsize=11, fontweight="bold", pad=12)
ax2.grid(axis='y', linestyle='--', alpha=0.7)
for bar in bars:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 0.15, int(yval), ha='center', va='bottom', fontweight='bold', fontsize=10)

plt.tight_layout()
plt.savefig("report_assets/fig1_risk_distribution.png", dpi=200)
plt.close()

# 2. Figure 2: Confusion Matrix & Performance Metrics
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), dpi=200)

# Normalized Confusion Matrix (XGBoost)
cm = np.array([[9993, 7], [17, 983]])
cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

im = ax1.imshow(cm_norm, interpolation='nearest', cmap=plt.cm.Blues)
ax1.set_title("XGBoost Confusion Matrix\n(Normalized)", fontsize=11, fontweight="bold", pad=10)
tick_marks = np.arange(2)
ax1.set_xticks(tick_marks)
ax1.set_yticks(tick_marks)
ax1.set_xticklabels(['Clean (0)', 'Fraud (1)'], fontsize=9, fontweight="bold")
ax1.set_yticklabels(['Clean (0)', 'Fraud (1)'], fontsize=9, fontweight="bold")
ax1.set_ylabel('True Financial Label', fontsize=10, fontweight="bold")
ax1.set_xlabel('Predicted Label', fontsize=10, fontweight="bold")

thresh = cm_norm.max() / 2.
for i in range(2):
    for j in range(2):
        ax1.text(j, i, f"{cm_norm[i, j]:.3f}\n(n={cm[i,j]})",
                 ha="center", va="center",
                 color="white" if cm_norm[i, j] > thresh else "#0f172a",
                 fontsize=9, fontweight="bold")

# Model Comparison Bar
models = ['Logistic Reg', 'Random Forest', 'XGBoost\n(SentinelX)']
f1_scores = [0.7772, 0.9396, 0.9861]
pr_auc = [0.8410, 0.9845, 0.9990]

x = np.arange(len(models))
width = 0.35

rects1 = ax2.bar(x - width/2, f1_scores, width, label='F1-Score', color='#0284c7')
rects2 = ax2.bar(x + width/2, pr_auc, width, label='PR-AUC', color='#10b981')

ax2.set_ylabel('Score Ratio (0..1.0)', fontsize=10, fontweight="bold")
ax2.set_title('Comparative Benchmark Performance', fontsize=11, fontweight="bold", pad=10)
ax2.set_xticks(x)
ax2.set_xticklabels(models, fontsize=9, fontweight="bold")
ax2.set_ylim(0.6, 1.05)
ax2.legend(loc='lower right', frameon=True)
ax2.grid(axis='y', linestyle='--', alpha=0.7)

for r in rects1 + rects2:
    h = r.get_height()
    ax2.text(r.get_x() + r.get_width()/2., h + 0.01, f"{h:.3f}", ha='center', va='bottom', fontsize=8, fontweight='bold')

plt.tight_layout()
plt.savefig("report_assets/fig2_confusion_matrix.png", dpi=200)
plt.close()

# 3. Figure 3: Tree SHAP Local Feature Attribution Waterfall
fig, ax = plt.subplots(figsize=(9, 4.8), dpi=200)

shap_features = [
    'errorBalanceOrig (₹0 remaining delta)',
    'COMPLETE_BALANCE_DRAIN (100% emptied)',
    'dest_zero_old (Unfunded destination)',
    'amount (₹1,85,000 CASH_OUT)',
    'type_TRANSFER / CASH_OUT',
    'step (Velocity burst hour 152)'
]
shap_values = [0.38, 0.26, 0.18, 0.12, 0.08, -0.04]
y_pos = np.arange(len(shap_features))
bar_colors = ['#ef4444' if v > 0 else '#10b981' for v in shap_values]

bars = ax.barh(y_pos, shap_values, color=bar_colors, edgecolor='#1e293b', height=0.6)
ax.set_yticks(y_pos)
ax.set_yticklabels(shap_features, fontsize=9, fontweight="bold")
ax.invert_yaxis()
ax.axvline(0, color='#64748b', linewidth=1.2, linestyle='--')
ax.set_xlabel('SHAP Shapley Value (Contribution to Fraud Probability)', fontsize=10, fontweight="bold")
ax.set_title('Local Tree SHAP Waterfall Explanation for TXN_30101 (Score: 88.3)', fontsize=11, fontweight="bold", pad=12)

for bar in bars:
    w = bar.get_width()
    offset = 0.01 if w > 0 else -0.04
    ax.text(w + offset, bar.get_y() + bar.get_height()/2, f"{w:+.2f}",
            va='center', fontsize=9, fontweight='bold',
            color='#b91c1c' if w > 0 else '#047857')

ax.set_xlim(-0.08, 0.45)
plt.tight_layout()
plt.savefig("report_assets/fig3_shap_waterfall.png", dpi=200)
plt.close()

# 4. Figure 4: NetworkX Directed Transaction Graph (Money Mule Ring)
fig, ax = plt.subplots(figsize=(8.5, 5), dpi=200)
G = nx.DiGraph()

# Mule ring
ring_nodes = ['ACC_MULE_1', 'ACC_MULE_2', 'ACC_MULE_3']
G.add_edge('ACC_MULE_1', 'ACC_MULE_2', weight=84000)
G.add_edge('ACC_MULE_2', 'ACC_MULE_3', weight=83500)
G.add_edge('ACC_MULE_3', 'ACC_MULE_1', weight=82900)
G.add_edge('ACC_MULE_3', 'ACC_CASH_OUT', weight=82000)

# Legitimate peripheral
G.add_edge('VICTIM_ACC_A', 'ACC_MULE_1', weight=85000)
G.add_edge('USER_LEGIT_1', 'MERCHANT_101', weight=1250)
G.add_edge('USER_LEGIT_2', 'MERCHANT_102', weight=3400)

pos = {
    'VICTIM_ACC_A': (-1.8, 0.0),
    'ACC_MULE_1': (-0.6, 1.0),
    'ACC_MULE_2': (0.8, 1.0),
    'ACC_MULE_3': (0.1, -0.6),
    'ACC_CASH_OUT': (1.8, -0.6),
    'USER_LEGIT_1': (-1.4, -1.5),
    'MERCHANT_101': (-0.4, -1.5),
    'USER_LEGIT_2': (0.6, -1.5),
    'MERCHANT_102': (1.6, -1.5)
}

node_colors = []
for n in G.nodes():
    if 'MULE' in n:
        node_colors.append('#ef4444')
    elif 'CASH_OUT' in n:
        node_colors.append('#dc2626')
    elif 'VICTIM' in n:
        node_colors.append('#f59e0b')
    else:
        node_colors.append('#10b981')

nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1600, edgecolors='#1e293b', linewidths=1.5, ax=ax)
nx.draw_networkx_labels(G, pos, font_size=7.5, font_weight='bold', font_color='white', ax=ax)
nx.draw_networkx_edges(G, pos, edge_color='#475569', arrowsize=18, width=1.8, connectionstyle='arc3,rad=0.08', ax=ax)

edge_labels = {
    ('ACC_MULE_1', 'ACC_MULE_2'): '₹84k',
    ('ACC_MULE_2', 'ACC_MULE_3'): '₹83.5k',
    ('ACC_MULE_3', 'ACC_MULE_1'): '₹82.9k\n(Ring Loop)',
    ('ACC_MULE_3', 'ACC_CASH_OUT'): '₹82k Cash-out',
    ('VICTIM_ACC_A', 'ACC_MULE_1'): '₹85k Ingest'
}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7.5, font_color='#0f172a', ax=ax)

ax.set_title("NetworkX Graph Intelligence: Automated Detection of Circular Money Laundering Mule Ring", fontsize=10.5, fontweight="bold", pad=12)
ax.axis('off')
plt.tight_layout()
plt.savefig("report_assets/fig4_network_mule_ring.png", dpi=200)
plt.close()

print("[SUCCESS] All 4 visual figures generated in report_assets/")
