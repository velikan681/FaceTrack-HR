import base64
import json
import os
import uuid

import cv2
import numpy as np
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

try:
    import face_recognition

    FACE_RECOGNITION_AVAILABLE = True
    FACE_IMPORT_ERROR = ""
except Exception as exc:  # pragma: no cover - depends on local environment.
    face_recognition = None
    FACE_RECOGNITION_AVAILABLE = False
    FACE_IMPORT_ERROR = str(exc)


def is_face_library_available() -> tuple[bool, str]:
    if FACE_RECOGNITION_AVAILABLE:
        return True, ""
    return False, (
        "Библиотека face_recognition недоступна. "
        f"Детали импорта: {FACE_IMPORT_ERROR}"
    )


def save_employee_photo(file_storage: FileStorage, upload_folder: str) -> tuple[str, str]:
    filename = secure_filename(file_storage.filename or "")
    extension = filename.rsplit(".", 1)[1].lower() if "." in filename else "jpg"
    stored_filename = f"{uuid.uuid4().hex}.{extension}"
    absolute_path = os.path.join(upload_folder, stored_filename)
    file_storage.save(absolute_path)
    return stored_filename, absolute_path


def create_face_encoding_from_file(image_path: str) -> tuple[str | None, str | None]:
    available, message = is_face_library_available()
    if not available:
        return None, message

    try:
        image = face_recognition.load_image_file(image_path)
        locations = face_recognition.face_locations(image, model="hog")
        if not locations:
            return None, "На фото не найдено лицо. Используйте фото с четким лицом анфас."
        if len(locations) > 1:
            return None, "На фото найдено несколько лиц. Загрузите фото только одного сотрудника."

        encodings = face_recognition.face_encodings(image, known_face_locations=locations)
        if not encodings:
            return None, "Не удалось создать face-encoding для этого изображения."

        encoding_json = json.dumps(encodings[0].tolist())
        return encoding_json, None
    except Exception as exc:  # pragma: no cover - external library behavior.
        return None, f"Ошибка обработки фото: {exc}"


def _decode_data_url_to_frame(data_url: str) -> tuple[np.ndarray | None, str | None]:
    try:
        if "," not in data_url:
            return None, "Неверный формат кадра с веб-камеры."
        encoded = data_url.split(",", 1)[1]
        image_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return None, "Не удалось декодировать изображение с веб-камеры."
        return frame, None
    except Exception as exc:
        return None, f"Ошибка чтения кадра: {exc}"


def _load_known_faces(employees):
    known_encodings = []
    known_employees = []
    for employee in employees:
        if not employee.face_encoding:
            continue
        try:
            encoding_list = json.loads(employee.face_encoding)
            known_encodings.append(np.array(encoding_list))
            known_employees.append(employee)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
    return known_encodings, known_employees


def recognize_from_data_url(data_url: str, employees, tolerance: float = 0.45) -> dict:
    available, message = is_face_library_available()
    if not available:
        return {"status": "error", "message": message}

    frame, frame_error = _decode_data_url_to_frame(data_url)
    if frame_error:
        return {"status": "error", "message": frame_error}

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame, model="hog")
    if not face_locations:
        return {"status": "no_face", "message": "Лицо в кадре не найдено."}

    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    if not face_encodings:
        return {"status": "no_face", "message": "Лицо обнаружено, но кодировка не получена."}

    known_encodings, known_employees = _load_known_faces(employees)
    if not known_encodings:
        return {
            "status": "error",
            "message": "В системе нет сотрудников с корректными face-encoding.",
        }

    best_match_index = None
    best_distance = 1e9
    for encoding in face_encodings:
        distances = face_recognition.face_distance(known_encodings, encoding)
        if len(distances) == 0:
            continue
        index = int(np.argmin(distances))
        distance = float(distances[index])
        if distance < best_distance:
            best_distance = distance
            best_match_index = index

    if best_match_index is None:
        return {"status": "unknown", "message": "Лицо не распознано."}

    if best_distance > tolerance:
        return {
            "status": "unknown",
            "message": "Лицо не найдено среди зарегистрированных сотрудников.",
            "distance": round(best_distance, 4),
        }

    employee = known_employees[best_match_index]
    confidence = round(max(0.0, (1.0 - best_distance)) * 100, 2)
    return {
        "status": "recognized",
        "employee": employee,
        "confidence": confidence,
        "distance": round(best_distance, 4),
        "faces_count": len(face_locations),
    }
