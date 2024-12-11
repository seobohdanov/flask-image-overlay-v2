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
        image = Image.open(io.BytysIO(response.content))
    else:
        file = request.files['image']
        image = Image.open(file)

    draw = ImageDraw.Draw(image)

    # Получаем размеры изображения
    W, H = image.size

    # Определяем размеры и позицию внутренней рамки
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
                try:
                    font = ImageFont.truetype("GreatVibes-Regular.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()
                break
                
            font_size += 10
            
        return font, text_width, text_height

    # Получаем оптимальный размер шрифта
    font, text_width, text_height = get_optimal_font_size(text, frame_width, frame_height)

    # Новые цвета и эффекты
    main_color = "#FFD700"      # Золотой цвет для основного текста
    stroke_color = "#8B4513"    # Темно-коричневый для обводки
    glow_color = "#FFA500"      # Оранжевый для внутреннего свечения
    shadow_color = "#000000"    # Черный для тени

    def draw_text_with_effects(draw, text, position, font):
        x, y = position
        
        # Создаем несколько слоев свечения
        for offset in range(15, 0, -3):
            glow_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_layer)
            glow_draw.text((x, y), text, font=font, fill=glow_color)
            glow_blur = glow_layer.filter(ImageFilter.GaussianBlur(offset))
            image.paste(glow_blur, (0, 0), glow_blur)

        # Слой для тени
        shadow_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_draw.text((x + 5, y + 5), text, font=font, fill=shadow_color)
        shadow_blur = shadow_layer.filter(ImageFilter.GaussianBlur(10))
        image.paste(shadow_blur, (0, 0), shadow_blur)

        # Рисуем обводку
        for offset in [(1,1), (-1,-1), (-1,1), (1,-1)]:
            draw.text((x + offset[0], y + offset[1]), text, font=font, fill=stroke_color)

        # Рисуем основной текст с дополнительной обводкой
        draw.text((x, y), text, font=font, fill=main_color, stroke_width=2, stroke_fill=stroke_color)

    # Вычисляем позицию для центрирования текста
    text_position = (
        frame_margin_x + (frame_width - text_width) / 2,
        frame_margin_y + (frame_height - text_height) / 2
    )

    # Применяем все эффекты
    draw_text_with_effects(draw, text, text_position, font)

    # Сохранение результата
    img_io = io.BytesIO()
    image.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')

if __name__ == "__main__":
    app.run(debug=True)