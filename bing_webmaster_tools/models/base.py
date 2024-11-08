from datetime import datetime
from typing import Any, ClassVar, Dict, Generic, List, Literal, Type, TypeVar, Union, overload

from pydantic import BaseModel, ConfigDict, field_validator

from bing_webmaster_tools.utils import parse_timestamp_from_api


def _snake_to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    return "".join(word.capitalize() for word in string.split("_"))


class BingModel(BaseModel):
    # Class variable to specify which fields should be treated as dates
    date_fields: ClassVar[set[str]] = {"date"}

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        validate_assignment=True,
        populate_by_name=True,
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_dates(cls, value: Any, info: Any) -> Any:
        """Validate and parse dates for all fields specified in date_fields."""
        if info.field_name not in cls.date_fields:
            return value

        if value is None or isinstance(value, datetime):
            return value

        return parse_timestamp_from_api(value)


T = TypeVar("T")
TItem = TypeVar("TItem", bound=BingModel)


class ApiResponse(BaseModel, Generic[T]):
    """Standardized API response wrapper.

    Attributes:
        data: The parsed response data of type T
        raw_response: The original API response for debugging/logging

    """

    data: T
    raw_response: Dict[str, Any]

    @overload
    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], model: Type[TItem], *, is_list: Literal[False] = False
    ) -> "ApiResponse[TItem]": ...

    @overload
    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], model: Type[TItem], *, is_list: Literal[True]
    ) -> "ApiResponse[List[TItem]]": ...

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], model: Type[TItem], *, is_list: bool = False
    ) -> Union["ApiResponse[TItem]", "ApiResponse[List[TItem]]"]:
        """Parse an API response into a Pydantic model.

        Args:
            response: Raw API response dictionary
            model: Pydantic model class to parse the data into
            is_list: Whether the response data should be parsed as a list of models

        Returns:
            ApiResponse instance with parsed data

        """
        api_data = response.get("d", [] if is_list else {})

        parsed_data: Union[TItem, List[TItem]]
        if is_list:
            parsed_data = [model.model_validate(item) for item in api_data]
        else:
            parsed_data = model.model_validate(api_data)

        return cls(data=parsed_data, raw_response=response)  # type: ignore
