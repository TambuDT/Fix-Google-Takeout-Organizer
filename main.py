import os
import json
import subprocess
import shutil
from datetime import datetime, timezone
from tqdm import tqdm

# --------------------------
# Utility per exiftool
# --------------------------
def run_exiftool(args):
    """Esegue exiftool evitando errori di codifica Windows."""
    result = subprocess.run(
        ["exiftool"] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    try:
        return result.stdout.decode("utf-8", errors="ignore")
    except:
        return ""


def read_exif(file):
    """Restituisce un dizionario EXIF."""
    try:
        output = run_exiftool(["-j", file])
        data = json.loads(output)
        if data and isinstance(data, list):
            return data[0]
    except:
        pass
    return {}


# --------------------------
# Lettura JSON Takeout
# --------------------------
def find_json_metadata(root, base, ext):
    """
    Cerca il JSON corretto:
    1) base.ext.json
    2) base.ext + .suppl / supplemental-metadata
    3) base senza ultimo carattere
    """
    candidates = []

    # 1) Nome completo .json
    candidates.append(os.path.join(root, base + ext + ".json"))

    # 2) Formati Takeout
    for suffix in [
        ".suppl",
        ".supplemen",
        ".supplemental",
        ".supplemental-metad",
        ".supplemental-metadata",
        ".json"
    ]:
        candidates.append(os.path.join(root, base + ext + suffix))

    # 3) Base troncata di un carattere
    if len(base) > 1:
        short_base = base[:-1]
        for suffix in [
            ".json",
            ".suppl",
            ".supplemen",
            ".supplemental",
            ".supplemental-metad",
            ".supplemental-metadata",
        ]:
            candidates.append(os.path.join(root, short_base + ext + suffix))

    # Leggi il primo valido
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf8") as f:
                    return json.load(f)
            except:
                continue

    return {}


# --------------------------
# Merge EXIF + JSON
# --------------------------
def merge_metadata(exif_data, json_metadata):
    merged = {}

    # Time (JSON ha priorità)
    if "photoTakenTime" in json_metadata:
        timestamp = int(json_metadata["photoTakenTime"]["timestamp"])
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        merged["DateTimeOriginal"] = dt.strftime("%Y:%m:%d %H:%M:%S")
    elif "DateTimeOriginal" in exif_data:
        merged["DateTimeOriginal"] = exif_data["DateTimeOriginal"]

    # GPS
    if "geoData" in json_metadata and json_metadata["geoData"]:
        lat = json_metadata["geoData"].get("latitude")
        lon = json_metadata["geoData"].get("longitude")
        if lat not in [None, 0.0] and lon not in [None, 0.0]:
            merged["GPSLatitude"] = lat
            merged["GPSLongitude"] = lon

    if "GPSLatitude" not in merged and "GPSLatitude" in exif_data:
        merged["GPSLatitude"] = exif_data["GPSLatitude"]
    if "GPSLongitude" not in merged and "GPSLongitude" in exif_data:
        merged["GPSLongitude"] = exif_data["GPSLongitude"]

    # Titolo / descrizione
    merged["Title"] = json_metadata.get("title", exif_data.get("Title", ""))
    merged["ImageDescription"] = json_metadata.get(
        "description",
        exif_data.get("ImageDescription", "")
    )

    return merged


# --------------------------
# Scrivi EXIF
# --------------------------
def write_exif(file, metadata):
    cmd = ["exiftool"]
    for k, v in metadata.items():
        if v:
            cmd.append(f"-{k}={v}")
    cmd += ["-overwrite_original", file]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# --------------------------
# Determinazione anno / mese
# --------------------------
def get_year_month(metadata, file_path):
    if "DateTimeOriginal" in metadata:
        dt = datetime.strptime(metadata["DateTimeOriginal"], "%Y:%m:%d %H:%M:%S")
        return dt.year, dt.month

    # fallback EXIF
    date_str = run_exiftool(["-DateTimeOriginal", "-s", "-s", "-s", file_path]).strip()
    if date_str:
        dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        return dt.year, dt.month

    return "unknown", "unknown"


# --------------------------
# File da elaborare
# --------------------------
def collect_files(input_dir):
    all_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if not file.endswith(".json"):
                all_files.append((root, file))
    return all_files


# --------------------------
# Process principale
# --------------------------
def process_takeout(input_dir, output_dir):
    all_files = collect_files(input_dir)
    print(f"📂 Trovati {len(all_files)} file da processare.\n")

    for root, file in tqdm(all_files, desc="Processando file", unit="file"):
        path = os.path.join(root, file)
        base, ext = os.path.splitext(file)

        # 1) cerca il json
        json_metadata = find_json_metadata(root, base, ext)

        # 2) leggi EXIF
        exif_data = read_exif(path)

        # 3) merge dati
        merged_metadata = merge_metadata(exif_data, json_metadata)

        # 4) classificazione: galleria / archiviate / eliminate
        is_archived = json_metadata.get("archived") is True
        is_deleted = json_metadata.get("trashed") is True or json_metadata.get("deleted") is True

        if is_deleted:
            target_dir = os.path.join(output_dir, "eliminate")
        elif is_archived:
            target_dir = os.path.join(output_dir, "archiviate")
        else:
            year, month = get_year_month(merged_metadata, path)
            month = str(month).zfill(2)
            target_dir = os.path.join(output_dir, str(year), month)

        os.makedirs(target_dir, exist_ok=True)

        # 5) copia file
        out_path = os.path.join(target_dir, file)
        shutil.copy2(path, out_path)

        # 6) scrivi EXIF
        write_exif(out_path, merged_metadata)


# --------------------------
# MAIN
# --------------------------
if __name__ == "__main__":
    print("=== Google Takeout → Immich Converter ===\n")

    input_dir = input("📂 Inserisci il percorso della cartella sorgente (Takeout): ").strip()
    while not os.path.isdir(input_dir):
        print("❌ Errore: cartella non valida. Riprova.\n")
        input_dir = input("📂 Cartella Takeout: ").strip()

    output_dir = input("📁 Inserisci la cartella di destinazione: ").strip()
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("\n▶️ Conversione in corso...\n")
    process_takeout(input_dir, output_dir)

    print("\n🎉 Finito! File organizzati in:")
    print(output_dir)
