from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InsightsPageTests(unittest.TestCase):
    def test_page_is_direct_topic_and_bullets_view(self):
        page = (ROOT / "briefing" / "index.html").read_text(encoding="utf-8")
        self.assertIn("<h1>Radar insights</h1>", page)
        self.assertIn("grouped by topic", page)
        self.assertIn('fetch("../radar.json?v="+Date.now()', page)
        self.assertIn('name:"Raw materials"', page)
        self.assertIn('name:"Research"', page)
        self.assertIn('name:"AI"', page)
        self.assertIn("<h2>${esc(g.name)}</h2><ul>", page)

        for old_ui in (
            "Radar relevance:",
            "Also touches",
            "How this page works",
            "TOPIC</div>",
            "institutional report",
            "briefing.json?",
            "source-label",
            "topic-nav",
        ):
            self.assertNotIn(old_ui, page)

    def test_publish_workflow_cannot_rebuild_briefing_html(self):
        workflow = (ROOT / ".github" / "workflows" / "radar-briefing.yml").read_text(encoding="utf-8")
        self.assertNotIn("build_briefing.py", workflow)
        self.assertNotIn("git add briefing", workflow)
        self.assertNotIn("briefing.json", workflow)
        self.assertIn("pages/builds", workflow)


if __name__ == "__main__":
    unittest.main()
