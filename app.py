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
    frame_margin_x = W * 0.2
    frame_margin_y = H * 0.15
    frame_width = W - (2 * frame_margin_x)
    frame_height = H - (2 * frame_margin_y)

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
            
            if text_width > max_width * 0.9 or text_height > max_height * 0.9:
                font_size -= 10
                final_size = int(font_size * 0.90)
                try:
                    font = ImageFont.truetype("GreatVibes-Regular.ttf", final_size)
                except IOError:
                    font = ImageFont.load_default()
                break
                
            font_size += 10
            
        return font, text_width, text_height

    def create_metallic_emboss(draw, text, position, font):
        x, y = position
        
        # 1. Глубокий эффект вдавленности (пресс)
        for depth in range(8, 0, -1):
            press_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            press_draw = ImageDraw.Draw(press_layer)
            
            # Создаем темную область вдавленности
            offset = depth * 0.5
            press_draw.text(
                (x + offset, y + offset),
                text,
                font=font,
                fill=(0, 0, 0, 25 + depth * 5)  # Увеличиваем непрозрачность с глубиной
            )
            
            # Размываем для реалистичности
            press_blur = press_layer.filter(ImageFilter.GaussianBlur(depth))
            image.paste(press_blur, (0, 0), press_blur)

        # 2. Металлический золотой эффект
        # Базовые цвета для золота
        gold_colors = [
            (255, 215, 0, 180),     # Яркое золото
            (238, 198, 0, 180),     # Темное золото
            (255, 223, 0, 180),     # Светлое золото
            (218, 165, 32, 180),    # Золотисто-коричневый
            (255, 240, 110, 180),   # Светлый блик
        ]

        # Создаем металлический эффект с бликами
        for i, color in enumerate(gold_colors):
            metallic_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            metallic_draw = ImageDraw.Draw(metallic_layer)
            
            # Смещение для создания эффекта объема
            offset_x = math.sin(i * math.pi / 4) * 2
            offset_y = math.cos(i * math.pi / 4) * 2
            
            metallic_draw.text(
                (x + offset_x, y + offset_y),
                text,
                font=font,
                fill=color
            )
            
            # Применяем разное размытие для разных слоев
            blur_radius = 0.5 if i == len(gold_colors)-1 else 1.5
            metallic_blur = metallic_layer.filter(ImageFilter.GaussianBlur(blur_radius))
            image.paste(metallic_blur, (0, 0), metallic_blur)

        # 3. Добавляем яркие блики
        highlight_positions = [(0.8, 0.8), (-0.8, -0.8), (0.8, -0.8), (-0.8, 0.8)]
        for pos in highlight_positions:
            highlight_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            highlight_draw = ImageDraw.Draw(highlight_layer)
            
            highlight_draw.text(
                (x + pos[0], y + pos[1]),
                text,
                font=font,
                fill=(255, 255, 255, 100)
            )
            
            highlight_blur = highlight_layer.filter(ImageFilter.GaussianBlur(0.5))
            image.paste(highlight_blur, (0, 0), highlight_blur)

        # 4. Добавляем эффект деформации кожи вокруг букв
        for radius in range(10, 0, -2):
            leather_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            leather_draw = ImageDraw.Draw(leather_layer)
            
            leather_draw.text(
                (x, y),
                text,
                font=font,
                fill=(0, 0, 0, 5)  # Очень прозрачный черный
            )
            
            leather_blur = leather_layer.filter(ImageFilter.GaussianBlur(radius))
            image.paste(leather_blur, (0, 0), leather_blur)

        # 5. Финальный блестящий акцент
        shine_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        shine_draw = ImageDraw.Draw(shine_layer)
        shine_draw.text(
            (x - 1, y - 1),
            text,
            font=font,
            fill=(255, 255, 255, 50)
        )
        shine_blur = shine_layer.filter(ImageFilter.GaussianBlur(0.3))
        image.paste(shine_blur, (0, 0), shine_blur)

    font, text_width, text_height = get_optimal_font_size(text, frame_width, frame_height)

    text_position = (
        frame_margin_x + (frame_width - text_width) / 2,
        frame_margin_y + (frame_height - text_height) / 2
    )

    create_metallic_emboss(draw, text, text_position, font)

    img_io = io.BytesIO()
    image = image.convert('RGB')
    image.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')

if __name__ == "__main__":
    app.run(debug=True)