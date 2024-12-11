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

    # Получаем точные размеры изображения
    W, H = image.size

    def get_font_and_size(text, max_width, max_height):
        font_size = 10
        while True:
            try:
                font = ImageFont.truetype("GreatVibes-Regular.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()

            # Используем getbbox() для более точного измерения
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

    def create_metallic_emboss(draw, text, position, font):
        x, y = position
        
        # 1. Глубокий эффект вдавленности
        for depth in range(8, 0, -1):
            press_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            press_draw = ImageDraw.Draw(press_layer)
            
            offset = depth * 0.5
            press_draw.text(
                (x + offset, y + offset),
                text,
                font=font,
                fill=(0, 0, 0, 20 + depth * 4)
            )
            press_blur = press_layer.filter(ImageFilter.GaussianBlur(depth))
            image.paste(press_blur, (0, 0), press_blur)

        # 2. Основные золотые слои
        gold_colors = [
            (218, 165, 32, 180),    # Базовый золотой
            (255, 215, 0, 160),     # Яркий золотой
            (205, 175, 49, 170),    # Тёмный золотой
            (234, 193, 23, 165),    # Насыщенный золотой
        ]

        # Наносим основные золотые слои
        for i, color in enumerate(gold_colors):
            gold_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            gold_draw = ImageDraw.Draw(gold_layer)
            
            offset_x = math.sin(i * math.pi / 6) * 1.5
            offset_y = math.cos(i * math.pi / 6) * 1.5
            
            gold_draw.text(
                (x + offset_x, y + offset_y),
                text,
                font=font,
                fill=color
            )
            
            blur = 0.8 if i == 0 else 1.2
            gold_blur = gold_layer.filter(ImageFilter.GaussianBlur(blur))
            image.paste(gold_blur, (0, 0), gold_blur)

        # 3. Минимальные блики (меньше чем раньше)
        highlight_positions = [(-0.5, -0.5), (0.5, 0.5)]
        for pos in highlight_positions:
            highlight_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            highlight_draw = ImageDraw.Draw(highlight_layer)
            
            highlight_draw.text(
                (x + pos[0], y + pos[1]),
                text,
                font=font,
                fill=(255, 255, 255, 30)  # Уменьшена прозрачность бликов
            )
            
            highlight_blur = highlight_layer.filter(ImageFilter.GaussianBlur(0.5))
            image.paste(highlight_blur, (0, 0), highlight_blur)

        # 4. Эффект деформации кожи
        for radius in range(10, 0, -2):
            leather_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            leather_draw = ImageDraw.Draw(leather_layer)
            
            leather_draw.text((x, y), text, font=font, fill=(0, 0, 0, 5))
            leather_blur = leather_layer.filter(ImageFilter.GaussianBlur(radius))
            image.paste(leather_blur, (0, 0), leather_blur)

    # Вычисляем размеры для центральной области (рамки)
    frame_width = W * 0.6    # Берем 60% ширины изображения
    frame_height = H * 0.7   # Берем 70% высоты изображения

    # Получаем шрифт и размеры текста
    font, text_width, text_height = get_font_and_size(text, frame_width, frame_height)

    # Точное центрирование
    x = (W - text_width) / 2
    y = (H - text_height) / 2

    # Применяем эффекты
    create_metallic_emboss(draw, text, (x, y), font)

    # Сохранение результата
    img_io = io.BytesIO()
    image = image.convert('RGB')
    image.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')

if __name__ == "__main__":
    app.run(debug=True)