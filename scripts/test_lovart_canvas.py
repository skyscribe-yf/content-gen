import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lovart_canvas


class PromptDiscoveryTest(unittest.TestCase):
    def make_article(self, root: Path) -> Path:
        article = root / "2026-07-20-tokenizer"
        (article / "prompts").mkdir(parents=True)
        (article / "weixin.md").write_text(
            '---\ntitle: "Tokenizer：AI 如何切词"\n---\n正文', encoding="utf-8"
        )
        return article

    def test_discovers_sorted_prompts_strips_front_matter_and_derives_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            article = self.make_article(Path(tmp))
            (article / "prompts" / "02-vector.md").write_text("vector prompt", encoding="utf-8")
            (article / "prompts" / "00-cover.md").write_text(
                "---\nartist: author\n---\ncover prompt", encoding="utf-8"
            )

            plan = lovart_canvas.discover_article(article)

            self.assertEqual(plan.project_name, "Tokenizer：AI 如何切词")
            self.assertEqual(
                [(job.source.name, job.aspect_ratio, job.output.name, job.prompt) for job in plan.jobs],
                [
                    ("00-cover.md", "21:9", "00-cover.png", "cover prompt"),
                    ("02-vector.md", "1:1", "02-vector.png", "vector prompt"),
                ],
            )

    def test_falls_back_to_directory_name_and_rejects_empty_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            article = Path(tmp) / "2026-07-20-tokenizer"
            (article / "prompts").mkdir(parents=True)
            (article / "prompts" / "01-empty.md").write_text("---\na: b\n---\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "01-empty.md.*empty"):
                lovart_canvas.discover_article(article)


if __name__ == "__main__":
    unittest.main()
