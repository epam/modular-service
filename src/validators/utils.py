from functools import wraps
from http import HTTPStatus
from typing import Callable, Any, TypeVar

from pydantic import BaseModel, ValidationError

from commons.lambda_response import ResponseFactory

T = TypeVar('T')


def validate_pydantic(model: type, value: dict) -> BaseModel:
    try:
        return model(**value)
    except ValidationError as e:
        errors = []
        for error in e.errors():
            errors.append({
                'location': error['loc'],
                'description': error['msg']
            })
        raise ResponseFactory(HTTPStatus.BAD_REQUEST).errors(errors).exc()


def validate_type(_type: type[T], value: Any) -> T:
    try:
        return _type(value) if not isinstance(value, _type) else value
    except (ValueError, TypeError):
        raise ResponseFactory(HTTPStatus.BAD_REQUEST).errors([{
            'location': ['path'],
            'message': f'\'{value}\' should have type {_type.__name__}'
        }])


def _validate(kwargs: dict[str, Any], types: dict[str, type],
              cast: bool = True) -> dict[str, Any]:
    """
    Received keys and values in `kwargs`, keys and expected values' types
    in `types`. Returns a dict with keys and validated values
    :param kwargs:
    :param types:
    :param cast:
    :return:
    """
    validated = {}
    for key, value in kwargs.items():
        if key not in types:
            validated[key] = value
            continue
        _type = types[key]
        if issubclass(_type, BaseModel):
            valid = validate_pydantic(_type, value)
            if not cast:
                valid = valid.dict()
            validated[key] = valid
        else:
            # supposedly here will be only dynamic url params. Their
            # rightness depends not on the user but on the developer. Value
            # shall be always cast-able
            valid = validate_type(_type, value)
            if not cast:
                valid = value
            validated[key] = valid
    return validated


def validate_kwargs(func: Callable) -> Callable:
    """
    Simply tries to cast async function's arguments to their annotated params.
    An argument must be a dict in case you annotate it with pydantic model
    :param func:
    :return:
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        validated = _validate(kwargs, func.__annotations__)
        result = func(*args, **validated)
        # _return = func.__annotations__.get('return')
        # if issubclass(_return, BaseModel):
        #     result['body'] = _return.parse_raw(result['body']).json()
        #     # in case validation fails here, it's developer's error
        return result

    return wrapper
