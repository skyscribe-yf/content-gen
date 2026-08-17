"""Focused tests for the generic, microphone-independent recording-studio helpers."""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess, run
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import voice_studio


class VoiceStudioHelpersTest(unittest.TestCase):
    def test_load_segments_uses_all_non_empty_tts_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "tts.txt"
            script.write_text("第一段。\n\n第二段。\n第三段。\n", encoding="utf-8")
            segments = voice_studio.load_segments(script)

        self.assertEqual(
            segments,
            [
                {"id": "s1", "text": "第一段。"},
                {"id": "s2", "text": "第二段。"},
                {"id": "s3", "text": "第三段。"},
            ],
        )

    def test_load_segments_rejects_an_empty_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "tts.txt"
            script.write_text(" \n\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "非空行"):
                voice_studio.load_segments(script)

    def test_sentence_clips_keep_every_pause_and_all_transcript_text(self) -> None:
        text = "第一句话。第二句话。第三句话。"
        clips = voice_studio.make_sentence_clips("s12", text, 12.0, [3.4, 8.1, 3.4, -1, 13])

        self.assertEqual([clip["id"] for clip in clips], ["s12-c01", "s12-c02", "s12-c03"])
        self.assertEqual([clip["start"] for clip in clips], [0.0, 3.4, 8.1])
        self.assertEqual([clip["end"] for clip in clips], [3.4, 8.1, 12.0])
        self.assertEqual("".join(clip["text"] for clip in clips), text)

    def test_trim_bounds_fall_back_to_the_full_audio_when_no_silence_is_found(self) -> None:
        with patch.object(voice_studio, "ffprobe_dur", return_value=9.25), patch.object(
            voice_studio.trim_silence, "speech_bounds", return_value=None
        ):
            self.assertEqual(voice_studio.build_trim_bounds(Path("take.wav")), (0.0, 9.25))

    def test_trim_only_removes_silence_that_touches_an_audio_edge(self) -> None:
        # The first 0.49 seconds contain speech, followed by an internal pause.
        # The old algorithm incorrectly started at the first silence_end (0.49).
        silence_log = """silence_start: 0.332\nsilence_end: 0.491\nsilence_start: 18.815\nsilence_end: 20.096\n"""
        with patch.object(
            voice_studio.trim_silence,
            "run",
            side_effect=[
                CompletedProcess([], 0, stderr=silence_log),
                CompletedProcess([], 0, stdout="20.096\n"),
            ],
        ):
            self.assertEqual(voice_studio.trim_silence.speech_bounds(Path("take.wav")), (0.0, 18.815))

    def test_trim_removes_a_real_leading_and_trailing_silence(self) -> None:
        silence_log = """silence_start: 0\nsilence_end: 1.2\nsilence_start: 8.4\nsilence_end: 10\n"""
        with patch.object(
            voice_studio.trim_silence,
            "run",
            side_effect=[
                CompletedProcess([], 0, stderr=silence_log),
                CompletedProcess([], 0, stdout="10\n"),
            ],
        ):
            self.assertEqual(voice_studio.trim_silence.speech_bounds(Path("take.wav")), (1.2, 8.4))

    def test_audio_stream_ignores_a_browser_cancelled_request(self) -> None:
        class CancelledClient:
            def write(self, _body: bytes) -> None:
                raise ConnectionResetError

        class FakeHandler:
            wfile = CancelledClient()

            def send_response(self, _status: int) -> None:
                return None

            def send_header(self, _name: str, _value: str) -> None:
                return None

            def end_headers(self) -> None:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            recording = Path(tmp) / "recordings"
            recording.mkdir()
            (recording / "s1.wav").write_bytes(b"wav")
            with patch.object(voice_studio, "WD", Path(tmp), create=True), patch.object(
                voice_studio, "find_segment", return_value={"id": "s1"}
            ):
                voice_studio.Handler._audio(FakeHandler(), "raw", "s1")

    def test_studio_page_disables_browser_caching(self) -> None:
        class FakeHandler:
            path = "/"
            wfile = io.BytesIO()

            def __init__(self) -> None:
                self.headers: list[tuple[str, str]] = []

            def send_response(self, _status: int) -> None:
                return None

            def send_header(self, name: str, value: str) -> None:
                self.headers.append((name, value))

            def end_headers(self) -> None:
                return None

        handler = FakeHandler()
        voice_studio.Handler.do_GET(handler)
        self.assertIn(("Cache-Control", "no-store"), handler.headers)

    def test_page_updates_only_the_countdown_during_steady_polling(self) -> None:
        self.assertIn("lastRenderKey=''", voice_studio.PAGE)
        self.assertIn("function updateLive(state)", voice_studio.PAGE)
        self.assertIn("const {countdown,...stable}=state", voice_studio.PAGE)
        self.assertIn("else{selectedSegmentId=null;await refresh()}return data", voice_studio.PAGE)

    def test_punctuation_blocks_are_the_smallest_editable_units(self) -> None:
        self.assertEqual(
            voice_studio.punctuation_blocks("先说一遍，然后解释：最后收束。"),
            ["先说一遍，", "然后解释：", "最后收束。"],
        )

    def test_alignment_groups_only_contiguous_punctuation_blocks(self) -> None:
        text = "第一句。第二句，第三句。"
        clips = voice_studio.validate_alignment(
            "s1",
            text,
            8.0,
            [
                {"start": 0, "end": 5, "block_start": 0, "block_end": 1, "text": "第一句。第二句，"},
                {"start": 5, "end": 8, "block_start": 2, "block_end": 2, "text": "第三句。"},
            ],
        )

        self.assertEqual([clip["text"] for clip in clips], ["第一句。第二句，", "第三句。"])
        self.assertEqual([clip["block_start"] for clip in clips], [0, 2])

    def test_alignment_rejects_a_partial_punctuation_block(self) -> None:
        with self.assertRaisesRegex(ValueError, "不对应"):
            voice_studio.validate_alignment(
                "s1",
                "第一句。第二句。",
                4.0,
                [
                    {"start": 0, "end": 2, "block_start": 0, "block_end": 0, "text": "第一"},
                    {"start": 2, "end": 4, "block_start": 1, "block_end": 1, "text": "第二句。"},
                ],
            )

    def test_queue_editor_supports_1_to_3_audio_and_text_blocks(self) -> None:
        self.assertIn("automaticPlan", voice_studio.PAGE)
        self.assertIn("连续 1～3 段音频", voice_studio.PAGE)
        self.assertIn("deletePiece", voice_studio.PAGE)
        self.assertIn("audio_count", voice_studio.PAGE)
        self.assertIn("confirmAutoSubtitle", voice_studio.PAGE)
        self.assertIn("确认字幕", voice_studio.PAGE)
        self.assertIn("当前字幕：", voice_studio.PAGE)

    def test_confirmed_segments_can_be_selected_for_rerecording(self) -> None:
        self.assertIn("selectedSegmentId", voice_studio.PAGE)
        self.assertIn("function selectSegment(segmentId)", voice_studio.PAGE)
        self.assertIn("s.status!=='pending'", voice_studio.PAGE)
        self.assertIn("segment.status==='approved'", voice_studio.PAGE)

    def test_start_record_allows_rerecording_an_approved_segment(self) -> None:
        original_segs = voice_studio.SEGS
        original_session = voice_studio.SESSION
        original_runtime = voice_studio.RUNTIME
        try:
            voice_studio.SEGS = [{"id": "s1", "text": "第一句。"}]
            voice_studio.SESSION = {"s1": {"status": "approved", "analysis": {}}}
            voice_studio.RUNTIME = {
                "recording": None,
                "process": None,
                "stop_event": None,
                "mic": {"available": True, "input_ready": True},
                "finalize": {"status": "complete", "message": ""},
            }
            with patch.object(voice_studio.threading, "Thread") as thread:
                ok, message = voice_studio.start_record("s1")

            self.assertTrue(ok)
            self.assertEqual(message, "倒计时开始")
            thread.return_value.start.assert_called_once_with()
            self.assertEqual(voice_studio.RUNTIME["recording"]["seg"], "s1")
            # A new take invalidates the previous handoff: the finished card
            # must offer regeneration again after the segment is re-approved.
            self.assertEqual(voice_studio.RUNTIME["finalize"]["status"], "idle")
        finally:
            voice_studio.SEGS = original_segs
            voice_studio.SESSION = original_session
            voice_studio.RUNTIME = original_runtime

    def test_public_state_marks_the_rerecorded_segment_as_active(self) -> None:
        original_segs = voice_studio.SEGS
        original_session = voice_studio.SESSION
        original_runtime = voice_studio.RUNTIME
        try:
            voice_studio.SEGS = [
                {"id": "s1", "text": "第一句。"},
                {"id": "s2", "text": "第二句。"},
            ]
            voice_studio.SESSION = {
                "s1": {"status": "approved", "analysis": {}},
                "s2": {"status": "approved", "analysis": {}},
            }
            voice_studio.RUNTIME = {
                "recording": {"seg": "s1", "started_at": 0},
                "mic": {},
                "finalize": {"status": "idle", "message": ""},
            }

            state = voice_studio.public_state()

            self.assertIsNone(state["current"])
            self.assertTrue(state["segments"][0]["is_current"])
            self.assertFalse(state["segments"][1]["is_current"])
        finally:
            voice_studio.SEGS = original_segs
            voice_studio.SESSION = original_session
            voice_studio.RUNTIME = original_runtime

    def test_queue_reflow_keeps_the_next_single_candidate_after_a_delete(self) -> None:
        # When the first audio is deleted, audio 2 and 3 consume text blocks 1
        # and 2.  The fourth audio must therefore start with block 3 alone;
        # grouping is deferred to the tail where it is unavoidable.
        script = voice_studio.PAGE.split("<script>", 1)[1].split("</script>", 1)[0]
        harness = """
const document={querySelector:()=>({innerHTML:'',textContent:''}),getElementById:()=>null};
const setInterval=()=>0;
const fetch=async()=>({json:async()=>({segments:[],countdown:0,mic:{},mic_probing:false,finalize:{}})});
"""
        probe = """
const blocks=['一。','二。','三。','四。','五。','六。','七。','八。'];
const pieces=Array.from({length:10},(_,i)=>({text:String(i),start:i,end:i+1}));
const model={blocks,pieces,overrides:new Map([[0,{delete:true}],[1,{audioCount:1,textCount:1}],[2,{audioCount:1,textCount:1}]]),plan:[],error:''};
rebuildPlan(model);
const fourth=model.plan.find(group=>group.audioStart===3);
if(!fourth||fourth.textStart!==2||fourth.textCount!==1)process.exit(1);
alignments.set('s1',model);
refreshAlignment=()=>{};
confirmAutoSubtitle('s1',3);
const confirmed=model.plan.find(group=>group.audioStart===3);
if(!confirmed||!confirmed.manual||!model.overrides.has(3))process.exit(2);
"""
        result = run(["node", "-e", harness + script + probe], check=False, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_piece_alignment_delete_leaves_the_next_piece_on_the_first_text_block(self) -> None:
        source = [
            {"id": "s1-c01", "start": 0, "end": 1},
            {"id": "s1-c02", "start": 1, "end": 2},
            {"id": "s1-c03", "start": 2, "end": 3},
        ]
        clips, deleted = voice_studio.validate_piece_alignment(
            "s1",
            "第一句。第二句。第三句。",
            3.0,
            source,
            [
                {"audio_start": 0, "delete": True},
                {"audio_start": 1, "audio_count": 1, "block_start": 0, "block_end": 0},
                {"audio_start": 2, "audio_count": 1, "block_start": 1, "block_end": 2},
            ],
        )

        self.assertEqual(deleted, [(0.0, 1.0)])
        self.assertEqual([clip["text"] for clip in clips], ["第一句。", "第二句。第三句。"])
        self.assertEqual(clips[0]["audio_start"], 1)

    def test_piece_alignment_allows_three_audio_pieces_for_one_text_block(self) -> None:
        source = [
            {"id": "s1-c01", "start": 0, "end": 1},
            {"id": "s1-c02", "start": 1, "end": 2},
            {"id": "s1-c03", "start": 2, "end": 3},
        ]
        clips, deleted = voice_studio.validate_piece_alignment(
            "s1",
            "一句话。",
            3.0,
            source,
            [{"audio_start": 0, "audio_count": 3, "block_start": 0, "block_end": 0}],
        )

        self.assertEqual(deleted, [])
        self.assertEqual(clips[0]["audio_count"], 3)
        self.assertEqual((clips[0]["start"], clips[0]["end"]), (0.0, 3.0))


if __name__ == "__main__":
    unittest.main()
