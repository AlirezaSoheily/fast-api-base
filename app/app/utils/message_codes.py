from app.core.middleware.get_accept_language_middleware import get_accept_language


def parseAcceptLanguage(acceptLanguage: str):
    language_codes = []
    for language in acceptLanguage.split(","):
        language = language.split(";", 1)[0]
        language = language.split("-", 1)[0]
        language = language.strip()
        language_codes.append(language)

    return language_codes


class MessageCodes:
    @classmethod
    def get_message(
        cls, message_code: int = 1, msg_code_params: dict | list | None = None
    ) -> str:
        parsed_accept_languages = parseAcceptLanguage(get_accept_language())

        #
        if message_code == None:
            message_code = 1

        message = cls.persian_message_names[message_code]

        for accept_language in parsed_accept_languages:
            match accept_language:
                case "fa":
                    message = cls.persian_message_names[message_code]
                    break
                case "en":
                    message = cls.english_message_names[message_code]
                    break

        if msg_code_params:
            if type(msg_code_params) == list:
                message = message.format(*msg_code_params)
            elif type(msg_code_params) == dict:
                message = message.format(**msg_code_params)

        return message

    successful_operation = 0
    internal_error = 1
    not_found = 2
    bad_request = 3
    input_error = 4
    operation_failed = 5
    incorrect_username_or_password = 6
    inactive_user = 7
    permission_error = 8
    already_exist_object = 9
    not_authorized = 10
    expired_token = 11
    access_token_not_found = 12
    refresh_token_not_found = 13
    invalid_token = 14
    provider_default_error = 15
    provider_timeout_error = 16

    english_message_names = {
        0: "Successful Operation",
        1: "Internal Error",
        2: "Not Found",
        3: "Bad Request",
        4: "Input Error",
        5: "Operation Failed",
        6: "Invalid Username Or Password",
        7: "Inactive User: {}",
        8: "Dont Have Access",
        9: "Object already exists",
        10: "Not Authorized",
        11: "Expired Token",
        12: "Access Token Not Found",
        13: "Refresh Token Not Found",
        14: "Invalid Token",
        15: "There is a problem in connecting to provider, please try again",
        16: "There is a problem in connecting to provider, please try again",
    }

    persian_message_names = {
        0: "عملیات موفق",
        1: "خطای داخلی",
        2: "پیدا نشد",
        3: "درخواست نا‌معتبر",
        4: "ورودی نامعتبر",
        5: "عملیات ناموفق",
        6: "ایمیل یا پسورد نامعتبر",
        7: "یوزر{} غیرفعال است",
        8: "سطح دسترسی غیرمجاز",
        9: "دیتای وارد شده تکرای است",
        10: "نام کاربری یا رمز عبور وارد نشده است",
        11: "توکن منقضی شده است",
        12: "اکسس توکن پیدا نشد",
        13: "رفرش توکن پیدا نشد",
        14: "توکن نامعتبر",
        15: "در برقراری ارتباط با تامین کننده مشکلی به وجود آمده است، لطفا مجددا تلاش کنید",
        16: "در برقراری ارتباط با تامین کننده مشکلی به وجود آمده است، لطفا مجددا تلاش کنید",
    }
