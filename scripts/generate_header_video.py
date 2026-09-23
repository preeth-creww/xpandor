#!/usr/bin/env python3
"""
XPANDOR Architectural Cinematic Header Video Generator
Generates a 1080p 30fps architectural wireframe motion sequence
matching the exact 10-scene storyboard and real-life Indiranagar photo.
"""

import sys
import os
import math
import subprocess
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------------------------------------------------
# Video Specifications
# ---------------------------------------------------------
WIDTH = 1920
HEIGHT = 1080
FPS = 30

# Scene Frame Allocation (Total: 1260 frames = 42.0 seconds)
TOTAL_FRAMES = 1260

# ---------------------------------------------------------
# Brand Color Palette (Strictly 2 Primary Brand Colors)
# ---------------------------------------------------------
COLOR_BG = (5, 6, 10)               # Midnight Blueprint Space #05060A
COLOR_BG_CARD = (11, 14, 20)         # Dark Slate Card #0B0E14
COLOR_GRID = (18, 24, 34)            # Blueprint Grid Lines
COLOR_GRID_BRIGHT = (30, 40, 56)     # Grid Major Accents

COLOR_BRASS = (197, 168, 128)        # Champagne Brass Primary #C5A880
COLOR_BRASS_LIGHT = (229, 197, 153)  # Champagne Brass Glow #E5C599
COLOR_BRASS_DIM = (110, 95, 75)      # Muted Brass #6E5F4B
COLOR_BRASS_DARK = (45, 38, 28)      # Deep Brass Shadow #2D261C

COLOR_WHITE = (245, 245, 247)        # Architectural Pure White
COLOR_MUTED = (120, 132, 148)        # Dimension & Telemetry Text #788494
COLOR_CYAN_DIM = (40, 60, 80)        # Subdued Blueprint Tone

# ---------------------------------------------------------
# Load Fonts & Assets
# ---------------------------------------------------------
FONT_PATH = "/System/Library/Fonts/Avenir Next.ttc"
LOGO_PATH = "public/images/logo.png"

def get_font(size, style="regular"):
    index_map = {
        "bold": 0,
        "demi": 2,
        "medium": 5,
        "regular": 7,
        "heavy": 8,
        "light": 10
    }
    idx = index_map.get(style, 7)
    try:
        return ImageFont.truetype(FONT_PATH, size, index=idx)
    except:
        return ImageFont.load_default()

# Preload standard fonts
FONT_HERO = get_font(72, "heavy")
FONT_H1 = get_font(52, "bold")
FONT_H2 = get_font(34, "demi")
FONT_TITLE = get_font(24, "bold")
FONT_BODY = get_font(18, "medium")
FONT_MONO = get_font(14, "demi")
FONT_TINY = get_font(11, "medium")

# Preload & Tint Logo in Brand Champagne Brass
logo_brass = None
if os.path.exists(LOGO_PATH):
    try:
        orig = Image.open(LOGO_PATH).convert("RGBA")
        arr = np.array(orig)
        mask = arr[:, :, 3] > 30
        # Tint non-transparent pixels to glowing Champagne Brass #E5C599
        arr[mask, 0] = COLOR_BRASS_LIGHT[0]
        arr[mask, 1] = COLOR_BRASS_LIGHT[1]
        arr[mask, 2] = COLOR_BRASS_LIGHT[2]
        logo_brass = Image.fromarray(arr)
    except Exception as e:
        print("Failed to process logo:", e)

# ---------------------------------------------------------
# Mathematical & Easing Helpers
# ---------------------------------------------------------
def clamp(v, min_v=0.0, max_v=1.0):
    return max(min_v, min(max_v, v))

def lerp(a, b, t):
    return a + (b - a) * t

def ease_in_out(t):
    t = clamp(t)
    return 3 * t**2 - 2 * t**3

def ease_out_cubic(t):
    t = clamp(t)
    return 1.0 - (1.0 - t)**3

def ease_out_quad(t):
    t = clamp(t)
    return 1.0 - (1.0 - t)**2

# ---------------------------------------------------------
# Drawing Primitive Helpers
# ---------------------------------------------------------
def draw_blueprint_grid(draw, w=WIDTH, h=HEIGHT, step=60):
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=COLOR_GRID, width=1)
    for y in range(0, h, step):
        draw.line([(0, y), (w, y)], fill=COLOR_GRID, width=1)
    
    # Registration ticks at intersections
    tick = 4
    for x in range(0, w, step * 3):
        for y in range(0, h, step * 3):
            draw.line([(x - tick, y), (x + tick, y)], fill=COLOR_GRID_BRIGHT, width=1)
            draw.line([(x, y - tick), (x, y + tick)], fill=COLOR_GRID_BRIGHT, width=1)

def draw_hud_header(draw, title, subtitle="", coords="12.9784° N, 77.6408° E", mode="[MODE: SURVEY]"):
    # Top Telemetry Bar
    draw.line([(60, 48), (WIDTH - 60, 48)], fill=COLOR_BRASS_DIM, width=1)
    
    # Left tag
    tag_str = "XPANDOR // SPECIFICATION"
    draw.text((60, 22), tag_str, font=FONT_MONO, fill=COLOR_BRASS)
    tag_bb = FONT_MONO.getbbox(tag_str)
    tag_w = tag_bb[2] - tag_bb[0]
    draw.text((60 + tag_w + 14, 22), "/", font=FONT_MONO, fill=COLOR_MUTED)
    draw.text((60 + tag_w + 28, 22), title.upper(), font=FONT_MONO, fill=COLOR_WHITE)
    
    # Right coordinate telemetry - dynamically measured
    mode_bbox = FONT_MONO.getbbox(mode)
    mode_w = mode_bbox[2] - mode_bbox[0]
    coords_bbox = FONT_MONO.getbbox(coords)
    coords_w = coords_bbox[2] - coords_bbox[0]
    
    mode_x = WIDTH - 60 - mode_w
    coords_x = mode_x - coords_w - 24
    
    draw.text((coords_x, 22), coords, font=FONT_MONO, fill=COLOR_BRASS)
    draw.text((mode_x, 22), mode, font=FONT_MONO, fill=COLOR_MUTED)
    
    # Bottom Telemetry Bar
    draw.line([(60, HEIGHT - 48), (WIDTH - 60, HEIGHT - 48)], fill=COLOR_BRASS_DIM, width=1)
    draw.text((60, HEIGHT - 36), "FOUNDER-GOVERNED INTEGRATED EXPANSION", font=FONT_TINY, fill=COLOR_MUTED)
    bot_str = "CAD ELEVATION • LEVEL 04"
    bb = FONT_TINY.getbbox(bot_str)
    bw = bb[2] - bb[0]
    draw.text((WIDTH - 60 - bw, HEIGHT - 36), bot_str, font=FONT_TINY, fill=COLOR_BRASS)

def draw_reticle(draw, x, y, size=28, color=COLOR_BRASS, label=""):
    s = size
    gap = 8
    # 4 corner brackets
    draw.line([(x - s, y - s), (x - s + gap, y - s)], fill=color, width=2)
    draw.line([(x - s, y - s), (x - s, y - s + gap)], fill=color, width=2)
    
    draw.line([(x + s, y - s), (x + s - gap, y - s)], fill=color, width=2)
    draw.line([(x + s, y - s), (x + s, y - s + gap)], fill=color, width=2)
    
    draw.line([(x - s, y + s), (x - s + gap, y + s)], fill=color, width=2)
    draw.line([(x - s, y + s), (x - s, y + s - gap)], fill=color, width=2)
    
    draw.line([(x + s, y + s), (x + s - gap, y + s)], fill=color, width=2)
    draw.line([(x + s, y + s), (x + s, y + s - gap)], fill=color, width=2)
    
    draw.line([(x - 4, y), (x + 4, y)], fill=color, width=1)
    draw.line([(x, y - 4), (x, y + 4)], fill=color, width=1)
    
    if label:
        draw.text((x + s + 12, y - 8), label, font=FONT_MONO, fill=color)

# ---------------------------------------------------------
# Scene 1: 3D Wireframe Globe
# ---------------------------------------------------------
INDIA_CONTOUR = [
    (34.0, 74.0), (32.0, 77.0), (30.0, 80.0), (28.0, 84.0), (27.0, 88.0),
    (26.0, 92.0), (24.0, 93.0), (22.0, 89.0), (20.0, 86.0), (17.5, 83.0),
    (15.0, 80.0), (13.0, 80.2), (10.0, 79.8), (8.1, 77.5), (9.5, 76.3),
    (12.0, 75.0), (15.0, 73.8), (19.0, 72.8), (21.5, 72.5), (23.0, 68.5),
    (24.5, 68.8), (27.0, 71.0), (31.0, 74.0), (34.0, 74.0)
]

EURASIA_AFRICA = [
    (36.0, -5.0), (37.0, 10.0), (32.0, 25.0), (30.0, 32.0), (12.0, 44.0),
    (0.0, 42.0), (-12.0, 40.0), (-25.0, 32.0), (-34.5, 20.0), (-30.0, 16.0),
    (-10.0, 12.0), (5.0, 9.0), (5.0, -2.0), (15.0, -17.0), (30.0, -10.0), (36.0, -5.0),
    (36.0, -5.0), (43.0, -9.0), (48.0, -4.0), (55.0, 8.0), (60.0, 25.0),
    (68.0, 50.0), (70.0, 90.0), (72.0, 130.0), (65.0, 170.0), (55.0, 140.0),
    (40.0, 120.0), (25.0, 105.0), (15.0, 100.0), (22.0, 90.0)
]

AMERICAS = [
    (70.0, -140.0), (55.0, -130.0), (40.0, -124.0), (25.0, -110.0), (15.0, -92.0),
    (8.0, -80.0), (-5.0, -80.0), (-20.0, -70.0), (-40.0, -72.0), (-55.0, -68.0),
    (-45.0, -65.0), (-25.0, -45.0), (-5.0, -35.0), (5.0, -50.0), (10.0, -75.0),
    (30.0, -80.0), (45.0, -65.0), (60.0, -60.0), (70.0, -140.0)
]

AUSTRALIA = [
    (-15.0, 130.0), (-12.0, 135.0), (-15.0, 145.0), (-25.0, 152.0), (-38.0, 148.0),
    (-35.0, 137.0), (-32.0, 125.0), (-22.0, 114.0), (-15.0, 130.0)
]

def project_3d_globe(lat_deg, lon_deg, rot_y_rad, tilt_x_rad=0.38, radius=320, cx=960, cy=540):
    phi = math.radians(lat_deg)
    lam = math.radians(lon_deg) + rot_y_rad
    
    x = math.cos(phi) * math.sin(lam)
    y = -math.sin(phi)
    z = math.cos(phi) * math.cos(lam)
    
    y_tilted = y * math.cos(tilt_x_rad) - z * math.sin(tilt_x_rad)
    z_tilted = y * math.sin(tilt_x_rad) + z * math.cos(tilt_x_rad)
    
    screen_x = cx + x * radius
    screen_y = cy + y_tilted * radius
    return screen_x, screen_y, z_tilted

def render_scene_1_globe(draw, frame_idx):
    t = frame_idx / 150.0
    
    target_rot = -math.radians(77.5)
    start_rot = target_rot + math.pi * 3.5
    curr_rot = lerp(start_rot, target_rot, ease_out_cubic(t))
    
    cx, cy = 960, 540
    R = 320
    
    draw_hud_header(draw, "GEODETIC SATELLITE INITIALIZATION", coords="GLOBAL TERRAIN SCAN // WGS-84", mode="[MODE: GLOBAL]")
    
    # Outer Glow Ring
    draw.ellipse([(cx - R - 6, cy - R - 6), (cx + R + 6, cy + R + 6)], outline=COLOR_BRASS_DARK, width=2)
    draw.ellipse([(cx - R, cy - R), (cx + R, cy + R)], outline=COLOR_BRASS, width=2)
    
    # Latitude lines
    for lat in range(-75, 80, 15):
        pts_front = []
        pts_back = []
        for lon in range(0, 365, 5):
            sx, sy, z = project_3d_globe(lat, lon, curr_rot, radius=R, cx=cx, cy=cy)
            if z >= 0:
                pts_front.append((sx, sy))
            else:
                pts_back.append((sx, sy))
        if len(pts_front) > 1:
            draw.line(pts_front, fill=COLOR_BRASS_DIM, width=1)
        if len(pts_back) > 1:
            draw.line(pts_back, fill=COLOR_GRID, width=1)
            
    # Longitude meridians
    for lon in range(0, 360, 15):
        pts_front = []
        for lat in range(-90, 95, 5):
            sx, sy, z = project_3d_globe(lat, lon, curr_rot, radius=R, cx=cx, cy=cy)
            if z >= 0:
                pts_front.append((sx, sy))
        if len(pts_front) > 1:
            draw.line(pts_front, fill=COLOR_BRASS_DIM, width=1)

    # Continents
    for contour, is_india in [(EURASIA_AFRICA, False), (AMERICAS, False), (AUSTRALIA, False), (INDIA_CONTOUR, True)]:
        screen_pts = []
        for lat, lon in contour:
            sx, sy, z = project_3d_globe(lat, lon, curr_rot, radius=R, cx=cx, cy=cy)
            if z >= -0.05:
                screen_pts.append((sx, sy))
            else:
                if len(screen_pts) > 1:
                    col = COLOR_BRASS_LIGHT if is_india else COLOR_MUTED
                    draw.line(screen_pts, fill=col, width=2 if is_india else 1)
                screen_pts = []
        if len(screen_pts) > 1:
            col = COLOR_BRASS_LIGHT if is_india else COLOR_MUTED
            draw.line(screen_pts, fill=col, width=3 if is_india else 1)
            
    # Target reticle locks onto India
    if t > 0.6:
        reticle_alpha = ease_out_quad((t - 0.6) / 0.4)
        sx, sy, _ = project_3d_globe(15.0, 77.5, curr_rot, radius=R, cx=cx, cy=cy)
        draw_reticle(draw, sx, sy, size=int(25 + 15 * (1.0 - reticle_alpha)), color=COLOR_BRASS_LIGHT, label="TARGET: INDIAN SUBCONTINENT")
        
        draw.rectangle([(cx - 180, cy + R + 30), (cx + 180, cy + R + 75)], fill=COLOR_BG_CARD, outline=COLOR_BRASS, width=1)
        draw.text((cx - 160, cy + R + 40), "ALIGNING PENINSULAR CORRIDOR", font=FONT_MONO, fill=COLOR_WHITE)
        draw.text((cx - 160, cy + R + 58), "LAT: 12.9716° N  •  LON: 77.5946° E", font=FONT_TINY, fill=COLOR_BRASS)

# ---------------------------------------------------------
# Scene 2: Zoom into South India & Regional Cities
# ---------------------------------------------------------
SOUTH_INDIA_POLY = [
    (21.0, 72.8), (19.0, 72.8), (17.5, 73.2), (15.5, 73.8), (14.0, 74.4),
    (12.5, 75.0), (11.0, 75.8), (9.5, 76.3), (8.1, 77.5), (8.8, 78.1),
    (10.0, 79.8), (11.8, 79.9), (13.1, 80.3), (14.5, 80.1), (16.0, 80.8),
    (17.7, 83.3), (19.0, 84.8), (19.5, 82.0), (18.0, 79.0), (17.0, 77.0),
    (16.0, 75.0), (18.5, 74.0), (21.0, 72.8)
]

CITIES_SOUTH = [
    ("HYDERABAD", 17.3850, 78.4867, "TELANGANA REGIONAL HUB"),
    ("CHENNAI", 13.0827, 80.2707, "COROMANDEL COMMERCIAL BELT"),
    ("KOCHI", 9.9312, 76.2673, "KERALA MARITIME BELT"),
    ("BENGALURU", 12.9716, 77.5946, "HEADQUARTERS // PRIMARY FOCUS")
]

def map_south_india_coord(lat, lon, zoom=1.0, center_lat=13.0, center_lon=77.6):
    dx = (lon - center_lon) * 110.0 * zoom
    dy = -(lat - center_lat) * 110.0 * zoom
    return 960 + dx, 540 + dy

def render_scene_2_south_india(draw, frame_idx):
    t = (frame_idx - 150) / 130.0
    draw_hud_header(draw, "REGIONAL MARKET SCOPING", coords="SOUTH INDIAN PENINSULA", mode="[MODE: REGIONAL SCAN]")
    
    zoom = lerp(0.8, 2.2, ease_in_out(t))
    center_lat = lerp(14.5, 13.0, ease_out_quad(t))
    center_lon = lerp(78.5, 77.6, ease_out_quad(t))
    
    pts = [map_south_india_coord(lat, lon, zoom, center_lat, center_lon) for lat, lon in SOUTH_INDIA_POLY]
    draw.polygon(pts, outline=COLOR_BRASS_LIGHT, fill=COLOR_BG_CARD)
    
    # Internal contours
    for offset in [0.85, 0.70, 0.55]:
        c_pts = []
        for x, y in pts:
            cx, cy = 960, 540
            c_pts.append((cx + (x - cx) * offset, cy + (y - cy) * offset))
        draw.polygon(c_pts, outline=COLOR_GRID_BRIGHT)
        
    for name, lat, lon, sub in CITIES_SOUTH:
        cx, cy = map_south_india_coord(lat, lon, zoom, center_lat, center_lon)
        is_blr = (name == "BENGALURU")
        pulse_r = (frame_idx * 2) % 35
        
        if is_blr:
            draw.ellipse([(cx - pulse_r, cy - pulse_r), (cx + pulse_r, cy + pulse_r)], outline=COLOR_BRASS_LIGHT, width=2)
            draw.ellipse([(cx - 8, cy - 8), (cx + 8, cy + 8)], fill=COLOR_BRASS_LIGHT)
            draw_reticle(draw, cx, cy, size=24, color=COLOR_BRASS_LIGHT)
            
            draw.rectangle([(cx + 35, cy - 25), (cx + 340, cy + 35)], fill=COLOR_BG, outline=COLOR_BRASS, width=1)
            draw.text((cx + 45, cy - 18), "BENGALURU (PRIMARY CLUSTER)", font=FONT_TITLE, fill=COLOR_WHITE)
            draw.text((cx + 45, cy + 10), "COMMERCIAL CORRIDORS: 100FT / CMH RD", font=FONT_TINY, fill=COLOR_BRASS)
        else:
            draw.ellipse([(cx - 4, cy - 4), (cx + 4, cy + 4)], fill=COLOR_BRASS_DIM)
            draw.ellipse([(cx - pulse_r//2, cy - pulse_r//2), (cx + pulse_r//2, cy + pulse_r//2)], outline=COLOR_BRASS_DIM, width=1)
            draw.text((cx + 12, cy - 8), name, font=FONT_MONO, fill=COLOR_MUTED)

# ---------------------------------------------------------
# Scene 3: Bengaluru Outline & Indiranagar Catchment Selection
# ---------------------------------------------------------
BLR_DISTRICT_POLY = [
    (13.15, 77.55), (13.12, 77.66), (13.05, 77.74), (12.96, 77.78),
    (12.85, 77.72), (12.80, 77.62), (12.83, 77.50), (12.92, 77.45),
    (13.02, 77.46), (13.10, 77.50), (13.15, 77.55)
]

INDIRANAGAR_POLY = [
    (12.986, 77.632), (12.985, 77.649), (12.970, 77.652),
    (12.968, 77.635), (12.986, 77.632)
]

def render_scene_3_bengaluru(draw, frame_idx):
    t = (frame_idx - 280) / 120.0
    draw_hud_header(draw, "METROPOLITAN CATCHMENT MAPPING", coords="BENGALURU URBAN • ZONE 08", mode="[MODE: CATCHMENT]")
    
    zoom = lerp(45.0, 160.0, ease_in_out(t))
    center_lat = lerp(12.9716, 12.9784, ease_in_out(t))
    center_lon = lerp(77.5946, 77.6408, ease_in_out(t))
    
    def blr_proj(lat, lon):
        x = 960 + (lon - center_lon) * 12000.0 * (zoom / 45.0)
        y = 540 - (lat - center_lat) * 12000.0 * (zoom / 45.0)
        return x, y
        
    city_pts = [blr_proj(lat, lon) for lat, lon in BLR_DISTRICT_POLY]
    draw.polygon(city_pts, outline=COLOR_BRASS_DIM, fill=COLOR_BG_CARD)
    
    arterials = [
        [(13.04, 77.55), (13.02, 77.65), (12.98, 77.69), (12.92, 77.68), (12.88, 77.60)],
        [(12.975, 77.600), (12.976, 77.620), (12.978, 77.641), (12.980, 77.660)],
        [(12.990, 77.641), (12.978, 77.641), (12.960, 77.641)]
    ]
    for road in arterials:
        road_pts = [blr_proj(lat, lon) for lat, lon in road]
        draw.line(road_pts, fill=COLOR_GRID_BRIGHT, width=3)
        
    in_pts = [blr_proj(lat, lon) for lat, lon in INDIRANAGAR_POLY]
    draw.polygon(in_pts, outline=COLOR_BRASS_LIGHT, fill=(35, 30, 22))
    
    min_y = int(min(p[1] for p in in_pts))
    max_y = int(max(p[1] for p in in_pts))
    for hy in range(min_y, max_y, 16):
        draw.line([(0, hy), (WIDTH, hy)], fill=COLOR_BRASS_DARK, width=1)
    draw.polygon(in_pts, outline=COLOR_BRASS_LIGHT, width=2)
    
    ix, iy = blr_proj(12.9784, 77.6408)
    draw_reticle(draw, ix, iy, size=28, color=COLOR_BRASS_LIGHT)
    
    draw.rectangle([(WIDTH - 460, 100), (WIDTH - 80, 260)], fill=COLOR_BG, outline=COLOR_BRASS, width=1)
    draw.text((WIDTH - 440, 115), "TARGET IDENTIFIED", font=FONT_TITLE, fill=COLOR_BRASS)
    draw.text((WIDTH - 440, 150), "ZONE: INDIRANAGAR (CATCHMENT 08)", font=FONT_BODY, fill=COLOR_WHITE)
    draw.text((WIDTH - 440, 180), "TRANSIT: METRO PURPLE LINE (CMH RD)", font=FONT_MONO, fill=COLOR_MUTED)
    draw.text((WIDTH - 440, 205), "FOOTFALL INDEX: 94.8 / 100 (TIER-1)", font=FONT_MONO, fill=COLOR_MUTED)
    draw.text((WIDTH - 440, 230), "RETAIL VACANCY: CONSTRAINED / ULTRA-PRIME", font=FONT_TINY, fill=COLOR_BRASS_LIGHT)

# ---------------------------------------------------------
# Scene 4: Indiranagar Real Map & Search Box Typing HUD
# ---------------------------------------------------------
# Well-spaced layout along CMH Road and 100 Feet Road
STORES_INDIRANAGAR = [
    # name, x, y, tag_y_offset, subtext
    ("POORVIKA MOBILES", 720, 500, -85, "CMH RD • TARGET ADJACENCY"),
    ("SANGEETHA MOBILES", 1180, 500, -85, "CMH RD • TARGET ADJACENCY"),
    ("SAMSUNG SMARTCAFE", 520, 500, 65, "CMH RD • REGIONAL SHOWROOM"),
    ("APPLE PREMIUM RESELLER", 1400, 680, 25, "100 FEET RD • HIGH STREET"),
    ("ONEPLUS EXPERIENCE STORE", 1400, 320, -75, "100 FEET RD • FLAGSHIP")
]

def render_scene_4_indiranagar_search(draw, frame_idx):
    t = (frame_idx - 400) / 130.0
    draw_hud_header(draw, "COMPETITIVE CATCHMENT AUDIT", coords="CMH ROAD CORRIDOR • INDIRANAGAR", mode="[MODE: RETAIL GIS]")
    
    # 1. Real Street Grid Layout
    cmh_y = 500
    # CMH Road Boulevard
    draw.line([(0, cmh_y - 35), (WIDTH, cmh_y - 35)], fill=COLOR_GRID_BRIGHT, width=2)
    draw.line([(0, cmh_y + 35), (WIDTH, cmh_y + 35)], fill=COLOR_GRID_BRIGHT, width=2)
    draw.line([(0, cmh_y), (WIDTH, cmh_y)], fill=COLOR_BRASS_DARK, width=1)
    draw.text((80, cmh_y - 25), "CHINMAYA MISSION HOSPITAL (CMH) ROAD", font=FONT_MONO, fill=COLOR_MUTED)
    
    # 100 Feet Road Boulevard
    feet_x = 1400
    draw.line([(feet_x - 35, 0), (feet_x - 35, HEIGHT)], fill=COLOR_GRID_BRIGHT, width=2)
    draw.line([(feet_x + 35, 0), (feet_x + 35, HEIGHT)], fill=COLOR_GRID_BRIGHT, width=2)
    draw.text((feet_x - 30, 80), "100 FEET ROAD", font=FONT_MONO, fill=COLOR_MUTED)
    
    # Indiranagar Metro Viaduct & Station (Overhead CMH Road, well-spaced)
    station_x1, station_x2 = 880, 1060
    draw.rectangle([(station_x1, cmh_y - 18), (station_x2, cmh_y + 18)], fill=COLOR_BG_CARD, outline=COLOR_BRASS_LIGHT, width=2)
    draw.text((station_x1 + 12, cmh_y - 7), "INDIRANAGAR METRO STATION", font=FONT_MONO, fill=COLOR_WHITE)
    
    # Secondary Cross Streets
    for sx in [350, 600, 1220, 1680]:
        draw.line([(sx, 120), (sx, HEIGHT - 120)], fill=COLOR_GRID, width=1)
        
    # 2. Bottom Search Box Sliding Up & Typing Animation
    search_query = "mobile phone stores"
    typing_progress = clamp((frame_idx - 415) / 55.0)
    chars_to_show = int(len(search_query) * typing_progress)
    typed_text = search_query[:chars_to_show]
    cursor = "|" if (frame_idx // 12) % 2 == 0 else ""
    
    sb_w, sb_h = 720, 64
    sb_x = (WIDTH - sb_w) // 2
    sb_y = HEIGHT - 135
    
    draw.rectangle([(sb_x, sb_y), (sb_x + sb_w, sb_y + sb_h)], fill=(12, 16, 24), outline=COLOR_BRASS, width=2)
    
    # Search Icon (Magnifying Glass in Brass)
    ix, iy = sb_x + 28, sb_y + 32
    draw.ellipse([(ix - 10, iy - 10), (ix + 6, iy + 6)], outline=COLOR_BRASS_LIGHT, width=2)
    draw.line([(ix + 4, iy + 4), (ix + 14, iy + 14)], fill=COLOR_BRASS_LIGHT, width=2)
    
    draw.text((sb_x + 60, sb_y + 18), f"{typed_text}{cursor}", font=FONT_H2, fill=COLOR_WHITE)
    status_str = "[LOCATING COMPETITORS...]" if typing_progress < 1.0 else "[MATCHES IDENTIFIED: 5]"
    draw.text((sb_x + sb_w - 240, sb_y + 24), status_str, font=FONT_MONO, fill=COLOR_BRASS)
    
    # 3. Light up Mobile Stores once search completes
    if frame_idx >= 465:
        for name, sx, sy, tag_y_off, desc in STORES_INDIRANAGAR:
            pulse = (frame_idx * 3) % 25
            draw.ellipse([(sx - pulse, sy - pulse), (sx + pulse, sy + pulse)], outline=COLOR_BRASS, width=1)
            draw.ellipse([(sx - 6, sy - 6), (sx + 6, sy + 6)], fill=COLOR_BRASS_LIGHT)
            
            # Non-overlapping label banner with leader line
            box_y = sy + tag_y_off
            draw.line([(sx, sy), (sx, box_y + 18)], fill=COLOR_BRASS_DIM, width=1)
            draw.rectangle([(sx - 20, box_y), (sx + 240, box_y + 42)], fill=COLOR_BG, outline=COLOR_BRASS_DIM, width=1)
            draw.text((sx - 10, box_y + 5), name, font=FONT_MONO, fill=COLOR_WHITE)
            draw.text((sx - 10, box_y + 23), desc, font=FONT_TINY, fill=COLOR_BRASS_LIGHT)

# ---------------------------------------------------------
# Scene 5: Pencil Circling the Metro Cluster
# ---------------------------------------------------------
def render_scene_5_pencil_circle(draw, frame_idx):
    t = (frame_idx - 530) / 90.0
    draw_hud_header(draw, "MICRO-CATCHMENT SELECTION", coords="CMH RD METRO CLUSTER • INDIRANAGAR", mode="[MODE: TARGETING]")
    
    cmh_y = 540
    # Elevated Metro Track running overhead
    draw.rectangle([(120, cmh_y - 20), (WIDTH - 120, cmh_y + 20)], fill=COLOR_BG_CARD, outline=COLOR_BRASS, width=2)
    draw.text((WIDTH // 2 - 140, cmh_y - 8), "NAMMA METRO ELEVATED VIADUCT", font=FONT_MONO, fill=COLOR_BRASS_LIGHT)
    
    # Well-proportioned site plots along CMH Road
    # Left: Poorvika (X: 380 - 660)
    draw.rectangle([(380, cmh_y - 190), (660, cmh_y - 35)], outline=COLOR_MUTED, fill=COLOR_BG_CARD, width=1)
    draw.text((400, cmh_y - 140), "POORVIKA MOBILES", font=FONT_TITLE, fill=COLOR_WHITE)
    draw.text((400, cmh_y - 110), "+ OPPO SHOWROOM", font=FONT_MONO, fill=COLOR_BRASS)
    
    # Center: Panache Yamaha Building (X: 720 - 1180, width 460)
    draw.rectangle([(720, cmh_y - 210), (1180, cmh_y - 35)], outline=COLOR_BRASS_LIGHT, fill=(28, 24, 18), width=2)
    draw.text((745, cmh_y - 165), "YAMAHA BUILDING", font=FONT_H2, fill=COLOR_WHITE)
    draw.text((745, cmh_y - 120), "VACANT GROUND FLOOR: 2,400 SQ. FT.", font=FONT_MONO, fill=COLOR_BRASS_LIGHT)
    draw.text((745, cmh_y - 95), "PRIME LEASE OPPORTUNITY • TRANSIT CORRIDOR", font=FONT_TINY, fill=COLOR_WHITE)
    
    # Right: Sangeetha Mobiles (X: 1240 - 1520)
    draw.rectangle([(1240, cmh_y - 190), (1520, cmh_y - 35)], outline=COLOR_MUTED, fill=COLOR_BG_CARD, width=1)
    draw.text((1260, cmh_y - 140), "SANGEETHA MOBILES", font=FONT_TITLE, fill=COLOR_WHITE)
    draw.text((1260, cmh_y - 110), "RETAIL HUB", font=FONT_MONO, fill=COLOR_BRASS)
    
    # Hand-drawn Architectural Pencil Loop Circling the Cluster
    loop_cx, loop_cy = 950, 440
    rx, ry = 620, 190
    
    circle_progress = clamp(t * 1.3)
    max_angle = circle_progress * (math.pi * 2.15)
    
    if max_angle > 0:
        num_steps = int(max_angle * 30)
        pts_pass1 = []
        pts_pass2 = []
        for i in range(num_steps):
            th = (i / num_steps) * max_angle
            wobble1 = math.sin(th * 8) * 3.5
            wobble2 = math.cos(th * 6) * 4.0
            
            x1 = loop_cx + (rx + wobble1) * math.cos(th)
            y1 = loop_cy + (ry + wobble1) * math.sin(th)
            pts_pass1.append((x1, y1))
            
            x2 = loop_cx + (rx - 2 + wobble2) * math.cos(th)
            y2 = loop_cy + (ry - 2 + wobble2) * math.sin(th)
            pts_pass2.append((x2, y2))
            
        if len(pts_pass1) > 1:
            draw.line(pts_pass1, fill=COLOR_BRASS, width=2)
        if len(pts_pass2) > 1:
            draw.line(pts_pass2, fill=COLOR_BRASS_LIGHT, width=1)
            
    if t > 0.65:
        draw.rectangle([(loop_cx - 240, loop_cy + ry + 25), (loop_cx + 240, loop_cy + ry + 75)], fill=COLOR_BG, outline=COLOR_BRASS, width=2)
        draw.text((loop_cx - 215, loop_cy + ry + 40), "TARGET CORRIDOR LOCKED: CMH RD METRO", font=FONT_TITLE, fill=COLOR_BRASS_LIGHT)

# ---------------------------------------------------------
# Scene 6, 7 & 8: 3D Axonometric Tilt & Parallel Isometric Street View
# (Strictly Matching the User's Real Reference Photo)
# ---------------------------------------------------------
def iso_project(x, y, z, origin_x=960, origin_y=720, scale=1.0):
    # Standard 30° parallel isometric projection
    iso_x = (x - y) * 0.8660254 * scale
    iso_y = (x + y) * 0.5 * scale - z * scale
    return origin_x + iso_x, origin_y + iso_y

def draw_iso_box(draw, x0, y0, z0, dx, dy, dz, outline=COLOR_BRASS, fill_top=None, fill_left=None, fill_right=None, width=1, ox=960, oy=720, scale=1.0):
    p0 = iso_project(x0, y0, z0, ox, oy, scale)
    p1 = iso_project(x0 + dx, y0, z0, ox, oy, scale)
    p2 = iso_project(x0 + dx, y0 + dy, z0, ox, oy, scale)
    p3 = iso_project(x0, y0 + dy, z0, ox, oy, scale)
    
    p4 = iso_project(x0, y0, z0 + dz, ox, oy, scale)
    p5 = iso_project(x0 + dx, y0, z0 + dz, ox, oy, scale)
    p6 = iso_project(x0 + dx, y0 + dy, z0 + dz, ox, oy, scale)
    p7 = iso_project(x0, y0 + dy, z0 + dz, ox, oy, scale)
    
    if fill_left:
        draw.polygon([p0, p3, p7, p4], fill=fill_left)
    draw.polygon([p0, p3, p7, p4], outline=outline, width=width)
    
    if fill_right:
        draw.polygon([p0, p1, p5, p4], fill=fill_right)
    draw.polygon([p0, p1, p5, p4], outline=outline, width=width)
    
    if fill_top:
        draw.polygon([p4, p5, p6, p7], fill=fill_top)
    draw.polygon([p4, p5, p6, p7], outline=outline, width=width)
    
    return p0, p1, p2, p3, p4, p5, p6, p7

def render_street_view(draw, fitout_progress=0.0, interior_zoom=0.0, spotlight_center=False):
    """
    Renders the exact parallel isometric street view from user's photo:
    - Left: POORVIKA MOBILES (with Oppo branding)
    - Center: PANACHE YAMAHA BUILDING (4 storeys, vertical architectural louvers, TO-LET ground floor)
    - Right: SANGEETHA MOBILES
    - Overhead: NAMMA METRO elevated viaduct positioned cleanly above roadway
    """
    scale = lerp(1.15, 2.5, interior_zoom)
    ox = lerp(960, 960, interior_zoom)
    oy = lerp(700, 960, interior_zoom)
    
    dim_outline = COLOR_GRID_BRIGHT if spotlight_center else COLOR_BRASS_DIM
    dim_text = COLOR_MUTED if spotlight_center else COLOR_WHITE
    
    # 1. Ground Plane & CMH Roadway
    road_p1 = iso_project(-650, -180, 0, ox, oy, scale)
    road_p2 = iso_project(650, -180, 0, ox, oy, scale)
    road_p3 = iso_project(650, 100, 0, ox, oy, scale)
    road_p4 = iso_project(-650, 100, 0, ox, oy, scale)
    draw.polygon([road_p1, road_p2, road_p3, road_p4], fill=(8, 10, 15), outline=COLOR_GRID)
    
    for rx in range(-550, 550, 80):
        m1 = iso_project(rx, -40, 0, ox, oy, scale)
        m2 = iso_project(rx + 40, -40, 0, ox, oy, scale)
        draw.line([m1, m2], fill=COLOR_GRID_BRIGHT, width=2)
        
    curb1 = iso_project(-650, 40, 0, ox, oy, scale)
    curb2 = iso_project(650, 40, 0, ox, oy, scale)
    draw.line([curb1, curb2], fill=COLOR_BRASS_DIM, width=2)

    # 2. Left Building: POORVIKA MOBILES (X = -460 to -160, Y = 60 to 180)
    b1_x, b1_y = -460, 60
    b1_w, b1_d = 270, 140
    b1_h = 320
    draw_iso_box(draw, b1_x, b1_y, 0, b1_w, b1_d, b1_h, outline=dim_outline, fill_left=(10, 13, 18), fill_top=(14, 18, 24), fill_right=(12, 15, 20), ox=ox, oy=oy, scale=scale)
    
    # Poorvika Signage Fascia & OPPO Box
    fascia_p1 = iso_project(b1_x + b1_w, b1_y, 190, ox, oy, scale)
    fascia_p2 = iso_project(b1_x, b1_y, 190, ox, oy, scale)
    fascia_p3 = iso_project(b1_x, b1_y, 240, ox, oy, scale)
    fascia_p4 = iso_project(b1_x + b1_w, b1_y, 240, ox, oy, scale)
    draw.polygon([fascia_p1, fascia_p2, fascia_p3, fascia_p4], fill=(24, 18, 12), outline=COLOR_BRASS, width=2)
    
    lbl1 = iso_project(b1_x + b1_w * 0.5, b1_y, 210, ox, oy, scale)
    draw.text((lbl1[0] - 70, lbl1[1] - 8), "POORVIKA MOBILES", font=FONT_TITLE, fill=COLOR_WHITE)
    draw.text((lbl1[0] - 70, lbl1[1] + 16), "OPPO SHOWROOM", font=FONT_MONO, fill=COLOR_BRASS_LIGHT)
    
    # Storefront windows
    draw_iso_box(draw, b1_x + 20, b1_y, 0, b1_w - 40, 10, 160, outline=COLOR_BRASS_DIM, fill_right=(20, 24, 30), ox=ox, oy=oy, scale=scale)
    
    tag1 = iso_project(b1_x + b1_w * 0.5, b1_y, b1_h + 30, ox, oy, scale)
    draw.rectangle([(tag1[0] - 120, tag1[1] - 30), (tag1[0] + 120, tag1[1] + 10)], fill=COLOR_BG, outline=COLOR_BRASS_DIM, width=1)
    draw.text((tag1[0] - 105, tag1[1] - 22), "COMPETITOR 01: POORVIKA MOBILES", font=FONT_TINY, fill=dim_text)

    # 3. Right Building: SANGEETHA MOBILES (X = 180 to 480, Y = 60 to 180)
    b3_x, b3_y = 180, 60
    b3_w, b3_d = 270, 140
    b3_h = 300
    draw_iso_box(draw, b3_x, b3_y, 0, b3_w, b3_d, b3_h, outline=dim_outline, fill_left=(10, 13, 18), fill_top=(14, 18, 24), fill_right=(12, 15, 20), ox=ox, oy=oy, scale=scale)
    
    # Sangeetha Signage Fascia
    fascia3_p1 = iso_project(b3_x + b3_w, b3_y, 180, ox, oy, scale)
    fascia3_p2 = iso_project(b3_x, b3_y, 180, ox, oy, scale)
    fascia3_p3 = iso_project(b3_x, b3_y, 230, ox, oy, scale)
    fascia3_p4 = iso_project(b3_x + b3_w, b3_y, 230, ox, oy, scale)
    draw.polygon([fascia3_p1, fascia3_p2, fascia3_p3, fascia3_p4], fill=(16, 20, 30), outline=COLOR_BRASS, width=2)
    
    lbl3 = iso_project(b3_x + b3_w * 0.5, b3_y, 200, ox, oy, scale)
    draw.text((lbl3[0] - 75, lbl3[1] - 8), "SANGEETHA MOBILES", font=FONT_TITLE, fill=COLOR_WHITE)
    draw.text((lbl3[0] - 75, lbl3[1] + 16), "RETAIL SMARTPHONE HUB", font=FONT_TINY, fill=COLOR_BRASS_LIGHT)
    
    draw_iso_box(draw, b3_x + 20, b3_y, 0, b3_w - 40, 10, 150, outline=COLOR_BRASS_DIM, fill_right=(20, 24, 30), ox=ox, oy=oy, scale=scale)
    
    tag3 = iso_project(b3_x + b3_w * 0.5, b3_y, b3_h + 30, ox, oy, scale)
    draw.rectangle([(tag3[0] - 125, tag3[1] - 30), (tag3[0] + 125, tag3[1] + 10)], fill=COLOR_BG, outline=COLOR_BRASS_DIM, width=1)
    draw.text((tag3[0] - 115, tag3[1] - 22), "COMPETITOR 02: SANGEETHA MOBILES", font=FONT_TINY, fill=dim_text)

    # 4. Center Building: PANACHE YAMAHA BUILDING (X = -150 to 160, Y = 60 to 200)
    b2_x, b2_y = -150, 60
    b2_w, b2_d = 310, 150
    b2_h = 380
    
    # Upper floors (Storeys 2, 3, 4)
    draw_iso_box(draw, b2_x, b2_y, 140, b2_w, b2_d, b2_h - 140, outline=COLOR_BRASS, fill_left=(16, 20, 28), fill_top=(24, 30, 40), fill_right=(20, 25, 34), width=2, ox=ox, oy=oy, scale=scale)
    
    # Parapet Sign: PANACHE
    top_p = iso_project(b2_x + b2_w * 0.5, b2_y, b2_h - 25, ox, oy, scale)
    draw.text((top_p[0] - 40, top_p[1]), "PANACHE", font=FONT_TITLE, fill=COLOR_WHITE)
    
    # Vertical Architectural Louvers on Floors 2 & 3
    for lx in range(int(b2_x + 30), int(b2_x + b2_w - 30), 22):
        lp1 = iso_project(lx, b2_y, 160, ox, oy, scale)
        lp2 = iso_project(lx, b2_y, 330, ox, oy, scale)
        draw.line([lp1, lp2], fill=COLOR_BRASS_DIM, width=2)
        
    tag2 = iso_project(b2_x + b2_w * 0.5, b2_y, b2_h + 35, ox, oy, scale)
    draw.rectangle([(tag2[0] - 160, tag2[1] - 35), (tag2[0] + 160, tag2[1] + 12)], fill=COLOR_BG, outline=COLOR_BRASS_LIGHT, width=2)
    draw.text((tag2[0] - 148, tag2[1] - 26), "SITE OPPORTUNITY: YAMAHA BUILDING GF", font=FONT_MONO, fill=COLOR_BRASS_LIGHT)
    draw.text((tag2[0] - 148, tag2[1] - 8), "2,400 SQ. FT. COMMERCIAL LEASE", font=FONT_TINY, fill=COLOR_WHITE)

    # 5. Overhead Namma Metro Viaduct (Positioned cleanly overhead framing the street)
    # Left Concrete Pier Pillar (at the far left screen perimeter)
    draw_iso_box(draw, -1060, -140, 0, 42, 32, 390, outline=COLOR_BRASS_DIM, fill_left=(14, 18, 26), fill_right=(18, 22, 32), ox=ox, oy=oy, scale=scale)
    # Right Concrete Pier Pillar (at the right screen perimeter)
    draw_iso_box(draw, 420, -140, 0, 42, 32, 390, outline=COLOR_BRASS_DIM, fill_left=(14, 18, 26), fill_right=(18, 22, 32), ox=ox, oy=oy, scale=scale)
    # Elevated Box Girder Beam spanning overhead across CMH Road above all rooftops
    draw_iso_box(draw, -1150, -155, 390, 1800, 65, 42, outline=COLOR_BRASS, fill_left=(18, 24, 34), fill_top=(26, 32, 44), fill_right=(20, 26, 36), ox=ox, oy=oy, scale=scale)
    
    vp = iso_project(-120, -140, 440, ox, oy, scale)
    draw.text((vp[0] - 130, vp[1] - 20), "NAMMA METRO ELEVATED VIADUCT (PURPLE LINE)", font=FONT_TINY, fill=COLOR_BRASS_LIGHT)

    # 6. GROUND FLOOR: The Transformers Fit-Out Animation!
    if fitout_progress <= 0.05:
        # Pre-fitout: Vacant retail space with shutter down and TO-LET board
        draw_iso_box(draw, b2_x, b2_y, 0, b2_w, b2_d, 140, outline=COLOR_BRASS_DIM, fill_right=(18, 16, 14), ox=ox, oy=oy, scale=scale)
        for sy in range(10, 130, 10):
            sp1 = iso_project(b2_x + b2_w - 20, b2_y, sy, ox, oy, scale)
            sp2 = iso_project(b2_x + 20, b2_y, sy, ox, oy, scale)
            draw.line([sp1, sp2], fill=COLOR_BRASS_DARK, width=1)
            
        tolet_p = iso_project(b2_x + b2_w * 0.5, b2_y, 70, ox, oy, scale)
        draw.rectangle([(tolet_p[0] - 80, tolet_p[1] - 25), (tolet_p[0] + 80, tolet_p[1] + 25)], fill=COLOR_BG, outline=COLOR_MUTED, width=1)
        draw.text((tolet_p[0] - 45, tolet_p[1] - 15), "COMMERCIAL", font=FONT_TINY, fill=COLOR_MUTED)
        draw.text((tolet_p[0] - 35, tolet_p[1] + 2), "TO-LET", font=FONT_TITLE, fill=COLOR_WHITE)
    else:
        # ANIMATED TRANSFORMERS FIT-OUT REASSEMBLY
        p = fitout_progress
        
        # Interior Showroom Floor Shell
        draw_iso_box(draw, b2_x, b2_y, 0, b2_w, b2_d, 140, outline=COLOR_BRASS, fill_right=(24, 28, 38), fill_top=(30, 36, 48), ox=ox, oy=oy, scale=scale)
        
        # 1. Structural Steel Columns & Portal Beams Flying In
        if p >= 0.15:
            steel_t = clamp((p - 0.15) / 0.35)
            col_offset = (1.0 - ease_out_cubic(steel_t)) * 180.0
            draw_iso_box(draw, b2_x + 10 - col_offset, b2_y, 0, 18, 18, 140, outline=COLOR_BRASS_LIGHT, fill_right=COLOR_BRASS_DARK, ox=ox, oy=oy, scale=scale)
            draw_iso_box(draw, b2_x + b2_w - 28 + col_offset, b2_y, 0, 18, 18, 140, outline=COLOR_BRASS_LIGHT, fill_right=COLOR_BRASS_DARK, ox=ox, oy=oy, scale=scale)
            
            if steel_t > 0.6:
                draw_iso_box(draw, b2_x + 10, b2_y, 120, b2_w - 20, 20, 20, outline=COLOR_BRASS_LIGHT, fill_right=COLOR_BRASS, ox=ox, oy=oy, scale=scale)
                # Welding Flash / Sparks
                spark_x, spark_y = iso_project(b2_x + 20, b2_y, 120, ox, oy, scale)
                draw.ellipse([(spark_x - 12, spark_y - 12), (spark_x + 12, spark_y + 12)], fill=COLOR_WHITE)
                draw.ellipse([(spark_x - 24, spark_y - 24), (spark_x + 24, spark_y + 24)], outline=COLOR_BRASS_LIGHT, width=2)
                
        # 2. Ceiling MEP Climate Ducts & Lighting Grid
        if p >= 0.40:
            mep_t = clamp((p - 0.40) / 0.30)
            mep_z = lerp(180, 125, ease_out_cubic(mep_t))
            draw_iso_box(draw, b2_x + 40, b2_y + 40, mep_z, b2_w - 80, 25, 12, outline=COLOR_BRASS_DIM, fill_right=(30, 36, 45), ox=ox, oy=oy, scale=scale)
            for tx in range(int(b2_x + 60), int(b2_x + b2_w - 60), 45):
                tp = iso_project(tx, b2_y + 50, mep_z, ox, oy, scale)
                draw.ellipse([(tp[0] - 3, tp[1] - 3), (tp[0] + 3, tp[1] + 3)], fill=COLOR_WHITE)
                
        # 3. Interior Retail Display Tables Rising from Floor
        if p >= 0.50:
            tab_t = clamp((p - 0.50) / 0.35)
            tab_h = lerp(0, 35, ease_out_cubic(tab_t))
            draw_iso_box(draw, b2_x + 50, b2_y + 50, 0, 80, 45, tab_h, outline=COLOR_BRASS_LIGHT, fill_top=(45, 52, 65), fill_right=COLOR_BRASS_DARK, ox=ox, oy=oy, scale=scale)
            draw_iso_box(draw, b2_x + 180, b2_y + 50, 0, 80, 45, tab_h, outline=COLOR_BRASS_LIGHT, fill_top=(45, 52, 65), fill_right=COLOR_BRASS_DARK, ox=ox, oy=oy, scale=scale)
            
            if tab_t > 0.7:
                p1 = iso_project(b2_x + 90, b2_y + 70, tab_h + 8, ox, oy, scale)
                draw.rectangle([(p1[0] - 6, p1[1] - 12), (p1[0] + 6, p1[1] + 4)], fill=COLOR_BRASS_LIGHT, outline=COLOR_WHITE)
                p2 = iso_project(b2_x + 220, b2_y + 70, tab_h + 8, ox, oy, scale)
                draw.rectangle([(p2[0] - 6, p2[1] - 12), (p2[0] + 6, p2[1] + 4)], fill=COLOR_BRASS_LIGHT, outline=COLOR_WHITE)

        # 4. Frameless Architectural Glass Curtain Wall
        if p >= 0.60:
            glass_t = clamp((p - 0.60) / 0.30)
            glass_h = lerp(0, 115, ease_out_cubic(glass_t))
            gp1 = iso_project(b2_x + b2_w - 25, b2_y, 120, ox, oy, scale)
            gp2 = iso_project(b2_x + 25, b2_y, 120, ox, oy, scale)
            gp3 = iso_project(b2_x + 25, b2_y, 120 - glass_h, ox, oy, scale)
            gp4 = iso_project(b2_x + b2_w - 25, b2_y, 120 - glass_h, ox, oy, scale)
            draw.polygon([gp1, gp2, gp3, gp4], fill=(30, 45, 60), outline=COLOR_BRASS_LIGHT, width=1)
            draw.line([(gp2[0] + 40, gp2[1] + 20), (gp4[0] - 40, gp4[1] - 20)], fill=(70, 95, 125), width=2)

        # 5. Illuminated Brand Storefront Fascia Snapping Into Place
        if p >= 0.75:
            fascia_t = clamp((p - 0.75) / 0.25)
            draw_iso_box(draw, b2_x + 5, b2_y - 8, 115, b2_w - 10, 16, 32, outline=COLOR_BRASS_LIGHT, fill_right=(15, 18, 25), fill_top=COLOR_BRASS_DARK, width=2, ox=ox, oy=oy, scale=scale)
            fp = iso_project(b2_x + b2_w * 0.5, b2_y - 8, 128, ox, oy, scale)
            draw.text((fp[0] - 110, fp[1] - 10), "XPANDOR FLAGSHIP STORE", font=FONT_TITLE, fill=COLOR_WHITE)
            
            if fascia_t >= 0.8:
                draw.rectangle([(fp[0] - 130, fp[1] + 35), (fp[0] + 130, fp[1] + 68)], fill=COLOR_BG, outline=COLOR_BRASS_LIGHT, width=2)
                draw.text((fp[0] - 115, fp[1] + 42), "STORE FIT-OUT COMPLETED", font=FONT_MONO, fill=COLOR_BRASS_LIGHT)

def render_scene_6_tilt(draw, frame_idx):
    t = (frame_idx - 620) / 70.0
    draw_hud_header(draw, "ELEVATION SURVEY // AXONOMETRIC PERSPECTIVE", coords="CMH ROAD RETAIL CORRIDOR", mode="[MODE: 3D AXIS]")
    render_street_view(draw, fitout_progress=0.0, interior_zoom=0.0, spotlight_center=False)

def render_scene_7_street_view(draw, frame_idx):
    t = (frame_idx - 690) / 110.0
    draw_hud_header(draw, "PARALLEL ISOMETRIC STREET ARCHITECTURE", coords="CMH RD • INDIRANAGAR METRO ADJACENCY", mode="[MODE: PARALLEL ISO]")
    render_street_view(draw, fitout_progress=0.0, interior_zoom=0.0, spotlight_center=False)

def render_scene_8_transformers(draw, frame_idx):
    t = (frame_idx - 800) / 140.0
    draw_hud_header(draw, "TURNKEY MECHANICAL FIT-OUT EXECUTION", coords="YAMAHA BUILDING GROUND FLOOR • 2,400 SQ. FT.", mode="[MODE: FIT-OUT REASSEMBLY]")
    render_street_view(draw, fitout_progress=t, interior_zoom=0.0, spotlight_center=True)

# ---------------------------------------------------------
# Scene 9: Store Interior Glide & Staffing ID Lanyards
# ---------------------------------------------------------
def draw_stylized_associate(draw, x, y, scale=1.0, lanyard_drop=0.0, role="RETAIL ASSOCIATE"):
    # Stylized architectural wireframe human figure (associate)
    head_r = int(18 * scale)
    draw.ellipse([(x - head_r, y - int(135 * scale)), (x + head_r, y - int(135 * scale) + head_r * 2)], outline=COLOR_BRASS_LIGHT, width=2)
    # Torso
    draw.line([(x, y - int(99 * scale)), (x, y - int(30 * scale))], fill=COLOR_BRASS_LIGHT, width=2)
    # Shoulders
    s_w = int(32 * scale)
    draw.line([(x - s_w, y - int(90 * scale)), (x + s_w, y - int(90 * scale))], fill=COLOR_BRASS_LIGHT, width=2)
    # Arms
    draw.line([(x - s_w, y - int(90 * scale)), (x - s_w - 8, y - int(40 * scale))], fill=COLOR_BRASS_LIGHT, width=2)
    draw.line([(x + s_w, y - int(90 * scale)), (x + s_w + 8, y - int(40 * scale))], fill=COLOR_BRASS_LIGHT, width=2)
    # Base legs
    draw.line([(x, y - int(30 * scale)), (x - 16, y)], fill=COLOR_BRASS_DIM, width=2)
    draw.line([(x, y - int(30 * scale)), (x + 16, y)], fill=COLOR_BRASS_DIM, width=2)
    
    # Gold Employee ID Lanyard dropping down and settling around neck
    if lanyard_drop > 0.05:
        drop_t = ease_out_cubic(clamp(lanyard_drop))
        start_y = y - int(320 * scale)
        target_neck_y = y - int(90 * scale)
        curr_y = lerp(start_y, target_neck_y, drop_t)
        
        # Woven gold ribbon loop around neck
        ribbon_pts = [
            (x - s_w // 2, curr_y),
            (x, curr_y + int(45 * scale)),
            (x + s_w // 2, curr_y)
        ]
        draw.line(ribbon_pts, fill=COLOR_BRASS_LIGHT, width=3)
        
        # Lanyard badge card hanging on chest
        badge_y = curr_y + int(45 * scale)
        bw, bh = int(46 * scale), int(64 * scale)
        draw.rectangle([(x - bw // 2, badge_y), (x + bw // 2, badge_y + bh)], fill=COLOR_BG, outline=COLOR_BRASS_LIGHT, width=2)
        # Gold badge details
        draw.line([(x - bw // 2 + 5, badge_y + 10), (x + bw // 2 - 5, badge_y + 10)], fill=COLOR_BRASS_LIGHT, width=2)
        draw.rectangle([(x - 10, badge_y + 18), (x + 10, badge_y + 38)], outline=COLOR_MUTED, fill=COLOR_BG_CARD)
        
        if lanyard_drop > 0.65:
            draw.rectangle([(x - 130, y + 25), (x + 130, y + 70)], fill=COLOR_BG, outline=COLOR_BRASS, width=1)
            draw.text((x - 110, y + 32), role.upper(), font=FONT_MONO, fill=COLOR_WHITE)
            draw.text((x - 110, y + 50), "DEPLOYED & LAUNCH READY", font=FONT_TINY, fill=COLOR_BRASS_LIGHT)

def render_scene_9_interior_staffing(draw, frame_idx):
    t = (frame_idx - 940) / 120.0
    draw_hud_header(draw, "STORE INTERIOR & RETAIL CREW READINESS", coords="XPANDOR FLAGSHIP SHOWROOM • CMH RD", mode="[MODE: STAFFING]")
    
    # 1. Perspective View Inside the Newly Fitted-Out Store
    vanish_x, vanish_y = 960, 380
    for fx in range(60, WIDTH + 60, 100):
        draw.line([(fx, HEIGHT - 70), (vanish_x, vanish_y)], fill=COLOR_GRID, width=1)
    for fy in range(HEIGHT - 70, vanish_y, -40):
        draw.line([(60, fy), (WIDTH - 60, fy)], fill=COLOR_GRID, width=1)
        
    # Illuminated LED Ceiling Light Panels
    for cx in range(320, 1650, 320):
        draw.polygon([(cx - 110, 80), (cx + 110, 80), (vanish_x + (cx + 110 - vanish_x) * 0.25, vanish_y - 100), (vanish_x + (cx - 110 - vanish_x) * 0.25, vanish_y - 100)], fill=(22, 28, 40), outline=COLOR_BRASS_LIGHT, width=1)
        
    # Side Wall Perimeter Display Bays
    # Left Wall
    draw.polygon([(60, 100), (240, 240), (240, 680), (60, HEIGHT - 70)], fill=(12, 16, 24), outline=COLOR_BRASS_DIM, width=2)
    # Right Wall
    draw.polygon([(WIDTH - 60, 100), (WIDTH - 240, 240), (WIDTH - 240, 680), (WIDTH - 60, HEIGHT - 70)], fill=(12, 16, 24), outline=COLOR_BRASS_DIM, width=2)
    
    # Phone Display Tables in Showroom
    draw.polygon([(420, 720), (760, 720), (710, 580), (470, 580)], fill=(18, 24, 32), outline=COLOR_BRASS, width=2)
    draw.polygon([(1160, 720), (1500, 720), (1450, 580), (1210, 580)], fill=(18, 24, 32), outline=COLOR_BRASS, width=2)
    
    for px in [510, 590, 670, 1250, 1330, 1410]:
        draw.rectangle([(px - 8, 640), (px + 8, 670)], fill=COLOR_BRASS_LIGHT, outline=COLOR_WHITE)

    # 2. Store Associates Appearing at Showroom Stations (Prominent & Well-detailed)
    draw_stylized_associate(draw, 960, 660, scale=1.4, lanyard_drop=t, role="STORE LEADERSHIP")
    draw_stylized_associate(draw, 380, 690, scale=1.2, lanyard_drop=max(0.0, (t - 0.15) / 0.85), role="RETAIL SPECIALIST")
    draw_stylized_associate(draw, 1540, 690, scale=1.2, lanyard_drop=max(0.0, (t - 0.25) / 0.75), role="CUSTOMER ADVISOR")
    
    if t > 0.55:
        draw.rectangle([(WIDTH // 2 - 270, 125), (WIDTH // 2 + 270, 180)], fill=COLOR_BG, outline=COLOR_BRASS_LIGHT, width=2)
        draw.text((WIDTH // 2 - 245, 140), "STORE STAFFED & 100% OPERATIONALLY READY", font=FONT_TITLE, fill=COLOR_BRASS_LIGHT)

# ---------------------------------------------------------
# Scene 10: Typographic Slides & Official XPANDOR Logo Reveal
# ---------------------------------------------------------
SLIDES = [
    ("From a list of locations\non paper . . .", 1061, 1098),
    ("to leasing . . .", 1099, 1134),
    ("to fit-out . . .", 1135, 1170),
    ("to staffing.", 1171, 1206),
    ("We do it all.", 1207, 1234),
    ("LOGO_REVEAL", 1235, 1260)
]

def render_scene_10_typography_and_logo(draw, frame_idx, base_img):
    for text, sf, ef in SLIDES:
        if sf <= frame_idx <= ef:
            dur = ef - sf
            rel = (frame_idx - sf) / float(dur)
            
            draw_blueprint_grid(draw, step=75)
            
            draw.text((80, 80), "XPANDOR SPECIFICATION // SUMMARY", font=FONT_MONO, fill=COLOR_BRASS_DIM)
            draw.text((WIDTH - 320, 80), "SINGLE MASTER CONTRACT", font=FONT_MONO, fill=COLOR_BRASS_DIM)
            
            if text == "LOGO_REVEAL":
                # Final Slide: Official XPANDOR Logo Reveal
                cx, cy = WIDTH // 2, HEIGHT // 2 - 40
                
                if logo_brass:
                    # Target logo width 680
                    lw = 680
                    lh = int(lw * (logo_brass.height / logo_brass.width))
                    resized_logo = logo_brass.resize((lw, lh), Image.Resampling.LANCZOS)
                    lx = cx - lw // 2
                    ly = cy - lh // 2
                    base_img.paste(resized_logo, (lx, ly), resized_logo)
                else:
                    draw.text((cx - 160, cy - 35), "XPANDOR", font=FONT_HERO, fill=COLOR_WHITE)
                    
                # Glowing Brass Underline
                uw = 560
                draw.line([(cx - uw // 2, cy + 90), (cx + uw // 2, cy + 90)], fill=COLOR_BRASS_LIGHT, width=2)
                
                # Tagline below logo
                draw.text((cx - 250, cy + 120), "TURNKEY RETAIL EXPANSION  •  SOUTH INDIA", font=FONT_TITLE, fill=COLOR_WHITE)
                draw.text((cx - 55, cy + 165), "xpandor.net", font=FONT_BODY, fill=COLOR_BRASS_LIGHT)
                
            else:
                lines = text.split("\n")
                cx, cy = WIDTH // 2, HEIGHT // 2
                
                is_statement = (text == "We do it all.")
                font_to_use = FONT_HERO if is_statement else FONT_H1
                
                line_spacing = 80
                total_h = len(lines) * line_spacing
                start_y = cy - total_h // 2
                
                for i, line in enumerate(lines):
                    bbox = font_to_use.getbbox(line)
                    tw = bbox[2] - bbox[0]
                    tx = cx - tw // 2
                    ty = start_y + i * line_spacing
                    
                    color_line = COLOR_BRASS_LIGHT if is_statement else COLOR_WHITE
                    draw.text((tx, ty), line, font=font_to_use, fill=color_line)
                    
                draw.line([(cx - 80, start_y + total_h + 30), (cx + 80, start_y + total_h + 30)], fill=COLOR_BRASS_DIM, width=1)
                
            break

# ---------------------------------------------------------
# Master Frame Dispatcher
# ---------------------------------------------------------
def render_frame(frame_idx):
    img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(img)
    
    draw_blueprint_grid(draw, step=60)
    
    if frame_idx <= 150:
        render_scene_1_globe(draw, frame_idx)
    elif frame_idx <= 280:
        render_scene_2_south_india(draw, frame_idx)
    elif frame_idx <= 400:
        render_scene_3_bengaluru(draw, frame_idx)
    elif frame_idx <= 530:
        render_scene_4_indiranagar_search(draw, frame_idx)
    elif frame_idx <= 620:
        render_scene_5_pencil_circle(draw, frame_idx)
    elif frame_idx <= 690:
        render_scene_6_tilt(draw, frame_idx)
    elif frame_idx <= 800:
        render_scene_7_street_view(draw, frame_idx)
    elif frame_idx <= 940:
        render_scene_8_transformers(draw, frame_idx)
    elif frame_idx <= 1060:
        render_scene_9_interior_staffing(draw, frame_idx)
    else:
        render_scene_10_typography_and_logo(draw, frame_idx, img)
        
    return img

# ---------------------------------------------------------
# CLI & Execution Pipeline
# ---------------------------------------------------------
def test_frames():
    os.makedirs("public/videos/preview_frames", exist_ok=True)
    sample_frames = [
        (80, "01_globe"),
        (220, "02_south_india"),
        (350, "03_bengaluru"),
        (480, "04_search_hud"),
        (580, "05_pencil_circle"),
        (660, "06_isometric_tilt"),
        (760, "07_street_view"),
        (880, "08_transformers_fitout"),
        (1000, "09_interior_staffing"),
        (1150, "10_typography_fitout"),
        (1245, "11_logo_reveal")
    ]
    print(f"Generating {len(sample_frames)} sample preview frames...")
    for f_idx, label in sample_frames:
        t0 = time.time()
        img = render_frame(f_idx)
        out_path = f"public/videos/preview_frames/{label}_frame_{f_idx:04d}.jpg"
        img.save(out_path, quality=95)
        print(f"  Frame {f_idx:4d} ({label:25s}) rendered in {time.time() - t0:.3f}s -> {out_path}")
        
    poster = render_frame(760)
    poster.save("public/videos/xpandor-journey-poster.jpg", quality=95)
    print("Poster saved to public/videos/xpandor-journey-poster.jpg")

def render_full_video():
    mp4_out = "public/videos/xpandor-journey.mp4"
    webm_out = "public/videos/xpandor-journey.webm"
    os.makedirs("public/videos", exist_ok=True)
    
    print("Generating poster image...")
    poster = render_frame(760)
    poster.save("public/videos/xpandor-journey-poster.jpg", quality=95)
    print("Poster saved to public/videos/xpandor-journey-poster.jpg")
    
    ffmpeg_cmd = [
        "/opt/homebrew/bin/ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        mp4_out
    ]
    
    print(f"Spawning FFmpeg for MP4 generation (1080p @ {FPS}fps, {TOTAL_FRAMES} frames)...")
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    
    start_time = time.time()
    for f in range(TOTAL_FRAMES):
        img = render_frame(f)
        raw_bytes = img.tobytes()
        proc.stdin.write(raw_bytes)
        
        if f % 90 == 0 or f == TOTAL_FRAMES - 1:
            elapsed = time.time() - start_time
            fps_speed = (f + 1) / max(0.001, elapsed)
            eta = (TOTAL_FRAMES - f - 1) / max(0.001, fps_speed)
            print(f"  Rendered frame {f:4d}/{TOTAL_FRAMES} ({((f+1)/TOTAL_FRAMES)*100:5.1f}%) | {fps_speed:4.1f} fps | ETA: {eta:4.1f}s")
            
    proc.stdin.close()
    proc.wait()
    print(f"\nMP4 generated successfully: {mp4_out} ({os.path.getsize(mp4_out) / 1024 / 1024:.2f} MB)")
    
    print("\nEncoding WebM (VP9) version for high-efficiency browser streaming...")
    webm_cmd = [
        "/opt/homebrew/bin/ffmpeg",
        "-y",
        "-i", mp4_out,
        "-c:v", "libvpx-vp9",
        "-b:v", "0",
        "-crf", "30",
        "-deadline", "good",
        "-cpu-used", "2",
        webm_out
    ]
    subprocess.run(webm_cmd, check=True)
    print(f"WebM generated successfully: {webm_out} ({os.path.getsize(webm_out) / 1024 / 1024:.2f} MB)")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_frames()
    else:
        render_full_video()
