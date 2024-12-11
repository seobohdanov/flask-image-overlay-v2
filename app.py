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

    def create_metallic_text(draw, text, position, font):
        x, y = position
        
        # Цвета для металлического эффекта
        colors = [
            (139, 117, 0, 255),    # Темное золото
            (255, 215, 0, 255),    # Чистое золото
            (218, 165, 32, 255),   # Золотисто-коричневый
            (255, 223, 0, 255),    # Яркое золото
            (207, 181, 59, 255),   # Античное золото
        ]
        
        # 1. Создаем эффект вдавленности
        for depth in range(6):
            offset = depth * 0.8
            shadow_color = (0, 0, 0, 50 - depth * 8)
            draw.text(
                (x + offset, y + offset),
                text,
                font=font,
                fill=shadow_color
            )

        # 2. Добавляем металлические слои
        for i, color in enumerate(colors):
            angle = math.pi * 2 * i / len(colors)
            offset_x = math.cos(angle) * 1.2
            offset_y = math.sin(angle) * 1.2
            
            # Создаем отдельный слой для каждого цвета
            layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            layer_draw = ImageDraw.Draw(layer)
            
            layer_draw.text(
                (x + offset_x, y + offset_y),
                text,
                font=font,
                fill=color
            )
            
            # Небольшое размытие для сглаживания
            layer = layer.filter(ImageFilter.GaussianBlur(0.5))
            image.paste(layer, (0, 0), layer)

        # 3. Добавляем яркие блики
        highlight_positions = [
            (-1.5, -1.5, 40),   # Верхний левый блик
            (1.5, -1.5, 40),    # Верхний правый блик
            (0, 0, 60),         # Центральный блик
            (-0.8, -0.8, 50),   # Дополнительный блик
        ]
        
        for offset_x, offset_y, opacity in highlight_positions:
            highlight = Image.new('RGBA', image.size, (0, 0, 0, 0))
            highlight_draw = ImageDraw.Draw(highlight)
            
            highlight_draw.text(
                (x + offset_x, y + offset_y),
                text,
                font=font,
                fill=(255, 255, 220, opacity)
            )
            
            highlight = highlight.filter(ImageFilter.GaussianBlur(0.8))
            image.paste(highlight, (0, 0), highlight)

        # 4. Добавляем финальный слой текста
        final_color = (255, 215, 0, 180)
        draw.text((x, y), text, font=font, fill=final_color)

    # Вычисляем размеры и позицию
    frame_width = W * 0.6
    frame_height = H * 0.7
    font, text_width, text_height = get_font_and_size(text, frame_width, frame_height)
    x = (W - text_width) / 2
    y = (H - text_height) / 2

    # Применяем эффекты
    create_metallic_text(draw, text, (x, y), font)

    # Сохраняем результат
    img_io = io.BytesIO()
    image = image.convert('RGB')
    image.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')

if __name__ == "__main__":
    app.run(debug=True)