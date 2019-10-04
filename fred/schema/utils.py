import operator
from typing import Callable, Any, List

from fred.schema.context import Context
from fred.types import Tag

Validator = Callable[[Context, Any], Any]
Predicate = Callable[[Any], bool]
NOT_GIVEN = object()
OPERATIONS = {
    ">=": operator.ge,
    ">": operator.gt,
    "<=": operator.le,
    "<": operator.lt,
    "!=": operator.ne,
}


#
# Validator compositions
#
def type_validator(cls: type, msg=None) -> Validator:
    """
    Create a validator that checks if argument is of the given type.
    """
    msg = msg or f"Expected type: {cls.__name__}, but got {{type}}"

    @set_name(f"{cls.__name__}_validator")
    def validator(ctx, x):
        if not isinstance(x, cls):
            ctx.type_error(msg.format(type=type(x).__name__))
        return x

    return validator


def predicate_validator(
    cond: Predicate, msg: str, name="condition_validator"
) -> Validator:
    """
    Create validator that checks if argument pass predicate.
    """

    @set_name(name)
    def validator(ctx, x):
        if not cond(x):
            ctx.value_error(msg)
        return x

    return validator


def constant_validator(cte) -> Validator:
    """
    Create validator that checks if value equals to constant.
    """

    if cte is None and null_validator is not None:
        return null_validator

    def validate_constant(ctx, x):
        if x != cte:
            ctx.value_error("invalid value")
        return cte

    return validate_constant


def null_validator(ctx, x):
    """
    Validate that x is None.
    """
    if x is not None:
        ctx.value_error("expected null value")
    return None


def range_validator(range, kind: type) -> List[Validator]:
    """
    Return validator that checks if number is in a range.

    Range can be any of:
        [a b]  -> minimum and maximum values (inclusive)
        (op a) -> where op is one of >, >=, <, <=, !=; check operation
    """
    if range is NOT_GIVEN:
        return []

    elif isinstance(range, list):
        if len(range) != 2:
            msg = "Invalid range: range must be a list of exactly two numbers"
            raise ValueError(msg)
        return [*range_validator(range[0], kind), *range_validator(range[1], kind)]

    elif isinstance(range, Tag):
        tag, meta, value = range.split()

        if tag not in (">=", "<=", ">", "<", "!="):
            raise ValueError(f"invalid range tag: {tag}")
        elif not isinstance(value, kind):
            msg = f"Limit must be of type {kind.__name__}, got {value}"
            raise ValueError(msg)

        msg = f"condition not met: {tag} {value}"
        op = OPERATIONS[tag]
        return [predicate_validator(lambda x: op(x, value), msg)]

    else:
        raise ValueError("invalid range especification")


def exclude_validator(exclude, kind: type) -> List[Validator]:
    if exclude is NOT_GIVEN:
        return []
    elif isinstance(exclude, list):
        if not all(isinstance(x, kind) for x in exclude):
            raise ValueError(f"all exclude items must be of type {kind.__name__}")
        try:
            exclude = set(exclude)
        except TypeError:
            pass
        return [
            predicate_validator(
                lambda x: x not in exclude, "value is not in the set of valid values"
            )
        ]
    raise ValueError("exclude must be a list of items")


def chain_validators(validations: list):
    """
    Receive a list of validators and chain all validations into a single
    operation.
    """
    if not validations:
        return lambda ctx, x: x
    elif len(validations) == 1:
        return validations[0]

    def validation_list(ctx, x):
        for validation in validations:
            x = validation(ctx, x)
        return x

    return validation_list


def extract_propositions(name, validations, args) -> List[Validator]:
    if not args:
        return []
    value = args[0]
    try:
        return [validations[value]]
    except KeyError:
        raise ValueError(f"invalid type proposition for {name}: {value}")


#
# Utilities
#
def set_name(name):
    """
    Decorator that sets the __name__ and __qualname__ of a function.
    """

    def decorator(f):
        f.__name__ = name
        f.__qualname__ = name
        return f

    return decorator


def expect_no_kwargs(which, kwargs):
    """
    Utility function that raises a ValueError if kwargs is not empty.
    """
    if kwargs:
        k, _ = kwargs.popitem()
        raise ValueError(f"invalid schema option for {which}: {k}")
