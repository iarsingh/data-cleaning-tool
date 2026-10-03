def clean(rows):
    seen = []
    dropped = 0
    for row in rows:
        if row in seen:
            dropped += 1
            continue
        seen.append(dict(row))
    stripped = 0
    for row in seen:
        for key, value in list(row.items()):
            if isinstance(value, str) and value != value.strip():
                row[key] = value.strip()
                stripped += 1
    filled = 0
    keys = list(seen[0]) if seen else []
    for key in keys:
        numbers = sorted(row[key] for row in seen if isinstance(row[key], (int, float)))
        if not numbers:
            continue
        median = numbers[len(numbers) // 2]
        for row in seen:
            if row[key] is None:
                row[key] = median
                filled += 1
    return {"rows": seen, "dropped_duplicates": dropped, "stripped": stripped, "filled": filled}
