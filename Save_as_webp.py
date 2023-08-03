import numpy as np
from PIL import Image
from datetime import datetime
import folder_paths
import os
import json

# by Kaharos94
# https://github.com/Kaharos94/ComfyUI-Saveaswebp
# comfyUI node to save an image in webp format
# Update by dimtoneff
# https://github.com/dimtoneff/ComfyUI-Saveaswebp

class Save_as_webp:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(s):
        return {"required": 
                    {"images": ("IMAGE", ),
                    "filename_prefix": ("STRING", {"default": "%date%/Image"}),
                    "mode":(["lossy","lossless"],),
                    "compression":("INT", {"default": 80, "min": 1, "max": 100, "step": 1},),
                    "save_jpg": (["disabled", "enabled"], {"default": "disabled"}),
                    "save_exif": (["disabled", "enabled"], {"default": "enabled"}),
                    "save_to": (["output", "input"], {"default": "output"})
                    },
                "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
                }

    RETURN_TYPES = ()
    FUNCTION = "Save_as_webp"

    OUTPUT_NODE = True

    CATEGORY = "image"

    def Save_as_webp(self, mode , compression, images, filename_prefix, prompt=None, extra_pnginfo=None, save_jpg="disabled", save_exif="enabled", save_to="output" ):
        def map_filename(filename):
            prefix_len = len(os.path.basename(filename_prefix))
            prefix = filename[:prefix_len + 1]
            try:
                digits = int(filename[prefix_len + 1:].split('_')[0])
            except:
                digits = 0
            return (digits, prefix)

        def compute_vars(input):
            input = input.replace("%width%", str(images[0].shape[1]))
            input = input.replace("%height%", str(images[0].shape[0]))
            input = input.replace("%date%", datetime.now().strftime("%Y-%m-%d"))
            return input
        
        match save_to:
            case "input":
                output_dir = folder_paths.get_input_directory()
                filename_prefix = "output-%date%"
            case _:
                output_dir = folder_paths.get_output_directory()

        filename_prefix = compute_vars(filename_prefix)

        subfolder = os.path.dirname(os.path.normpath(filename_prefix))
        filename = os.path.basename(os.path.normpath(filename_prefix))

        full_output_folder = os.path.join(output_dir, subfolder)

        try:
            counter = max(filter(lambda a: a[1][:-1] == filename and a[1][-1] == "_", map(map_filename, os.listdir(full_output_folder))))[0] + 1
        except ValueError:
            counter = 1
        except FileNotFoundError:
            os.makedirs(full_output_folder, exist_ok=True)
            counter = 1

        results = list()
        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            workflowmetadata = str()
            promptstr = str()
            imgexif = img.getexif() #get the (empty) Exif data of the generated Picture
            
            if save_exif == "enabled":
                if prompt is not None:
                    promptstr="".join(json.dumps(prompt)) #prepare prompt String
                    imgexif[0x010f] ="Prompt:"+ promptstr #Add PromptString to EXIF position 0x010f (Exif.Image.Make)
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        workflowmetadata += "".join(json.dumps(extra_pnginfo[x]))
                imgexif[0x010e] = "Workflow:"+ workflowmetadata #Add Workflowstring to EXIF position 0x010e (Exif.Image.ImageDescription)
            
            file = f"{filename}_{counter:05}_"
            if mode =="lossless":
                boolloss = True
            if mode =="lossy":
                boolloss = False
            

            img.save(os.path.join(full_output_folder, file + ".webp"), method=6 , exif=imgexif, lossless=boolloss , quality=compression) #Save as webp - options to be determined
            if save_jpg =="enabled":
                img.save(os.path.join(full_output_folder, file + ".jpeg"), exif=imgexif, quality=compression) #Save as jpeg
            
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            });
            counter += 1

        return { "ui": { "images": results } }
NODE_CLASS_MAPPINGS = {
    "Save_as_webp": Save_as_webp
}
