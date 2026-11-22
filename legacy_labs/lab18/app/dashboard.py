from matplotlib import pyplot as plt


def create_architecture_diagram(output_path: str):
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.axis("off")
    blocks = [
        ("Threat Intelligence\nSources", (0.05, 0.68)),
        ("Python Threat\nProcessing App", (0.35, 0.68)),
        ("MongoDB", (0.12, 0.45)),
        ("Cassandra", (0.42, 0.45)),
        ("Neo4j", (0.72, 0.45)),
        ("False-Positive\nDetection", (0.42, 0.18)),
        ("Comparative\nDashboard", (0.68, 0.18)),
        ("Benchmark\nReport", (0.68, 0.05)),
    ]
    for text, (x, y) in blocks:
        ax.text(x, y, text, va='center', ha='center', bbox=dict(boxstyle='round,pad=0.4', facecolor='#dfeeff', edgecolor='#333'), fontsize=10)
    arrows = [
        ((0.18, 0.68), (0.3, 0.68)),
        ((0.52, 0.68), (0.62, 0.68)),
        ((0.2, 0.56), (0.2, 0.49)),
        ((0.52, 0.56), (0.52, 0.49)),
        ((0.78, 0.56), (0.78, 0.49)),
        ((0.52, 0.42), (0.52, 0.28)),
        ((0.78, 0.39), (0.78, 0.28)),
        ((0.52, 0.18), (0.52, 0.12)),
    ]
    for start, end in arrows:
        ax.annotate('', xy=end, xytext=start, arrowprops=dict(arrowstyle='->', lw=1.2, color='#2f3b52'))
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def create_performance_chart(csv_path: str, output_path: str):
    import pandas as pd
    data = pd.read_csv(csv_path)
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(data))
    values = data['median_latency_ms'].tolist()
    labels = [f"{row['database']}\n{row['query']}" for _, row in data.iterrows()]
    ax.bar(x, values, color=['#4f81bd', '#c0504d', '#9bbb59', '#8064a2', '#4bacc6', '#f79646', '#ff0000', '#00b050', '#7f7f7f'])
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=25, ha='right')
    ax.set_ylabel('Median latency (ms)')
    ax.set_title('Threat Intelligence Benchmark Comparison')
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
