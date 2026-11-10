import json

from envcheck_101126 import cli


def test_json_output(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["envcheck_101126", "--json"])
    cli.main()
    output = json.loads(capsys.readouterr().out)
    assert "python_version" in output
    assert isinstance(output["python_version"], str)
