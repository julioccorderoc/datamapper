from string import Template

from pydamapper._errors_handling.registry import ErrorRegistry

# ---------------------------------------------
# Functions to create the summary error message
# ---------------------------------------------


def generate_summary(error_registry: ErrorRegistry, target_name: str) -> str:
    """Generates a summary report of errors found during mapping."""
    summary = [f"'{len(error_registry)}' error(s) found while mapping '{target_name}':\n"]
    for error_type, errors in error_registry.items():
        summary.append(f"  > {len(errors)} {error_type.name}")
    return "\n".join(summary)


def generate_details(error_registry: ErrorRegistry) -> str:
    """Generates a detailed report of all errors in the error list."""
    details = []
    for error_type, errors in error_registry.items():
        for error in errors:
            details.append(
                f"      + Field: {error.field_path}\n"
                f"        Type: {error_type.name}\n"
                f"        Description: {error_type.value}\n"
                f"        Message: {error.details}"
            )
    return "\n".join(details) if details else "No errors found."


# ----------------------------
# Templates for error messages
# ----------------------------

field_required = Template(
    "The field '$field_name' is required in the '$parent_model_name' model "
    "and could not be matched in the '$source_model_name' model."
)

type_validation = Template(
    "The field '$field_name' of type '$field_type' cannot match "
    "the value '$value' of type '$value_type'"
)

partial_model = Template("The new model '$new_model_name' was partially built.")

empty_model = Template("No data found to build the new model '$new_model_name'.")

limit_reach = Template(
    "Limit of '$limit' reach for building list of '$new_model_name' models. "
    "IF YOU WANT TO EXTEND THE LIMIT UPDATE THE CONFIG."
)
