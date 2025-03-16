# Roadmap

The ultimate goal of this package would be to map any kind of data to any kind of model. So it can be used as the single interface to integrate two systems.

Ideally, it would receive the raw data without any transformations and just use one pydantic model to do the mapping.

## Next features

- [ ] Support source with lists in it's root
- [ ] Support source data as a json or dict
- [ ] Work with target's field aliases
- [ ] Support fields defined by methods
- [ ] Add caching for the model traversal

## Know issues

- [ ] Model corruption when building a new model from scattered fields:
  - When building a new model (especially a list of models), it's possible that the field name is repeated in different unrelated nested models.
  - This can lead to unexpected models being built (some partial, some complete but with the wrong data).
  - One solution could be: once you got a match for the building of a new model, lock-in there, and finish all the matches there.
  - Another solution could be: for Pydantic models, just match the models that have the same name.

## Improvements

- [ ] Add a tuturial module
- [ ] Extend the tests to cover more cases
- [ ] Add more support for Union, Set, Tuple, and Dict types
- [ ] Refactor the core logic to be more SOLID
