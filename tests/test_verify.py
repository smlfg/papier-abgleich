#!/usr/bin/env python3
"""Tests für tools/verify.py: Chrome-Suche und CLI-Parsing, ohne Browserstart."""
import unittest

from tools.verify import find_chrome, parse_args


class FindChromeTest(unittest.TestCase):
    def test_explicit_gewinnt(self):
        self.assertEqual(
            find_chrome(explicit="/opt/chrome", env={"CHROME": "/env/chrome"},
                        which=lambda name: "/usr/bin/google-chrome",
                        exists=lambda path: True),
            "/opt/chrome",
        )

    def test_env_gewinnt_gegen_path(self):
        self.assertEqual(
            find_chrome(env={"CHROME": "/env/chrome"},
                        which=lambda name: "/usr/bin/google-chrome",
                        exists=lambda path: False),
            "/env/chrome",
        )

    def test_linux_kandidat_aus_path(self):
        def which(name):
            return "/usr/bin/chromium" if name == "chromium" else None
        self.assertEqual(
            find_chrome(env={}, which=which, exists=lambda path: False),
            "/usr/bin/chromium",
        )

    def test_macos_app_bundle(self):
        bundle = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        self.assertEqual(
            find_chrome(env={"HOME": "/Users/test"},
                        which=lambda name: None,
                        exists=lambda path: path == bundle),
            bundle,
        )

    def test_nicht_gefunden(self):
        self.assertIsNone(
            find_chrome(env={"HOME": "/Users/test"},
                        which=lambda name: None,
                        exists=lambda path: False),
        )


class ParseArgsTest(unittest.TestCase):
    def test_chrome_option(self):
        self.assertEqual(
            parse_args(["page.html", "#node", "--text", "--chrome", "/opt/chrome"]),
            ("page.html", "#node", True, "/opt/chrome"),
        )

    def test_chrome_option_mit_gleichheitszeichen(self):
        self.assertEqual(
            parse_args(["page.html", "--chrome=/opt/chrome"]),
            ("page.html", "", False, "/opt/chrome"),
        )


if __name__ == "__main__":
    unittest.main()
