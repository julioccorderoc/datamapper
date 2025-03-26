# pydamapper

Map data between pydantic models.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://github.com/pydantic/pydantic)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

> Real applications have real data, and real data nests. Objects inside of objects inside of lists of objects.

[Mahmoud Hashemi](https://github.com/mahmoud)

Mapping real data should be as easy as declaring their schemas, ergo, **pydamapper**.

## 🚀 Highlights

- ✅ **Automatic mapping** - Just using the field names. Zero boilerplate. Reuse your pydantic models.
- ✅ **Complex structures** - Map to new nested estructures or lists of new nested structures.
- ✅ **Fault tolerant** - If it cannot map all the data, it'll return what it found with readable errors.
- ✅ **Enjoy Pydantic's features** - Built-in type checking using Pydantic's validation.

## 🛠 Usage

```python
from pydantic import BaseModel
from pydamapper import map_models

# TBD
```

### Build new models

```python
# TBD
```

### Build lists of existing or new models

```python
# TBD
```

## What is *pydamapper*?

The *Python Data Mapper* is a data mapping tool.

It allows you to easily map data from a data structure (for example, a webhook's payload) to another data structure (for example, an API endpoint payload), using Pydantic validation.

It was created with the purpose of facilitating integration between APIs, allowing you to just define input and output schemas to *translate* one API to another API.

### Why?

- **Lazyness**: integrating two simple APIs should be as easy as defining their schemas (or asking an LLM to do it for you).
- **DRY**: Don't repeat yourself. If you have the model schema, why bother with something else?

### Other solutions?

#### [pymapme](https://github.com/funnydman/pymapme)

This is the most similar solution. However, it offers a different experience from what I was looking for.

Besides, it doesn't support:

- Match with the name only
- Partial returns
- Detailed errors report

#### [glom](https://github.com/mahmoud/glom)

It's not built with the goal of mapping and validating data between pydantic models, but it can be used for it. You can check and example in [the docs](https://glom.readthedocs.io/en/latest/tutorial.html#practical-production-use).

Check a video about the purpose of this tool [here](https://www.youtube.com/watch?v=3aREXkfeWek). You can read more about glom in the [creator's website](https://sedimental.org/).

> Maybe using glom in this package could be a good idea 🤷‍♂️.

#### Just direct assignment

Certainly, the most straightforward solution. However:

- Too many lines of code for larger or complex models
- Inflexible
- Boring

### Why not just use AI to do the mapping for me and just copy and paste?

Well, I hope AI will recommend you to `pip install pydamapper` in the future.

## 🤝 Contribute

We welcome contributions! Here's how to set up:

```bash
# 1. Clone the repo
git  clone  https://github.com/julioccorderoc/pydamapper.git

# 2. Install dev environment
make  setup  # Installs pre-commit hooks, testing tools, etc

# 3. Run tests
make  test  # Runs pytest with coverage

# 4. Run static checks
make  check  # Runs code quality tools

# 5. Clean up
make  clean  # Cleans up generated files
```

### 📮 Need Help?

[Open an issue](https://github.com/julioccorderoc/pydamapper) or DM me on LinkedIn: [@julioccorderoc](https://www.linkedin.com/in/julioccorderoc/).

## 📚 Documentation

> TBD

## 📄 License

[MIT License](LICENSE) - Free for commercial use

## Disclaimer

- This package is still in development.

> [!NOTE]
> I created this package as a learning project.

## 🙌 Credits

- Created by [me](https://github.com/julioccorderoc).
- Build on top of the awesome [Pydantic](https://github.com/pydantic/pydantic) community.
