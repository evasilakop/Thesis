import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

def parse_summary_xml(filename):
    """Parse a SUMO summary XML file and return time + meanWaitingTime arrays."""
    times, waiting_times = [], []
    tree = ET.parse(filename)
    root = tree.getroot()
    for step in root.findall("step"):
        t = float(step.get("time"))
        w = float(step.get("meanWaitingTime"))
        times.append(t)
        waiting_times.append(w)
    return times, waiting_times

# === CONFIGURATION ===
files = [
    r"C:\Users\User\Documents\GitHub\Thesis\src\evaluation\2025-09-25-13-02-54\my_tls_5x_complete_no-noise\mine_5x_summary.xml",
    r"C:\Users\User\Documents\GitHub\Thesis\src\evaluation\2025-09-25-13-02-54\stadard_tls_5x_complete_no-noise\std_5x_summary.xml"
]

labels = [
    "Προτεινόμενο σύστημα",
    "Χρονοπρογραμματισμένοι σηματοδότες"
]

output_file = r"C:\Users\User\Desktop\waiting_time.png"

# === PLOTTING ===
plt.figure(figsize=(8,5))

for filename, label in zip(files, labels):
    times, waiting_times = parse_summary_xml(filename)
    plt.plot(times, waiting_times, label=label)

plt.xlabel("Χρόνος (s)")
plt.ylabel("Μέσος χρόνος αναμονής (s)")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.show()
