from flask import Flask, request, send_file
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

app = Flask(__name__)

@app.route('/overlay', methods=['POST'])
def overlay_text():
    image_url = request.form.get('image_url')
    text = request.form.get('text')

    # Загрузка изображения по URL
    if image_url:
        response = requests.get(image_url)
        image = Image.open(io.BytesIO(response.content))
    else:
        file = request.files['image']
        image = Image.open(file)

    draw = ImageDraw.Draw(image)

    # Получаем размеры изображения
    W, H = image.size

    # Функция для подбора оптимального размера шрифта
    def get_optimal_font_size(text, max_width, max_height):
        font_size = 10  # Начальный размер шрифта
        font = None
        text_width = 0
        text_height = 0
        
        # Увеличиваем размер шрифта, пока текст не станет слишком большим
        while True:
            try:
                font = ImageFont.truetype("GreatVibes-Regular.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
                
            text_width, text_height = draw.textsize(text, font=font)
            
            # Оставляем небольшой отступ от краев (80% от размера изображения)
            if text_width > max_width * 0.8 or text_height > max_height * 0.8:
                font_size -= 10  # Возвращаемся к последнему подходящему размеру
                try:
                    font = ImageFont.truetype("GreatVibes-Regular.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()
                break
                
            font_size += 10
            
        return font, text_width, text_height

    # Получаем оптимальный размер шрифта
    font, text_width, text_height = get_optimal_font_size(text, W, H)

    # Цвета
    stroke_color = "#a3716f"
    text_color = "white"
    shadow_color = "black"

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

    # Вычисляем позицию для центрирования текста
    text_position = ((W - text_width) / 2, (H - text_height) / 2)

    # Рисуем текст с тенью
    draw_text_with_blurred_shadow(
        draw, text, text_position, font,
        shadow_offset=7,
        shadow_color=shadow_color,
        text_color=text_color,
        stroke_width=7,
        stroke_fill=stroke_color
    )

    # Сохранение результата во временный файл
    img_io = io.BytesIO()
    image.save(img_io, 'JPEG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')

if __name__ == "__main__":
    app.run(debug=True)