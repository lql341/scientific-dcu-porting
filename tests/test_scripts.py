import json
import pathlib
import struct
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_evidence  # noqa: E402
import compare_oracle  # noqa: E402
import validate  # noqa: E402


def write_npy(path, values, descr="<f8"):
    header = "{'descr': '%s', 'fortran_order': False, 'shape': (%d,), }" \
        % (descr, len(values))
    pad = 64 - ((10 + len(header) + 1) % 64)
    header = header + " " * pad + "\n"
    with open(str(path), "wb") as fh:
        fh.write(b"\x93NUMPY\x01\x00")
        fh.write(struct.pack("<H", len(header)))
        fh.write(header.encode("latin1"))
        fh.write(struct.pack("<%dd" % len(values), *values))


class CompareOracleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = pathlib.Path(self.tmp.name)
        self.oracle = self.dir / "oracle.txt"
        self.device = self.dir / "device.txt"

    def write(self, a, b):
        self.oracle.write_text("\n".join(str(v) for v in a), encoding="utf-8")
        self.device.write_text("\n".join(str(v) for v in b), encoding="utf-8")

    def run_cli(self, *extra):
        return compare_oracle.main(
            [str(self.oracle), str(self.device)] + [str(a) for a in extra])

    def test_identical_passes(self):
        self.write([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
        self.assertEqual(0, self.run_cli())

    def test_within_tolerance_passes(self):
        self.write([1.0, 2.0], [1.0 + 1e-6, 2.0 - 1e-6])
        self.assertEqual(0, self.run_cli("--atol", "1e-5", "--rtol", "1e-5"))

    def test_beyond_tolerance_fails(self):
        self.write([1.0], [1.1])
        self.assertEqual(1, self.run_cli("--atol", "1e-6", "--rtol", "1e-6"))

    def test_size_mismatch_is_error(self):
        self.write([1.0, 2.0], [1.0])
        self.assertEqual(2, self.run_cli())

    def test_require_finite_fails_on_nan(self):
        self.write([1.0, float("nan")], [1.0, float("nan")])
        self.assertEqual(1, self.run_cli("--require-finite"))

    def test_positive_fails_on_nonpositive(self):
        self.write([1.0, 0.5], [1.0, -0.1])
        self.assertEqual(1, self.run_cli("--positive", "--atol", "1",
                                         "--rtol", "1"))

    def test_conservation_fails_on_sum_drift(self):
        self.write([1.0, 1.0, 1.0], [1.0, 1.0, 1.5])
        self.assertEqual(1, self.run_cli("--atol", "1", "--rtol", "1",
                                         "--conservation", "1e-6"))

    def test_headers_skipped_and_report_written(self):
        self.oracle.write_text("step rho u\n1.0 2.0 3.0\n", encoding="utf-8")
        self.device.write_text("step rho u\n1.0 2.0 3.0\n", encoding="utf-8")
        report = self.dir / "report.json"
        rc = compare_oracle.main([str(self.oracle), str(self.device),
                                  "--report", str(report)])
        self.assertEqual(0, rc)
        data = json.loads(report.read_text(encoding="utf-8"))
        self.assertTrue(data["passed"])
        self.assertEqual(1, data["skipped_header_lines"]["oracle"])
        self.assertEqual(3, data["metrics"]["elements"])

    def test_npy_roundtrip_without_numpy(self):
        values = [1.5, -2.5, 3.25]
        npy = self.dir / "a.npy"
        write_npy(npy, values)
        loaded, _ = compare_oracle.load_field(npy)
        self.assertEqual(values, loaded)
        self.device.write_text("\n".join(str(v) for v in values),
                               encoding="utf-8")
        self.assertEqual(0, compare_oracle.main(
            [str(npy), str(self.device)]))


def valid_card():
    return {
        "schema_version": 1,
        "application": "minicfd",
        "upstream_version": "v2.3",
        "dtk_version": "24.04",
        "target_arch": "gfx906",
        "node_context": "compute-node",
        "evidence_level": "stage-on-device",
        "visible_devices": 1,
        "resource_tuple": {"partition": "dcu", "nodes": 1, "dcus": 1},
        "test_summary": "42/42 gtest",
        "tolerance_baseline": "max_rel=2e-12, CPU oracle gcc build",
        "untested_boundaries": ["multi-node", "fp16"],
    }


class CheckEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cases = pathlib.Path(self.tmp.name) / "assets" / "cases"
        self.cases.mkdir(parents=True)

    def lint(self):
        check_evidence.errors.clear()
        check_evidence.warnings.clear()
        return check_evidence.main(["--root", str(pathlib.Path(self.tmp.name))])

    def write_card(self, card, name="card.json"):
        (self.cases / name).write_text(json.dumps(card), encoding="utf-8")

    def test_valid_card_passes(self):
        self.write_card(valid_card())
        self.assertEqual(0, self.lint())

    def test_missing_field_fails(self):
        card = valid_card()
        del card["dtk_version"]
        self.write_card(card)
        self.assertEqual(1, self.lint())

    def test_login_node_cannot_claim_stage_on_device(self):
        card = valid_card()
        card["node_context"] = "login-node"
        self.write_card(card)
        self.assertEqual(1, self.lint())

    def test_private_path_fails(self):
        card = valid_card()
        card["test_summary"] = "logs in " + "/public/" + "home/alice/run"
        self.write_card(card)
        self.assertEqual(1, self.lint())

    def test_job_id_key_fails(self):
        card = valid_card()
        card["slurm_job_id"] = "123456"
        self.write_card(card)
        self.assertEqual(1, self.lint())

    def test_underscore_files_skipped(self):
        (self.cases / "_template.json").write_text("{}", encoding="utf-8")
        self.write_card(valid_card())
        self.assertEqual(0, self.lint())

    def test_repo_template_parses(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        check_evidence.errors.clear()
        check_evidence.warnings.clear()
        self.assertEqual(0, check_evidence.main(["--root", str(root)]))


class ValidateTests(unittest.TestCase):
    def test_repository_passes_self_validation(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        validate.errors.clear()
        self.assertEqual(0, validate.main(["--root", str(root)]))


if __name__ == "__main__":
    unittest.main()
