#!/usr/bin/env python3
import argparse
import xml.etree.ElementTree as ET
from collections import Counter

def count_by_type(xml_file: str):
    """
    Parses the XML file and returns a Counter of vehicle types (vType).
    Uses iterparse to keep memory usage low.
    """
    counts = Counter()
    # iterparse fires an 'end' event whenever it finishes an element
    for event, elem in ET.iterparse(xml_file, events=('end',)):
        if elem.tag == 'tripinfo':
            vtype = elem.get('vType', 'UNKNOWN')
            counts[vtype] += 1
            elem.clear()  # drop the element to save memory
    return counts

def main():
    parser = argparse.ArgumentParser(
        description="Count vehicles per vType from a SUMO tripinfo XML."
    )
    parser.add_argument('xml', help="Path to tripinfo XML file")
    parser.add_argument(
        '-o', '--out', help="Optional CSV output (vType,count)", default=None
    )
    args = parser.parse_args()

    counts = count_by_type(args.xml)

    if args.out:
        with open(args.out, 'w') as fout:
            fout.write("vType,count\n")
            for vtype, cnt in counts.most_common():
                fout.write(f"{vtype},{cnt}\n")
        print(f"Wrote counts to {args.out}")
    else:
        print("Vehicle counts by type:")
        for vtype, cnt in counts.most_common():
            print(f"  {vtype:20s} : {cnt}")

if __name__ == '__main__':
    main()
