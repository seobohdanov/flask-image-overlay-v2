from flask import Flask, request, send_file
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

app = Flask(__name__)

@app.route('/overlay', methods=['POST'])
def overlay_text():
    image_url = request.form.get('image_url')
    text = request.form.get('text')
    date = request.form.get('date')

    # Загрузка изображения по URL
    if image_url:
        response = requests.get(image_url)
        image = Image.open(io.BytesIO(response.content))
    else:
        file = request.files['image']
        image = Image.open(file)

    draw = ImageDraw.Draw(image)

    # Настройка шрифта
    try:
        font_zodiac = ImageFont.truetype("EFCO Brookshire Regular.ttf", 250)  # Верхний шрифт 250px
        font_date = ImageFont.truetype("EFCO Brookshire Regular.ttf", 200)  # Нижний шрифт 200px
    except IOError:
        font_zodiac = ImageFont.load_default()
        font_date = ImageFont.load_default()

    # Цвет обводки, цвет текста и цвет тени
    stroke_color = "#a3716f"
    text_color = "white"
    shadow_color = "black"

    # Создаем изображение для тени и основной текст
    def draw_text_with_blurred_shadow(draw, text, position, font, shadow_offset, shadow_color, text_color, stroke_width, stroke_fill):
        x, y = position

        # Создаем слой для тени
        shadow_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)

        # Рисуем тень с смещением
        shadow_draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)

        # Размытие слоя с тенью
        blurred_shadow = shadow_layer.filter(ImageFilter.GaussianBlur(10))

        # Наложение тени на основное изображение
        image.paste(blurred_shadow, (0, 0), blurred_shadow)

        # Рисуем основной текст поверх размытой тени
        draw.text(position, text, font=font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_fill)

    # Получение размера изображения для центрирования текста
    W, H = image.size

    # Позиции для знака зодиака и даты
    zodiac_w, zodiac_h = draw.textsize(text, font=font_zodiac)
    date_w, date_h = draw.textsize(date, font=font_date)

    # Ещё меньший отступ сверху для знака зодиака (например, 2 пикселя)
    zodiac_position = ((W - zodiac_w) / 2, 2)
    date_position = ((W - date_w) / 2, H - date_h - 50)

    # Рисуем знак зодиака с размытой тенью
    draw_text_with_blurred_shadow(draw, text, zodiac_position, font_zodiac, shadow_offset=7, shadow_color=shadow_color, text_color=text_color, stroke_width=7, stroke_fill=stroke_color)

    # Рисуем дату с размытой тенью
    draw_text_with_blurred_shadow(draw, date, date_position, font_date, shadow_offset=7, shadow_color=shadow_color, text_color=text_color, stroke_width=7, stroke_fill=stroke_color)

    # Сохранение результата во временный файл
    img_io = io.BytesIO()
    image.save(img_io, 'JPEG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')

if __name__ == "__main__":
    app.run(debug=True)