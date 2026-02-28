import os

base_path = r"c:\Users\sivan\Learning\Code\sparkantrigravity\PrincipleDataArchitect"

# The 7 files per concept folder
FILE_TEMPLATES = [
    ("01_Concept_Overview.md", "Concept Overview",
     "What it is, why a Principal Architect must know it, and where it fits in the bigger picture."),
    ("02_How_It_Works.md", "How It Works — Deep Internals",
     "Technical mechanics, algorithms, data structures, Mermaid diagrams, step-by-step walkthroughs."),
    ("03_Hands_On_Examples.md", "Hands-On Examples",
     "Real SQL/Python/Spark code, configuration examples, before-vs-after comparisons, exercises."),
    ("04_Real_World_Scenarios.md", "FAANG War Stories & Real-World Scenarios",
     "How Netflix, Amazon, LinkedIn, Uber, and Microsoft use this. Scale numbers, production incidents, lessons learned."),
    ("05_Pitfalls_And_Anti_Patterns.md", "Common Pitfalls & Anti-Patterns",
     "The top mistakes people make, why they are dangerous, and how to detect and fix them."),
    ("06_Interview_Angle.md", "Interview Angle",
     "How this topic appears in Principal-level interviews. Sample questions, strong answer frameworks, what interviewers are really testing."),
    ("07_Further_Reading.md", "Further Reading & References",
     "Papers, books, blog posts, conference talks, official documentation, and cross-references to related concepts in this curriculum."),
]

created_count = 0
skipped_count = 0

print("Generating 7 markdown files per L3 concept folder...")

for l1 in sorted(os.listdir(base_path)):
    l1_path = os.path.join(base_path, l1)
    if not os.path.isdir(l1_path) or l1.startswith('.') or l1.endswith('.py') or l1 == "README.md":
        continue

    for l2 in sorted(os.listdir(l1_path)):
        l2_path = os.path.join(l1_path, l2)
        if not os.path.isdir(l2_path):
            continue

        for l3 in sorted(os.listdir(l2_path)):
            l3_path = os.path.join(l2_path, l3)
            if not os.path.isdir(l3_path):
                continue

            # This is a Level 3 concept folder — generate 7 files
            concept_name = l3.replace('_', ' ')
            # Remove leading number prefix for display
            if concept_name[:3].strip().isdigit():
                concept_name = concept_name[3:].strip()

            for filename, section_title, section_desc in FILE_TEMPLATES:
                filepath = os.path.join(l3_path, filename)
                if not os.path.exists(filepath):
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(f"# {concept_name} — {section_title}\n\n")
                        f.write(f"> {section_desc}\n\n")
                        f.write(f"*Content to be developed at FAANG Principal-level depth.*\n")
                    created_count += 1
                else:
                    skipped_count += 1

print(f"\nDone!")
print(f"  Created: {created_count} new markdown files")
print(f"  Skipped: {skipped_count} (already existed)")
print(f"  Total L3 concept folders: {created_count // 7 + skipped_count // 7} (approx)")
print(f"  Files per folder: 7")
print(f"  Total markdown files: ~{created_count + skipped_count}")
