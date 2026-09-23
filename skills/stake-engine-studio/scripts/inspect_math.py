#!/usr/bin/env python3
"""Read-only structural and payout-integrity checks for Studio math artifacts.

Does not certify approval, statistical risk limits, or event semantics.
Uses temporary SQLite storage; --books additionally requires zstandard.
"""

import argparse
import csv
from decimal import Decimal, localcontext
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile

UINT64_MAX = 2**64 - 1


class Invalid(ValueError):
    pass


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise Invalid(f"Non-finite JSON number: {value}")


def load_json(text):
    return json.loads(text, parse_float=Decimal, parse_constant=reject_constant,
                      object_pairs_hook=reject_duplicates)


def uint(value, label):
    if isinstance(value, str):
        if not re.fullmatch(r"[0-9]+", value):
            raise Invalid(f"{label}: expected an unsigned integer")
        value = int(value)
    if type(value) is not int or not 0 <= value <= UINT64_MAX:
        raise Invalid(f"{label}: expected uint64")
    return value


def artifact(root, value, suffix):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise Invalid("Artifact path must be a nonempty relative path")
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise Invalid(f"Artifact escapes publication directory: {value}")
    if not value.endswith(suffix) or not path.is_file():
        raise Invalid(f"Missing file or incorrect extension ({suffix}): {value}")
    return path


def load_table(path, db):
    db.execute("CREATE TABLE outcomes (id TEXT PRIMARY KEY, payout TEXT NOT NULL, seen INTEGER NOT NULL DEFAULT 0)")
    count = total = weighted = weighted_squared = winning = zero_weights = maximum = reachable = 0
    with path.open(newline="", encoding="utf-8") as handle:
        for number, row in enumerate(csv.reader(handle), 1):
            if number == 1 and row and row[0].startswith("\ufeff"):
                raise Invalid(f"{path.name}: file starts with a UTF-8 BOM; export without a BOM")
            if not row or all(not value.strip() for value in row):
                raise Invalid(f"{path.name}:{number}: blank CSV row")
            if len(row) != 3:
                raise Invalid(f"{path.name}:{number}: expected exactly three CSV columns without header")
            identifier, weight, payout = [uint(value, f"{path.name}:{number}") for value in row]
            try:
                db.execute("INSERT INTO outcomes(id,payout) VALUES (?,?)", (str(identifier), str(payout)))
            except sqlite3.IntegrityError as exc:
                raise Invalid(f"Duplicate CSV ID: {identifier}") from exc
            count += 1
            total += weight
            weighted += weight * payout
            weighted_squared += weight * payout * payout
            winning += weight if payout > 0 else 0
            zero_weights += weight == 0
            maximum = max(maximum, payout)
            if weight:
                reachable = max(reachable, payout)
    if not count or total == 0:
        raise Invalid("Lookup table must contain outcomes with positive total weight")
    db.commit()
    return {"outcomes": count, "weight_sum": total, "weighted_payout_sum": weighted,
            "weighted_payout_squared_sum": weighted_squared,
            "winning_weight": winning, "zero_weight_outcomes": zero_weights,
            "max_recorded_payout": maximum, "max_reachable_payout": reachable}


def verify_lines(lines, db):
    count = 0
    for number, line in enumerate(lines, 1):
        if isinstance(line, bytes):
            try:
                line = line.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise Invalid(f"Book line {number}: not UTF-8") from exc
        if isinstance(line, str) and not line.strip():
            raise Invalid(f"Book line {number}: blank JSONL record")
        try:
            record = load_json(line)
        except (ValueError, TypeError) as exc:
            raise Invalid(f"Book line {number}: invalid JSON: {exc}") from exc
        if not isinstance(record, dict) or not all(key in record for key in ("id", "events", "payoutMultiplier")):
            raise Invalid(f"Book line {number}: missing required record fields")
        # Book fields must be JSON integers, not numeric strings.
        if type(record["id"]) is not int or type(record["payoutMultiplier"]) is not int:
            raise Invalid(f"Book line {number}: id and payoutMultiplier must be JSON integers")
        identifier = uint(record["id"], "book id")
        payout = uint(record["payoutMultiplier"], "book payout")
        if not isinstance(record["events"], list) or not all(isinstance(event, dict) for event in record["events"]):
            raise Invalid(f"Book ID {identifier}: events must be an array of objects")
        row = db.execute("SELECT payout, seen FROM outcomes WHERE id=?", (str(identifier),)).fetchone()
        if row is None:
            raise Invalid(f"Book ID {identifier} has no CSV row")
        if row[1]:
            raise Invalid(f"Duplicate book ID: {identifier}")
        if int(row[0]) != payout:
            raise Invalid(f"Payout mismatch for ID {identifier}: CSV={row[0]}, book={payout}")
        db.execute("UPDATE outcomes SET seen=1 WHERE id=?", (str(identifier),))
        count += 1
    missing = db.execute("SELECT id FROM outcomes WHERE seen=0 LIMIT 1").fetchone()
    if missing:
        raise Invalid(f"CSV ID {missing[0]} has no book record")
    return count


def compressed_lines(path, zstandard):
    """Decode concatenated frames, rejecting missing frame ends/checksums.

    stream_reader alone accepts certain truncated streams after yielding all
    records. decompressobj.eof lets us distinguish a full frame from that case.
    """
    decoder = None
    pending = bytearray()
    completed = False
    with path.open("rb") as handle:
        while chunk := handle.read(16_384):
            while chunk:
                if decoder is None:
                    decoder = zstandard.ZstdDecompressor().decompressobj()
                try:
                    decoded = decoder.decompress(chunk)
                except zstandard.ZstdError as exc:
                    raise Invalid(f"Invalid Zstandard stream: {exc}") from exc
                # Scan each newly decoded byte once, even for very long records.
                lines = decoded.split(b"\n")
                for line in lines[:-1]:
                    pending.extend(line)
                    yield bytes(pending)
                    pending.clear()
                pending.extend(lines[-1])
                if decoder.eof:
                    chunk = decoder.unused_data
                    decoder = None
                    completed = True
                else:
                    chunk = b""
    if decoder is not None or not completed:
        raise Invalid("Incomplete or empty Zstandard stream")
    if pending:
        yield bytes(pending)


def inspect(root, books=False):
    root = Path(root).resolve()
    manifest_path = artifact(root, "index.json", ".json")
    manifest = load_json(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modes"), list) or not manifest["modes"]:
        raise Invalid("index.json must contain a nonempty modes array")
    if books:
        try:
            import zstandard
        except ImportError as exc:
            raise Invalid("--books requires the optional zstandard package in this Python environment") from exc
    reports, names, used_paths, warnings = [], set(), {}, []
    for mode in manifest["modes"]:
        if not isinstance(mode, dict) or not all(key in mode for key in ("name", "cost", "events", "weights")):
            raise Invalid("Mode must define name, cost, events, and weights")
        name = mode["name"]
        if not isinstance(name, str) or not name.strip() or name in names:
            raise Invalid("Mode names must be nonempty and unique")
        names.add(name)
        if type(mode["cost"]) not in (int, Decimal):
            raise Invalid(f"Mode {name}: cost must be a positive JSON number")
        cost = Decimal(mode["cost"])
        if not cost.is_finite() or cost <= 0:
            raise Invalid(f"Mode {name}: cost must be finite and positive")
        events = artifact(root, mode["events"], ".jsonl.zst")
        weights = artifact(root, mode["weights"], ".csv")
        for path in (events, weights):
            if path in used_paths:
                warnings.append({"kind": "shared_artifact", "artifact": str(path.relative_to(root)),
                                 "modes": [used_paths[path], name]})
            else:
                used_paths[path] = name
        with tempfile.TemporaryDirectory(prefix="studio-math-") as directory:
            db = sqlite3.connect(str(Path(directory) / "outcomes.sqlite"))
            try:
                stats = load_table(weights, db)
                if books:
                    verify_lines(compressed_lines(events, zstandard), db)
            finally:
                db.close()
        with localcontext() as ctx:
            ctx.prec = 40
            rtp = Decimal(stats["weighted_payout_sum"]) / Decimal(stats["weight_sum"]) / 100 / cost
            hit = Decimal(stats["winning_weight"]) / Decimal(stats["weight_sum"])
            # Form the numerator with exact integers to avoid cancellation.
            variance_numerator = (stats["weighted_payout_squared_sum"] * stats["weight_sum"]
                                  - stats["weighted_payout_sum"] ** 2)
            variance = Decimal(variance_numerator) / Decimal(stats["weight_sum"] ** 2) / 10_000
            std_dev = variance.sqrt()
            normalized_std_dev = std_dev / cost
            max_recorded = Decimal(stats["max_recorded_payout"]) / 100
            max_reachable = Decimal(stats["max_reachable_payout"]) / 100
        reports.append({"mode": name, "cost": str(cost), "outcomes": stats["outcomes"],
                        "weight_sum": str(stats["weight_sum"]), "zero_weight_outcomes": stats["zero_weight_outcomes"],
                        "rtp_fraction": str(rtp), "nonzero_hit_probability": str(hit),
                        "payout_variance_base_bets_squared": str(variance),
                        "payout_std_dev_base_bets": str(std_dev),
                        "payout_std_dev_per_mode_cost": str(normalized_std_dev),
                        "max_recorded_payout_hundredths": stats["max_recorded_payout"],
                        "max_reachable_payout_hundredths": stats["max_reachable_payout"],
                        "max_recorded_payout_base_bets": str(max_recorded),
                        "max_reachable_payout_base_bets": str(max_reachable),
                        "events_bytes": events.stat().st_size, "books_verified": books})
    return {"ok": True, "scope": "structural and payout integrity; not Studio approval", "warnings": warnings, "modes": reports}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--books", action="store_true", help="Decompress and validate every book record")
    args = parser.parse_args(argv)
    try:
        report = inspect(args.directory, args.books)
    except (Invalid, OSError, ValueError, sqlite3.Error, csv.Error) as exc:
        print(json.dumps({"ok": False, "kind": "invalid", "books_requested": args.books, "error": str(exc)}, indent=2))
        return 1
    except Exception as exc:
        print(json.dumps({"ok": False, "kind": "internal_error", "error": str(exc)}, indent=2))
        return 3
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
