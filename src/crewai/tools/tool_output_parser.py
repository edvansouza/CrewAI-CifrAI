import json
from typing import Any, List

import regex
from langchain.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.outputs import Generation
from langchain_core.pydantic_v1 import ValidationError


class ToolOutputParser(PydanticOutputParser):
    """
    This class extends the PydanticOutputParser and is used to parse the output of a tool usage.
    It provides methods to parse the result and transform the output into valid JSON.
    """

    def parse_result(self, result: List[Generation], *, partial: bool = False) -> Any:
        """
        This method is used to parse the result of a tool usage. It first transforms the result into valid JSON.
        It then calls the parse_result method of the superclass to parse the JSON object.
        If parsing fails, it raises an OutputParserException.
        """
        result[0].text = self._transform_in_valid_json(result[0].text)
        json_object = super().parse_result(result)
        try:
            return self.pydantic_object.parse_obj(json_object)
        except ValidationError as e:
            name = self.pydantic_object.__name__
            msg = f"Failed to parse {name} from completion {json_object}. Got: {e}"
            raise OutputParserException(msg, llm_output=json_object)

    def _transform_in_valid_json(self, text) -> str:
        """
        This method is used to transform the output of a tool usage into valid JSON.
        It first removes any backticks and the word 'json' from the text.
        It then uses a regular expression to find all JSON objects in the text.
        It attempts to parse each match as JSON and returns the first successfully parsed JSON object.
        If no match can be parsed as JSON, it returns the original text.
        """
        text = text.replace("```", "").replace("json", "")
        json_pattern = r"\{(?:[^{}]|(?R))*\}"
        matches = regex.finditer(json_pattern, text)

        for match in matches:
            try:
                # Attempt to parse the matched string as JSON
                json_obj = json.loads(match.group())
                # Return the first successfully parsed JSON object
                json_obj = json.dumps(json_obj)
                return str(json_obj)
            except json.JSONDecodeError:
                # If parsing fails, skip to the next match
                continue
        return text
