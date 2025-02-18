import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
from openai import OpenAI
from PIL import Image 


class ImageVariationApp:
    """
    A GUI application to generate variations of an image using OpenAI's DALLE-2 API.
    The program allows users to select an image, specify the number of variations,
    and save the generated images to a specified directory.
    """

    def __init__(self, root):
        """
        Initialize the application.

        Args:
            root (tk.Tk): The root window for the application.
        """
        self.root = root
        self.root.title("Image Variation Generator")
        self.root.geometry("400x290")  # Set window size
        self.root.resizable(False, False)  # Disable window resizing

        # Initialize OpenAI client
        self.client = OpenAI()

        # Initialize file and directory paths
        self.file_path = None  # Path to the selected image file
        self.output_directory = None  # Path to the output directory

        # Initialize rate-limiting variables
        self.request_timestamps = []  # Stores timestamps of recent API requests

        # Set up the UI components
        self.setup_ui()

    def setup_ui(self):
        """
        Set up the user interface components.
        """
        # Main container for UI elements
        self.main_frame = tk.Frame(self.root, padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Button to select an image file
        self.select_file_button = tk.Button(
            self.main_frame, text="Select Image File", command=self.select_file, width=20
        )
        self.select_file_button.grid(row=0, column=0, pady=5, sticky=tk.W)

        # Label to display the selected file status
        self.file_label = tk.Label(self.main_frame, text="No file selected", fg="gray")
        self.file_label.grid(row=0, column=1, pady=5, sticky=tk.W)

        # Button to select the output directory
        self.select_dir_button = tk.Button(
            self.main_frame, text="Select Output Directory", command=self.select_directory, width=20
        )
        self.select_dir_button.grid(row=1, column=0, pady=5, sticky=tk.W)

        # Label to display the selected directory status
        self.dir_label = tk.Label(self.main_frame, text="No directory selected", fg="gray")
        self.dir_label.grid(row=1, column=1, pady=5, sticky=tk.W)

        # Label and entry for the number of variations
        self.num_variations_label = tk.Label(self.main_frame, text="Number of Variations:")
        self.num_variations_label.grid(row=2, column=0, pady=5, sticky=tk.W)

        self.num_variations_entry = tk.Entry(self.main_frame, width=10)
        self.num_variations_entry.grid(row=2, column=1, pady=5, sticky=tk.W)

        # Progress bar to show generation progress
        self.progress = ttk.Progressbar(self.main_frame, orient=tk.HORIZONTAL, length=300, mode="determinate")
        self.progress.grid(row=3, column=0, columnspan=2, pady=10)

        # Label to display the current status
        self.status_label = tk.Label(self.main_frame, text="Ready", fg="blue")
        self.status_label.grid(row=4, column=0, columnspan=2, pady=5)

        # Button to start generating variations
        self.start_button = tk.Button(
            self.main_frame, text="Generate Variations", command=self.generate_variations, width=20
        )
        self.start_button.grid(row=5, column=0, columnspan=2, pady=20)

        # Configure grid to center the button
        self.main_frame.grid_rowconfigure(5, weight=1)  # Allow row 5 to expand
        self.main_frame.grid_columnconfigure(0, weight=1)  # Center the button horizontally

    def select_file(self, max_size_mb = 4):
        """
        Open a file dialog to select an image file.
        Compress the image if it exceeds 4 MB.

        Args:
            max_size_mb (int): maximum allowed size in MB.
        """
        self.file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if self.file_path:
            file_size = os.path.getsize(self.file_path) / (1024 * 1024)  # Size in MB
            if file_size > max_size_mb:
                self.status_label.config(text="Compressing image...", fg="orange")
                self.root.update()  # Update the UI
                self.file_path = self.compress_image(self.file_path)  # Compress the image
                self.status_label.config(text="Image compressed", fg="green")
            self.file_label.config(text="File selected", fg="green")  # Update file label
        else:
            self.file_label.config(text="No file selected", fg="gray")  # Reset file label

    def select_directory(self):
        """
        Open a directory dialog to select the output directory.
        """
        self.output_directory = filedialog.askdirectory()
        if self.output_directory:
            self.dir_label.config(text="Directory selected", fg="green")  # Update directory label
        else:
            self.dir_label.config(text="No directory selected", fg="gray")  # Reset directory label

    def compress_image(self, image_path, max_size_mb=4, quality=85):
        """
        Compress an image to ensure it is under the specified size limit.

        Args:
            image_path (str): Path to the image file.
            max_size_mb (int): Maximum allowed size in MB.
            quality (int): Quality of the compressed image (1-100).

        Returns:
            str: Path to the compressed image.
        """
        img = Image.open(image_path)
        original_format = img.format

        # Save the image with reduced quality
        compressed_path = os.path.join(os.path.dirname(image_path), f"compressed_{os.path.basename(image_path)}")
        img.save(compressed_path, format=original_format, quality=quality)

        # Check if the file size is within the limit
        file_size = os.path.getsize(compressed_path) / (1024 * 1024)  # Size in MB
        if file_size > max_size_mb:
            # If still too large, resize the image iteratively
            while file_size > max_size_mb:
                width, height = img.size
                img = img.resize((int(width * 0.9), int(height * 0.9)), Image.Resampling.LANCZOS)  # Resize using LANCZOS
                img.save(compressed_path, format=original_format, quality=quality)
                file_size = os.path.getsize(compressed_path) / (1024 * 1024)

        return compressed_path

    def enforce_rate_limit(self, num_requests = 5):
        """
        Ensure no more than 5 requests are made in a 60-second window.
        If the limit is reached, wait until the oldest request falls outside the window.
        
        Args:
            num_requests (int): Number of requests per minute, based on OpenAI credits
        """
        current_time = time.time()

        # Remove timestamps older than 60 seconds
        self.request_timestamps = [t for t in self.request_timestamps if current_time - t < 60]

        # If 5 or more requests have been made in the last 60 seconds, wait
        if len(self.request_timestamps) >= num_requests:
            sleep_time = 60 - (current_time - self.request_timestamps[0])
            self.status_label.config(text=f"Rate limit reached. Waiting for {sleep_time:.1f} seconds...", fg="orange")
            self.root.update()  # Update the UI
            time.sleep(sleep_time)
            # Update timestamps after waiting
            self.request_timestamps = self.request_timestamps[1:]

        # Record the current request timestamp
        self.request_timestamps.append(current_time)

    def reset_ui(self):
        """
        Reset the UI to its initial state.
        """
        self.file_path = None
        self.output_directory = None
        self.file_label.config(text="No file selected", fg="gray")
        self.dir_label.config(text="No directory selected", fg="gray")
        self.num_variations_entry.delete(0, tk.END)
        self.progress["value"] = 0
        self.status_label.config(text="Ready", fg="blue")
        self.select_file_button.config(state=tk.NORMAL)
        self.select_dir_button.config(state=tk.NORMAL)
        self.start_button.config(state=tk.NORMAL)

    def generate_variations(self):
        """
        Generate variations of the selected image using OpenAI's API.
        Save the generated images to the specified output directory.
        """
        try:
            # Validate the number of variations
            repetitions = int(self.num_variations_entry.get())
            if repetitions <= 0:
                messagebox.showerror("Input Error", "Please enter a valid number greater than 0.")
                return
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number for variations.")
            return

        # Validate file and directory selection
        if not self.file_path:
            messagebox.showerror("Input Error", "Please select an image file.")
            return

        if not self.output_directory:
            messagebox.showerror("Input Error", "Please select an output directory.")
            return

        # Disable buttons during processing
        self.select_file_button.config(state=tk.DISABLED)
        self.select_dir_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.DISABLED)
        self.status_label.config(text="Processing...", fg="blue")
        self.progress["value"] = 0
        self.root.update()  # Update the UI

        try:
            image_name = os.path.basename(self.file_path)
            images_created = 0

            # Generate variations in batches of up to 5
            while images_created < repetitions:
                self.enforce_rate_limit()  # Enforce rate limiting

                # Determine how many images to request in this batch (max 5 per request)
                n_value = min(5, repetitions - images_created)

                with open(self.file_path, "rb") as file:
                    response = self.client.images.create_variation(
                        image=file,
                        n=n_value,
                        size="1024x1024"
                    )

                # Save the generated variations
                for i in range(n_value):
                    image_url = response.data[i].url
                    img_data = requests.get(image_url).content
                    final_path = os.path.join(self.output_directory, f"regen{images_created + 1}_{image_name}")
                    with open(final_path, 'wb') as handler:
                        handler.write(img_data)

                    print(f"Image {images_created + 1} created: {final_path}")
                    images_created += 1
                    self.progress["value"] = (images_created / repetitions) * 100
                    self.status_label.config(text=f"Generated {images_created}/{repetitions} images", fg="blue")
                    self.root.update()  # Update the UI

            # Notify the user of successful completion
            self.status_label.config(text="Variations generated successfully!", fg="green")
            messagebox.showinfo("Success", "Variations generated successfully!")
            self.reset_ui()  # Reset the UI after successful generation

        except Exception as e:
            # Handle errors and notify the user
            print(f"Error: {e}")
            self.status_label.config(text=f"Error: {e}", fg="red")
            messagebox.showerror("Error", f"An error occurred while processing: {e}")

        finally:
            # Re-enable buttons after processing
            self.select_file_button.config(state=tk.NORMAL)
            self.select_dir_button.config(state=tk.NORMAL)
            self.start_button.config(state=tk.NORMAL)
            self.progress["value"] = 0


if __name__ == "__main__":
    # Create the main application window
    root = tk.Tk()
    app = ImageVariationApp(root)
    root.mainloop()