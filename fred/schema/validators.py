import datetime

from .utils import (
    predicate_validator,
    expect_no_kwargs,
    chain_validators,
    type_validator,
    extract_propositions,
    range_validator,
    exclude_validator,
    Validator,
    NOT_GIVEN,
)
from ..types import Symbol, Tag

INT_VALIDATORS = {
    Symbol("ODD"): predicate_validator(lambda x: x % 2 == 1, "integer must be odd"),
    Symbol("EVEN"): predicate_validator(lambda x: x % 2, "integer must be even"),
}
FLOAT_VALIDATORS = {
    Symbol("INT"): predicate_validator(lambda x: x == int(x), "must be an integer"),
    Symbol("FINITE"): predicate_validator(
        lambda x: str(float) not in ("inf", "nan", "-inf"), "must be finite"
    ),
}


def make_validator(spec: Tag, memo: dict, lib: dict = None) -> Validator:
    """
    Create a validator from declaration.
    """
    tag, attrs, value = spec.split()
    lib = LIB if lib is None else lib

    if attrs:
        raise NotImplementedError("attrs", attrs)
    if tag in memo or tag in lib:
        raise ValueError(f"duplicated declaration of {tag}")

    # Attribute validation
    attrs_validator = lambda ctx, x: x

    # Value validation
    if isinstance(value, Tag):
        value_validator = get_validator(value, memo, lib)

    elif isinstance(value, list):
        if len(value) == 1:
            value_validator = make_validator(Tag("List", value[0]), memo, lib)
        else:
            raise NotImplementedError

    elif isinstance(value, dict):
        obj_spec = {}
        for k, v in value.items():
            if not isinstance(v, Tag):
                raise ValueError("invalid type declaration at {tag}.{k}")
            if v.tag.endswith("?"):
                obj_spec[k] = False, get_validator(v.retag(v.tag[:-1]), memo, lib)
            else:
                obj_spec[k] = True, get_validator(v, memo, lib)
        value_validator = object_validator(obj_spec)

    else:
        raise TypeError(f"invalid schema spec, {spec!r}")

    validator = tag_validator(tag, attrs_validator, value_validator)
    memo[tag] = validator
    return validator


def get_std_validator(value, lib):
    tag, attrs, value = value.split()
    if value is None:
        return lib[tag](**attrs)
    else:
        return lib[tag](value, **attrs)


def get_validator(value, memo, lib):
    if value.tag in memo:
        return memo[value.tag]
    return get_std_validator(value, lib)


def tag_validator(*args, **kwargs):
    """
    Tag validator
    """
    expected_tag, attrs_validator, obj_validator = args
    expect_no_kwargs(f"tag ({expected_tag})", kwargs)

    def validator(ctx, obj):
        if not isinstance(obj, Tag):
            ctx.type_error("not a tag")
            return obj

        tag, attrs, obj = obj.split()
        attrs = attrs_validator(ctx, attrs)
        obj = obj_validator(ctx, obj)
        return Tag.new(tag, attrs, obj)

    return validator


def list_validator(*args, **kwargs):
    """
    Receives a single validator as positional argument and return a validator
    that checks if all elements of the list validate against validator.
    """
    expect_no_kwargs("list", kwargs)
    item_validator, = args

    def validator(ctx, lst):
        if not isinstance(lst, list):
            ctx.type_error("expect a list")
            return lst
        return [item_validator(ctx, item) for item in lst]

    return validator


def object_validator(*args, **kwargs):
    expect_no_kwargs("dict", kwargs)
    validator_spec, = args

    def validator(ctx, obj):
        if not isinstance(obj, dict):
            ctx.type_error("expect a dict")
            return obj

        missing = set(validator_spec)
        result = {}

        for field, value in obj.items():
            ctx.set_field(field)
            try:
                is_required, item_validator = validator_spec[field]
            except KeyError:
                ctx.value_error(f"unexpected field: {field}")
            else:
                if not is_required and value is None:
                    result[field] = None
                else:
                    result[field] = item_validator(ctx, value)
                missing.discard(field)
        for field in missing:
            if validator_spec[field][0]:
                ctx.set_field(field)
                ctx.value_error(f"missing field {field}")
            else:
                result[field] = None
        return result

    return validator


def dict_validator(*args, **kwargs):
    expect_no_kwargs("dict", kwargs)
    validator_decl, = args

    def validator(ctx, dic):
        if not isinstance(dic, dict):
            ctx.type_error("expect a dict")
            return dic

        # Syntax guarantees that keys are always valid
        return {k: validator_decl(ctx, v) for k, v in dic.items()}

    return validator


def int_validator(*args, **kwargs):
    return chain_validators(numeric_validator(int, *args, **kwargs))


def float_validator(*args, **kwargs):
    return chain_validators(numeric_validator(float, *args, **kwargs))


def numeric_validator(*args, exclude=NOT_GIVEN, **kwargs):
    range = kwargs.pop("range", NOT_GIVEN)
    expect_no_kwargs(int.__name__, kwargs)
    kind, *args = args
    validations = [type_validator(kind)]
    validations.extend(extract_propositions(kind.__name__, INT_VALIDATORS, args))
    validations.extend(range_validator(range, kind))
    validations.extend(exclude_validator(exclude, kind))
    return validations


LIB = {
    "Date": lambda: type_validator(datetime.date),
    "Datetime": lambda: type_validator(datetime.datetime),
    "Time": lambda: type_validator(datetime.time),
    "String": lambda: type_validator(str),
    "Bool": lambda: type_validator(bool),
    "Bytes": lambda: type_validator(bytes),
    "Int": int_validator,
    "Float": float_validator,
    "Dict": dict_validator,
    "List": list_validator,
}
