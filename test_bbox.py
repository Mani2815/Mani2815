import datetime as dt

def get_bbox(DX, DY, DZ, OX, OY):
    # Dummy days
    today = dt.date.today()
    days = [(today - dt.timedelta(days=i), (i*7)%25 if (i*7)%25 > 10 else 0) for i in range(365)]
    days.sort()

    start_dow = days[0][0].weekday()
    start_dow = (start_dow + 1) % 7
    
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')
    
    for i, (_, count) in enumerate(days):
        week = (i + start_dow) // 7
        day = (i + start_dow) % 7
        
        px = (week - day) * DX + OX
        py = (week + day) * DY + OY
        h = count * DZ if count > 0 else 0
        if count > 0 and h < DZ:
            h = DZ
            
        # block left = px - DX
        # block right = px + DX
        # block top = py - h - DY
        # block bottom = py + DY
        min_x = min(min_x, px - DX)
        max_x = max(max_x, px + DX)
        min_y = min(min_y, py - h - DY)
        max_y = max(max_y, py + DY)
        
    return min_x, max_x, min_y, max_y

print("BBox 1:", get_bbox(14, 8, 3, 150, 120))
