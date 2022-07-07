import pathlib

import pytest
import json

from typer.testing import CliRunner

from toml_cli import app

runner = CliRunner()


def normalized(item):
  if isinstance(item, dict):
      return sorted((key, normalized(values)) for key, values in item.items())
  if isinstance(item, list):
      return sorted(normalized(x) for x in item)
  else:
      return item


def compare(item1, item2):
    assert normalized(item1) == normalized(item2)


def test_get_value(tmp_path: pathlib.Path):
    test_toml_path = tmp_path / "test.toml"
    test_toml_path.write_text(
        """
[person]
name = "MyName"
age = 12

[person.education]
name = "University"
"""
    )

    def get(args):
        result = runner.invoke(app, args)
        assert result.exit_code == 0
        return json.loads(result.stdout.strip())

    compare(
        get(["get", "--toml-path", str(test_toml_path), "person"]),
        {
            "name": "MyName",
            "age": 12,
            "education": {
                "name": "University"
            }
        }
    )

    compare(
        get(["get", "--toml-path", str(test_toml_path), "person", "education"]),
        { "name": "University" }
    )

    compare(
        get(["get", "--toml-path", str(test_toml_path), "person", "education", "name"]),
        "University"
    )

    compare(
        get(["get", "--toml-path", str(test_toml_path), "person", "age"]),
        12
    )


def test_set_value(tmp_path: pathlib.Path):
    test_toml_path = tmp_path / "test.toml"
    test_toml_path.write_text(
        """
[person]
name = "MyName"
happy = false
age = 12

[person.education]
name = "University"
"""
    )

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "15", "person", "age"])
    assert result.exit_code == 0
    assert 'age = "15"' in test_toml_path.read_text()

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "--to-int", "15", "person", "age"])
    assert result.exit_code == 0
    assert "age = 15" in test_toml_path.read_text()

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "male", "person", "gender"])
    assert result.exit_code == 0
    assert 'age = 15\ngender = "male"' in test_toml_path.read_text()

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "--to-float", "15", "person", "age"])
    assert result.exit_code == 0
    assert "age = 15.0" in test_toml_path.read_text()

    result = runner.invoke(app, ["set", "--toml-path", str(test_toml_path), "--to-bool", "True", "person", "happy"])
    assert result.exit_code == 0
    assert "happy = true" in test_toml_path.read_text()


def test_add_section(tmp_path: pathlib.Path):
    test_toml_path = tmp_path / "test.toml"
    test_toml_path.write_text(
        """
[person]
name = "MyName"
age = 12

[person.education]
name = "University"
"""
    )

    result = runner.invoke(app, ["add_section", "--toml-path", str(test_toml_path), "address"])
    assert result.exit_code == 0
    assert "[address]" in test_toml_path.read_text()

    result = runner.invoke(app, ["add_section", "--toml-path", str(test_toml_path), "address.work"])
    assert result.exit_code == 0
    assert "[address]\n[address.work]" in test_toml_path.read_text()


def test_unset(tmp_path: pathlib.Path):
    test_toml_path = tmp_path / "test.toml"
    test_toml_path.write_text(
        """
[person]
name = "MyName"
age = 12

[person.education]
name = "University"
"""
    )

    result = runner.invoke(app, ["unset", "--toml-path", str(test_toml_path), "person", "education", "name"])
    assert result.exit_code == 0
    assert "[person.education]" in test_toml_path.read_text()
    assert "University" not in test_toml_path.read_text()

    result = runner.invoke(app, ["unset", "--toml-path", str(test_toml_path), "person", "education"])
    assert result.exit_code == 0
    assert "[persion.education]" not in test_toml_path.read_text()

    result = runner.invoke(app, ["unset", "--toml-path", str(test_toml_path), "person"])
    assert result.exit_code == 0
    assert len(test_toml_path.read_text()) == 1  # just a newline


def test_no_command():
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "--help" in result.stdout
    assert "Commands" in result.stdout
