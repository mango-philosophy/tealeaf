from typing import Any

class LowerCase(dict):

    def __init__(self, **kws):
        for key, value in kws.items():
            self[key] = value

    def __setitem__(self, key, value):
        super().__setitem__(key.lower(), value)
    
    def __getitem__(self, __key: Any) -> Any:
        return super().__getitem__(__key.lower())
    
    def __delitem__(self, __key: Any) -> None:
        return super().__delitem__(__key.lower())

    def update(self, data: dict):
        return super().update({k.lower(): v for k, v in data.items()})
    
class Headers(LowerCase):
    pass