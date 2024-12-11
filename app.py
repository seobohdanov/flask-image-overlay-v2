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

    # Конвертируем изображение в RGBA
    image = image.convert('RGBA')
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
                final_size = int(font_size * 0.97)
                try:
                    font = ImageFont.truetype("GreatVibes-Regular.ttf", final_size)
                except IOError:
                    font = ImageFont.load_default()
                break
                
            font_size += 10
            
        return font, text_width, text_height

    def create_realistic_emboss(draw, text, position, font):
        x, y = position
        
        # 1. Создаем эффект углубления (темная область)
        depression_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        depression_draw = ImageDraw.Draw(depression_layer)
        
        # Многослойная тень для глубины
        for offset in range(3):
            depression_draw.text(
                (x + offset, y + offset),
                text,
                font=font,
                fill=(0, 0, 0, 40)  # Очень прозрачный черный
            )
        
        # Размываем для мягкости
        depression_blur = depression_layer.filter(ImageFilter.GaussianBlur(2))
        image.paste(depression_blur, (0, 0), depression_blur)

        # 2. Создаем эффект приподнятых краев вокруг букв
        edge_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        edge_draw = ImageDraw.Draw(edge_layer)
        
        # Верхний и левый края (светлые)
        for i in range(2):
            edge_draw.text(
                (x - i, y - i),
                text,
                font=font,
                fill=(255, 255, 255, 60)  # Полупрозрачный белый
            )
        
        # Размываем края
        edge_blur = edge_layer.filter(ImageFilter.GaussianBlur(1))
        image.paste(edge_blur, (0, 0), edge_blur)

        # 3. Основной текст (углубленный)
        main_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        main_draw = ImageDraw.Draw(main_layer)
        
        # Рисуем основной текст с золотым оттенком
        main_draw.text(
            (x, y),
            text,
            font=font,
            fill=(218, 165, 32, 180)  # Золотой цвет с прозрачностью
        )
        
        # 4. Добавляем текстуру "примятой кожи"
        texture_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        texture_draw = ImageDraw.Draw(texture_layer)
        
        # Создаем эффект деформации вокруг букв
        for offset in [(1,1), (-1,-1), (1,-1), (-1,1)]:
            texture_draw.text(
                (x + offset[0], y + offset[1]),
                text,
                font=font,
                fill=(0, 0, 0, 20)  # Очень прозрачный черный
            )
        
        # Размываем текстуру
        texture_blur = texture_layer.filter(ImageFilter.GaussianBlur(3))
        image.paste(texture_blur, (0, 0), texture_blur)
        
        # Накладываем основной текст
        image.paste(main_layer, (0, 0), main_layer)

    # Получаем оптимальный размер шрифта
    font, text_width, text_height = get_optimal_font_size(text, frame_width, frame_height)

    # Вычисляем позицию для центрирования текста
    text_position = (
        frame_margin_x + (frame_width - text_width) / 2,
        frame_margin_y + (frame_height - text_height) / 2
    )

    # Применяем эффект тиснения
    create_realistic_emboss(draw, text, text_position, font)

    # Сохранение результата
    img_io = io.BytesIO()
    image = image.convert('RGB')
    image.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')

if __name__ == "__main__":
    app.run(debug=True)