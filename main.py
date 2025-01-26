from openai import OpenAI
import requests
import os
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox


class ImageVariationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Variation Generator")

        # OpenAI client setup
        self.client = OpenAI()

        # File selection
        self.file_path = None
        self.output_directory = None
        self.repetitions = 0

        # Set up the UI components
        self.setup_ui()
        self.num_variations_entry = None
        self.num_variations_label = None
        self.select_dir_button = None
        self.select_file_button = None
        self.start_button = None

    # name: setup_ui
    # function: display a UI to get file directory, file to create variations of, and number of variations from the user
    # inputs: self
    def setup_ui(self):
        # Select image file
        self.select_file_button = tk.Button(self.root, text="Select Image File", command=self.select_file)
        self.select_file_button.pack(pady=10)

        # Select output directory
        self.select_dir_button = tk.Button(self.root, text="Select Output Directory", command=self.select_directory)
        self.select_dir_button.pack(pady=10)

        # Number of variations input
        self.num_variations_label = tk.Label(self.root, text="Number of Variations:")
        self.num_variations_label.pack(pady=5)
        self.num_variations_entry = tk.Entry(self.root)
        self.num_variations_entry.pack(pady=5)

        # Start button
        self.start_button = tk.Button(self.root, text="Generate Variations",
                                      command=self.generate_variations)
        self.start_button.pack(pady=20)

    # name: select_file
    # function: open a dialog to select a png image file
    # inputs: self
    def select_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png")])

        if self.file_path:
            print(f"Selected file: {self.file_path}")
        else:
            print("No file selected.")

    # name: select_directory
    # function: open a dialog to select the output directory
    # inputs: self
    def select_directory(self):
        self.output_directory = filedialog.askdirectory()

        if self.output_directory:
            print(f"Selected output directory: {self.output_directory}")
        else:
            print("No directory selected.")

    # name: generate_variations
    # function: generate variations of the image selected by the user
    # inputs: self
    def generate_variations(self):
        # validate number of variations
        try:
            self.repetitions = int(self.num_variations_entry.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number for variations.")
            return

        # validate image file selection
        if not self.file_path:
            messagebox.showerror("Input Error", "Please select an image file.")
            return

        # validate output directory selection
        if not self.output_directory:
            messagebox.showerror("Input Error", "Please select an output directory.")
            return

        try:
            image_name = os.path.basename(self.file_path)
            images_created = 0

            while images_created < self.repetitions:
                # Determine how many images to request in this batch (max 5 per request)
                n_value = min(5, self.repetitions - images_created)

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

                # Pause for rate limit if necessary
                if n_value == 5:
                    print("Image per minute limit reached, pausing 60 seconds.")
                    time.sleep(60)

            # return dialog upon completion
            messagebox.showinfo("Success", "Variations generated successfully!")

        # broad error handling
        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"An error occurred while processing: {e}")


# initialize tkinter
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageVariationApp(root)
    root.mainloop()
