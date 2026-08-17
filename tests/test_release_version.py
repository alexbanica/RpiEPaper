import contextlib
import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.release_version import parse_release_tag, prepare_release_tree


class ReleaseTagTestCase(unittest.TestCase):
    def test_stable_tags_map_to_the_same_python_version(self):
        for tag in ("0.0.1", "1.2.3", "10.20.30"):
            with self.subTest(tag=tag):
                self.assertEqual(tag, parse_release_tag(tag))

    def test_beta_tags_map_to_pep440_beta_versions(self):
        cases = {
            "1.2.3-beta1": "1.2.3b1",
            "1.2.3-beta4": "1.2.3b4",
            "10.20.30-beta12": "10.20.30b12",
        }
        for tag, expected in cases.items():
            with self.subTest(tag=tag):
                self.assertEqual(expected, parse_release_tag(tag))

    def test_rejects_tags_outside_the_exact_stable_and_beta_grammar(self):
        invalid_tags = (
            "v1.2.3",
            " 1.2.3",
            "1.2.3 ",
            "01.2.3",
            "1.02.3",
            "1.2.03",
            "1.2.3-beta0",
            "1.2.3-beta",
            "1.2.3-beta01",
            "1.2.3-alpha1",
            "1.2.3-rc1",
            "1.2.3-beta1.2",
            "1.2.3-beta1+build7",
            "1.2.3+build7",
            "1.2",
            "1.2.3.4",
            "",
            "١.2.3",
            "1.٠.3",
            "1.2.٣",
            "1.2.3-beta١",
            "１２.13.14",
            "12.１３.14",
            "12.13.１４",
            "12.13.14-beta２",
        )
        for tag in invalid_tags:
            with self.subTest(tag=tag):
                with self.assertRaises(ValueError):
                    parse_release_tag(tag)


class ReleaseTreePreparationTestCase(unittest.TestCase):
    def _source_tree(self, parent):
        source = Path(parent) / "source"
        (source / "cluster_monitor").mkdir(parents=True)
        (source / "pyproject.toml").write_text(
            '[project]\nname = "cluster_monitor"\nversion = "9.8.7"\n',
            encoding="utf-8",
        )
        (source / "cluster_monitor" / "__init__.py").write_text(
            '__version__ = "9.8.7"\n', encoding="utf-8"
        )
        return source

    def test_prepares_isolated_tree_with_aligned_metadata_and_cleans_it_up(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            source = self._source_tree(tmp_dir)
            before = {
                path: hashlib.sha256(path.read_bytes()).digest()
                for path in (source / "pyproject.toml", source / "cluster_monitor" / "__init__.py")
            }

            with prepare_release_tree(source, "2.3.4-beta5") as release_tree:
                release_tree = Path(release_tree)
                self.assertNotEqual(source.resolve(), release_tree.resolve())
                self.assertTrue(release_tree.exists())
                metadata = (release_tree / "pyproject.toml").read_text(encoding="utf-8")
                runtime = (release_tree / "cluster_monitor" / "__init__.py").read_text(
                    encoding="utf-8"
                )
                self.assertIn('version = "2.3.4b5"', metadata)
                self.assertIn('__version__ = "2.3.4b5"', runtime)
                self.assertEqual("2.3.4b5", parse_release_tag("2.3.4-beta5"))

            self.assertFalse(release_tree.exists())
            for path, digest in before.items():
                self.assertEqual(digest, hashlib.sha256(path.read_bytes()).digest())
            self.assertEqual(
                '[project]\nname = "cluster_monitor"\nversion = "9.8.7"\n',
                (source / "pyproject.toml").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                '__version__ = "9.8.7"\n',
                (source / "cluster_monitor" / "__init__.py").read_text(encoding="utf-8"),
            )

    def test_cleanup_occurs_when_release_tree_body_raises(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            source = self._source_tree(tmp_dir)
            manager = prepare_release_tree(source, "2.3.4")
            with self.assertRaises(RuntimeError):
                with contextlib.ExitStack() as stack:
                    release_tree = Path(stack.enter_context(manager))
                    self.assertTrue(release_tree.exists())
                    raise RuntimeError("stop inside release tree")
            self.assertFalse(release_tree.exists())


if __name__ == "__main__":
    unittest.main()
