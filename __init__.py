from .nodes.webhook import WebhookImage

NODE_CLASS_MAPPINGS = {
    "Notif-Webhook": WebhookImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Notif-Webhook": "WebhookImage",
}

WEB_DIRECTORY = "./web"
