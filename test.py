
def create_image_with_wrapped_text(text, output_path="output.png", width=800, height=400, font_size=40, padding=20):
    from PIL import Image, ImageDraw, ImageFont

    # Create a blank white image
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Load a font
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Wrapping text dynamically
    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = words[0]

        for word in words[1:]:
            # Check the width if we add the next word
            test_line = f"{current_line} {word}"
            if draw.textlength(test_line, font=font) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        lines.append(current_line)  # Add the last line
        return lines

    # Calculate text area width (accounting for padding)
    text_width = width - 2 * padding
    lines = wrap_text(text, font, text_width)

    # Calculate the total height of the text block
    box = font.getbbox('A')
    line_height = (box[3] - box[1]) * 1.1
    text_block_height = line_height * len(lines)

    # Start drawing from the vertical center
    y = (height - text_block_height) // 2

    for line in lines:
        # Calculate horizontal center for each line
        line_width = draw.textlength(line, font=font)
        x = (width - line_width) // 2
        draw.text((x, y), line, font=font, fill="black")
        y += line_height

    # Save the image
    image.save(output_path)
    return output_path

# Example usage
image_path = create_image_with_wrapped_text(
    "Сосал?"
)
print(f"Image saved at {image_path}")
