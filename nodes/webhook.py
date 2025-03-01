import requests
import json
import os
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import numpy as np
from datetime import datetime
import folder_paths
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebhookImage:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = 'output'
        self.prefix_append = ''
 
    
    @classmethod
    def INPUT_TYPES(cls):
        """
        Defines the input types for the node.
        
        Returns:
            dict: A dictionary specifying required and hidden inputs.
        """
        return {
            "required": {
                'images': ('IMAGE', ),
                "webhook_url": ("STRING", {'default': '<yourwebhook>'}),
                "verify_ssl": ("BOOLEAN", {"default": True}),
                "safe_prompt": (["enable", "disable"], {"default": "disable"}),
                "notification_text": ('STRING', {'default': 'Your image is ready.'}),
                "json_format": ('STRING', {'default': '{"text": "<notification_text>"}'}),
                "send_notification": (["enable", "disable"], {"default": "disable"}),
                "send_image": (["enable", "disable"], {"default": "disable"}),
                "timeout": ('FLOAT', {'default': 3, 'min': 0, 'max': 60}),
                'image_preview': (['disabled', 'enabled'], {'default': 'enabled'}),
            },
			"optional": {
                    "positive_text_opt": ("STRING", {"forceInput": True}),
					"negative_text_opt": ("STRING", {"forceInput": True}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    FUNCTION = 'hookImage'
    OUTPUT_NODE = True
    RETURN_TYPES = tuple()
    CATEGORY = "notifications"

    @staticmethod
    def sendTxtMessage( webhook_url, notification_text, json_format, timeout, verify_ssl ):
        """
        handles sending text message to the webhook
        
        Args:
            webhook_url (str): The webhook URL.
            notification_text (str): The notification text.
            json_format (str): The JSON format for the message.
            timeout (float): The request timeout.
            verify_ssl (bool): Whether to verify SSL certificates.
        """
        payload = json_format.replace("<notification_text>", notification_text)
        payload = json.loads(payload)
        try:
            res = requests.post(webhook_url, json=payload, timeout=timeout, verify=verify_ssl)
            res.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to send text message: {e}")
            raise

    def hookImage(self, 
                images, 
                webhook_url, 
                notification_text, 
                json_format, 
                timeout, 
                verify_ssl, 
                negative_text_opt=None, 
                positive_text_opt=None, 
                extra_pnginfo=None, 
                prompt=None, 
                safe_prompt="disable", 
                image_preview="disable", 
                send_notification="disable",
                send_image="disable"
                ):
        counter = 1
        
        
        results = list()
        
        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            
            metadata = PngInfo()
            metadata.add_text("webhook_url", webhook_url )
            metadata.add_text("notification_text", notification_text)
            
            if prompt is not None:
                if safe_prompt == 'enable':
                    metadata.add_text("prompt", json.dumps(prompt))
            
            if positive_text_opt is not None:
                metadata.add_text("positive_text_opt", json.dumps(positive_text_opt))
            if negative_text_opt is not None:
                metadata.add_text("negative_text_opt", json.dumps(negative_text_opt))
            if extra_pnginfo is not None:
                for x in extra_pnginfo:
                    metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            timestamp = datetime.now().strftime('%c') 
            file = f"telegram_notification_{counter:05}_{timestamp}.png"
            
            image_path = os.path.join(self.output_dir, file)
            img.save(image_path, format="PNG", pnginfo=metadata)
            
            results.append({ 'filename': file, 'subfolder': '', 'type': self.type})
            counter += 1
            
            # do we send the image
            if send_image == 'enable':
                try:
                    with open(image_path, 'rb') as image_file:
                        files = {
                            'file': ('photo', image_file, 'image/png')
                        }
                
                        res = requests.post( webhook_url, files=files, timeout=timeout, verify=verify_ssl)
                        res.raise_for_status()
                        logger.info("Image posted successfully!")
                    
                except OSError as e:
                    logger.error(f"An error occurred while sending: {e}")
                else:
                    if send_notification == 'enable':
                        WebhookImage.sendTxtMessage(  webhook_url, notification_text, json_format, timeout, verify_ssl)
            else:    
                # maybe only send the message        
                if send_notification == 'enable':
                    WebhookImage.sendTxtMessage(  webhook_url, notification_text, json_format, timeout, verify_ssl)
            

        if image_preview == 'disabled':
            results = list()
            
        return { 'ui': { 'images': results } }
