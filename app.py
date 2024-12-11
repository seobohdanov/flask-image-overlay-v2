from flask import Flask, request, send_file
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import math
from colorsys import hsv_to_rgb

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

    def create_metallic_gradient(size, angle=45):
        """Создает градиент металлического блеска с исправленной конвертацией цветов"""
        gradient = Image.new('RGBA', size)
        draw = ImageDraw.Draw(gradient)
        
        for y in range(size[1]):
            for x in range(size[0]):
                # Создаем волнообразный паттерн
                wave = math.sin(x/20.0 + y/20.0) * 0.3 + 0.7
                # Добавляем угловой градиент
                angle_factor = (x * math.cos(math.radians(angle)) + 
                              y * math.sin(math.radians(angle))) / (size[0] + size[1])
                
                # Ограничиваем значения для HSV
                hue = max(0.0, min(1.0, 0.13 + angle_factor * 0.02))  # Золотой оттенок
                saturation = max(0.0, min(1.0, 0.8 + wave * 0.2))
                value = max(0.0, min(1.0, 0.6 + wave * 0.4))
                
                # Конвертируем HSV в RGB с проверкой значений
                rgb = hsv_to_rgb(hue, saturation, value)
                color = (
                    max(0, min(255, int(rgb[0] * 255))),
                    max(0, min(255, int(rgb[1] * 255))),
                    max(0, min(255, int(rgb[2] * 255))),
                    180  # Полупрозрачность
                )
                draw.point((x, y), color)
        
        return gradient

    def apply_metallic_effect(draw, text, position, font):
        x, y = position
        
        # 1. Базовое тиснение
        for depth in range(8, 0, -1):
            press_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            press_draw = ImageDraw.Draw(press_layer)
            press_draw.text(
                (x + depth*0.5, y + depth*0.5),
                text,
                font=font,
                fill=(0, 0, 0, 20 + depth * 4)
            )
            press_blur = press_layer.filter(ImageFilter.GaussianBlur(depth))
            image.paste(press_blur, (0, 0), press_blur)

        # 2. Создаем маску текста
        text_mask = Image.new('L', image.size, 0)
        mask_draw = ImageDraw.Draw(text_mask)
        mask_draw.text((x, y), text, font=font, fill=255)

        # 3. Создаем и накладываем металлический градиент
        for angle in [30, 45, 60]:  # Несколько градиентов под разными углами
            metallic = create_metallic_gradient(image.size, angle)
            image.paste(metallic, (0, 0), text_mask)

        # 4. Добавляем блики
        angles = [30, 45, 60]
        for angle in angles:
            highlight_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            highlight_draw = ImageDraw.Draw(highlight_layer)
            
            offset_x = math.cos(math.radians(angle)) * 2
            offset_y = math.sin(math.radians(angle)) * 2
            
            highlight_draw.text(
                (x + offset_x, y + offset_y),
                text,
                font=font,
                fill=(255, 255, 220, 30)
            )
            
            highlight_blur = highlight_layer.filter(ImageFilter.GaussianBlur(1))
            image.paste(highlight_blur, (0, 0), text_mask)

        # 5. Финальный слой для усиления эффекта
        final_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        final_draw = ImageDraw.Draw(final_layer)
        final_draw.text(
            (x, y),
            text,
            font=font,
            fill=(255, 223, 0, 100)
        )
        image.paste(final_layer, (0, 0), final_layer)

    # Вычисляем размеры и позицию
    frame_width = W * 0.6
    frame_height = H * 0.7
    font, text_width, text_height = get_font_and_size(text, frame_width, frame_height)
    x = (W - text_width) / 2
    y = (H - text_height) / 2

    # Применяем эффекты
    apply_metallic_effect(draw, text, (x, y), font)

    # Сохраняем результат
    img_io = io.BytesIO()
    image = image.convert('RGB')
    image.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')

if __name__ == "__main__":
    app.run(debug=True)