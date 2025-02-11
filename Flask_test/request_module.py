import requests

def call_js_method(url, command):
    """Отправляет POST-запрос на URL, чтобы вызвать JS-метод."""
    try:
        response = requests.post(url, data=command)  # Отправляем команду в теле запроса
        response.raise_for_status()
        return response.text #  Возвращаем True при успешном запросе
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {response.status_code}, {response.text}")
        return False


if __name__ == '__main__':
    while True:
        command = input("Введите команду (display <текст> или delete <текст>) или 'exit': ")
        if command.startswith("display"):
            url = 'http://127.0.0.1:5000/display_text'
            result = call_js_method(url, command)
            if result != False:
                print(result)
        elif command.startswith("delete"):
            url = 'http://127.0.0.1:5000/delete_text'
            result = call_js_method(url, command)
            if result != False:
                    print(result)
        elif command == "exit":
             break
        else:
            print("Неверная команда.")