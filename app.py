from flask import Flask, request, send_file
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import numpy as np

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

    # Определяем размеры и позицию внутренней рамки (примерно 60% от общего размера)
    frame_margin_x = W * 0.2  # 20% отступ слева и справа
    frame_margin_y = H * 0.15  # 15% отступ сверху и снизу
    frame_width = W - (2 * frame_margin_x)
    frame_height = H - (2 * frame_margin_y)

    # Функция для подбора оптимального размера шрифта с учетом рамки
    def get_optimal_font_size(text, max_width, max_height):
        font_size = 10
        font = None
        text_width = 0
        text_height = 0
        
        while True:
            try:
                font = ImageFont.truetype("GreatVibes-Regular.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
                
            text_width, text_height = draw.textsize(text, font=font)
            
            # Используем 90% от размера рамки для текста
            if text_width > max_width * 0.9 or text_height > max_height * 0.9:
                font_size -= 10
                try:
                    font = ImageFont.truetype("GreatVibes-Regular.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()
                break
                
            font_size += 10
            
        return font, text_width, text_height

    # Получаем оптимальный размер шрифта для рамки
    font, text_width, text_height = get_optimal_font_size(text, frame_width, frame_height)

    # Цвета в стиле изображения
    stroke_color = "#8B4513"  # Темно-коричневый
    text_color = "#D2691E"    # Светло-коричневый
    shadow_color = "#2F1810"  # Очень темный коричневый

    def draw_text_with_blurred_shadow(draw, text, position, font, shadow_offset, shadow_color, text_color, stroke_width, stroke_fill):
        x, y = position

        # Создаем слой для тени
        shadow_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)

        # Рисуем тень с смещением
        shadow_draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)

        # Размытие слоя с тенью
        blurred_shadow = shadow_layer.filter(ImageFilter.GaussianBlur(12))  # Увеличенное размытие

        # Наложение тени на основное изображение
        image.paste(blurred_shadow, (0, 0), blurred_shadow)

        # Рисуем основной текст поверх размытой тени
        draw.text(position, text, font=font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_fill)

    # Вычисляем позицию для центрирования текста в рамке
    text_position = (
        frame_margin_x + (frame_width - text_width) / 2,
        frame_margin_y + (frame_height - text_height) / 2
    )

    # Рисуем текст с тенью
    draw_text_with_blurred_shadow(
        draw, text, text_position, font,
        shadow_offset=8,        # Увеличенное смещение тени
        shadow_color=shadow_color,
        text_color=text_color,
        stroke_width=3,         # Уменьшенная толщина обводки
        stroke_fill=stroke_color
    )

    # Сохранение результата во временный файл
    img_io = io.BytesIO()
    image.save(img_io, 'JPEG', quality=95)  # Увеличенное качество
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')

if __name__ == "__main__":
    app.run(debug=True)