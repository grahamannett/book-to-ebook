import os
import subprocess

import img2pdf
from PIL import Image

# prefer to user preview or PIL for time being, seems better than img2pdf


def convert_images_to_pdf(input_folder, output_pdf):
    """Convert all PNG files in the input folder to a single PDF."""
    # Get all PNG files and sort them
    png_files = sorted([os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith(".png")])

    if not png_files:
        print("No PNG files found in the input folder!")
        return

    print(f"Found {len(png_files)} PNG files")

    try:
        # Convert to PDF using img2pdf
        with open(output_pdf, "wb") as f:
            f.write(img2pdf.convert(png_files))

        print(f"\nSuccessfully created PDF: {output_pdf}")
        print(f"Total pages: {len(png_files)}")

    except Exception as e:
        print(f"Error creating PDF: {str(e)}")


def main():
    # Install required package if not present
    try:
        import img2pdf
    except ImportError:
        print("img2pdf is not installed. Installing required package...")
        subprocess.run(["pip3", "install", "img2pdf"])
        print("Package installed. Please run the script again.")
        exit()

    # Define input folder and output PDF name
    input_folder = "kindle_screenshots_cropped"  # Your cropped screenshots folder
    output_pdf = "combined_book.pdf"  # Name of the output PDF

    print(f"Converting images from {input_folder} to {output_pdf}")
    convert_images_to_pdf(input_folder, output_pdf)


if __name__ == "__main__":
    main()
