from PIL import Image
from pathlib import Path

# Input image
input_file = "Arcade - Pac-Man - Miscellaneous - Maze Parts.png"

# Sprite sheet location in the original image
SHEET_X = 225
SHEET_Y = 0

SPRITE_SIZE = 8
COLS = 16
ROWS = 9

# Output directory
output_dir = Path("assets")
output_dir.mkdir(exist_ok=True)

image = Image.open(input_file).convert("RGBA")

for row in [3, 4, 5]:
    for col in range(COLS):
        left = SHEET_X + col * (SPRITE_SIZE +1) 
        top = SHEET_Y + row * (SPRITE_SIZE +1)

        box = (
            left,
            top,
            left + SPRITE_SIZE,
            top + SPRITE_SIZE,
        )

        sprite = image.crop(box)

        filename = output_dir / f"sprite_{row-3}_{col}.png"
        sprite.save(filename)

        print(f"Saved {filename}")

# sprit_coord = [(3,i) for i in range(14)]
# sprit_coord = sprit_coord + [(4,j) for j in range(12, 16)]
# sprit_coord = sprit_coord + [(5,k) for k in range(0, 2)]
# sprit_coord = sprit_coord + [(5,k) for k in range(12, 16)]

# for row, col in sprit_coord:
#         left = SHEET_X + col * (SPRITE_SIZE +1) 
#         top = SHEET_Y + row * (SPRITE_SIZE +1)

#         box = (
#             left,
#             top,
#             left + SPRITE_SIZE,
#             top + SPRITE_SIZE,
#         )

#         sprite = image.crop(box)

#         filename = output_dir / f"sprite_{row-3}_{col}.png"
#         sprite.save(filename)

#         print(f'"{filename}"')



print("Done!")