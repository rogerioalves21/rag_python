import base64
import ollama


def get_html(html_path: str) -> bytes:
    with open(html_path, 'r', encoding='utf-8') as file:
        return file.read()

def to_base64(image_path):
    """Getting the base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def main():
    html_path = '/Users/rogerio.rodrigues/Documents/work_java_pessoal/tabbypdf-master/src/test/resources/pdf/edit/html/0702763-79.2024.8.07.0014_0001.pdf.0.html'
    html = f"""<html><body>{get_html(html_path)}</body></html>"""

    print(html)

    response = ollama.chat(
        model='reader-lm:1.5b-fp16',
        messages=[
            {
                'role': 'user',
                'content': html
            },
        ],
        options={"temperature": 0.7, "num_ctx": 5096},
        keep_alive=0,
        stream=False
    )
    print(response['message']['content'])

if __name__ == "__main__":
    main()
    