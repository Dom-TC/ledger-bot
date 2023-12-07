from ledger_bot.errors.airtable_error import AirTableError


class TestAirTableError:
    def test_airtable_error_with_dict_error(self):
        url = "https://example.com/api"
        response_dict = {"error": {"type": "SomeType", "message": "SomeMessage"}}
        error = AirTableError(url=url, response_dict=response_dict)

        assert error.url == url
        assert error.error_type == "SomeType"
        assert error.error_message == "SomeMessage"
        assert (
            repr(error)
            == f"{AirTableError}(type:SomeType, message:'SomeMessage', url:{url})"
        )
        assert (
            str(error)
            == f"Error from AirTable operation of type 'SomeType', with message:'SomeMessage'. Request URL: {url}"
        )

    def test_airtable_error_with_string_error(self):
        url = "https://example.com/api"
        response_dict = {"error": "SomeType"}
        error = AirTableError(url=url, response_dict=response_dict)

        assert error.url == url
        assert error.error_type == "SomeType"
        assert error.error_message == ""
        assert repr(error) == f"{AirTableError}(type:SomeType, message:'', url:{url})"
        assert (
            str(error)
            == f"Error from AirTable operation of type 'SomeType', with message:''. Request URL: {url}"
        )

    def test_airtable_error_with_empty_error(self):
        url = "https://example.com/api"
        response_dict = {"error": {}}
        error = AirTableError(url=url, response_dict=response_dict)

        assert error.url == url
        assert error.error_type is None
        assert error.error_message is None
        assert repr(error) == f"{AirTableError}(type:None, message:'None', url:{url})"
        assert (
            str(error)
            == f"Error from AirTable operation of type 'None', with message:'None'. Request URL: {url}"
        )
