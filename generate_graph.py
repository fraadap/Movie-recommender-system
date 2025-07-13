import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

# Dati
labels = [
    'Single User', 'Light Small', 'Light', 'Low',
    'Moderate', 'Increased', 'Medium-High', 'High', 'Peak'
]
values = [1, 3, 5, 9, 16, 23, 34, 47, 61]

# Colormap: da freddo a caldo (cool → warm)
cmap = cm.get_cmap('turbo', len(values))  # oppure 'plasma', 'turbo', 'RdYlBu_r' per alternative
colors = [cmap(i) for i in range(len(values))]

# Creazione del grafico
plt.figure(figsize=(10, 6))
bars = plt.bar(labels, values, color=colors)
plt.xlabel('Test types')
plt.ylabel('Maximum concurrent executions')
plt.xticks(rotation=45, ha='right')

# Etichette sopra ogni barra
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 1, int(yval), ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.show()
