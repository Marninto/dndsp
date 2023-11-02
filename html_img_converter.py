from html2image import Html2Image
from jinja2 import Template


def render_and_capture_html(data, cache, image_path, template_path, size, db_image_link=None):
    if not cache and db_image_link:
        # If cache is False and a db_image_link is provided, return the link directly
        return db_image_link

    hti = Html2Image()

    # Load and render the HTML template
    with open(template_path, 'r') as file:
        template = Template(file.read())
        html_content = template.render(data=data)

    # Save the HTML to an image
    hti.screenshot(html_str=html_content, save_as=image_path, size=size)

    # Returning the path to the new image
    return image_path
