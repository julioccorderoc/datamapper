# TODO

## FEATURES

- [ ] Work with field aliases: use the aliases of the target model to match the fields in the source model.
- [ ] Support for fields that require a function to fetch the value: for complex target models that don't consume the raw data directly from the source model.
- [ ] Caching logic to avoid checking the same field multiple times: take advantage of the firsts times the model is checked.
- [ ] Accept the source model as a json or dict: to provide better support for APIs integration use cases.
- [ ] Support the list of models in the root of the source model: when the source model is a list in it's root.
- [ ] Support for multiple aliases: handle the case where the target model could support multiple aliases.
- [ ] Use the map_model function without class instanciation: is it possible to avoid the class instanciation?
- [ ] Add option to return a fully serializable dict as a result from the partial returns, instead of a dict of objects.

## TESTS

- [x] Tests for the 5 main use cases:

  - [x] Simple field matching
  - [x] Nested field matching
  - [x] Build new models from scattered fields
  - [x] List of models with same instance
  - [x] List of new models
  - [x] List of models in root

- [ ] Tests for the error handling:

  - [x] Required field in the target not found in the source
  - [ ] Non required field in the target not found in the source
  - [ ] Field found with different type that can be coerced
  - [x] Field found with different type that can't be coerced
  - [ ] Empty new model
  - [ ] No mapa mapped

- [x] Test for returns with partial fields
- [ ] Test for aliases
- [ ] Test for non required fields

## IMPROVEMENTS

- [ ] Move the "name" level from the logger in the error_manager module to where the error is raised
- [ ] Add to the log the number of models found in the lists of models
- [ ] Add more support for Union, Set, Tuple, and Dict types
- [x] Add support for a log file using the env variable LOG_FILE
- [x] Add support for a log level using the env variable LOG_LEVEL
- [ ] Add cache and logging for the lists of models
- [x] Not just validate if the source model has the field, but also if the field is not null
- [ ] Add counter and summary for the types of errors in the list of errors

## BUGS

- [ ] Corrupted models:

  - When building a new model (usually a list of models), it's possible that the field name is repeated in different nested models.
  - This can cause to build a unexpected models.
  - The solution could be to gather the data from the same level, instead of looking through the whole source model again.
  - Another solution could be to always match a nested model if it has the same name as the model being built.

- [x] Currently, when returning a partial model, this is not serializable. Fix it so it always does. || They're not serializable due to the use of pydantic models within the dict. For them to be serializable, a special function has to be used as the default in the json.dumps function. Maybe, it could be useful to have an option to return the partial data as just serialable dicts.
- [ ] Fix the log of the display method for the error manager: currently it's using a print

## REFACTORING

- [ ] Move the field matching logic to a separate module
- [x] Move the error handling logic to a separate module

## MINOR

- [ ] Model validation before starting the mapping
- [ ] Add more mapping error cases
- [x] Improve the error messages
- [ ] Improve error handling for "dependencies" like DynamicPathManager, etc...
- [ ] Improve Single Responsibility Principle with the traverse function
- [ ] Would be better to have source and target models as arguments to the class?
- [ ] Would be better to "flat" the source model before matching?
- [ ] Would be better to "flat" the target model before building?
- [ ] Would be better to return a pure dict instead of a dict of pydantic models for the partial return?
