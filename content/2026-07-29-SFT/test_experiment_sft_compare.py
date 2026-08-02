import ast
from pathlib import Path


SCRIPT = Path(__file__).with_name("experiment_sft_compare.py")


def test_uses_matched_qwen3_base_and_instruct_checkpoints():
    assignments = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in ast.parse(SCRIPT.read_text(encoding="utf-8")).body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in {"MODEL_BASE", "MODEL_INSTRUCT"}
    }

    assert assignments == {
        "MODEL_BASE": "Qwen/Qwen3-8B-Base",
        "MODEL_INSTRUCT": "Qwen/Qwen3-8B",
    }


def test_preserves_both_8b_checkpoints():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "rmtree"
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.Name) and node.id == "BitsAndBytesConfig"
        for node in ast.walk(tree)
    )


def test_disables_instruct_thinking_for_answer_token_comparison():
    calls = [
        node
        for node in ast.walk(ast.parse(SCRIPT.read_text(encoding="utf-8")))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "apply_chat_template"
    ]

    assert any(
        keyword.arg == "enable_thinking"
        and isinstance(keyword.value, ast.Constant)
        and keyword.value.value is False
        for call in calls
        for keyword in call.keywords
    )
