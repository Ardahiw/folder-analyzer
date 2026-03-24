import os

def analyze_folder(folder_path):
    """
    Seçilen klasörü analiz eder.
    Geriye sonuçları sözlük olarak döndürür.
    """
    if not folder_path:
        raise ValueError("Klasör yolu boş.")

    if not os.path.exists(folder_path):
        raise FileNotFoundError("Klasör bulunamadı.")

    if not os.path.isdir(folder_path):
        raise NotADirectoryError("Girilen yol bir klasör değil.")

    items = os.listdir(folder_path)

    folders = []
    files = []

    for item in items:
        full_path = os.path.join(folder_path, item)

        if os.path.isdir(full_path):
            folders.append(item)
        elif os.path.isfile(full_path):
            files.append(item)

    result = {
        "folder_path": folder_path,
        "total_items": len(items),
        "folder_count": len(folders),
        "file_count": len(files),
        "folders": sorted(folders),
        "files": sorted(files),
    }

    return result