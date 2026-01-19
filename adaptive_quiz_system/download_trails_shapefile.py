#!/usr/bin/env python3
"""
Script to download the hiking trails shapefile.

This script automatically downloads the French hiking trails shapefile
from data.gouv.fr and extracts it to the data/source/ directory to be used
by the trail recommendation system.

Usage:
    python download_trails_shapefile.py

The downloaded shapefile will be used by backend/init_db.py to load
trails into the database.
"""
import requests
import zipfile
import os
from pathlib import Path

# Dataset URL on data.gouv.fr
DATASET_URL = "https://www.data.gouv.fr/api/1/datasets/itineraires-de-randonnee-dans-openstreetmap/"
OUTPUT_DIR = Path(__file__).parent / "data" / "source"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_download_url():
    """Get the direct download URL from the dataset API"""
    try:
        response = requests.get(DATASET_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Look for shapefile resources
        resources = data.get("resources", [])
        for resource in resources:
            if "shapefile" in resource.get("format", "").lower() or "shp" in resource.get("title", "").lower():
                return resource.get("url")
            # Also check for zip files that might contain shapefiles
            if resource.get("format", "").lower() == "zip":
                return resource.get("url")
        
        # If no shapefile found, return the first resource
        if resources:
            return resources[0].get("url")
        
        return None
    except Exception as e:
        print(f"Error fetching dataset info: {e}")
        return None

def download_file(url, output_path):
    """Download a file from URL"""
    print(f"Downloading from: {url}")
    print(f"Output: {output_path}")
    
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rProgress: {percent:.1f}%", end='', flush=True)
    
    print(f"\nDownloaded {downloaded / (1024*1024):.2f} MB")

def extract_shapefile(zip_path, output_dir):
    """Extract shapefile components from zip"""
    print(f"\nExtracting {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Find shapefile components
        shapefile_files = [f for f in zip_ref.namelist() if f.endswith(('.shp', '.dbf', '.shx', '.prj'))]
        
        if not shapefile_files:
            print("No shapefile components found in zip. Listing all files:")
            for f in zip_ref.namelist()[:20]:
                print(f"  - {f}")
            return False
        
        # Extract to output directory
        for file in shapefile_files:
            zip_ref.extract(file, output_dir)
            # Rename to standard name if needed
            if 'hiking' in file.lower() or 'route' in file.lower():
                base_name = Path(file).stem
                ext = Path(file).suffix
                new_name = f"hiking_foot_routes_lineLine{ext}"
                old_path = output_dir / file
                new_path = output_dir / new_name
                if old_path.exists():
                    old_path.rename(new_path)
                    print(f"  Extracted and renamed: {new_name}")
                else:
                    print(f"  Extracted: {file}")
            else:
                print(f"  Extracted: {file}")
    
    return True

if __name__ == "__main__":
    print("=" * 70)
    print("DOWNLOADING HIKING TRAILS SHAPEFILE")
    print("=" * 70)
    print("\nThis script will download the shapefile from data.gouv.fr")
    print("and extract it to data/source/ to be used by init_db.py\n")
    
    print("Fetching dataset information from data.gouv.fr...")
    download_url = get_download_url()
    
    if not download_url:
        print("\n✗ Could not find download URL. Please download manually from:")
        print("https://www.data.gouv.fr/datasets/itineraires-de-randonnee-dans-openstreetmap/")
        exit(1)
    
    print(f"✓ Found download URL: {download_url}")
    
    # Download to zip file first
    zip_path = OUTPUT_DIR / "hiking_trails.zip"
    try:
        download_file(download_url, zip_path)
        
        # Extract shapefile
        if extract_shapefile(zip_path, OUTPUT_DIR):
            print("\n" + "=" * 70)
            print("✓ SUCCESS: Shapefile downloaded and extracted successfully!")
            print("=" * 70)
            print(f"\nFiles available in: {OUTPUT_DIR}")
            print("\nYou can now run:")
            print("  python backend/init_db.py")
            print("\nto load trails into the database.")
        else:
            print("\n⚠ Could not extract shapefile. Please check the zip file manually.")
        
        # Optionally remove zip file
        # zip_path.unlink()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print(f"Downloaded file is at: {zip_path}")
        print("You may need to extract it manually.")
        exit(1)
