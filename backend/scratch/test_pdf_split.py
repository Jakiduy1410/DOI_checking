from core.document_converter import convert_to_md
from core.pdf_preprocessing import get_references

file_path = "temporary/QlanticjournalofSocialSciences_25June2024.pdf"
md_content = convert_to_md(file_path)
refs, fmt = get_references(md_content, "Qlantic")

print(f"Format: {fmt}")
print(f"Total references: {len(refs)}")
for i, r in enumerate(refs[:10]):
    print(f"{i+1}: {r[:100]}...")

# Check for the specific merged case
found_merged = False
for r in refs:
    if "Damon, W." in r and "Foot, H. C." in r:
        found_merged = True
        print(f"\n[ERROR] Merged ref found: {r}")

if not found_merged:
    print("\n[SUCCESS] Damon and Foot are split correctly!")
