# Some notes

## About the aliases

- There's not needed to take into account the aliases in the source model, the complication is not worth it, why? It'd never be used
  - The case for the aliases is when we're trying to integrate 2 external APIs.
  - We receive the data using the aliases. After that, Pydantic uses the field names.
  - Then, aliases could be useful again to match the names in the API we're trying to send data to. It's here when we would like to use them, because they will be the names used for the serialization to the external API.

## About the singleton (Dynamic Path Manager + Error Manager)

- I decided to design that class as a singleton because, following the 3 rules set in this [StackOverflow answer](https://stackoverflow.com/questions/228164/on-design-patterns-when-should-i-use-the-singleton):
  - The path/error it's a shared result, and it must be just one
  - The path/error will be accessed by multiple parts of the system
  - There can only be one path/error
- Using dependency injection in this case could be unnecessarily messy, so I decided to use a singleton.

## Edge cases
