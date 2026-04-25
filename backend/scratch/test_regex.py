import re

text = "Damon, W., & Phelps, E. (1989). Critical distinctions among three approaches to peer education. International Journal of Educational Research, 13 (1), 9-19. https://doi.org/10.1016/08830355(89)90013-XFoot, H. C., Morgan, M. J., & Shute, R. H. (1990). Children helping children."

# Logic from pdf_preprocessing.py
pattern = r'\n(?=[A-Z][a-z])|(?<=[.\d/X])\s*(?=[A-Z][a-z]+,\s+[A-Z]\.)|(?<=[.\d/X])\s*(?=[A-Z][a-z]+\s+[A-Z]\.)'
parts = re.split(pattern, text)

print(f"Parts: {len(parts)}")
for i, p in enumerate(parts):
    print(f"{i+1}: {p}")
