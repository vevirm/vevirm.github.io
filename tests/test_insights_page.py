from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InsightsPageTests(unittest.TestCase):
    def test_insights_is_only_topics_and_bullets(self):
        page = (ROOT / "insights" / "index.html").read_text(encoding="utf-8")
        self.assertIn("<h1>Radar insights</h1>", page)
        self.assertIn("One point per radar signal, grouped by topic.", page)
        self.assertIn('fetch("../radar.json?v="+Date.now()', page)
        self.assertIn('name:"Raw materials & supply chains"', page)
        self.assertIn('name:"Research & science"', page)
        self.assertIn('name:"AI"', page)
        self.assertIn("<h2>${esc(g.name)}</h2><ul>", page)
        self.assertIn("<li>${esc(x.point)}</li>", page)

        for clutter in (
            "Radar relevance:",
            "Strand A",
            "Strand B",
            "Strand C",
            "source_tier",
            "Also touches",
            "How this page works",
            "topic-nav",
            "item count",
        ):
            self.assertNotIn(clutter, page)

    def test_old_briefing_url_redirects_to_new_insights_path(self):
        page = (ROOT / "briefing" / "index.html").read_text(encoding="utf-8")
        self.assertIn("../insights/?v=6", page)
        self.assertNotIn("Radar relevance:", page)
        self.assertNotIn("Strand A", page)

    def test_main_page_links_to_new_insights_path(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="insights/?v=6"', page)
        self.assertNotIn('href="briefing/?v=5"', page)

    def test_no_separate_briefing_generator_workflow_exists(self):
        self.assertFalse((ROOT / ".github" / "workflows" / "radar-briefing.yml").exists())


if __name__ == "__main__":
    unittest.main()
