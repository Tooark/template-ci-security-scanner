"""Reads the component templates the way GitLab does.

GitLab validates the inputs of an ``include:`` and interpolates them into the
template only when a pipeline is created -- which happens in a consuming
project, never here. This module reproduces the parts of that which can be
checked offline, so the scripts and tests in this repository can ask the same
questions ahead of time:

  * :func:`check_inputs` -- would GitLab accept these inputs?
  * :func:`render` -- what job does the template generate from them?

It follows the documented behaviour of ``spec:inputs`` (types, ``options``,
``regex``, required inputs) and of ``$[[ inputs.name ]]`` interpolation. It is
not GitLab, and makes no attempt at the rest of the CI YAML semantics.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
  import yaml
except ImportError:  # pragma: no cover - environment problem, not a template one
  sys.exit("PyYAML is required: python3 -m pip install pyyaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
INPUT_REF = re.compile(r"\$\[\[\s*inputs\.([A-Za-z0-9_]+)\s*\]\]")

# What `type:` accepts, and the Python types a YAML value of that kind loads as.
# bool is listed before the check for numbers because it is an int in Python.
INPUT_TYPES = {
    "string": (str,),
    "number": (int, float),
    "boolean": (bool,),
    "array": (list,),
}


@dataclass
class Component:
  """One file of templates/: its declared inputs and its unrendered job."""

  name: str
  path: Path
  inputs: dict[str, dict]
  config_text: str


def split_documents(text: str) -> tuple[str, str]:
  """Splits a component template into its spec and config halves."""
  parts = re.split(r"^---\s*$", text, maxsplit=1, flags=re.MULTILINE)
  if len(parts) != 2:
    raise ValueError("missing the '---' separator between spec and config")
  return parts[0], parts[1]


def load(path: Path) -> Component:
  """Loads one template. A bare ``name:`` input is a required one: {}."""
  spec_text, config_text = split_documents(path.read_text(encoding="utf-8"))
  declared = yaml.safe_load(spec_text)["spec"]["inputs"]
  inputs = {name: (definition or {}) for name, definition in declared.items()}
  return Component(name=path.stem, path=path, inputs=inputs, config_text=config_text)


def load_all() -> dict[str, Component]:
  """Loads every template, keyed by the name a consumer includes it under."""
  return {path.stem: load(path) for path in sorted(TEMPLATES_DIR.glob("*.yml"))}


def _matches_type(value, declared_type: str) -> bool:
  if declared_type == "number" and isinstance(value, bool):
    return False
  return isinstance(value, INPUT_TYPES[declared_type])


def check_inputs(component: Component, provided: dict) -> list[str]:
  """Returns what GitLab would reject about `provided`, as readable problems."""
  problems: list[str] = []

  for name in provided:
    if name not in component.inputs:
      problems.append(f"passes '{name}', which {component.name} does not declare")

  for name, definition in component.inputs.items():
    if name not in provided:
      if "default" not in definition:
        problems.append(f"omits '{name}', which {component.name} requires")
      continue

    value = provided[name]
    declared_type = definition.get("type", "string")
    if not _matches_type(value, declared_type):
      problems.append(
          f"passes {name}: {value!r}, but {component.name} declares it as {declared_type}"
          + (" (quote the value)" if declared_type == "string" else "")
      )
      continue

    options = definition.get("options")
    if options is not None and value not in options:
      problems.append(f"passes {name}: {value!r}, which is not one of {options}")

    pattern = definition.get("regex")
    if pattern is not None and not re.search(pattern, value):
      problems.append(f"passes {name}: {value!r}, which does not match {pattern}")

  return problems


def as_text(value) -> str:
  """A value written out as text, as GitLab does for an input interpolated into
  the middle of a string and for a scalar under ``variables:``."""
  if isinstance(value, bool):
    return "true" if value else "false"
  if isinstance(value, (list, dict)):
    return json.dumps(value)
  return str(value)


def _interpolate(node, values: dict):
  if isinstance(node, dict):
    return {_interpolate(key, values): _interpolate(item, values) for key, item in node.items()}
  if isinstance(node, list):
    return [_interpolate(item, values) for item in node]
  if not isinstance(node, str):
    return node

  # A value that is nothing but one reference keeps the type of the input:
  # `tags: $[[ inputs.tags ]]` becomes a list, not the text of one.
  whole = INPUT_REF.fullmatch(node.strip())
  if whole:
    return values[whole.group(1)]
  return INPUT_REF.sub(lambda match: as_text(values[match.group(1)]), node)


def render(component: Component, provided: dict | None = None) -> tuple[str, dict]:
  """Returns (job name, job) as generated from `provided` plus the defaults."""
  provided = provided or {}
  problems = check_inputs(component, provided)
  if problems:
    raise ValueError(f"{component.name}: " + "; ".join(problems))

  values = {name: definition.get("default") for name, definition in component.inputs.items()}
  values.update(provided)

  rendered = _interpolate(yaml.safe_load(component.config_text), values)
  (job_name, job), = rendered.items()
  return job_name, job
