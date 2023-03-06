import gradio as gr
import modules.sd_samplers
import modules.scripts as scripts
from modules import shared
import json
import os
import shutil
from pprint import pprint
from modules.ui import gr_show
from collections import namedtuple
from pathlib import Path

update_flag = "preset_manager_update_check"

presets_config_target = "presets.json"

file_path = scripts.basedir() # file_path is basedir
scripts_path = os.path.join(file_path, "scripts")
path_to_update_flag = os.path.join(scripts_path, update_flag)
is_update_available = False
if os.path.exists(path_to_update_flag):
    is_update_available = True
                    
class PresetManager(scripts.Script):

    BASEDIR = scripts.basedir()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.compinfo = namedtuple("CompInfo", ["component", "label", "elem_id", "kwargs"])

        self.settings_file = "presets.json"

        self.txt2img_component_ids = [
            "txt2img_prompt",
            "txt2img_neg_prompt",
            "txt2img_sampling",
            "txt2img_steps",
            "txt2img_restore_faces",
            "txt2img_tiling",
            "txt2img_enable_hr",
            "txt2img_hr_upscaler",
            "txt2img_hires_steps",
            "txt2img_denoising_strength",
            "txt2img_hr_scale",
            "txt2img_hr_resize_x",
            "txt2img_hr_resize_y",
            "txt2img_width",
            "txt2img_height",
            "txt2img_batch_count",
            "txt2img_batch_size",
            "txt2img_cfg_scale",
        ]

        self.txt2img_component_map = {k: None for k in self.txt2img_component_ids}

        self.txt2img_config_presets = {
            "Default": {},
            "Low quality ------ 512x512, steps: 10, batch size: 8, DPM++ 2M Karras": {
                "txt2img_sampling": "DPM++ 2M Karras",
                "txt2img_steps": 10,
                "txt2img_width": 512,
                "txt2img_height": 512,
                "txt2img_batch_count": 1,
                "txt2img_batch_size": 8,
                "txt2img_cfg_scale": 7,
            },
        }

    def fakeinit(self, *args, **kwargs):
        self.elm_prfx = "quick_preset"

        if self.is_txt2img:
            PresetManager.t2i_preset_dropdown = gr.Dropdown(
                label="",
                choices=list(self.txt2img_config_presets.keys()),
                render = False,
                elem_id=f"{self.elm_prfx}_preset_dd"
            )
        self.save_as     = gr.Text(render=False, label="Save", elem_id=f"{self.elm_prfx}_save")
        self.save_button = gr.Button(value="💾", variant="secondary", render=False, visible=True, elem_id=f"{self.elm_prfx}_save")

    def title(self):
        return "Quick Preset"
    
    def show(self, is_img2img):
        self.fakeinit()
        return scripts.AlwaysVisible
    
    def after_component(self, component, **kwargs):

        self.component_map = self.txt2img_component_map
        self.component_ids = self.txt2img_component_ids

        if component.elem_id in self.component_map:
            self.component_map[component.elem_id] = component

        if component.elem_id == "txt2img_generation_info_button":
            for component_name, component in self.component_map.items():
                if component is None:
                    print(f"[ERROR][Config-Presets] The component '{component_name}' no longer exists in the Web UI. Try updating the Config-Presets extension. This extension will not work until this issue is resolved.")
                    return

            # Mark components with type "index" to be transform
            self.index_type_components = []
            for component in self.component_map.values():
                if getattr(component, "type", "No type attr") == "index":
                    self.index_type_components.append(component.elem_id)
            self._ui()

        if component.elem_id == "txt2img_clear_prompt":
            PresetManager.t2i_preset_dropdown.render()

        if component.elem_id == "txt2img_styles":
            self.save_as.render()
            self.save_button.render()

    def preset_dropdown_change(self, selector, *components):
        config_preset = self.txt2img_config_presets[selector]
        current_components = dict(zip(self.component_map.keys(), components))
        current_components.update(config_preset)

        for component_name, component_value in current_components.items():
            if component_name in self.index_type_components and type(component_value) == int:
                current_components[component_name] = self.component_map[component_name].choices[component_value]

        return list(current_components.values())

    def _ui(self):
        components = list(self.component_map.values())
        PresetManager.t2i_preset_dropdown.change(
            fn = self.preset_dropdown_change,
            inputs = [PresetManager.t2i_preset_dropdown, *components],
            outputs = components
        )
        self.save_as.change(
            fn = lambda x: gr.update(variant = "primary" if bool(x) else "secondary"),
            inputs = self.save_as,
            outputs = self.save_button
        )
        self.save_button.click(
            fn=None,
            inputs=[],
            outputs=[]
        )