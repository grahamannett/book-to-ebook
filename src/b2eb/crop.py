import argparse
import os
from pathlib import Path

import numpy as np

try:
    from PIL import Image
except ImportError:
    import subprocess

    print("Pillow is not installed. Installing required packages...")
    subprocess.run(["pip3", "install", "Pillow", "numpy"])
    print("Packages installed. Please run the script again.")
    exit()


def find_content_bounds(im):
    """Find the actual content boundaries by detecting the transition from background to content."""
    # Convert image to numpy array for faster processing
    img_array = np.array(im)

    # Convert to grayscale if image is RGB
    if len(img_array.shape) == 3:
        img_array = np.mean(img_array, axis=2)

    # Find rows and columns that aren't completely black or white
    threshold = 250  # Adjust this value if needed
    rows = np.where(np.mean(img_array, axis=1) < threshold)[0]
    cols = np.where(np.mean(img_array, axis=0) < threshold)[0]

    # Get the boundaries
    if len(rows) == 0 or len(cols) == 0:
        return None

    top = rows[0]
    bottom = rows[-1]
    left = cols[0]
    right = cols[-1]

    # Add a small padding
    padding = 10
    top = max(top - padding, 0)
    bottom = min(bottom + padding, img_array.shape[0])
    left = max(left - padding, 0)
    right = min(right + padding, img_array.shape[1])

    return (left, top, right, bottom)


def process_folder(
    input_folder,
    output_folder,
    manual_bounds=None,
    verify_idx: int | None = 0,
    output_pdf: bool = False,
    limit: int = None,
):
    """Process all PNG files in the input folder using specified or auto-detected bounds."""
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    png_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith(".png")])
    if not png_files:
        print("No PNG files found in input folder")
        return

    first_image_path = os.path.join(input_folder, png_files[verify_idx or 0])
    # Determine bounds
    first_image = Image.open(first_image_path)
    if manual_bounds:
        bounds = manual_bounds
        print(f"Using manual bounds: {bounds}")
    else:
        bounds = find_content_bounds(first_image)
        if not bounds:
            print("Could not detect content bounds in first image")
            return

    if verify_idx is not None:
        cropped_image = first_image.crop(bounds)
        cropped_image.show()
        print(f"Detected bounds: {bounds}")
        print("Using these bounds for all images. Press Enter to continue or Ctrl+C to abort...")
        print(f"Input file: {first_image_path=}")
        user_input = input()
        if user_input.lower() == "q":
            print("Aborted by user.")
            return
    first_image.close()

    if limit:
        print(f"Limiting to {limit} files...")
        png_files = png_files[:limit]

    total_files = len(png_files)
    print(f"\nProcessing {total_files} PNG files...")

    images = []

    for i, filename in enumerate(png_files, 1):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, f"cropped_{filename}")

        try:
            with Image.open(input_path) as im:
                # Crop image using the bounds from first image
                cropped = im.crop(bounds)
                # Save cropped image with original quality
                cropped.save(output_path, "PNG", quality=100)
                print(f"[{i}/{total_files}] Successfully processed: {filename}")

                if output_pdf:
                    images.append(cropped)

        except Exception as e:
            print(f"[{i}/{total_files}] Error processing {filename}: {str(e)}")

    if output_pdf:
        pdf_filepath = os.path.join(output_folder, "all-cropped.pdf")
        pdf_file = images.pop(0)  # the rest of image files will be image_files[1:]
        pdf_file.save(pdf_filepath, save_all=True, append_images=images)
        print(f"Combined all cropped images into a PDF: {pdf_file=}")


def main():
    parser = argparse.ArgumentParser(description="Crop PNG images in a folder")
    parser.add_argument(
        "--bounds",
        type=int,
        nargs=4,
        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
        help="Manual bounds for cropping (left top right bottom)",
    )
    parser.add_argument(
        "--verify-idx",
        type=int,
        help="Verify the bounds by displaying the cropped image",
        dest="verify_idx",
        default=None,
    )
    parser.add_argument("--limit", type=int, help="Limit the number of images to process")
    parser.add_argument("--input", default="png", help="Input folder path (default: png)")
    parser.add_argument(
        "--output",
        default="output_cropped",
        help="Output folder path (default: output_cropped)",
    )
    parser.add_argument("--pdf", action="store_true", help="Combine cropped images into a PDF")
    args = parser.parse_args()

    print(f"Processing images from {args.input} to {args.output}")
    process_folder(args.input, args.output, args.bounds, args.verify_idx, args.pdf, limit=args.limit)
    print("\nProcessing complete!")


if __name__ == "__main__":
    main()
