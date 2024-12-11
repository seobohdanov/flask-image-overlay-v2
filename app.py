from flask import Flask, request, send_file
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import math

app = Flask(__name__)

@app.route('/overlay', methods=['POST'])
def overlay_text():
    image_url = request.form.get('image_url')
    text = request.form.get('text')

    if image_url:
        response = requests.get(image_url)
        image = Image.open(io.BytesIO(response.content))
    else:
        file = request.files['image']
        image = Image.open(file)

    image = image.convert('RGBA')
    draw = ImageDraw.Draw(image)
    W, H = image.size

    def get_font_and_size(text, max_width, max_height):
        font_size = 10
        while True:
            try:
                font = ImageFont.truetype("GreatVibes-Regular.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            if text_width > max_width * 0.8 or text_height > max_height * 0.8:
                font_size -= 10
                final_size = int(font_size * 0.97)
                try:
                    font = ImageFont.truetype("GreatVibes-Regular.ttf", final_size)
                except IOError:
                    font = ImageFont.load_default()
                bbox = draw.textbbox((0, 0), text, font=font)
                return font, bbox[2] - bbox[0], bbox[3] - bbox[1]
            
            font_size += 10

    def create_metallic_effect(draw, text, position, font):
        x, y = position
        
        # Предварительно определенные цвета золота
        gold_colors = [
            (255, 215, 0, 255),     # Pure Gold
            (238, 198, 0, 255),     # Dark Gold
            (255, 223, 0, 255),     # Light Gold
            (212, 175, 55, 255),    # Metallic Gold
            (207, 181, 59, 255),    # Antique Gold
            (197, 179, 88, 255),    # Pale Gold
        ]

        # 1. Создаем эффект глубокого тиснения
        for depth in range(10):
            shadow_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            
            # Усиливаем эффект вдавленности
            offset = depth * 0.8
            opacity = int(25 - depth * 2)
            if opacity > 0:
                shadow_draw.text(
                    (x + offset, y + offset),
                    text,
                    font=font,
                    fill=(0, 0, 0, opacity)
                )
                
                shadow_blur = shadow_layer.filter(ImageFilter.GaussianBlur(depth * 0.5))
                image.paste(shadow_blur, (0, 0), shadow_blur)

        # 2. Создаем базовый золотой слой
        for color in gold_colors:
            for offset in [(0, 0), (-0.5, -0.5), (0.5, 0.5)]:
                layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
                layer_draw = ImageDraw.Draw(layer)
                
                layer_draw.text(
                    (x + offset[0], y + offset[1]),
                    text,
                    font=font,
                    fill=color
                )
                
                # Легкое размытие для сглаживания
                layer = layer.filter(ImageFilter.GaussianBlur(0.5))
                image.paste(layer, (0, 0), layer)

        # 3. Добавляем блики
        highlights = [
            ((1, 1), 40),      # Нижний правый блик
            ((-1, -1), 40),    # Верхний левый блик
            ((0, -1), 50),     # Верхний блик
            ((0, 0), 30),      # Центральный блик
        ]

        for (offset_x, offset_y), opacity in highlights:
            highlight = Image.new('RGBA', image.size, (0, 0, 0, 0))
            highlight_draw = ImageDraw.Draw(highlight)
            
            highlight_draw.text(
                (x + offset_x, y + offset_y),
                text,
                font=font,
                fill=(255, 255, 255, opacity)
            )
            
            # Размытие для мягкости бликов
            highlight = highlight.filter(ImageFilter.GaussianBlur(1))
            image.paste(highlight, (0, 0), highlight)

        # 4. Финальный слой для усиления контраста
        final_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        final_draw = ImageDraw.Draw(final_layer)
        
        # Добавляем контрастный золотой контур
        final_draw.text(
            (x, y),
            text,
            font=font,
            fill=(255, 215, 0, 100)
        )
        
        image.paste(final_layer, (0, 0), final_layer)

    # Вычисляем размеры и позицию
    frame_width = W * 0.6
    frame_height = H * 0.7
    font, text_width, text_height = get_font_and_size(text, frame_width, frame_height)
    x = (W - text_width) / 2
    y = (H - text_height) / 2

    # Применяем эффекты
    create_metallic_effect(draw, text, (x, y), font)

    # Сохраняем результат
    img_io = io.BytesIO()
    image = image.convert('RGB')
    image.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')

if __name__ == "__main__":
    app.run(debug=True)