def format_required_field_error(fields):
    message = "<ul>"
    for f in fields:
        message += f"<li>{f.title().replace('_', ' ')} is required. </li>"
    message += "</ul>"

    return message