import os
import subprocess
from PIL import Image, ImageDraw

def create_app_icon():
    # Base size for full-resolution canvas
    size = 1024
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # 1. Background Squircle (macOS Squircle shape)
    # Background gradient fill (Deep Dark Gray / Indigo aesthetic)
    bg_color = (25, 28, 36, 255)
    border_radius = 224  # Standard macOS squircle radius ratio at 1024px

    # Draw rounded background
    draw.rounded_rectangle(
        [(96, 96), (size - 96, size - 96)],
        radius=border_radius,
        fill=bg_color,
        outline=(255, 255, 255, 30),
        width=3
    )

    # 2. Render Stylized Audio Waveform (representing Whisper STT)
    # Bar configurations
    heights = [120, 220, 380, 520, 320, 460, 240, 140]
    bar_width = 36
    gap = 28
    total_width = len(heights) * bar_width + (len(heights) - 1) * gap
    start_x = (size - total_width) // 2
    center_y = size // 2

    # Draw colorful waveform bars
    colors = [
        (99, 102, 241),   # Indigo
        (139, 92, 246),   # Violet
        (168, 85, 247),   # Purple
        (236, 72, 153),   # Pink
        (244, 63, 94),    # Rose
        (168, 85, 247),   # Purple
        (139, 92, 246),   # Violet
        (99, 102, 241)    # Indigo
    ]

    for i, h in enumerate(heights):
        x0 = start_x + i * (bar_width + gap)
        y0 = center_y - (h // 2)
        x1 = x0 + bar_width
        y1 = center_y + (h // 2)

        draw.rounded_rectangle(
            [(x0, y0), (x1, y1)],
            radius=bar_width // 2,
            fill=colors[i]
        )

    # 3. Save icons to iconset folder for macOS compilation
    iconset_dir = "AppIcon.iconset"
    os.makedirs(iconset_dir, exist_ok=True)

    sizes = [16, 32, 128, 256, 512]
    for s in sizes:
        # Standard @1x
        resized = image.resize((s, s), Image.Resampling.LANCZOS)
        resized.save(f"{iconset_dir}/icon_{s}x{s}.png")

        # Retina @2x
        resized_2x = image.resize((s * 2, s * 2), Image.Resampling.LANCZOS)
        resized_2x.save(f"{iconset_dir}/icon_{s}x{s}@2x.png")

    # 4. Convert iconset into macOS .icns file using native iconutil
    subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", "AppIcon.icns"])
    print("Successfully generated AppIcon.icns!")

if __name__ == "__main__":
    create_app_icon()