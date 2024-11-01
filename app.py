import streamlit as st
from streamlit_cropper import st_cropper
from PIL import Image
import io
import cv2
import numpy as np
from playwright.sync_api import sync_playwright
import time

# Função para salvar uma captura de tela como imagem
def save_screenshot(page):
    screenshot_path = "screenshot.png"
    page.screenshot(path=screenshot_path)
    return screenshot_path

# Função para localizar imagem na tela
def locate_image_on_screen(screen_image_path, template_image_path, threshold=0.8):
    screen = cv2.imread(screen_image_path, cv2.IMREAD_GRAYSCALE)
    template = cv2.imread(template_image_path, cv2.IMREAD_GRAYSCALE)

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= threshold:
        template_height, template_width = template.shape[:2]
        center_x = max_loc[0] + template_width // 2
        center_y = max_loc[1] + template_height // 2
        return center_x, center_y
    else:
        return None

# Função para clicar na imagem
def click_on_image(page, template_image_path):
    screenshot_path = save_screenshot(page)
    coords = locate_image_on_screen(screenshot_path, template_image_path)
    
    if coords:
        st.write(f"Imagem localizada nas coordenadas: {coords}")
        page.mouse.click(coords[0], coords[1])
    else:
        st.write("Imagem não encontrada na tela.")

# Interface do Streamlit
st.title("Ferramenta de Recorte e Autoclique de Imagem")

# Inicializa o Playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://exemplo.com")  # URL desejada para captura

    st.write("Capturando a tela da página...")

    # Captura inicial da tela
    screenshot_path = save_screenshot(page)
    screenshot = Image.open(screenshot_path)
    
    # Exibir captura para recorte
    st.write("Capture a área desejada para o clique:")
    realtime_update = st.sidebar.checkbox("Atualizar em Tempo Real", value=True)
    box_color = st.sidebar.color_picker("Cor da Caixa", value='#0000FF')
    aspect_choice = st.sidebar.radio("Razão de Aspecto", ["Livre", "1:1", "16:9", "4:3", "2:3"])
    
    aspect_dict = {
        "1:1": (1, 1),
        "16:9": (16, 9),
        "4:3": (4, 3),
        "2:3": (2, 3),
        "Livre": None
    }
    aspect_ratio = aspect_dict[aspect_choice]

    cropped_img = st_cropper(screenshot, realtime_update=realtime_update, box_color=box_color, aspect_ratio=aspect_ratio)

    if cropped_img is not None:
        st.image(cropped_img, caption="Imagem Recortada", use_column_width=True)
        
        # Salvar imagem recortada temporariamente para usar no Playwright
        img_byte_arr = io.BytesIO()
        cropped_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        with open("cropped_image.png", "wb") as f:
            f.write(img_byte_arr.getvalue())
        
        target_image_path = "cropped_image.png"

        # Botão para iniciar o clique na imagem
        if st.button("Clique na Imagem"):
            click_on_image(page, target_image_path)

            # Captura nova tela após 20 segundos
            st.write("Aguarde 20 segundos para uma nova captura...")
            time.sleep(20)

            # Nova captura e exibição para recorte
            st.write("Capturando nova tela...")
            screenshot_path = save_screenshot(page)
            screenshot = Image.open(screenshot_path)
            cropped_img = st_cropper(screenshot, realtime_update=realtime_update, box_color=box_color, aspect_ratio=aspect_ratio)

            if cropped_img is not None:
                st.image(cropped_img, caption="Nova Imagem Recortada", use_column_width=True)

    browser.close()
