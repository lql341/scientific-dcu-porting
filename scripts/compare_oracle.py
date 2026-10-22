#!/usr/bin/env python3
"""Compare a device/HIP field dump against a CPU oracle dump (stdlib only).

Implements the numerical contract from references/porting-playbook.md:
absolute and scaled-relative error with numpy-allclose semantics
(|device - oracle| <= atol + rtol * |oracle|, elementwise), plus physical
invariants: finite values, positivity, and global-sum conservation.

Inputs are flat text dumps (whitespace/comma-separated numbers; lines that
are not numeric at all, such as headers, are skipped and counted) or .npy
files (little-endian f4/f8/i4/i8/u4/u8, C-order; parsed without numpy).

Exit codes: 0 pass, 1 comparison failed, 2 usage/IO error.
"""

import argparse
import ast
import json
import math
import pathlib
import re
import struct
import sys

VERSION = "1.0.0"

_NPY_TYPES = {
    "<f8": ("d", 8), "<f4": ("f", 4),
    "<i8": ("q", 8), "<i4": ("i", 4),
    "<u8": ("Q", 8), "<u4": ("I", 4),
}
_SPLIT = re.compile(r"[\s,;]+")


def load_npy(path):
    raw = path.read_bytes()
    if raw[:6] != b"\x93NUMPY":
        raise ValueError("%s: not an .npy file" % path)
    major = raw[6]
    if major == 1:
        (hlen,) = struct.unpack("<H", raw[8:10])
        off = 10
    else:
        (hlen,) = struct.unpack("<I", raw[8:12])
        off = 12
    header = ast.literal_eval(raw[off:off + hlen].decode("latin1").strip())
    descr = header["descr"]
    if descr not in _NPY_TYPES:
        raise ValueError("%s: unsupported dtype %r" % (path, descr))
    if header.get("fortran_order"):
        raise ValueError("%s: Fortran-order arrays are not supported" % path)
    shape = header["shape"]
    count = 1
    for dim in shape:
        count *= dim
    code, size = _NPY_TYPES[descr]
    body = raw[off + hlen:off + hlen + count * size]
    if len(body) != count * size:
        raise ValueError("%s: truncated array payload" % path)
    return [float(v) for v in struct.unpack("<%d%s" % (count, code), body)]


def load_text(path):
    values = []
    skipped = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.split("#", 1)[0].split("//", 1)[0].strip()
        if not line:
            continue
        tokens = [t for t in _SPLIT.split(line) if t]
        try:
            values.extend(float(t) for t in tokens)
        except ValueError:
            skipped += 1
    return values, skipped


def load_field(path):
    if path.suffix == ".npy":
        return load_npy(path), 0
    return load_text(path)


def compare(oracle, device, atol, rtol):
    failures = 0
    worst_abs = 0.0
    worst_rel = 0.0
    sum_abs2 = 0.0
    sum_ref2 = 0.0
    for ref, got in zip(oracle, device):
        diff = abs(got - ref)
        worst_abs = max(worst_abs, diff)
        scale = abs(ref)
        if scale > 0.0:
            worst_rel = max(worst_rel, diff / scale)
        sum_abs2 += diff * diff
        sum_ref2 += ref * ref
        if diff > atol + rtol * scale:
            failures += 1
    l2 = math.sqrt(sum_abs2)
    l2_rel = l2 / math.sqrt(sum_ref2) if sum_ref2 > 0.0 else (0.0 if l2 == 0.0 else float("inf"))
    return {
        "max_abs_error": worst_abs,
        "max_rel_error": worst_rel,
        "l2_error": l2,
        "l2_rel_error": l2_rel,
        "elements": len(oracle),
        "failing_elements": failures,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("oracle", type=pathlib.Path, help="CPU oracle dump (text or .npy)")
    parser.add_argument("device", type=pathlib.Path, help="device/HIP dump (text or .npy)")
    parser.add_argument("--atol", type=float, default=1e-8)
    parser.add_argument("--rtol", type=float, default=1e-5)
    parser.add_argument("--require-finite", action="store_true",
                        help="fail if either side contains NaN/Inf")
    parser.add_argument("--positive", action="store_true",
                        help="fail if the device field is not strictly positive "
                             "(density, pressure, ...)")
    parser.add_argument("--conservation", type=float, metavar="RTOL", default=None,
                        help="require |sum(device)-sum(oracle)| <= RTOL*|sum(oracle)|")
    parser.add_argument("--report", type=pathlib.Path, default=None,
                        help="write a JSON evidence report to this path")
    args = parser.parse_args(argv)

    try:
        oracle, skip_o = load_field(args.oracle)
        device, skip_d = load_field(args.device)
    except (OSError, ValueError) as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 2
    if not oracle or not device:
        print("ERROR: empty field (oracle=%d, device=%d values)"
              % (len(oracle), len(device)), file=sys.stderr)
        return 2
    if len(oracle) != len(device):
        print("ERROR: size mismatch: oracle=%d device=%d"
              % (len(oracle), len(device)), file=sys.stderr)
        return 2

    metrics = compare(oracle, device, args.atol, args.rtol)
    report = {
        "tool": "compare_oracle.py",
        "tool_version": VERSION,
        "oracle": str(args.oracle),
        "device": str(args.device),
        "atol": args.atol,
        "rtol": args.rtol,
        "skipped_header_lines": {"oracle": skip_o, "device": skip_d},
        "metrics": metrics,
        "invariants": {},
        "passed": True,
    }

    failures = []
    if metrics["failing_elements"]:
        failures.append("%d/%d elements exceed atol=%g rtol=%g (max_abs=%g, max_rel=%g)"
                        % (metrics["failing_elements"], metrics["elements"],
                           args.atol, args.rtol,
                           metrics["max_abs_error"], metrics["max_rel_error"]))

    nonfinite_oracle = sum(1 for v in oracle if not math.isfinite(v))
    nonfinite_device = sum(1 for v in device if not math.isfinite(v))
    report["invariants"]["nonfinite"] = {"oracle": nonfinite_oracle, "device": nonfinite_device}
    if args.require_finite and (nonfinite_oracle or nonfinite_device):
        failures.append("non-finite values: oracle=%d device=%d"
                        % (nonfinite_oracle, nonfinite_device))

    if args.positive:
        nonpos = sum(1 for v in device if not (v > 0.0) or not math.isfinite(v))
        report["invariants"]["positive"] = {"device_violations": nonpos}
        if nonpos:
            failures.append("positivity violated in %d device values" % nonpos)

    if args.conservation is not None:
        sum_o = math.fsum(oracle)
        sum_d = math.fsum(device)
        denom = abs(sum_o)
        cons_err = abs(sum_d - sum_o) / denom if denom > 0.0 else abs(sum_d - sum_o)
        report["invariants"]["conservation"] = {
            "oracle_sum": sum_o, "device_sum": sum_d,
            "rel_error": cons_err, "rtol": args.conservation,
        }
        if cons_err > args.conservation:
            failures.append("conservation violated: rel error %g > rtol %g"
                            % (cons_err, args.conservation))

    report["passed"] = not failures
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("elements=%d failing=%d max_abs=%.6g max_rel=%.6g l2_rel=%.6g"
          % (metrics["elements"], metrics["failing_elements"],
             metrics["max_abs_error"], metrics["max_rel_error"], metrics["l2_rel_error"]))
    for msg in failures:
        print("FAIL: %s" % msg)
    print("comparison: %s" % ("PASS" if not failures else "FAIL"))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
