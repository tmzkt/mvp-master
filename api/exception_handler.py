from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # check that a ValidationError exception is raised
    if isinstance(exc, ValidationError):
        # here prepare the 'custom_error_response' and
        # set the custom response data on response object
        new_data = {}

        for key in response.data.keys():
            new_data["detail"] = response.data[key][0] if isinstance(response.data[key], list) else response.data[key]

        response.data = new_data


        # if response.data.get("email", None):
        #     response.data["detail"] = response.data["email"][0]
        #     del response.data["email"]
        #     del response.data["password"]
        # elif response.data.get("password", None):
        #     response.data["detail"] = response.data["password"][0]
        #     del response.data["password"]
        # elif response.data.get("device_uuid", None):
        #     response.data["detail"] = response.data["device_uuid"][0]
        #     del response.data["device_uuid"]
        #     del response.data["device_model"]
        # elif response.data.get("device_model", None):
        #     response.data["detail"] = response.data["device_model"][0]
        #     del response.data["device_model"]

    # Now add the HTTP status code to the response.
    # if response is not None:
    #     response.data['code'] = response.status_code

    return response
