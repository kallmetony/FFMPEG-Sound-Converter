import os
import sys
import subprocess
from pathlib import Path

# Фикс для кириллицы в Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Находим ffmpeg
def find_ffmpeg():
    """
    Сначала проверяем системную команду ffmpeg, затем ищем в директории скрипта
    """
    # Пытаемся использовать системный ffmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print("Using system ffmpeg command\n")
            return "ffmpeg"
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    # Если системный ffmpeg не найден, ищем в директории скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Проверяем ffmpeg.exe для Windows в папке bin
    ffmpeg_exe = os.path.join(script_dir, "bin", "ffmpeg.exe")
    if os.path.exists(ffmpeg_exe):
        print(f"Using local ffmpeg: {ffmpeg_exe}\n")
        return ffmpeg_exe

    # Проверяем ffmpeg без расширения для Linux/Mac в папке bin
    ffmpeg_bin = os.path.join(script_dir, "bin", "ffmpeg")
    if os.path.exists(ffmpeg_bin):
        print(f"Using local ffmpeg: {ffmpeg_bin}\n")
        return ffmpeg_bin

    # Проверяем ffmpeg.exe для Windows в корне (для обратной совместимости)
    ffmpeg_exe_root = os.path.join(script_dir, "ffmpeg.exe")
    if os.path.exists(ffmpeg_exe_root):
        print(f"Using local ffmpeg: {ffmpeg_exe_root}\n")
        return ffmpeg_exe_root

    # Проверяем ffmpeg без расширения для Linux/Mac в корне
    ffmpeg_bin_root = os.path.join(script_dir, "ffmpeg")
    if os.path.exists(ffmpeg_bin_root):
        print(f"Using local ffmpeg: {ffmpeg_bin_root}\n")
        return ffmpeg_bin_root

    # Если ничего не найдено
    print("ERROR: ffmpeg not found!")
    print("Please either:")
    print("  1. Install ffmpeg system-wide (recommended)")
    print("  2. Download ffmpeg and place it in the script folder")
    sys.exit(1)

ffmpeg_path = find_ffmpeg()

def convert_m4a_to_ogg(input_folder, output_folder):
    """
    Конвертирует все m4a файлы из input_folder в ogg формат и сохраняет в output_folder
    """
    # Создаем выходную папку, если её нет
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # Получаем список всех аудио файлов
    input_path = Path(input_folder)
    m4a_files = list(input_path.glob("*.m4a"))
    ogg_files = list(input_path.glob("*.ogg"))
    mp3_files = list(input_path.glob("*.mp3"))

    all_files = m4a_files + ogg_files + mp3_files

    if not all_files:
        print(f"No audio files (m4a, ogg, mp3) found in folder {input_folder}")
        return

    print(f"Found {len(all_files)} files to convert (m4a: {len(m4a_files)}, ogg: {len(ogg_files)}, mp3: {len(mp3_files)})\n")

    # Конвертируем каждый файл
    for i, audio_file in enumerate(all_files, 1):
        try:
            print(f"[{i}/{len(all_files)}] Converting {audio_file.name}...", end=" ")

            # Формируем путь для выходного файла
            output_file = Path(output_folder) / f"{audio_file.stem}.ogg"

            # Команда ffmpeg для конвертации в формат совместимый с Minecraft
            # Используем моно, 44.1kHz, качество 5 (средне-высокое)
            # + обрезка тишины в начале и конце
            cmd = [
                ffmpeg_path,
                "-i", str(audio_file.absolute()),
                "-af", "silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB,areverse",
                "-c:a", "libvorbis",      # Кодек Vorbis
                "-ac", "1",               # Моно
                "-ar", "44100",           # Частота дискретизации 44.1kHz
                "-q:a", "5",              # Качество 5 (0-10)
                "-y",                     # Перезаписывать без подтверждения
                str(output_file.absolute())
            ]

            # Запускаем ffmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            if result.returncode == 0:
                print("✓")
            else:
                print(f"✗")
                print(f"  ffmpeg error: {result.stderr[:200]}")

        except Exception as e:
            print(f"✗ Error: {e}")

    print(f"\nDone! Files saved to {output_folder}")

if __name__ == "__main__":
    # Можно указать папки через аргументы командной строки
    if len(sys.argv) >= 3:
        input_folder = sys.argv[1]
        output_folder = sys.argv[2]
    else:
        input_folder = "input"
        output_folder = "output"

    print(f"Input folder: {input_folder}")
    print(f"Output folder: {output_folder}\n")

    convert_m4a_to_ogg(input_folder, output_folder)
