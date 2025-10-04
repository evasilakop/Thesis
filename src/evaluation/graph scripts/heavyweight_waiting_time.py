import xml.etree.ElementTree as ET
import statistics

def get_waiting_stats(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    heavy, light = [], []

    for trip in root.findall('tripinfo'):
        vtype = trip.get('vType', '').lower()
        wt = float(trip.get('waitingTime', 0.0))
        if 'truck' in vtype or 'bus' in vtype:
            heavy.append(wt)
        else:
            light.append(wt)

    def stats(lst):
        if not lst:
            return (0,0)
        return (statistics.mean(lst), statistics.pstdev(lst))

    avg_h, std_h = stats(heavy)
    avg_l, std_l = stats(light)
    ratio = (avg_h / avg_l) if avg_l > 0 else 0
    return avg_h, std_h, avg_l, std_l, ratio

# Compare the two files
mine_stats = get_waiting_stats("mine_5x_tripInfos.xml")
std_stats  = get_waiting_stats("std_5x_tripinfos.xml")

# Print results
print("Proposed:", mine_stats)
print("Standard :", std_stats)

# Write LaTeX table
with open("waiting_comparison.tex", "w", encoding="utf-8") as f:
    f.write(r"""\begin{table}[h]
\centering
\begin{tabular}{l|cc|cc|c}
\toprule
Σενάριο & \multicolumn{2}{c|}{Βαρέα Οχήματα} & \multicolumn{2}{c|}{Λοιπά Οχήματα} & Λόγος Βαρέων/Λοιπών \\
 & Μέσος [s] & Τυπ. Απόκλ. [s] & Μέσος [s] & Τυπ. Απόκλ. [s] &  \\
\midrule
Mine & %.2f & %.2f & %.2f & %.2f & %.2f \\
Standard & %.2f & %.2f & %.2f & %.2f & %.2f \\
\bottomrule
\end{tabular}
\caption{Σύγκριση μέσου χρόνου αναμονής βαρέων και λοιπών οχημάτων μεταξύ προτεινόμενου και τυπικού σεναρίου.}
\end{table}
""" % (mine_stats[0], mine_stats[1], mine_stats[2], mine_stats[3], mine_stats[4],
       std_stats[0], std_stats[1], std_stats[2], std_stats[3], std_stats[4]))
