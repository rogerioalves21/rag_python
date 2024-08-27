from langchain_community.llms import Ollama
from PIL import Image
import base64
from io import BytesIO

def convert_to_base64(pil_image: Image):
    buffered = BytesIO()
    pil_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

def load_image(image_path: str):
    pil_image = Image.open(image_path)
    image_b64 = convert_to_base64(pil_image)
    print("Loaded image successfully!")
    return image_b64


llm = Ollama(base_url="http://localhost:11434", model="llava:latest")

image_b64 = load_image("./images/chevy.jpg")
resp = llm.invoke("What's in the image?", images=[image_b64])
print(resp)