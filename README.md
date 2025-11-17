# 📸 Google Takeout Fixer → Immich Ready

### *Simple tool to fix Google Photos Takeout and merge JSON metadata with images & videos*

Google Takeout exports all your Google Photos, but the structure and
metadata are often messy: - JSON metadata files are separated from the
media\
- Some metadata filenames are truncated or inconsistent\
- EXIF data is missing or incomplete\
- Deleted or archived items are mixed with your main library\
- Many tools (like **Immich**) need clean EXIF timestamps to sort files
correctly

**This tool solves all of that automatically.**

## 🚀 What this tool does

This script cleans and restructures your Google Photos Takeout export,
merging all available metadata and preparing your library for migration
to any cloud or self-hosted photo service --- **especially Immich**.

### ✔ Features

-   **Merges JSON metadata into EXIF** (timestamps, titles,
    descriptions, GPS, etc.)

-   **Matches supplemental metadata files**, even if:

    -   filenames don't match exactly\
    -   `.suppl` or `.supplemental-metadata` extensions are used\
    -   filenames are truncated (Google Takeout bug)

-   **Reads existing EXIF** and merges non-conflicting values

-   **Rebuilds your library** into:

        /YYYY/MM/file.jpg
        /archiviate/file.jpg
        /eliminate/file.jpg

-   Fully **compatible with Immich**, so all dates, locations and info
    appear correctly.

-   Works with **photos and videos**

-   **Non-destructive**: your Takeout folder is untouched.

-   Supports Windows, macOS, Linux (requires `exiftool`)

## 📂 Folder output example

    output/
     ├── 2021/
     │    ├── 01/
     │    ├── 02/
     │    └── ...
     ├── 2022/
     │    └── 07/
     ├── archiviate/
     └── eliminate/

## 🛠 Requirements

-   **Python 3.8+**
-   **exiftool** installed

## ▶️ How to use

1.  Extract your Google Takeout ZIPs\
2.  Run the script\
3.  Insert the path to your Takeout root folder\
4.  Insert the output path\
5.  Wait for processing\
6.  Upload the output folder into **Immich** or any other system

## 💡 Why this exists

Google Takeout is notoriously messy: inconsistent metadata files,
missing EXIF, archived/deleted items mixed together, and filenames that
don't match their JSON metadata.

I built this tool specifically to fix those issues and produce a
**clean, structured, metadata-complete library** ready for **Immich
self-hosted**.

## ⚠️ Notes

-   **Your Takeout files are never modified** --- the script writes new
    copies only.
-   Some metadata fields (like face recognition) are not supported by
    Google Takeout and cannot be restored.
-   Videos have limited EXIF support, but timestamps are still applied
    via Immich-readable fields.

## 📬 Contribute

Feel free to open issues or submit improvements --- this project was
born to help anyone escaping Google Photos.
