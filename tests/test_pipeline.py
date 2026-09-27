import json
import tempfile
import unittest
from pathlib import Path

from anime_knowledge_video.contracts import GateError, check_duration, check_storyboard
from anime_knowledge_video.episode import create_episode
from anime_knowledge_video.io import slug
from anime_knowledge_video.romance.content_dedup import check_new_content
from anime_knowledge_video.romance.workflow import create_chapter, create_series


class PipelineTests(unittest.TestCase):
    def test_episode_pack_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            result = create_episode("为什么夜空是黑的？", output_root=directory)
            self.assertEqual(result["status"], "planning_only")
            self.assertIsNone(result["final_mp4"])
            project = Path(result["project_dir"])
            shots = json.loads((project / "storyboard/storyboard.json").read_text())
            check_storyboard(shots, 60)
            claims = json.loads((project / "research/claims.json").read_text())
            self.assertTrue(all(c["source_url"].startswith("https://") for c in claims))
            self.assertFalse((project / "renders/final.mp4").exists())

    def test_duration_gate(self):
        for value in (54, 66):
            with self.assertRaises(GateError):
                check_duration(value)
        check_duration(60)
        check_duration(120, romance=True)

    def test_unknown_topic_stops_before_inventing_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(GateError, "No source pack"):
                create_episode("没有资料的新主题", output_root=directory)
            self.assertFalse((Path(directory) / slug("没有资料的新主题")).exists())

    def test_romance_binding_and_continuity(self):
        with tempfile.TemporaryDirectory() as directory:
            create_series(output_root=directory)
            first = create_chapter("after-the-rain-route", 1, output_root=directory)
            self.assertIsNone(first["final_mp4"])
            chapter = Path(first["chapter_dir"])
            lines = json.loads((chapter / "script/dialogue_timed.json").read_text())
            captions = (chapter / "subtitles/zh-CN.srt").read_text()
            self.assertTrue(all(x["zh_CN"] in captions for x in lines))
            with self.assertRaisesRegex(GateError, "in order"):
                create_chapter("after-the-rain-route", 3, output_root=directory)
            second = create_chapter("after-the-rain-route", 2, output_root=directory)
            self.assertEqual(second["status"], "planning_only")
            state = json.loads((Path(directory) / "after-the-rain-route/continuity/state.json").read_text())
            self.assertEqual(state["last_chapter"], 2)

    def test_dedup_rejects_old_dialogue(self):
        with self.assertRaisesRegex(GateError, "dialogue repeats"):
            check_new_content([{"ja": "同じ言葉。"}], [{"composition": "new", "action": "walk"}],
                              {"dialogue_hashes": [__import__("hashlib").sha256("同じ言葉".encode()).hexdigest()], "shot_hashes": []})


if __name__ == "__main__":
    unittest.main()

