import copy
import re
from datetime import datetime

STRATEGIES = {"median", "mean", "zero", "drop", "none"}
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%b %d %Y")


class CleaningError(ValueError):
    pass


def snake(name):
    name = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip())
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.strip("_").lower() or "column"


def coerce(value):
    if isinstance(value, str):
        stripped = value.strip().replace(",", "")
        if re.fullmatch(r"-?\d+", stripped):
            return int(stripped)
        if re.fullmatch(r"-?\d*\.\d+", stripped):
            return float(stripped)
    return value


def iso_date(value):
    if not isinstance(value, str):
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def median(values):
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def quartiles(values):
    ordered = sorted(values)
    half = len(ordered) // 2
    lower = ordered[:half]
    upper = ordered[half + (len(ordered) % 2):]
    return median(lower), median(upper)


def clean(rows, fill="median", date_columns=(), flag_outliers=True):
    if fill not in STRATEGIES:
        raise CleaningError(f"fill must be one of {', '.join(sorted(STRATEGIES))}")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise CleaningError("rows must be a list of objects")
    original = copy.deepcopy(rows)
    report = {"renamed": {}, "dropped_duplicates": 0, "stripped": 0, "coerced": 0, "dates": 0, "filled": 0, "dropped_missing": 0, "outliers": []}

    renamed_rows = []
    for row in rows:
        renamed = {}
        for key, value in row.items():
            new_key = snake(key)
            if new_key != key:
                report["renamed"][key] = new_key
            renamed[new_key] = value
        renamed_rows.append(renamed)

    for row in renamed_rows:
        for key, value in list(row.items()):
            if isinstance(value, str) and value != value.strip():
                row[key] = value.strip()
                report["stripped"] += 1
            if isinstance(row[key], str) and row[key] == "":
                row[key] = None
            converted = coerce(row[key])
            if converted is not row[key] and converted != row[key]:
                row[key] = converted
                report["coerced"] += 1

    for column in date_columns:
        key = snake(column)
        for row in renamed_rows:
            if row.get(key) is None:
                continue
            parsed = iso_date(row[key])
            if parsed is None:
                raise CleaningError(f"{column} has a value that is not a known date format: {row[key]}")
            if parsed != row[key]:
                row[key] = parsed
                report["dates"] += 1

    unique = []
    for row in renamed_rows:
        if row in unique:
            report["dropped_duplicates"] += 1
            continue
        unique.append(row)

    keys = list(dict.fromkeys(key for row in unique for key in row))
    numeric = [key for key in keys if any(isinstance(row.get(key), (int, float)) and not isinstance(row.get(key), bool) for row in unique)]
    if fill == "drop":
        kept = [row for row in unique if all(row.get(key) is not None for key in numeric)]
        report["dropped_missing"] = len(unique) - len(kept)
        unique = kept
    elif fill != "none":
        for key in numeric:
            values = [row[key] for row in unique if isinstance(row.get(key), (int, float))]
            if fill == "median":
                replacement = median(values)
            elif fill == "mean":
                replacement = round(sum(values) / len(values), 4)
            else:
                replacement = 0
            for row in unique:
                if row.get(key) is None:
                    row[key] = replacement
                    report["filled"] += 1

    if flag_outliers:
        for key in numeric:
            values = [row[key] for row in unique if isinstance(row.get(key), (int, float))]
            if len(values) < 4:
                continue
            q1, q3 = quartiles(values)
            spread = q3 - q1
            low, high = q1 - 1.5 * spread, q3 + 1.5 * spread
            for index, row in enumerate(unique):
                value = row.get(key)
                if isinstance(value, (int, float)) and (value < low or value > high):
                    report["outliers"].append({"row": index, "column": key, "value": value, "low": low, "high": high})

    if rows != original:
        raise CleaningError("input rows were modified")
    return {"rows": unique, **report}
