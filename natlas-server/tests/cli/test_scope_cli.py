import json

from app.cli.scope import export_items, import_items
from app.models import ScopeItem

DEFAULT_SCOPE_ITEMS = ["10.0.0.0/8", "192.168.1.0/24", "192.168.5.0/28"]


def mock_scope_file(scope_items: list = DEFAULT_SCOPE_ITEMS) -> str:
    with open("scope.txt", "w") as f:
        f.write("\n".join(scope_items))
    return "scope.txt"


def test_import_items_no_flags(runner):
    with runner.isolated_filesystem():
        scope_file = mock_scope_file()
        result = runner.invoke(import_items, [scope_file])
        assert result.exit_code == 0
        imported_scope = [item.target for item in ScopeItem.getScope()]
        assert imported_scope == DEFAULT_SCOPE_ITEMS
        result_dict = json.loads(result.output)
        assert len(result_dict["scope"]) == len(DEFAULT_SCOPE_ITEMS)


def test_import_items_scope_flag(runner):
    with runner.isolated_filesystem():
        scope_file = mock_scope_file()
        result = runner.invoke(import_items, ["--scope", scope_file])
        assert result.exit_code == 0
        imported_scope = [item.target for item in ScopeItem.getScope()]
        assert imported_scope == DEFAULT_SCOPE_ITEMS
        result_dict = json.loads(result.output)
        assert len(result_dict["scope"]) == len(DEFAULT_SCOPE_ITEMS)


def test_import_items_blacklist_flag(runner):
    with runner.isolated_filesystem():
        scope_file = mock_scope_file()
        result = runner.invoke(import_items, ["--blacklist", scope_file])
        assert result.exit_code == 0
        imported_blacklist = [item.target for item in ScopeItem.getBlacklist()]
        assert imported_blacklist == DEFAULT_SCOPE_ITEMS
        result_dict = json.loads(result.output)
        assert len(result_dict["blacklist"]) == len(DEFAULT_SCOPE_ITEMS)


def test_export_items_tagged(runner):
    scope_items = ["10.0.0.0/8,a", "192.168.5.0/28"]
    blacklist_items = ["192.168.1.0/24,b"]
    ScopeItem.import_scope_list(scope_items, False)
    ScopeItem.import_scope_list(blacklist_items, True)
    result = runner.invoke(export_items)
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    assert len(result_dict["scope"]) == 2
    assert result_dict["scope"][0]["tags"] == ["a"]
    assert result_dict["scope"][1]["tags"] == []
    assert len(result_dict["blacklist"]) == 1
    assert result_dict["blacklist"][0]["blacklist"] is True
    assert result_dict["blacklist"][0]["tags"] == ["b"]
