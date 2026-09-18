import numpy as np
import cv2     
import os
import csv

# === Canvas and Border ===
width, height = 3840, 2160
border_thickness = 174
border_color = (72, 72, 72)
target = np.full((height, width, 3), border_color, dtype=np.uint8)
rectangle_records = []

def draw_commanded_rectangle(x1, y1, x2, y2, color):
    cv2.rectangle(target, (x1, y1), (x2, y2), color, -1)
    rectangle_records.append((
        (x1 + x2) // 2,
        (y1 + y2) // 2,
        color[2],
        color[1],
        color[0],
    ))

# === Active Area ===
active_x = border_thickness
active_y = border_thickness
active_width = width - 2 * border_thickness  # 3492
active_height = height - 2 * border_thickness  # 1812

# === Checkerboard Border ===
checker_size = border_thickness
checker_colors = [(0, 0, 0), (255, 255, 255)]

def draw_checkerboard_rect(x_start, y_start, x_end, y_end, origin_x, origin_y):
    for y in range(y_start, y_end, checker_size):
        for x in range(x_start, x_end, checker_size):
            color = checker_colors[
                ((x - origin_x) // checker_size + (y - origin_y) // checker_size) % 2
            ]
            x2 = min(x + checker_size, x_end)
            y2 = min(y + checker_size, y_end)
            cv2.rectangle(target, (x, y), (x2, y2), color, -1)

# Top border
draw_checkerboard_rect(0, 0, width, border_thickness, 0, 0)
# Bottom border
draw_checkerboard_rect(0, height - border_thickness, width, height, 0, 0)
# Left border
draw_checkerboard_rect(0, border_thickness, border_thickness, height - border_thickness, 0, 0)
# Right border (shifted by one checker size)
right_origin_x = width - border_thickness - checker_size
draw_checkerboard_rect(
    width - border_thickness,
    border_thickness,
    width,
    height - border_thickness,
    right_origin_x,
    0,
)

# Solid black corners to keep white crosses readable
corner_block = border_thickness
cv2.rectangle(target, (0, 0), (corner_block, corner_block), (0, 0, 0), -1)
cv2.rectangle(target, (width - corner_block, 0), (width, corner_block), (0, 0, 0), -1)
cv2.rectangle(target, (0, height - corner_block), (corner_block, height), (0, 0, 0), -1)
cv2.rectangle(target, (width - corner_block, height - corner_block), (width, height), (0, 0, 0), -1)

# === Bar Setup ===
bar_height = 300
zone_height = active_height // 6
bar_y_positions = [active_y + i * zone_height + (zone_height - bar_height) // 2 for i in range(6)]




# === Step Setup (shared by grayscale + repeating RGBW+Black bars) ===
step_count = 16
step_width = active_width // step_count
tablet_margin = (active_width - step_width * step_count) // 2

# === Bars 1-3: Red, Green, and Blue Color Steps ===
for bar_index in range(3):
    y1 = bar_y_positions[bar_index]
    y2 = y1 + bar_height
    for i in range(step_count):
        x1 = active_x + tablet_margin + i * step_width
        x2 = x1 + step_width
        value = i * 17
        color = [
            (0, 0, value),
            (0, value, 0),
            (value, 0, 0),
        ][bar_index]
        draw_commanded_rectangle(x1, y1, x2, y2, color)

# === Bar 5: Custom 16-Step Tablet ===
y1 = bar_y_positions[4]
y2 = y1 + bar_height
tablet_values = [
    255, 252, 249, 245, 242, 239, 236, 233,
    35, 28, 22, 16, 12, 8, 4, 0,
]
for i, value in enumerate(tablet_values):
    x1 = active_x + tablet_margin + i * step_width
    x2 = x1 + step_width
    draw_commanded_rectangle(x1, y1, x2, y2, (value, value, value))

# === Bar 6: Split White/Black ===
y1 = bar_y_positions[5]
y2 = y1 + bar_height
mid_x = active_x + active_width // 2
draw_commanded_rectangle(active_x, y1, mid_x, y2, (255, 255, 255))
draw_commanded_rectangle(mid_x, y1, active_x + active_width, y2, (0, 0, 0))

# === Bar 4: Grayscale Tablet (White to Black, 16 steps) ===
y1 = bar_y_positions[3]
y2 = y1 + bar_height

for i in range(step_count):
    val = 255 - i * 17
    x1 = active_x + tablet_margin + i * step_width
    x2 = x1 + step_width
    draw_commanded_rectangle(x1, y1, x2, y2, (val, val, val))
    # Draw step number (i+1) centered at the bottom of this step
    step_label = str(i + 1)
    font = cv2.FONT_HERSHEY_SIMPLEX
    # scale and thickness relative to bar height so it remains small but readable
    font_scale = max(0.6, bar_height / 300)
    thickness = max(1, bar_height // 150)
    (text_w, text_h), _ = cv2.getTextSize(step_label, font, font_scale, thickness)
    text_x = x1 + (step_width - text_w) // 2
    # baseline y: a small inset from the bottom of the bar
    text_y = y2 - int(bar_height * 0.06)
    # choose contrasting text color against the step background
    text_color = (0, 0, 0) if val > 128 else (255, 255, 255)
    cv2.putText(target, step_label, (text_x, text_y), font, font_scale, text_color, thickness, cv2.LINE_AA)

    # === Corner Crosses (Visible Inside Border) ===
cross_color = (255, 255, 255)
cross_thickness = max(1, border_thickness // 10)
cross_length = border_thickness

def draw_cross(x, y):
    # Horizontal line
    start_h = (x, y)
    end_h = (x + cross_length, y)
    cv2.line(target, start_h, end_h, cross_color, cross_thickness)

    # Vertical line (intersects horizontal at midpoint)
    mid_x = x + cross_length // 2
    start_v = (mid_x, y - cross_length // 2)
    end_v = (mid_x, y + cross_length // 2)
    cv2.line(target, start_v, end_v, cross_color, cross_thickness)

# Offset from edges to stay within border
offset = border_thickness // 4

# Top-left
draw_cross(0, offset + offset)

# Top-right
draw_cross(width - cross_length, offset + offset)

# Bottom-left
draw_cross(0, height - offset * 2)

# Bottom-right
draw_cross(width - cross_length, height - offset * 2)

# === Save as BMP ===
output_path = os.path.join(os.getcwd(), "uhd_targetRamps.bmp")
cv2.imwrite(output_path, target)
print(f"Saved to: {output_path}")

white_target = target.copy()
cv2.rectangle(
    white_target,
    (active_x, active_y),
    (active_x + active_width - 1, active_y + active_height - 1),
    (239, 239, 239),
    -1,
)

white_output_path = os.path.join(os.getcwd(), "uhd_targetRamps_white.bmp")
cv2.imwrite(white_output_path, white_target)
print(f"Saved to: {white_output_path}")

csv_path = os.path.join(os.getcwd(), "uhd_targetRamps.csv")
with open(csv_path, "w", newline="") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["index", "horizontal", "vertical", "R", "G", "B"])
    for index, record in enumerate(rectangle_records, start=1):
        writer.writerow([index, *record])
print(f"Saved to: {csv_path}")