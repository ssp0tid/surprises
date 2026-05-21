"""Variable interpolation engine."""

import re

INTERPOLATION_PATTERN = re.compile(r"\$\{([^}]+)\}")


def interpolate(value: str, variables: dict[str, str]) -> str:
    def replace_var(match: re.Match) -> str:
        var_name = match.group(1)
        if var_name in variables:
            return variables[var_name]
        return match.group(0)

    result = value
    prev = ""
    while prev != result:
        prev = result
        result = INTERPOLATION_PATTERN.sub(replace_var, result)
    return result


def interpolate_vars(env_data: dict[str, str]) -> dict[str, str]:
    result = {}
    for key, value in env_data.items():
        result[key] = interpolate(value, env_data)
    return result
