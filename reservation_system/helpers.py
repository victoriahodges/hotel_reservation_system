def room_image_location():
    return "img/hotel_rooms/"


def format_required_field_error(fields):
    message = "<ul>"
    for f in fields:
        message += f"<li>{f.title().replace('_', ' ')} is required. </li>"
    message += "</ul>"

    return message


def previous_page_url(redirect_url: str):
    # TODO: validate/sanitize empty form fields prevent sumitting 'None'
    if redirect_url and redirect_url != "None":
        if "calendar" in redirect_url:
            url_parts = redirect_url.strip("/").split("/")
            return int(url_parts[1]), int(url_parts[2])
        else:
            return redirect_url.replace("/", ".").lstrip(".")
    return None
